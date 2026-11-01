from datetime import timedelta

import pytest

from app.core.security import create_access_token, decode_access_token, hash_password, verify_password


def test_password_hash_is_not_plaintext_and_verifies():
    password = "A-Strong-Test-Password-123!"
    stored_hash = hash_password(password)
    assert stored_hash != password
    assert stored_hash.startswith("$argon2")
    assert verify_password(password, stored_hash) is True
    assert verify_password("wrong-password", stored_hash) is False


def test_token_contains_user_subject_and_valid_claims():
    token = create_access_token("42")
    payload = decode_access_token(token)
    assert payload["sub"] == "42"
    assert payload["type"] == "access"
    assert "exp" in payload and "iss" in payload and "aud" in payload


def test_expired_token_is_rejected():
    token = create_access_token("42", expires_delta=timedelta(seconds=-1))
    with pytest.raises(ValueError):
        decode_access_token(token)


def test_tampered_token_is_rejected():
    token = create_access_token("42")
    with pytest.raises(ValueError):
        decode_access_token(token + "tampered")


def test_invalid_password_hash_returns_false():
    assert verify_password("some-password", "not-an-argon2-hash") is False
