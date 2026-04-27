// ============================================================
// services/phoneValidator.js — Hibrit Telefon Validasyonu v2
// ============================================================
// Katman 1: libphonenumber-js (Google kütüphanesi — deterministik)
// Katman 2: Groq GPT-OSS 120B (metin+numara karışık girdiler için)
// Katman 3: libphonenumber-js override (Groq hatalıysa güvenlik ağı)
// ============================================================
// v2 Değişiklik: El yazısı regex kaldırıldı → libphonenumber-js
// Sebep: Regex'teki hane sayısı hataları tekrarlayan bug'lara yol açıyordu
// ============================================================

const { parsePhoneNumberFromString } = require('libphonenumber-js');
const { config } = require('../config/env');
const log = require('../utils/logger');

const GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions";

const SYSTEM_PROMPT = `Sen bir veri dönüştürme aracısın. Gelen metinden telefon numarasını çıkar ve SADECE JSON döndür.
JSON formatı:
{"valid": true, "normalized": "+905321234567", "reason": "", "confidence": 0.95, "extracted_raw": "0532 123 45 67"}
veya
{"valid": false, "normalized": null, "reason": "Numara yok", "confidence": 0.0, "extracted_raw": null}

KURALLAR (KRİTİK):
1. Rakamların sırasını ASLA değiştirme. Girdiği gibi çıkar. Halüsinasyon yaparsan sistem çöker.
2. Sadece boşlukları ve tireleri temizle.
3. Numara '5' ile başlıyorsa ve toplam 10 rakamsa başa '+90' ekle.
4. Numara '05' ile başlıyorsa ve toplam 11 rakamsa başa '+9' ekle.
5. Numara '905' ile başlıyorsa ve toplam 12 rakamsa başa '+' ekle.
6. Kullanıcı sohbet veya itiraz ediyorsa valid: false döndür.
7. ÇOKLU NUMARA DURUMU: Eğer metinde birden fazla numara varsa, bağlama bakarak "güncel", "yeni" veya "benim" gibi kelimelerle ilişkilendirilen numarayı seç. 
8. BELİRSİZ ÇOKLU NUMARA DURUMU: Eğer bağlam belirsizse (hangisinin doğru olduğu açık değilse), metinde geçen EN SON numarayı baz al. Ancak bu durumda "confidence" (güven) değerini düşür (örneğin 0.4). Tek numara varsa veya açıkça hangisi olduğu belliyse confidence'ı yüksek tut (örneğin 0.9 - 1.0 arası).`;

// ─── KATMAN 1: libphonenumber-js Pre-Validation ─────────────
// Saf numerik girdiler için. Deterministik, ücretsiz, hatasız.
// Google'ın kütüphanesi tüm ülke formatlarını bilir.
function libraryValidate(input) {
  const cleaned = input.trim();

  // Metin içeriyorsa (harf, özel karakter) → kütüphane parse edemez, LLM'e gönder
  if (!/^[\d\s\-\(\)\.\+\/]+$/.test(cleaned)) {
    return null;
  }

  // Türkiye varsayılan ülke olarak denenecek formatlar
  // libphonenumber birçok formatı otomatik tanır
  const candidates = [cleaned];

  // Başında + yoksa ve sadece rakamlardan oluşuyorsa, + ekli versiyonu da dene
  const digitsOnly = cleaned.replace(/\D/g, '');
  if (!cleaned.startsWith('+') && digitsOnly.length >= 10) {
    candidates.push(`+${digitsOnly}`);
  }

  for (const candidate of candidates) {
    // Varsayılan ülke TR olarak parse et
    const phone = parsePhoneNumberFromString(candidate, 'TR');
    if (phone && phone.isValid()) {
      const normalized = phone.number; // E.164 format: +905380168954
      log.info(`[phoneValidator] ✅ libphonenumber başarılı: "${input}" → ${normalized} (${phone.country})`);
      return {
        valid: true,
        normalized,
        reason: `libphonenumber (${phone.country})`,
        confidence: 1.0,
        extracted_raw: input
      };
    }
  }

  return null; // Tanımlanamadı → Groq'a gönder
}

// ─── KATMAN 2: Groq LLM Validasyonu ─────────────────────────
// Karmaşık girdiler için (metin + numara karışık, çoklu numara vb.)
async function groqValidate(input) {
  try {
    const response = await fetch(GROQ_API_URL, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${config.groqApiKey}`,
        'Content-Type': 'application/json'
      },
      signal: AbortSignal.timeout(5000), // 5s timeout
      body: JSON.stringify({
        model: "llama-3.3-70b-versatile",
        messages: [
          { role: "system", content: SYSTEM_PROMPT },
          { role: "user", content: input }
        ],
        max_tokens: 200,
        temperature: 0,
        response_format: { type: "json_object" }
      })
    });

    if (!response.ok) {
      throw new Error(`Groq HTTP ${response.status}: ${await response.text()}`);
    }

    const data = await response.json();
    const result = JSON.parse(data.choices[0].message.content);
    log.info(`[phoneValidator] Groq sonuç: ${JSON.stringify(result)}`);
    return result;

  } catch (error) {
    log.error(`[phoneValidator] Groq hatası: ${error.message}`, error.stack);

    // Groq tamamen down — admin'e alert gönder (1 saat cooldown, spam önleme)
    if (!global._groqAlertSent) {
      global._groqAlertSent = true;
      setTimeout(() => { global._groqAlertSent = false; }, 3600000);
      try {
        const resend = require('./resend');
        await resend.sendAdminAlertEmail(
          '[PHONE] Groq API down — fallback aktif',
          { body: `Groq API'ye ulaşılamıyor. Tüm telefon validasyonları libphonenumber fallback'ine düşüyor.\n\nHata: ${error.message}` }
        );
      } catch (_) { /* alert gönderilemezse bile devam et */ }
    }

    return null; // Groq başarısız → null dön, fallback devreye girsin
  }
}

// ─── KATMAN 3: libphonenumber Fallback (Groq'a override) ────
// Groq down ise VEYA Groq hatalı sonuç döndürürse,
// girdiden rakamları çıkarıp kütüphaneye son kez sor.
function libraryFallback(input) {
  const digitsOnly = input.replace(/\D/g, '');

  // Farklı prefix kombinasyonlarını dene
  const candidates = [
    `+${digitsOnly}`,      // +905380168954
    `+90${digitsOnly}`,    // Başında ülke kodu yoksa ekle
    digitsOnly             // Ham rakamlar
  ];

  for (const candidate of candidates) {
    const phone = parsePhoneNumberFromString(candidate, 'TR');
    if (phone && phone.isValid()) {
      log.info(`[phoneValidator] ✅ libphonenumber fallback başarılı: "${input}" → ${phone.number}`);
      return {
        valid: true,
        normalized: phone.number,
        reason: `libphonenumber fallback (${phone.country})`,
        confidence: 1.0,
        extracted_raw: input
      };
    }
  }

  return { valid: false, normalized: null, reason: "Geçerli telefon numarası bulunamadı", confidence: 0.0, extracted_raw: input };
}

// ─── ANA FONKSİYON ──────────────────────────────────────────
async function validatePhone(input) {
  // KATMAN 1: libphonenumber pre-validation (saf numerik girdiler)
  const libResult = libraryValidate(input);
  if (libResult) {
    return libResult;
  }

  // KATMAN 2: Groq LLM (karmaşık girdiler için)
  log.info(`[phoneValidator] Kütüphane eşleşmedi, Groq GPT-OSS 120B'ye gönderiliyor: "${input}"`);
  const groqResult = await groqValidate(input);

  if (groqResult) {
    // Groq bir numara çıkardıysa, kütüphane ile doğrula
    if (groqResult.valid && groqResult.normalized) {
      const verifyPhone = parsePhoneNumberFromString(groqResult.normalized, 'TR');
      if (verifyPhone && verifyPhone.isValid()) {
        groqResult.normalized = verifyPhone.number; // E.164 normalize
        groqResult.reason = `groq+libphonenumber (${verifyPhone.country})`;
        return groqResult;
      }
      // Groq'un çıkardığı numara kütüphaneden geçemediyse → düşük güven
      log.warn(`[phoneValidator] ⚠️ Groq valid dedi ama libphonenumber doğrulamadı: ${groqResult.normalized}`);
      groqResult.confidence = Math.min(groqResult.confidence || 0, 0.4);
      groqResult.reason = `groq-only (libphonenumber doğrulamadı)`;
      return groqResult;
    }

    // Groq "false" dedi → fallback ile son şans
    if (!groqResult.valid) {
      const overrideResult = libraryFallback(input);
      if (overrideResult.valid) {
        log.warn(`[phoneValidator] ⚠️ GROQ OVERRIDE: Groq false dedi ama libphonenumber geçerli numara buldu.`);
        overrideResult.reason = `groq-override (Groq: ${groqResult.reason})`;
        return overrideResult;
      }
    }
    return groqResult;
  }

  // Groq tamamen başarısız oldu → kütüphane fallback
  log.warn(`[phoneValidator] Groq tamamen başarısız, libphonenumber fallback kullanılıyor.`);
  return libraryFallback(input);
}

module.exports = { validatePhone };
