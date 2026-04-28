// services/knowledge_base.js
const OpenAI = require('openai');
const { config } = require('../config/env');
const { supabase } = require('./memory');
const log = require('../utils/logger');

const openai = new OpenAI({ apiKey: config.openaiApiKey });

const PRICING_KEYWORDS = ['fiyat', 'ücret', 'price', 'ne kadar', 'kaç dolar', 'paket', 'standard', 'premium', 'vip', 'aylık', 'yıllık', 'indirim', 'kampanya'];
const AUTOMATION_KEYWORDS = ['otomasyon', 'automation', 'youtube', 'otel', 'süpermarket', 'e-ticaret', 'influencer', 'linkedin', 'emlakçı', 'emlak', 'video üret', 'otomatik paylaş', 'kanalım', 'içerik üret', 'shorts', 'reels', 'tiktok', 'instagram', 'meltem'];
const LINK_KEYWORDS = ['link', 'odeme', 'uyelik', 'nasil ulasacagim', 'nasil erisecegim', 'classroom', 'nereden basla', 'egitim video', 'kayit', 'uye ol', 'nereden uye', 'giris', 'nasil yapacam', 'nasil yapacagim', 'nereden baslayacagim', 'ulasamiyorum', 'erisim'];

async function queryKnowledge(question) {
  try {
    log.debug(`[knowledge_base] Soru embed ediliyor...`);
    const embeddingResponse = await openai.embeddings.create({
      model: 'text-embedding-3-small',
      input: question,
      dimensions: 1536
    });
    
    const embedding = embeddingResponse.data[0].embedding;
    
    log.debug(`[knowledge_base] Supabase similarity search yapılıyor...`);
    const { data, error } = await supabase.rpc('match_knowledge_chunks', {
      query_embedding: embedding,
      match_threshold: 0.6,
      match_count: 7
    });

    if (error) throw error;

    let contextText = "";
    if (!data || data.length === 0) {
      log.warn(`[knowledge_base] İlgili chunk bulunamadı.`);
    } else {
      log.info(`[knowledge_base] ${data.length} adet chunk bulundu.`);
      contextText = data.map(chunk => `[${chunk.section_title}]\n${chunk.content}`).join('\n\n');
    }

    // Fiyat sorusu tespiti
    const lowerQuestion = question.toLowerCase();
    const isPricingQuestion = PRICING_KEYWORDS.some(kw => lowerQuestion.includes(kw));

    if (isPricingQuestion) {
      const { data: pricingChunks } = await supabase
        .from('knowledge_chunks')
        .select('section_title, content')
        .or('section_title.ilike.%Üyelik Paketleri%,section_title.ilike.%Fiyat Güvenlik%,section_title.ilike.%Sıkça Sorulan%');
      
      if (pricingChunks && pricingChunks.length > 0) {
        const pinnedContext = pricingChunks.map(c => `[${c.section_title}]\n${c.content}`).join('\n\n');
        // RAG sonuçlarının BAŞINA ekle (LLM başa daha fazla ağırlık verir)
        return pinnedContext + '\n\n' + contextText;
      }
    }

    // Otomasyon sorusu tespiti
    const isAutomationQuestion = AUTOMATION_KEYWORDS.some(kw => lowerQuestion.includes(kw));
    
    if (isAutomationQuestion) {
      const { data: automationChunks } = await supabase
        .from('knowledge_chunks')
        .select('section_title, content')
        .or('section_title.ilike.%Otomasyon Kütüphanesi%,section_title.ilike.%Başarı Hikâyeleri%');
      
      if (automationChunks && automationChunks.length > 0) {
        const pinnedContext = automationChunks.map(c => "[" + c.section_title + "]\n" + c.content).join('\n\n');
        return pinnedContext + '\n\n' + contextText;
      }
    }

    // Link sorusu tespiti
    const isLinkQuestion = LINK_KEYWORDS.some(kw => lowerQuestion.includes(kw));

    if (isLinkQuestion) {
      const { data: linkChunks } = await supabase
        .from('knowledge_chunks')
        .select('section_title, content')
        .or('section_title.ilike.%Onemli Linkler%,section_title.ilike.%Önemli Linkler%,section_title.ilike.%Sikca Sorulan%,section_title.ilike.%Sıkça Sorulan%,section_title.ilike.%Uyelik Yasam%,section_title.ilike.%Üyelik Yaşam%,section_title.ilike.%Odeme%,section_title.ilike.%Ödeme%');

      if (linkChunks && linkChunks.length > 0) {
        const pinnedContext = linkChunks.map(c => "[" + c.section_title + "]\n" + c.content).join('\n\n');
        return pinnedContext + '\n\n' + contextText;
      }
    }

    return contextText;
  } catch (error) {
    log.error(`[knowledge_base] queryKnowledge hatası: ${error.message}`, error);
    return "";
  }
}

module.exports = {
  queryKnowledge
};
