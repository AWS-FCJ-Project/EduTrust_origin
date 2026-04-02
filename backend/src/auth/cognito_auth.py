from typing import Any

import boto3
import jwt
from botocore.exceptions import ClientError
from jwt import InvalidTokenError, PyJWKClient, PyJWKClientError
from src.app_config import app_config

COGNITO_GROUPS = {"admin", "teacher", "student"}


class CognitoAuthError(Exception):
    def __init__(self, message: str, status_code: int = 401):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class CognitoAuthService:
    def __init__(self) -> None:
        self.user_pool_id = (app_config.COGNITO_USER_POOL_ID or "").strip()
        self.app_client_id = (app_config.COGNITO_APP_CLIENT_ID or "").strip()
        self.region = (
            (app_config.COGNITO_REGION or "").strip()
            or (app_config.AWS_REGION or "").strip()
            or "ap-southeast-1"
        )
        self._jwk_client: PyJWKClient | None = None
        self._client = None

    @property
    def configured(self) -> bool:
        return bool(self.user_pool_id and self.app_client_id)

    @property
    def issuer(self) -> str:
        return f"https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}"

    @property
    def client(self):
        if self._client is None:
            client_kwargs = {"region_name": self.region}
            if app_config.AWS_ACCESS_KEY_ID and app_config.AWS_SECRET_ACCESS_KEY:
                client_kwargs.update(
                    {
                        "aws_access_key_id": app_config.AWS_ACCESS_KEY_ID,
                        "aws_secret_access_key": app_config.AWS_SECRET_ACCESS_KEY,
                    }
                )
            self._client = boto3.client("cognito-idp", **client_kwargs)
        return self._client

    def ensure_configured(self) -> None:
        if not self.configured:
            raise CognitoAuthError(
                "Cognito authentication is not configured on the backend.",
                status_code=500,
            )

    def _get_jwk_client(self) -> PyJWKClient:
        if self._jwk_client is None:
            self._jwk_client = PyJWKClient(f"{self.issuer}/.well-known/jwks.json")
        return self._jwk_client

    @staticmethod
    def _attrs_to_dict(attributes: list[dict[str, str]]) -> dict[str, str]:
        return {item["Name"]: item["Value"] for item in attributes}

    def get_user(self, email: str) -> dict[str, str] | None:
        self.ensure_configured()
        try:
            response = self.client.admin_get_user(
                UserPoolId=self.user_pool_id,
                Username=email,
            )
        except self.client.exceptions.UserNotFoundException:
            return None

        attrs = self._attrs_to_dict(response.get("UserAttributes", []))
        attrs["Username"] = response.get("Username", email)
        return attrs

    def set_user_password(self, email: str, password: str) -> None:
        self.ensure_configured()
        self.client.admin_set_user_password(
            UserPoolId=self.user_pool_id,
            Username=email,
            Password=password,
            Permanent=True,
        )

    def sync_user_group(
        self, email: str, target_group: str | None, current_group: str | None = None
    ) -> None:
        self.ensure_configured()
        normalized_target = (target_group or "").strip().lower()
        normalized_current = (current_group or "").strip().lower()

        if (
            normalized_current in COGNITO_GROUPS
            and normalized_current != normalized_target
        ):
            try:
                self.client.admin_remove_user_from_group(
                    UserPoolId=self.user_pool_id,
                    Username=email,
                    GroupName=normalized_current,
                )
            except self.client.exceptions.ResourceNotFoundException:
                pass
            except self.client.exceptions.UserNotFoundException:
                return

        if normalized_target in COGNITO_GROUPS:
            self.client.admin_add_user_to_group(
                UserPoolId=self.user_pool_id,
                Username=email,
                GroupName=normalized_target,
            )

    def ensure_user(
        self,
        email: str,
        password: str,
        *,
        name: str | None = None,
        role: str | None = None,
        email_verified: bool = True,
    ) -> dict[str, str]:
        self.ensure_configured()
        user = self.get_user(email)
        if user is None:
            attributes = [
                {"Name": "email", "Value": email},
                {
                    "Name": "email_verified",
                    "Value": "true" if email_verified else "false",
                },
            ]
            if name:
                attributes.append({"Name": "name", "Value": name})
            self.client.admin_create_user(
                UserPoolId=self.user_pool_id,
                Username=email,
                UserAttributes=attributes,
                MessageAction="SUPPRESS",
            )
        elif name:
            self.client.admin_update_user_attributes(
                UserPoolId=self.user_pool_id,
                Username=email,
                UserAttributes=[{"Name": "name", "Value": name}],
            )

        self.set_user_password(email, password)
        self.sync_user_group(email, role)
        return self.get_user(email) or {}

    def authenticate_user(self, email: str, password: str) -> dict[str, Any]:
        self.ensure_configured()
        try:
            response = self.client.initiate_auth(
                ClientId=self.app_client_id,
                AuthFlow="USER_PASSWORD_AUTH",
                AuthParameters={"USERNAME": email, "PASSWORD": password},
            )
        except self.client.exceptions.NotAuthorizedException as error:
            raise CognitoAuthError("Invalid credentials") from error
        except self.client.exceptions.UserNotFoundException as error:
            raise CognitoAuthError("Invalid credentials") from error
        except self.client.exceptions.UserNotConfirmedException as error:
            raise CognitoAuthError(
                "User account is not confirmed.",
                status_code=403,
            ) from error
        except self.client.exceptions.PasswordResetRequiredException as error:
            raise CognitoAuthError(
                "Password reset is required before logging in.",
                status_code=403,
            ) from error
        except ClientError as error:
            raise CognitoAuthError(
                "Unable to authenticate with Cognito.",
                status_code=500,
            ) from error

        return response.get("AuthenticationResult", {})

    def forgot_password(self, email: str) -> None:
        self.ensure_configured()
        try:
            self.client.forgot_password(ClientId=self.app_client_id, Username=email)
        except self.client.exceptions.UserNotFoundException:
            return
        except ClientError as error:
            if (
                error.response.get("Error", {}).get("Code")
                == "InvalidParameterException"
            ):
                return
            raise CognitoAuthError(
                "Unable to start password reset.",
                status_code=500,
            ) from error

    def confirm_forgot_password(
        self, email: str, confirmation_code: str, new_password: str
    ) -> None:
        self.ensure_configured()
        try:
            self.client.confirm_forgot_password(
                ClientId=self.app_client_id,
                Username=email,
                ConfirmationCode=confirmation_code,
                Password=new_password,
            )
        except (
            self.client.exceptions.CodeMismatchException,
            self.client.exceptions.ExpiredCodeException,
        ) as error:
            raise CognitoAuthError("Invalid or expired OTP", status_code=400) from error
        except ClientError as error:
            raise CognitoAuthError(
                "Unable to reset password.",
                status_code=500,
            ) from error

    def delete_user(self, email: str) -> None:
        self.ensure_configured()
        try:
            self.client.admin_delete_user(
                UserPoolId=self.user_pool_id,
                Username=email,
            )
        except self.client.exceptions.UserNotFoundException:
            return

    def verify_token(self, token: str) -> dict[str, Any]:
        self.ensure_configured()
        try:
            signing_key = self._get_jwk_client().get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self.app_client_id,
                issuer=self.issuer,
                options={"require": ["exp", "iat", "token_use"]},
            )
        except (PyJWKClientError, InvalidTokenError) as error:
            raise CognitoAuthError("Could not validate credentials") from error

        if claims.get("token_use") != "id":
            raise CognitoAuthError("Unsupported token type")

        return claims


cognito_auth_service = CognitoAuthService()
