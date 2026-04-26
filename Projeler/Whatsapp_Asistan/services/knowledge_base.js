// services/knowledge_base.js
const OpenAI = require('openai');
const { config } = require('../config/env');
const { supabase } = require('./memory');
const log = require('../utils/logger');

const openai = new OpenAI({ apiKey: config.openaiApiKey });

const PRICING_KEYWORDS = ['fiyat', 'ücret', 'price', 'ne kadar', 'kaç dolar', 'paket', 'standard', 'premium', 'vip', 'aylık', 'yıllık', 'indirim', 'kampanya'];

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
      match_count: 5
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

    return contextText;
  } catch (error) {
    log.error(`[knowledge_base] queryKnowledge hatası: ${error.message}`, error);
    return "";
  }
}

module.exports = {
  queryKnowledge
};
