import pytest

from src.contact_finder import (
    _is_noise_email,
    _select_best_email,
    _select_best_personal,
    _select_best_general,
    get_domain_from_url,
)


@pytest.mark.parametrize(
    "email,expected",
    [
        ("partnerships@brand.com", False),
        ("hello@brand.ai", False),
        ("noreply@brand.com", True),
        ("postmaster@brand.com", True),
        ("example@gmail.com", True),
        ("test@test.com", True),
        ("john.doe@example.com", True),
        ("foo@bar.png", True),
        ("user@brand.0", True),  # bad TLD
        ("abcdef0123456789ab@sentry.io", True),
        ("a@b.c", True),
        ("dolunay@dolunay.ai", False),
    ],
)
def test_is_noise_email(email, expected):
    assert _is_noise_email(email) is expected


def test_select_best_email_prefers_partnerships():
    pool = ["info@brand.com", "partnerships@brand.com", "hello@brand.com"]
    assert _select_best_email(pool) == "partnerships@brand.com"


def test_select_best_email_falls_back_to_first():
    # Hiçbiri PREFERRED_PREFIXES'e uymuyor → ilk dönüyor.
    pool = ["random@brand.com", "another@brand.com"]
    assert _select_best_email(pool) == "random@brand.com"


def test_select_best_personal_prefers_partnership_role():
    personal = [
        {"email": "ceo@brand.com", "name": "CEO Person", "position": "CEO"},
        {"email": "marketing@brand.com", "name": "M Person", "position": "Head of Marketing"},
    ]
    sel = _select_best_personal(personal)
    assert sel["email"] == "marketing@brand.com"


def test_select_best_general_prefers_partnerships_prefix():
    pool = ["info@brand.com", "partnerships@brand.com", "support@brand.com"]
    assert _select_best_general(pool) == "partnerships@brand.com"


@pytest.mark.parametrize(
    "url,expected_domain",
    [
        ("https://www.brand.com/contact", "brand.com"),
        ("brand.ai", "brand.ai"),
        ("https://sub.brand.io", "sub.brand.io"),
        ("", ""),
    ],
)
def test_get_domain_from_url(url, expected_domain):
    assert get_domain_from_url(url) == expected_domain
