from unittest.mock import MagicMock

import pytest
from src.auth.email_service import send_email


def test_send_email_success(mocker):
    mocker.patch("src.auth.email_service.app_config.EMAIL_SENDER", "sender@example.com")
    mocker.patch("src.auth.email_service.app_config.EMAIL_PASSWORD", "password123")

    mock_smtp_class = mocker.patch("src.auth.email_service.smtplib.SMTP")
    mock_smtp_instance = MagicMock()
    mock_smtp_class.return_value = mock_smtp_instance

    result = send_email("receiver@example.com", "Test Subject", "Test Body")

    assert result is True
    mock_smtp_class.assert_called_once()
    mock_smtp_instance.starttls.assert_called_once()
    mock_smtp_instance.login.assert_called_once_with(
        "sender@example.com", "password123"
    )
    mock_smtp_instance.sendmail.assert_called_once()
    mock_smtp_instance.quit.assert_called_once()


def test_send_email_missing_credentials(mocker):
    mocker.patch("src.auth.email_service.app_config.EMAIL_SENDER", "")
    mocker.patch("src.auth.email_service.app_config.EMAIL_PASSWORD", "")

    with pytest.raises(RuntimeError, match="Email credentials not set"):
        send_email("receiver@example.com", "Test Subject", "Test Body")


def test_send_email_smtp_error(mocker):
    mocker.patch("src.auth.email_service.app_config.EMAIL_SENDER", "sender@example.com")
    mocker.patch("src.auth.email_service.app_config.EMAIL_PASSWORD", "password123")

    mock_smtp_class = mocker.patch("src.auth.email_service.smtplib.SMTP")
    mock_smtp_class.side_effect = Exception("SMTP Connection Error")

    with pytest.raises(RuntimeError, match="Failed to send email"):
        send_email("receiver@example.com", "Test Subject", "Test Body")
