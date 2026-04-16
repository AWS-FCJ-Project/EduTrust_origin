from src.auth.auth_utils import generate_otp, hash_password, verify_password


def test_hash_password_round_trip():
    hashed = hash_password("super-secret")

    assert hashed != "super-secret"
    assert verify_password("super-secret", hashed) is True


def test_verify_password_rejects_invalid_password():
    hashed = hash_password("super-secret")

    assert verify_password("wrong-password", hashed) is False


def test_generate_otp_returns_six_digit_string(monkeypatch):
    monkeypatch.setattr("src.auth.auth_utils.random.randint", lambda start, end: 123456)

    otp = generate_otp()

    assert otp == "123456"
    assert otp.isdigit()
    assert len(otp) == 6
