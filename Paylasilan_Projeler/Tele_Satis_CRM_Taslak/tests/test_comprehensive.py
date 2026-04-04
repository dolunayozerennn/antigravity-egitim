"""
Tele Satış CRM — Kapsamlı Test Paketi
Tüm modülleri test eder: sheets_reader, data_cleaner, notion_writer.

Testler:
  1. data_cleaner: telefon, isim, email, bütçe, timing, lead temizleme
  2. sheets_reader: _filter_recent_rows, restart recovery, normal polling
  3. notion_writer: WhatsApp link üretimi
  4. Uçtan uca: Sheet verisi → temizleme → Notion uyumluluğu
"""
import sys
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

# Proje köküne path ekle
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_cleaner import clean_phone, clean_name, clean_email, clean_budget, clean_timing, clean_lead
from sheets_reader import SheetsReader
from notion_writer import NotionWriter

# ═══════════════════════════════════════════════════════════════════
#  1. DATA CLEANER TESTLERI
# ═══════════════════════════════════════════════════════════════════

def test_clean_phone_standard():
    """Standart TR numaraları."""
    assert clean_phone("905551234567") == "+90 555 123 4567"
    assert clean_phone("p:+905551234567") == "+90 555 123 4567"
    assert clean_phone("+90 555 123 4567") == "+90 555 123 4567"
    assert clean_phone("p:905551234567") == "+90 555 123 4567"
    print("  ✅ clean_phone — standart formatlar")

def test_clean_phone_without_country_code():
    """Ülke kodu olmayan numaralar (bug fix: 13 Mart)."""
    assert clean_phone("5348970627") == "+90 534 897 0627"
    assert clean_phone("5461383982") == "+90 546 138 3982"
    assert clean_phone("05013304413") == "+90 501 330 4413"
    assert clean_phone("05393802102") == "+90 539 380 2102"
    print("  ✅ clean_phone — ülke kodsuz numaralar")

def test_clean_phone_090_prefix():
    """090 prefix temizleme."""
    assert clean_phone("0905321234567") == "+90 532 123 4567"
    print("  ✅ clean_phone — 090 prefix")

def test_clean_phone_edge_cases():
    """Uç durumlar."""
    assert clean_phone("") == ""
    assert clean_phone(None) == ""
    assert clean_phone("447911123456") == "+447911123456"  # Uluslararası
    assert clean_phone("p:+") == ""  # Sadece prefix
    assert clean_phone("abc") == ""  # Tamamen geçersiz
    print("  ✅ clean_phone — edge case'ler")

def test_clean_phone_real_sheet_data():
    """14 Mart sheet'ten gelen gerçek telefon verileri."""
    assert clean_phone("p:+905013304413") == "+90 501 330 4413"
    assert clean_phone("p:+905306643471") == "+90 530 664 3471"
    assert clean_phone("5393802102") == "+90 539 380 2102"
    assert clean_phone("p:+905349354990") == "+90 534 935 4990"
    assert clean_phone("5350515407") == "+90 535 051 5407"
    assert clean_phone("5316286159") == "+90 531 628 6159"
    assert clean_phone("05338222869") == "+90 533 822 2869"
    print("  ✅ clean_phone — gerçek 14 Mart verileri")

def test_clean_name():
    assert clean_name("ahmet yılmaz") == "Ahmet Yılmaz"
    assert clean_name("MEHMET KURT") == "Mehmet Kurt"
    assert clean_name("  ali  ") == "Ali"
    assert clean_name("duran/baris") == "Duran/baris"
    assert clean_name("selamiacet") == "Selamiacet"
    assert clean_name("") == ""
    assert clean_name(None) == ""
    print("  ✅ clean_name")

def test_clean_email():
    assert clean_email("  Test@Gmail.COM  ") == "test@gmail.com"
    assert clean_email("user@example.com") == "user@example.com"
    assert clean_email("") == ""
    assert clean_email(None) == ""
    print("  ✅ clean_email")

def test_clean_budget():
    assert clean_budget("$0_-_$20") == "$0 - $20"
    assert clean_budget("$20_-_$50") == "$20 - $50"
    assert clean_budget("$50 - $150") == "$50 - $150"
    assert clean_budget("$150+") == "$150+"
    assert clean_budget("invalid") == ""
    assert clean_budget("") == ""
    assert clean_budget(None) == ""
    print("  ✅ clean_budget")

def test_clean_timing():
    """Timing temizleme — Notion select uyumluluğu."""
    assert clean_timing("akşam_6'dan_sonra") == "Akşam 6'dan sonra"
    assert clean_timing("gün_içinde") == "Gün içinde"
    assert clean_timing("haftasonu") == "Haftasonu"
    assert clean_timing("aramayın,_mesaj_atın") == "Aramayın mesaj atın"
    assert clean_timing("Aramayın, mesaj atın") == "Aramayın mesaj atın"
    # Bilinmeyen değer → boş (Notion 400 hatası önlenir)
    assert clean_timing("random_deger") == ""
    assert clean_timing("") == ""
    assert clean_timing(None) == ""
    print("  ✅ clean_timing")

def test_clean_timing_real_data():
    """14 Mart sheet'ten gelen gerçek timing verileri."""
    # Bu veriler Meta form'dan alt çizgili geliyor
    assert clean_timing("akşam_6'dan_sonra") == "Akşam 6'dan sonra"
    assert clean_timing("gün_içinde") == "Gün içinde"
    assert clean_timing("aramayın,_mesaj_atın") == "Aramayın mesaj atın"
    print("  ✅ clean_timing — gerçek veriler")

def test_clean_lead_full():
    """Tam lead temizleme — sheet formatında."""
    raw = {
        "full_name": "ahmet yılmaz",
        "email": "  AHMET@test.com  ",
        "phone_number": "p:+905551234567",
        "100%_otomatik_youtube_kanalı_açmak_için_yatırım_bütçeniz_nedir?": "$50_-_$150",
        "size_ne_zaman_ulaşalım?": "akşam_6'dan_sonra",
    }
    result = clean_lead(raw)
    assert result["clean_name"] == "Ahmet Yılmaz"
    assert result["clean_email"] == "ahmet@test.com"
    assert result["clean_phone"] == "+90 555 123 4567"
    assert result["clean_budget"] == "$50 - $150"
    assert result["clean_timing"] == "Akşam 6'dan sonra"
    assert result["raw"] == raw
    print("  ✅ clean_lead — tam pipeline")

def test_clean_lead_empty_name_detection():
    """İsim boşsa lead atlanacağını doğrula."""
    raw = {
        "full_name": "",
        "email": "test@test.com",
        "phone_number": "5551234567",
    }
    result = clean_lead(raw)
    assert result["clean_name"] == ""  # main.py bunu atlar
    print("  ✅ clean_lead — boş isim tespiti")


# ═══════════════════════════════════════════════════════════════════
#  2. SHEETS READER TESTLERI
# ═══════════════════════════════════════════════════════════════════

def test_filter_recent_rows_basic():
    """Son 48 saat filtreleme — temel test."""
    now = datetime.now(timezone.utc)
    rows = [
        {"created_time": (now - timedelta(hours=1)).isoformat(), "full_name": "Yeni1"},
        {"created_time": (now - timedelta(hours=24)).isoformat(), "full_name": "Yeni2"},
        {"created_time": (now - timedelta(hours=47)).isoformat(), "full_name": "Sınırda"},
        {"created_time": (now - timedelta(hours=49)).isoformat(), "full_name": "Eski1"},
        {"created_time": (now - timedelta(days=7)).isoformat(), "full_name": "Eski2"},
    ]
    
    recent = SheetsReader._filter_recent_rows(rows, hours=48)
    names = [r["full_name"] for r in recent]
    
    assert "Yeni1" in names
    assert "Yeni2" in names
    assert "Sınırda" in names
    assert "Eski1" not in names
    assert "Eski2" not in names
    assert len(recent) == 3
    print("  ✅ _filter_recent_rows — temel filtreleme")

def test_filter_recent_rows_meta_format():
    """Meta'dan gelen ISO 8601 formatı (-05:00 offset)."""
    now = datetime.now(timezone.utc)
    # Meta lead'leri US Eastern timezone (-05:00) ile gelir
    from datetime import timezone as tz
    eastern = tz(timedelta(hours=-5))
    recent_time = (now - timedelta(hours=5)).astimezone(eastern).isoformat()
    old_time = (now - timedelta(days=5)).astimezone(eastern).isoformat()
    
    rows = [
        {"created_time": recent_time, "full_name": "Yeni"},
        {"created_time": old_time, "full_name": "Eski"},
    ]
    
    recent = SheetsReader._filter_recent_rows(rows, hours=48)
    assert len(recent) == 1
    assert recent[0]["full_name"] == "Yeni"
    print("  ✅ _filter_recent_rows — Meta timezone formatı (-05:00)")

def test_filter_recent_rows_no_created_time():
    """created_time olmayan satırlar atlanır."""
    rows = [
        {"full_name": "İsimsiz"},  # created_time yok
        {"created_time": "", "full_name": "Boş"},
        {"created_time": "geçersiz_tarih", "full_name": "Geçersiz"},
    ]
    
    recent = SheetsReader._filter_recent_rows(rows, hours=48)
    assert len(recent) == 0
    print("  ✅ _filter_recent_rows — eksik/geçersiz tarih")

def test_filter_recent_rows_empty():
    """Boş liste."""
    recent = SheetsReader._filter_recent_rows([], hours=48)
    assert len(recent) == 0
    print("  ✅ _filter_recent_rows — boş liste")

def test_get_new_rows_restart_recovery():
    """
    KRİTİK TEST: Restart sonrası son 48 saatteki lead'ler döndürülmeli.
    Bu test, 14 Mart'ta yaşanan bug'ın tekrar etmeyeceğini doğrular.
    """
    reader = SheetsReader()
    
    now = datetime.now(timezone.utc)
    
    # Simüle: Sheet'te 100 satır var, son 5'i son 48 saatte
    mock_rows = []
    for i in range(95):
        mock_rows.append({
            "created_time": (now - timedelta(days=10+i)).isoformat(),
            "full_name": f"Eski_{i}",
        })
    for i in range(5):
        mock_rows.append({
            "created_time": (now - timedelta(hours=i+1)).isoformat(),
            "full_name": f"Yeni_{i}",
        })
    
    # Mock get_all_rows
    with patch.object(reader, 'get_all_rows', return_value=mock_rows):
        # İlk çalıştırma (restart) — son 48 saatteki satırları döndürmeli
        result = reader.get_new_rows("test-tab")
        
        assert len(result) == 5, f"5 yeni satır bekleniyordu, {len(result)} geldi"
        for row in result:
            assert row["full_name"].startswith("Yeni_")
        
        # Başarıyla işlendi — state'i onayla
        reader.confirm_processed()
        
        # İkinci çalıştırma — yeni satır yoksa boş döndürmeli
        result2 = reader.get_new_rows("test-tab")
        assert len(result2) == 0
    
    print("  ✅ get_new_rows — restart recovery (KRİTİK)")

def test_get_new_rows_restart_no_recent():
    """Restart sonrası son 48 saatte veri yoksa boş dönmeli."""
    reader = SheetsReader()
    
    now = datetime.now(timezone.utc)
    mock_rows = [
        {"created_time": (now - timedelta(days=10)).isoformat(), "full_name": "Çok Eski"},
    ]
    
    with patch.object(reader, 'get_all_rows', return_value=mock_rows):
        result = reader.get_new_rows("test-tab")
        # Fallback: son 50 satır döner (1 satır var → 1 döner)
        # Duplikasyon kontrolü zaten var olanları atlayacak
        assert len(result) == 1
        reader.confirm_processed()
    
    print("  ✅ get_new_rows — restart ama yeni veri yok (fallback)")

def test_get_new_rows_normal_polling():
    """Normal polling — sadece yeni eklenen satırları döndürmeli."""
    reader = SheetsReader()
    
    now = datetime.now(timezone.utc)
    
    # İlk 10 satır (mevcut)
    initial_rows = [
        {"created_time": (now - timedelta(hours=i)).isoformat(), "full_name": f"Initial_{i}"}
        for i in range(10)
    ]
    
    # İlk okuma — restart recovery aktif (son 48 saattekiler gelir)
    with patch.object(reader, 'get_all_rows', return_value=initial_rows):
        reader.get_new_rows("test-tab")
        reader.confirm_processed()
    
    # 3 yeni satır ekleniyor
    new_rows = initial_rows + [
        {"created_time": now.isoformat(), "full_name": f"New_{i}"}
        for i in range(3)
    ]
    
    with patch.object(reader, 'get_all_rows', return_value=new_rows):
        result = reader.get_new_rows("test-tab")
        assert len(result) == 3
        for row in result:
            assert row["full_name"].startswith("New_")
    
    print("  ✅ get_new_rows — normal polling")

def test_get_new_rows_no_change():
    """Satır sayısı değişmezse boş dönmeli."""
    reader = SheetsReader()
    
    now = datetime.now(timezone.utc)
    mock_rows = [
        {"created_time": (now - timedelta(hours=1)).isoformat(), "full_name": "Same"}
    ]
    
    # İlk çalıştırma
    with patch.object(reader, 'get_all_rows', return_value=mock_rows):
        reader.get_new_rows("test-tab")
        reader.confirm_processed()
    
    # İkinci çalıştırma — aynı satır sayısı
    with patch.object(reader, 'get_all_rows', return_value=mock_rows):
        result = reader.get_new_rows("test-tab")
        assert len(result) == 0
    
    print("  ✅ get_new_rows — değişiklik yok")

def test_get_new_rows_tabs_independent():
    """Her tab bağımsız izlenmeli — bir tab diğerini etkilememeli."""
    reader = SheetsReader()
    
    now = datetime.now(timezone.utc)
    
    tab1_rows = [
        {"created_time": (now - timedelta(hours=1)).isoformat(), "full_name": "Tab1_Lead"}
    ]
    tab2_rows = [
        {"created_time": (now - timedelta(hours=1)).isoformat(), "full_name": "Tab2_Lead_1"},
        {"created_time": (now - timedelta(hours=2)).isoformat(), "full_name": "Tab2_Lead_2"},
    ]
    
    with patch.object(reader, 'get_all_rows', side_effect=[tab1_rows, tab2_rows]):
        result1 = reader.get_new_rows("tab1")
        result2 = reader.get_new_rows("tab2")
    
    assert len(result1) == 1  # Tab1'den 1 satır (restart recovery)
    assert len(result2) == 2  # Tab2'den 2 satır (restart recovery)
    reader.confirm_processed()
    
    print("  ✅ get_new_rows — tab bağımsızlığı")


# ═══════════════════════════════════════════════════════════════════
#  3. NOTION WRITER TESTLERI
# ═══════════════════════════════════════════════════════════════════

def test_whatsapp_link_generation():
    """WhatsApp link doğrulama."""
    assert NotionWriter._build_whatsapp_link("+90 555 123 4567") == "https://wa.me/905551234567"
    assert NotionWriter._build_whatsapp_link("+90 534 897 0627") == "https://wa.me/905348970627"
    assert NotionWriter._build_whatsapp_link("") == ""
    assert NotionWriter._build_whatsapp_link("+90 501 330 4413") == "https://wa.me/905013304413"
    print("  ✅ WhatsApp link üretimi")


# ═══════════════════════════════════════════════════════════════════
#  4. UÇTAN UCA TESTLER
# ═══════════════════════════════════════════════════════════════════

def test_e2e_real_sheet_row():
    """Gerçek sheet satırı → temizleme → Notion uyumluluğu."""
    # 14 Mart'tan gerçek bir satır
    raw = {
        "id": "l:1643587153501528",
        "created_time": "2026-03-14T00:27:21-05:00",
        "ad_id": "ag:120239117828310289",
        "ad_name": "Yeni Potansiyel Müşteriler Reklamı",
        "form_id": "f:741475502234023",
        "form_name": "Skool-Form-0326-Saat Bazlı-120326",
        "platform": "ig",
        "100%_otomatik_youtube_kanalı_açmak_için_yatırım_bütçeniz_nedir?": "$20_-_$50",
        "size_ne_zaman_ulaşalım?": "akşam_6'dan_sonra",
        "full_name": "duran/baris",
        "email": "ornek_kullanici@gmail.com",
        "phone_number": "p:+905013304413",
        "lead_status": "CREATED",
    }
    
    cleaned = clean_lead(raw)
    
    # İsim temiz mi?
    assert cleaned["clean_name"] == "Duran/baris"
    assert cleaned["clean_name"]  # boş değil
    
    # Telefon doğru formatta mı?
    assert cleaned["clean_phone"] == "+90 501 330 4413"
    
    # Email küçük harf mi?
    assert cleaned["clean_email"] == "ornek_kullanici@gmail.com"
    
    # Bütçe Notion select'e uygun mu?
    assert cleaned["clean_budget"] == "$20 - $50"
    
    # Timing Notion select'e uygun mu?
    assert cleaned["clean_timing"] == "Akşam 6'dan sonra"
    
    # WhatsApp link doğru mu?
    wa_link = NotionWriter._build_whatsapp_link(cleaned["clean_phone"])
    assert wa_link == "https://wa.me/905013304413"
    
    print("  ✅ uçtan uca — gerçek 14 Mart satırı")

def test_e2e_country_code_missing():
    """Ülke kodu olmayan numara → doğru WhatsApp linki."""
    raw = {
        "full_name": "Test Kullanici",
        "email": "test_user1@example.com",
        "phone_number": "5393802102",
    }
    
    cleaned = clean_lead(raw)
    assert cleaned["clean_phone"] == "+90 539 380 2102"
    
    wa_link = NotionWriter._build_whatsapp_link(cleaned["clean_phone"])
    assert wa_link == "https://wa.me/905393802102"
    
    print("  ✅ uçtan uca — ülke kodsuz numara")

def test_e2e_local_format_phone():
    """Yerel format (05XX) → doğru temizleme."""
    raw = {
        "full_name": "Test Ogrenci",
        "email": "test_user2@example.com",
        "phone_number": "05338222869",
    }
    
    cleaned = clean_lead(raw)
    assert cleaned["clean_phone"] == "+90 533 822 2869"
    
    wa_link = NotionWriter._build_whatsapp_link(cleaned["clean_phone"])
    assert wa_link == "https://wa.me/905338222869"
    
    print("  ✅ uçtan uca — yerel format telefon")

def test_e2e_test_lead_skipped():
    """Meta test lead'i (isim: <test lead...>) atlanabilir mi?"""
    raw = {
        "full_name": "<test lead: dummy data for full_name>",
        "email": "test@meta.com",
        "phone_number": "p:<test lead: dummy data for phone_number>",
    }
    
    cleaned = clean_lead(raw)
    # İsim var ama test verisi — clean_name boş olmaz
    # ama bu test lead'i phone'dan tanınır
    assert cleaned["clean_phone"] == ""  # geçersiz numara → boş
    print("  ✅ uçtan uca — Meta test lead'i")

def test_config_tab_names():
    """Config'deki tab isimleri doğru mu?"""
    from config import Config
    tab_names = [t["name"] for t in Config.SHEET_TABS]
    # En az bir tab tanımlı olmalı
    assert len(tab_names) >= 1
    print("  ✅ config — tab tanımları")

def test_config_spreadsheet_id():
    """Spreadsheet ID tanımlı mı?"""
    from config import Config
    # Kendi Spreadsheet ID'nizi .env dosyasından ayarlayın
    assert Config.SPREADSHEET_ID is not None and len(Config.SPREADSHEET_ID) > 10
    print("  ✅ config — spreadsheet ID tanımlı")

def test_config_notion_db():
    """Notion database ID tanımlı mı?"""
    from config import Config
    # Kendi Notion Database ID'nizi .env dosyasından ayarlayın
    assert Config.NOTION_DATABASE_ID is not None and len(Config.NOTION_DATABASE_ID) > 10
    print("  ✅ config — Notion database ID tanımlı")


# ═══════════════════════════════════════════════════════════════════
#  5. EDGE CASE TESTLER
# ═══════════════════════════════════════════════════════════════════

def test_restart_then_immediate_new_row():
    """
    Senaryo: Servis restart → ilk döngüde recovery → 
    hemen ardından yeni satır gelirse ikinci döngüde yakalamalı.
    """
    reader = SheetsReader()
    now = datetime.now(timezone.utc)
    
    # Restart: 10 satır var, 2'si son 48 saatte
    initial_rows = [
        {"created_time": (now - timedelta(days=5+i)).isoformat(), "full_name": f"Old_{i}"}
        for i in range(8)
    ] + [
        {"created_time": (now - timedelta(hours=6)).isoformat(), "full_name": "Recent_1"},
        {"created_time": (now - timedelta(hours=2)).isoformat(), "full_name": "Recent_2"},
    ]
    
    # Döngü 1: Restart recovery — 2 recent satır
    with patch.object(reader, 'get_all_rows', return_value=initial_rows):
        result1 = reader.get_new_rows("test-tab")
        assert len(result1) == 2
    reader.confirm_processed()
    
    # Hemen ardından 1 yeni satır ekleniyor
    new_rows = initial_rows + [
        {"created_time": now.isoformat(), "full_name": "BrandNew"}
    ]
    
    # Döngü 2: Normal polling — 1 yeni satır
    with patch.object(reader, 'get_all_rows', return_value=new_rows):
        result2 = reader.get_new_rows("test-tab")
        assert len(result2) == 1
        assert result2[0]["full_name"] == "BrandNew"
    
    print("  ✅ restart → hemen yeni satır senaryosu")

def test_multiple_restarts():
    """
    Senaryo: Servis birden fazla kez restart oluyor.
    Her seferinde recovery doğru çalışmalı.
    """
    now = datetime.now(timezone.utc)
    rows = [
        {"created_time": (now - timedelta(hours=3)).isoformat(), "full_name": "Lead_A"},
        {"created_time": (now - timedelta(hours=1)).isoformat(), "full_name": "Lead_B"},
    ]
    
    # Restart 1
    reader1 = SheetsReader()
    with patch.object(reader1, 'get_all_rows', return_value=rows):
        result1 = reader1.get_new_rows("tab")
        assert len(result1) == 2
    # confirm_processed çağrılmıyor — restart simülasyonu
    # (state diske kaydedilmez → ikinci instance de recovery yapmalı)
    
    # Restart 2 (yeni instance)
    reader2 = SheetsReader()
    with patch.object(reader2, 'get_all_rows', return_value=rows):
        result2 = reader2.get_new_rows("tab")
        assert len(result2) == 2  # Yine recovery yapmalı
    
    print("  ✅ çoklu restart senaryosu")

def test_created_time_column_missing_in_tab():
    """
    Mart-2026-Saat Bazlı-v2 tab'ında created_time sütunu yoksa
    _filter_recent_rows boş dönmeli ve hata vermemeli.
    """
    rows = [
        {"full_name": "Ali", "email": "ali@test.com"},
        {"full_name": "Veli", "email": "veli@test.com"},
    ]
    
    recent = SheetsReader._filter_recent_rows(rows, hours=48)
    assert len(recent) == 0  # Hata vermeden boş dönmeli
    print("  ✅ created_time eksik tab — güvenli boş dönüş")

def test_rollback_on_network_error():
    """
    KRİTİK TEST: Ağ hatası olduğunda rollback_pending çağrılırsa
    sonraki polling aynı satırları tekrar okumalı.
    Bu test, yeni pending mekanizmasının doğru çalıştığını doğrular.
    """
    reader = SheetsReader()
    now = datetime.now(timezone.utc)
    
    rows = [
        {"created_time": (now - timedelta(hours=1)).isoformat(), "full_name": "Lead_A"},
        {"created_time": (now - timedelta(hours=2)).isoformat(), "full_name": "Lead_B"},
    ]
    
    # İlk çalıştırma — confirm ile state kaydet
    with patch.object(reader, 'get_all_rows', return_value=rows):
        result1 = reader.get_new_rows("test-tab")
        assert len(result1) == 2
    reader.confirm_processed()
    
    # 2 yeni satır ekleniyor
    new_rows = rows + [
        {"created_time": now.isoformat(), "full_name": "New_1"},
        {"created_time": now.isoformat(), "full_name": "New_2"},
    ]
    
    # İkinci çalıştırma — 2 yeni satır okunur ama ağ hatası olur
    with patch.object(reader, 'get_all_rows', return_value=new_rows):
        result2 = reader.get_new_rows("test-tab")
        assert len(result2) == 2  # New_1 ve New_2
    
    # Ağ hatası! Rollback yapılır
    reader.rollback_pending()
    
    # Üçüncü çalıştırma — rollback yapıldığı için aynı 2 satır tekrar gelir
    with patch.object(reader, 'get_all_rows', return_value=new_rows):
        result3 = reader.get_new_rows("test-tab")
        assert len(result3) == 2  # Aynı 2 yeni satır tekrar!
        assert result3[0]["full_name"] == "New_1"
        assert result3[1]["full_name"] == "New_2"
    reader.confirm_processed()
    
    print("  ✅ rollback_pending — ağ hatası sonrası lead kurtarma (KRİTİK)")


# ═══════════════════════════════════════════════════════════════════
#  ÇALIŞTIR
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Tele Satış CRM — Kapsamlı Test Paketi")
    print("=" * 60)
    
    all_passed = True
    test_count = 0
    failed_tests = []
    
    # Tüm test fonksiyonlarını topla
    tests = [
        # Data Cleaner
        ("Veri Temizleme", [
            test_clean_phone_standard,
            test_clean_phone_without_country_code,
            test_clean_phone_090_prefix,
            test_clean_phone_edge_cases,
            test_clean_phone_real_sheet_data,
            test_clean_name,
            test_clean_email,
            test_clean_budget,
            test_clean_timing,
            test_clean_timing_real_data,
            test_clean_lead_full,
            test_clean_lead_empty_name_detection,
        ]),
        # Sheets Reader
        ("Sheets Reader (Restart Recovery)", [
            test_filter_recent_rows_basic,
            test_filter_recent_rows_meta_format,
            test_filter_recent_rows_no_created_time,
            test_filter_recent_rows_empty,
            test_get_new_rows_restart_recovery,
            test_get_new_rows_restart_no_recent,
            test_get_new_rows_normal_polling,
            test_get_new_rows_no_change,
            test_get_new_rows_tabs_independent,
        ]),
        # Notion Writer
        ("Notion Writer", [
            test_whatsapp_link_generation,
        ]),
        # Uçtan Uca
        ("Uçtan Uca (E2E)", [
            test_e2e_real_sheet_row,
            test_e2e_country_code_missing,
            test_e2e_local_format_phone,
            test_e2e_test_lead_skipped,
        ]),
        # Config
        ("Konfigürasyon", [
            test_config_tab_names,
            test_config_spreadsheet_id,
            test_config_notion_db,
        ]),
        # Edge Cases
        ("Edge Case'ler", [
            test_restart_then_immediate_new_row,
            test_multiple_restarts,
            test_created_time_column_missing_in_tab,
            test_rollback_on_network_error,
        ]),
    ]
    
    for section_name, test_fns in tests:
        print(f"\n── {section_name} ──")
        for test_fn in test_fns:
            try:
                test_fn()
                test_count += 1
            except Exception as e:
                all_passed = False
                failed_tests.append((test_fn.__name__, str(e)))
                print(f"  ❌ {test_fn.__name__}: {e}")
                test_count += 1
    
    print("\n" + "=" * 60)
    if all_passed:
        print(f"🎉 Tüm {test_count} test BAŞARILI!")
    else:
        print(f"⚠️  {len(failed_tests)}/{test_count} test BAŞARISIZ:")
        for name, err in failed_tests:
            print(f"   ❌ {name}: {err}")
    print("=" * 60)
    
    sys.exit(0 if all_passed else 1)
