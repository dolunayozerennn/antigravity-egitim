# 🤝 Marka İş Birliği

Markalarla iş birliği kurma ve outreach yönetim projesi.

---

## 📌 Amaç

Dolunay Özeren'in influencer olarak markalarla iş birliği kurmak için kullandığı outreach sistemidir.
Marka listeleri üzerinden kişiselleştirilmiş HTML mail şablonları ile iş birliği teklifleri gönderir.

## 🔗 Antigravity Entegrasyonu

Bu proje artık Antigravity ekosisteminin bir parçasıdır ve aşağıdaki skill/agent'larla çalışır:

| Bileşen | Yol | İlişki |
|---------|-----|--------|
| **Müşteri Kazanım Agenti** | `_agents/musteri-kazanim/AGENT.md` | Orkestrasyon |
| **Lead Generation Skill** | `_skills/lead-generation/SKILL.md` | Marka bulma |
| **E-posta Gönderim Skill** | `_skills/eposta-gonderim/SKILL.md` | Mail gönderim motoru |
| **API Anahtarları** | `_knowledge/api-anahtarlari.md` | Credential'lar |
| **Şifre Yönetici** | `_skills/sifre-yonetici/SKILL.md` | Token yönetimi |

## 📂 Proje Yapısı

```
Marka_Is_Birligi/
├── README.md                          ← Bu dosya
├── config/
│   ├── settings.py                    ← ⚠️ LEGACY — Sadece referans amaçlı
│   └── kampanya.yaml                  ← ✅ Antigravity format kampanya config
├── data/
│   └── markalar.csv                   ← Marka listesi (Antigravity standart CSV)
├── mail_templates/
│   └── collaboration_tr.html          ← HTML mail şablonu
├── markalar/
│   ├── eski-markalar                  ← Geçmiş markalar
│   └── marka-isimleri                 ← Aktif marka listesi
├── dolunay-tanitim                    ← Influencer tanıtım dosyası
└── src/
    └── mail_sender.py                 ← ⚠️ LEGACY — _skills/eposta-gonderim kullanılır
```

## 🚀 Nasıl Kullanılır

Bu proje artık doğrudan `mail_sender.py` ile değil, Antigravity workflow'larıyla çalıştırılır:

1. **Marka lead toplama:** `/lead-toplama` veya `/marka-outreach`
2. **Mail gönderme:** `/mail-gonder`
3. **Tüm pipeline:** `/marka-outreach` (lead bulma + kişiselleştirme + gönderim)

## ⚠️ Legacy Uyarı

`config/settings.py` ve `src/mail_sender.py` dosyaları eski bağımsız yapıdan kalmadır.
Yeni çalışmalarda **kesinlikle** Antigravity skill'leri ve workflow'ları kullanılmalıdır.
