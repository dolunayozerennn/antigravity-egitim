// services/knowledge_base.js
const OpenAI = require('openai');
const { config } = require('../config/env');
const { supabase } = require('./memory');
const log = require('../utils/logger');

const openai = new OpenAI({ apiKey: config.openaiApiKey });

async function queryKnowledge(question) {
  try {
    log.debug(`[knowledge_base] Soru embed ediliyor...`);
    const embeddingResponse = await openai.embeddings.create({ model: 'text-embedding-3-small', input: question, dimensions: 1536 });
    const embedding = embeddingResponse.data[0].embedding;
    log.debug(`[knowledge_base] Supabase similarity search yapılıyor...`);
    const { data, error } = await supabase.rpc('match_knowledge_chunks', { query_embedding: embedding, match_threshold: 0.5, match_count: 5 });
    if (error) throw error;
    if (!data || data.length === 0) { log.warn(`[knowledge_base] İlgili chunk bulunamadı.`); return ""; }
    log.info(`[knowledge_base] ${data.length} adet chunk bulundu.`);
    const contextText = data.map(chunk => `[${chunk.section_title}]\n${chunk.content}`).join('\n\n');
    return contextText;
  } catch (error) { log.error(`[knowledge_base] queryKnowledge hatası: ${error.message}`, error); return ""; }
}

module.exports = { queryKnowledge };
