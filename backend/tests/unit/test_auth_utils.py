from src.auth.auth_utils import generate_otp, hash_password, verify_password


def test_hash_and_verify_password():
    dummy_secret = "MySuperSecretString123!"
    hashed = hash_password(dummy_secret)

    assert hashed != dummy_secret
    assert verify_password(dummy_secret, hashed) is True
    assert verify_password("WrongString!", hashed) is False


def test_generate_otp():
    otp = generate_otp()

    assert isinstance(otp, str)
    assert len(otp) == 6
    assert otp.isdigit()
