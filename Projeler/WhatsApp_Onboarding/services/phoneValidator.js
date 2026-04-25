// ============================================================
// services/phoneValidator.js — Hibrit Telefon Validasyonu
// ============================================================
// Katman 1: Regex pre-validation (hızlı, kesin, ücretsiz)
// Katman 2: Groq GPT-OSS 120B (karmaşık girdiler için LLM)
// Katman 3: Regex override (Groq hatalıysa güvenlik ağı)
// ============================================================

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

// ─── KATMAN 1: Regex Pre-Validation ─────────────────────────
function regexValidate(input) {
  const cleaned = input.trim();
  const digits = cleaned.replace(/[\s\-\(\)\.\/]/g, '');

  if (!/^[\d\s\-\(\)\.\+\/]+$/.test(cleaned)) {
    return null;
  }

  if (/^905\d{8}$/.test(digits)) {
    return { valid: true, normalized: `+${digits}`, reason: "regex-direct (905)", confidence: 1.0, extracted_raw: input };
  }
  if (/^\+905\d{8}$/.test(cleaned.replace(/[\s\-]/g, ''))) {
    return { valid: true, normalized: cleaned.replace(/[\s\-]/g, ''), reason: "regex-direct (+905)", confidence: 1.0, extracted_raw: input };
  }
  if (/^05\d{9}$/.test(digits)) {
    return { valid: true, normalized: `+9${digits}`, reason: "regex-direct (05)", confidence: 1.0, extracted_raw: input };
  }
  if (/^5\d{9}$/.test(digits)) {
    return { valid: true, normalized: `+90${digits}`, reason: "regex-direct (5)", confidence: 1.0, extracted_raw: input };
  }
  if (/^\d{10,15}$/.test(digits) && !digits.startsWith('90')) {
    return { valid: true, normalized: `+${digits}`, reason: "regex-direct (uluslararası)", confidence: 0.8, extracted_raw: input };
  }

  return null;
}

// ─── KATMAN 2: Groq LLM Validasyonu ─────────────────────────
async function groqValidate(input) {
  try {
    const response = await fetch(GROQ_API_URL, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${config.groqApiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model: "gpt-oss-120b",
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
    return null;
  }
}

// ─── KATMAN 3: Regex Fallback (Groq'a override) ─────────────
function regexFallback(input) {
  const digits = input.replace(/\D/g, '');

  if (/^905\d{8}$/.test(digits)) {
    return { valid: true, normalized: `+${digits}`, reason: "regex fallback", confidence: 1.0, extracted_raw: input };
  }
  if (/^05\d{9}$/.test(digits)) {
    return { valid: true, normalized: `+9${digits}`, reason: "regex fallback", confidence: 1.0, extracted_raw: input };
  }
  if (/^5\d{9}$/.test(digits)) {
    return { valid: true, normalized: `+90${digits}`, reason: "regex fallback", confidence: 1.0, extracted_raw: input };
  }
  if (/^\d{10,15}$/.test(digits) && !digits.startsWith('90')) {
    return { valid: true, normalized: `+${digits}`, reason: "regex fallback - uluslararası", confidence: 1.0, extracted_raw: input };
  }

  return { valid: false, normalized: null, reason: "Geçerli telefon numarası bulunamadı", confidence: 0.0, extracted_raw: input };
}

// ─── ANA FONKSİYON ──────────────────────────────────────────
async function validatePhone(input) {
  const regexResult = regexValidate(input);
  if (regexResult) {
    log.info(`[phoneValidator] ✅ Regex pre-validation başarılı: ${JSON.stringify(regexResult)}`);
    return regexResult;
  }

  log.info(`[phoneValidator] Regex eşleşmedi, Groq GPT-OSS 120B'ye gönderiliyor: "${input}"`);
  const groqResult = await groqValidate(input);

  if (groqResult) {
    if (!groqResult.valid) {
      const overrideResult = regexFallback(input);
      if (overrideResult.valid) {
        log.warn(`[phoneValidator] ⚠️ GROQ OVERRIDE: Groq false dedi ama regex geçerli numara buldu. Regex sonucu kullanılıyor.`);
        overrideResult.reason = `groq-override (Groq: ${groqResult.reason})`;
        return overrideResult;
      }
    }
    return groqResult;
  }

  log.warn(`[phoneValidator] Groq tamamen başarısız, regex fallback kullanılıyor.`);
  return regexFallback(input);
}

module.exports = { validatePhone };
