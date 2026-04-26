// services/intent_classifier.js
const { config } = require('../config/env');
const log = require('../utils/logger');
const fetch = require('node-fetch');

/**
 * Kullanıcının mesajından KVKK onay niyetini Groq LLM kullanarak analiz eder.
 * @param {string} text Kullanıcı mesajı
 * @returns {Promise<boolean>} KVKK onaylanmışsa true, aksi halde false
 */
async function checkKVKKIntent(text) {
  if (!text || text.trim() === '') return false;

  try {
    const response = await fetch('https://api.groq.com/openai/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${config.groqApiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model: 'llama-3.3-70b-versatile',
        messages: [
          { 
            role: 'system', 
            content: 'Kullanıcının yazdığı mesajın KVKK (Kişisel Verilerin Korunması Kanunu) sözleşmesini veya herhangi bir aydınlatma metnini "onaylama", "kabul etme", "izin verme" niyeti taşıyıp taşımadığını analiz et.\n\nSADECE "true" veya "false" yanıtı ver. Asla başka bir şey yazma.\n\nÖrnekler:\n- "onaylıyorum" -> true\n- "kabul ediyorum" -> true\n- "evet" -> true\n- "ok" -> true\n- "olur" -> true\n- "tamamdır" -> true\n- "👍" -> true\n- "hayır" -> false\n- "kabul etmiyorum" -> false\n- "bu ne demek" -> false\n- "onaylamıyorum" -> false\n- "onaylyrm" -> true' 
          },
          { role: 'user', content: text }
        ],
        temperature: 0.1,
        max_tokens: 5
      })
    });

    const data = await response.json();
    if (data.error) throw new Error(data.error.message);

    const result = data.choices[0].message.content.trim().toLowerCase();
    
    // Güvenlik ve temizlik amaçlı regex ile sadece true kelimesini arayalım
    if (result.includes('true')) {
      log.debug(`[intent_classifier] KVKK intent LLM ile onaylandı: "${text}"`);
      return true;
    }
    
    log.debug(`[intent_classifier] KVKK intent LLM ile reddedildi: "${text}" -> ${result}`);
    return false;

  } catch (error) {
    log.error(`[intent_classifier] LLM analizi başarısız, Fallback kullanılıyor: ${error.message}`);
    // LLM Çökerse: Güçlü Regex Fallback
    const regex = /^(onayl[ıi]yorum|evet|kabul\s*ediyorum|kabul|ok|tamam|olur|👍)/i;
    const isFallbackAccepted = regex.test(text.trim());
    log.debug(`[intent_classifier] Fallback sonucu: ${isFallbackAccepted}`);
    return isFallbackAccepted;
  }
}

module.exports = {
  checkKVKKIntent
};
