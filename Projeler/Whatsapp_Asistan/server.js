// server.js
const express = require('express');
const { config } = require('./config/env');
const log = require('./utils/logger');

// Servisler
const { getSubscriber, createSubscriber, acceptKVKK, saveMessage } = require('./services/memory');
const { isAudioUrl, transcribeAudio } = require('./services/transcription');
const { detectLanguage } = require('./services/language_detector');
const { generateResponse } = require('./services/ai_engine');
const { setCustomField, sendFlow } = require('./services/manychat');

const app = express();
app.use(express.json());

const KVKK_MESSAGE = `Merhaba! \ud83d\udc4b Ben Dolunay \u00d6zeren'in yapay zek\u00e2 asistan\u0131y\u0131m.\n\nSana yard\u0131mc\u0131 olabilmem i\u00e7in ki\u015fisel verilerin hakk\u0131nda bilgilendirme yapmam gerekiyor.\n\nKVKK Ayd\u0131nlatma Metni: https://dolunay.ai/sozlesmeler/kvkk\n\nDevam etmek i\u00e7in l\u00fctfen \"Onayl\u0131yorum\" yaz.`;

const WELCOME_MESSAGE = `Te\u015fekkurler! \ud83d\ude4f Art\u0131k sana AI Factory hakk\u0131nda her konuda yard\u0131mc\u0131 olabilirim. Sormak istedi\u011fin bir \u015fey var m\u0131?`;

app.post('/webhook/message', async (req, res) => {
  res.status(200).send({ status: 'received' });
  try {
    const payload = req.body;
    const subscriberId = payload.kullanici_id;
    let messageContent = payload.last_text_input;
    const phoneNumber = payload.phone_number || '';
    if (!subscriberId || !messageContent) { log.warn(`[webhook] Eksik payload verisi.`, { subscriberId, messageContent: !!messageContent }); return; }
    log.info(`[webhook] Yeni mesaj al\u0131nd\u0131.`, { subscriberId });
    let subscriber = await getSubscriber(subscriberId);
    if (!subscriber) {
      log.info(`[webhook] Yeni subscriber olu\u015fturuluyor...`, { subscriberId });
      subscriber = await createSubscriber(subscriberId, phoneNumber);
      await setCustomField(subscriberId, config.manychatFieldId, KVKK_MESSAGE);
      await sendFlow(subscriberId, config.manychatFlowId);
      return;
    }
    if (!subscriber.kvkk_accepted) {
      const lowerMsg = messageContent.toLowerCase().trim();
      const isAccepted = lowerMsg === 'onayl\u0131yorum' || lowerMsg === 'evet' || lowerMsg === 'kabul ediyorum' || lowerMsg === 'kabul';
      if (isAccepted) {
        log.info(`[webhook] Kullan\u0131c\u0131 KVKK onaylad\u0131.`, { subscriberId });
        await acceptKVKK(subscriberId);
        await setCustomField(subscriberId, config.manychatFieldId, WELCOME_MESSAGE);
        await sendFlow(subscriberId, config.manychatFlowId);
      } else {
        log.info(`[webhook] Kullan\u0131c\u0131 hen\u00fcz KVKK onaylamad\u0131, hat\u0131rlatma g\u00f6nderiliyor.`, { subscriberId });
        await setCustomField(subscriberId, config.manychatFieldId, KVKK_MESSAGE);
        await sendFlow(subscriberId, config.manychatFlowId);
      }
      return;
    }
    if (isAudioUrl(messageContent)) {
      log.info(`[webhook] Ses mesaj\u0131 alg\u0131land\u0131, transkribe ediliyor...`, { subscriberId });
      try { messageContent = await transcribeAudio(messageContent); }
      catch (err) {
        log.error(`[webhook] Ses mesaj\u0131 \u00e7evrilemedi.`, err);
        await setCustomField(subscriberId, config.manychatFieldId, "\u00d6z\u00fcr dilerim, sesli mesaj\u0131n\u0131 \u015fu an dinleyemiyorum. L\u00fctfen bana yaz\u0131l\u0131 olarak iletebilir misin?");
        await sendFlow(subscriberId, config.manychatFlowId);
        return;
      }
    }
    await saveMessage(subscriberId, 'user', messageContent);
    const detectedLanguage = await detectLanguage(messageContent);
    const aiResponse = await generateResponse(subscriberId, messageContent, detectedLanguage);
    await saveMessage(subscriberId, 'assistant', aiResponse);
    await setCustomField(subscriberId, config.manychatFieldId, aiResponse);
    await sendFlow(subscriberId, config.manychatFlowId);
    log.info(`[webhook] \u0130\u015flem ba\u015far\u0131yla tamamland\u0131.`, { subscriberId });
  } catch (error) { log.error(`[webhook] Beklenmeyen hata: ${error.message}`, error); }
});

app.get('/health', (req, res) => {
  res.status(200).json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Admin: RAG bilgi taban\u0131n\u0131 seed et
app.post('/admin/seed-knowledge', async (req, res) => {
  try {
    const fs = require('fs');
    const path = require('path');
    const OpenAI = require('openai');
    const { supabase } = require('./services/memory');
    const openai = new OpenAI({ apiKey: config.openaiApiKey });
    const mdPath = path.join(__dirname, 'ai-factory-asistan-bilgi-tabani-v2.md');
    if (!fs.existsSync(mdPath)) { return res.status(404).json({ error: 'Bilgi taban\u0131 dosyas\u0131 bulunamad\u0131.' }); }
    const mdContent = fs.readFileSync(mdPath, 'utf8');
    const chunks = [];
    const lines = mdContent.split('\n');
    let currentSection = '', currentTitle = '', currentContent = [];
    for (const line of lines) {
      if (line.startsWith('## ') || line.startsWith('### ')) {
        if (currentContent.length > 0 && currentTitle) {
          chunks.push({ section: currentSection || '0', section_title: currentTitle, content: currentContent.join('\n').trim() });
          currentContent = [];
        }
        const titleText = line.replace(/^#+\s/, '');
        const sectionMatch = titleText.match(/^([\d.]+)\s*/);
        if (sectionMatch) { currentSection = sectionMatch[1].trim(); currentTitle = titleText.substring(sectionMatch[0].length).trim(); }
        else { currentTitle = titleText; }
      } else { currentContent.push(line); }
    }
    if (currentContent.length > 0 && currentTitle) { chunks.push({ section: currentSection || '0', section_title: currentTitle, content: currentContent.join('\n').trim() }); }
    await supabase.from('knowledge_chunks').delete().neq('id', '00000000-0000-0000-0000-000000000000');
    let processedCount = 0;
    for (const chunk of chunks) {
      if (!chunk.content || chunk.content.trim() === '') continue;
      const embeddingResponse = await openai.embeddings.create({ model: 'text-embedding-3-small', input: `[${chunk.section_title}]\n${chunk.content}`, dimensions: 1536 });
      const embedding = embeddingResponse.data[0].embedding;
      const { error } = await supabase.from('knowledge_chunks').insert({ section: chunk.section, section_title: chunk.section_title, content: chunk.content, embedding: embedding, metadata: { source: 'ai-factory-asistan-bilgi-tabani-v2' } });
      if (error) { log.error(`[seed] Kay\u0131t hatas\u0131: ${chunk.section_title} \u2014 ${error.message}`); } else { processedCount++; }
      await new Promise(r => setTimeout(r, 200));
    }
    log.info(`[seed] ${processedCount} chunk kaydedildi.`);
    res.json({ status: 'ok', chunks_processed: processedCount, total_chunks: chunks.length });
  } catch (error) { log.error(`[seed] Seed hatas\u0131: ${error.message}`, error); res.status(500).json({ error: error.message }); }
});

app.listen(config.port, () => {
  log.info(`[server] Whatsapp_Asistan ${config.port} portunda \u00e7al\u0131\u015f\u0131yor.`);
});
