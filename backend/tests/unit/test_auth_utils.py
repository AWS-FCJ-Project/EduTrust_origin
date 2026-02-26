from src.auth.auth_utils import generate_otp, hash_password, verify_password


def test_hash_and_verify_password():
    plain_text = "MyTestStringXYZ123!"
    hashed = hash_password(plain_text)

    assert hashed != plain_text
    assert verify_password(plain_text, hashed) is True
    assert verify_password("WrongString!", hashed) is False


def test_generate_otp():
    otp = generate_otp()

    assert isinstance(otp, str)
    assert len(otp) == 6
    assert otp.isdigit()
