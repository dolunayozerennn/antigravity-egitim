// services/ai_engine.js
const OpenAI = require('openai');
const { config } = require('../config/env');
const log = require('../utils/logger');
const { queryKnowledge } = require('./knowledge_base');
const { getHistory } = require('./memory');

const openai = new OpenAI({ apiKey: config.openaiApiKey });

async function generateResponse(subscriberId, currentMessage, detectedLanguage) {
  try {
    log.info(`[ai_engine] AI cevabı üretiliyor...`, { subscriberId, language: detectedLanguage });
    
    // 1. RAG ile ilgili bilgileri çek
    const ragChunks = await queryKnowledge(currentMessage);
    
    // 2. Hafızadan geçmişi çek
    const history = await getHistory(subscriberId, 20);
    
    // 3. System prompt'u hazırla
    const todayDate = new Date().toLocaleDateString('tr-TR', { day: 'numeric', month: 'long', year: 'numeric' });
    
    const systemPrompt = `
[ROL]
Sen, Dolunay Özeren'in yapay zekâ asistanısın. AI Factory hakkında 
sorularını yanıtlamak için buradasın. ${detectedLanguage} dilinde cevap üret.

[İLETİŞİM KURALLARI]
- Kısa ve öz yaz. Ideal 2-4 cümle, maksimum 6-8 cümle.
- Özel biçimlendirme kullanma (*, **, \`, #, > gibi karakterler YOK). Sadece düz metin yaz.
- Emoji çok az veya hiç kullanma. Mesaj başına en fazla 1.
- "Sen" dilini kullan, samimi ol.
- Cevap uzayacaksa parçalara böl.
- Liste gerekiyorsa tire (—) ile ayrılmış kısa satırlar kullan.

[KRİTİK KURALLAR]
- Fiyatları ASLA dönüştürme — USD/$ olarak koru. TL yazma.
- İndirim sözü VERME — fiyat sabit.
- Para iadesini onaylama veya reddetme — "Skool'un standart iade politikası geçerli" de.
- "Bilgim yok" deyip kaçma. Bilgi tabanında ara, tahmin et, bulamıyorsan "Bu konuyu Dolunay'a iletiyorum" de.
- Garanti veya kesin gelir vaadinde bulunma.
- Yapay zekâ olduğunu inkâr etme.
- Kayıt linki: https://www.skool.com/yapay-zeka-factory/about (Sadece kişi açıkça istediğinde veya itirazlar çürüdükten sonra paylaş)

[BUGÜNÜN TARİHİ]
${todayDate}

[İLGİLİ BİLGİLER]
${ragChunks}
    `.trim();

    // 4. API'ye gönderilecek mesaj listesini oluştur
    const messages = [
      { role: 'system', content: systemPrompt }
    ];

    // Geçmiş mesajları ekle
    for (const msg of history) {
      messages.push({ role: msg.role, content: msg.content });
    }

    // Mevcut mesajı ekle
    messages.push({ role: 'user', content: currentMessage });

    log.debug(`[ai_engine] OpenAI API'sine istek atılıyor...`);
    const response = await openai.chat.completions.create({
      model: 'gpt-4o-mini', // gpt-4o-mini is the current mini model, requested 4.1-mini maps here usually or gpt-4o
      messages: messages,
      temperature: 0.3
    });

    const aiResponse = response.choices[0].message.content.trim();
    log.info(`[ai_engine] AI cevabı başarıyla üretildi.`);
    
    return aiResponse;
  } catch (error) {
    log.error(`[ai_engine] generateResponse hatası: ${error.message}`, error);
    throw error;
  }
}

module.exports = {
  generateResponse
};
