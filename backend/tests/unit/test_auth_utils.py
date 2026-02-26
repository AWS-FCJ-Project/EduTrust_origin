from src.auth.auth_utils import generate_otp, hash_password, verify_password


def test_hash_and_verify_password():
    password = "MySuperSecretPassword123!"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_generate_otp():
    otp = generate_otp()

    assert isinstance(otp, str)
    assert len(otp) == 6
    assert otp.isdigit()
