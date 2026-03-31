"""
Tele Satış CRM — Veri Temizleme Testleri
"""
import sys
import os

# Proje köküne path ekle
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_cleaner import clean_phone, clean_name, clean_email, clean_budget, clean_lead


def test_clean_phone():
    # Türk numarası
    assert clean_phone("905551234567") == "+90 555 123 4567"
    assert clean_phone("p:+905551234567") == "+90 555 123 4567"
    assert clean_phone("+90 555 123 4567") == "+90 555 123 4567"
    # Prefix temizleme
    assert clean_phone("p:905551234567") == "+90 555 123 4567"
    # Uluslararası
    assert clean_phone("447911123456") == "+447911123456"
    # Boş
    assert clean_phone("") == ""
    assert clean_phone(None) == ""
    print("✅ clean_phone testleri geçti")


def test_clean_name():
    assert clean_name("ahmet yılmaz") == "Ahmet Yılmaz"
    assert clean_name("MEHMET KURT") == "Mehmet Kurt"
    assert clean_name("  ali  ") == "Ali"
    assert clean_name("") == ""
    assert clean_name(None) == ""
    print("✅ clean_name testleri geçti")


def test_clean_email():
    assert clean_email("  Test@Gmail.COM  ") == "test@gmail.com"
    assert clean_email("user@example.com") == "user@example.com"
    assert clean_email("") == ""
    assert clean_email(None) == ""
    print("✅ clean_email testleri geçti")


def test_clean_budget():
    assert clean_budget("$0_-_$20") == "$0 - $20"
    assert clean_budget("$50 - $150") == "$50 - $150"
    assert clean_budget("$150+") == "$150+"
    assert clean_budget("invalid") == ""
    assert clean_budget("") == ""
    assert clean_budget(None) == ""
    print("✅ clean_budget testleri geçti")


def test_clean_lead():
    raw = {
        "full_name": "ahmet yılmaz",
        "email": "  AHMET@test.com  ",
        "phone_number": "p:+905551234567",
        "100%_otomatik_youtube_kanalı_açmak_için_yatırım_bütçeniz_nedir?": "$50_-_$150",
    }
    result = clean_lead(raw)
    assert result["clean_name"] == "Ahmet Yılmaz"
    assert result["clean_email"] == "ahmet@test.com"
    assert result["clean_phone"] == "+90 555 123 4567"
    assert result["clean_budget"] == "$50 - $150"
    assert result["raw"] == raw
    print("✅ clean_lead testleri geçti")


if __name__ == "__main__":
    test_clean_phone()
    test_clean_name()
    test_clean_email()
    test_clean_budget()
    test_clean_lead()
    print("\n🎉 Tüm testler başarılı!")
