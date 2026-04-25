// services/language_detector.js
const { config } = require('../config/env');
const log = require('../utils/logger');
const fetch = require('node-fetch');

async function detectLanguage(text) {
  if (!text || text.trim() === '') return 'tr';

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
          { role: 'system', content: 'Bu metnin dilini sadece 2 harfli ISO koduyla döndür: tr, en, de, fr vb. Asla başka bir kelime yazma.' },
          { role: 'user', content: text }
        ],
        temperature: 0.1,
        max_tokens: 10
      })
    });

    const data = await response.json();
    if (data.error) throw new Error(data.error.message);

    const lang = data.choices[0].message.content.trim().toLowerCase();
    
    // Sadece 2 harfliyse kabul et, değilse varsayılan tr
    if (lang.length === 2) {
      log.debug(`[language_detector] Tespit edilen dil: ${lang}`);
      return lang;
    }
    
    return 'tr';
  } catch (error) {
    log.error(`[language_detector] Dil tespiti başarısız: ${error.message}`, error);
    return 'tr'; // Fallback
  }
}

module.exports = {
  detectLanguage
};
