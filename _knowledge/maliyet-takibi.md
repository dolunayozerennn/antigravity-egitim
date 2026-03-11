# 💰 API Servisleri Maliyet & Kota Takibi

Bu dosya kullanılan API servislerinin maliyet, kota ve yenileme bilgilerini takip eder.
Her token güncelleme veya kota değişikliğinde bu dosya da güncellenir.

**Son Güncelleme:** 11 Mart 2026

---

## Aktif Servisler

| Servis | Plan | Aylık Maliyet | Kota / Limit | Kullanım Notu | Son Kontrol |
|--------|------|---------------|-------------|---------------|-------------|
| OpenAI | Pay-as-you-go | ~$5-15/ay | Token bazlı | GPT-4.1 kullanımı | 11 Mar 2026 |
| Railway | Hobby | $5/ay | 3 aktif servis | Swc + Shorts + TeleSatis | 11 Mar 2026 |
| Apify | Free | $0 | Aylık kredi limiti | 2 hesap (ana + yedek) | 11 Mar 2026 |
| Kie AI | Pay-as-you-go | Değişken | Task bazlı | Sora 2, Kling video üretimi | 11 Mar 2026 |
| Fal AI | Pay-as-you-go | Değişken | Credit bazlı | Yedek video üretim | 11 Mar 2026 |
| Telegram | Ücretsiz | $0 | Sınırsız | Bot API | 11 Mar 2026 |
| Hunter.io | Free | $0 | 25 istek/ay | Email bulma | 11 Mar 2026 |
| Apollo.io | Free | $0 | Sınırlı | B2B lead bulma | 11 Mar 2026 |
| Groq | Free | $0 | Rate limit var | Whisper transkript | 11 Mar 2026 |
| Perplexity | Free | $0 | Rate limit var | Web araştırması | 11 Mar 2026 |
| ImgBB | Free | $0 | Sınırsız | Görsel upload | 11 Mar 2026 |
| ElevenLabs | Free | $0 | 10.000 karakter/ay | TTS (henüz aktif değil) | 11 Mar 2026 |

---

## Token Geçerlilik Durumu

| Servis | Token Durumu | Yenileme Gerekiyor mu? | Not |
|--------|-------------|----------------------|-----|
| OpenAI | ✅ Aktif | — | — |
| Kie AI | ✅ Aktif | — | Eski key bazı modellerde çalışmıyor, yenisi kullanılıyor |
| Fal AI | ✅ Aktif | — | — |
| Telegram (Shorts Bot) | ✅ Aktif | — | — |
| Railway | ✅ Aktif | — | — |
| Groq | ✅ Aktif | — | — |
| Perplexity | ✅ Aktif | — | — |
| Supadata | ⚠️ Yenilenmeli | Evet | Kullanıcıdan yeni key istenmeli |
| ElevenLabs | ⚠️ Eklenmedi | Evet | Kullanıcıdan key istenmeli |
| Gmail (Outreach) | ✅ OAuth aktif | — | Token süresi dolunca yeniden onay gerekir |
| Gmail (Sweatcoin) | ✅ OAuth aktif | — | Token süresi dolunca yeniden onay gerekir |

---

## Aylık Tahmini Toplam

| Kalem | Tutar |
|-------|-------|
| Railway (3 servis) | $5 |
| OpenAI (GPT-4.1) | ~$5-15 |
| Kie AI + Fal AI (video) | ~$5-20 |
| **Tahmini Toplam** | **~$15-40/ay** |

---

> 💡 Bu dosya aylık gözden geçirilmeli. Yeni servis eklendiğinde buraya da eklenmeli.
> 📊 Kesin maliyet takibi için her servisin dashboard'unu kontrol et.
