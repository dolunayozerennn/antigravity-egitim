# 💰 API Servisleri Maliyet & Kota Takibi

Bu dosya kullanılan API servislerinin maliyet, kota ve yenileme bilgilerini takip eder.
Her token güncelleme veya kota değişikliğinde bu dosya da güncellenir.

---

## Aktif Servisler

| Servis | Plan | Aylık Maliyet | Kota / Limit | Kullanım Notu |
|--------|------|---------------|-------------|---------------|
| OpenAI | Pay-as-you-go | ~$5-15/ay | Token bazlı | GPT-4.1 kullanımı |
| Railway | Hobby | $5/ay | Kullanım bazlı | Worker + Cron servisleri |
| Apify | Free | $0 | Aylık kredi limiti | Web scraping |
| Kie AI | Pay-as-you-go | Değişken | Task bazlı | Video üretimi |
| Fal AI | Pay-as-you-go | Değişken | Credit bazlı | Yedek video üretim |
| Telegram | Ücretsiz | $0 | Sınırsız | Bot API |
| Hunter.io | Free | $0 | 25 istek/ay | Email bulma |
| Apollo.io | Free | $0 | Sınırlı | B2B lead bulma |
| Groq | Free | $0 | Rate limit var | LLM + Whisper |
| ImgBB | Free | $0 | Sınırsız | Görsel upload |

---

## Token Geçerlilik Durumu

| Servis | Token Durumu | Yenileme Gerekiyor mu? |
|--------|-------------|----------------------|
| OpenAI | ✅ Aktif | — |
| Kie AI | ✅ Aktif | — |
| Fal AI | ✅ Aktif | — |
| Telegram | ✅ Aktif | — |
| Railway | ✅ Aktif | — |
| Groq | ✅ Aktif | — |
| Gmail (OAuth) | ✅ OAuth aktif | Token süresi dolunca yeniden onay gerekir |

---

## Aylık Tahmini Toplam

| Kalem | Tutar |
|-------|-------|
| Railway | $5 |
| OpenAI (GPT-4.1) | ~$5-15 |
| Video üretim (Kie/Fal) | ~$5-20 |
| **Tahmini Toplam** | **~$15-40/ay** |

---

> 💡 Bu dosya aylık gözden geçirilmeli. Yeni servis eklendiğinde buraya da eklenmeli.
> 📊 Kesin maliyet takibi için her servisin dashboard'unu kontrol et.
