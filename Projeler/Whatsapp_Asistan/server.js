// server.js
const express = require('express');
const { config } = require('./config/env');
const log = require('./utils/logger');

// ManyChat field ve flow ID'leri
const FIELD_ID = config.manychatFieldId;
const FLOW_ID = config.manychatFlowId;

// Servisler
const { getSubscriber, createSubscriber, acceptKVKK, saveMessage } = require('./services/memory');
const { isAudioUrl, transcribeAudio } = require('./services/transcription');
const { detectLanguage } = require('./services/language_detector');
const { generateResponse } = require('./services/ai_engine');
const { setCustomField, sendFlow } = require('./services/manychat');

const app = express();
app.use(express.json({ limit: '5mb' }));

// KVKK Aydinlatma Mesaji
const KVKK_MESSAGE = `Merhaba! \ud83d\udc4b Ben Dolunay \u00d6zeren'in yapay zek\u00e2 asistan\u0131y\u0131m.

Sana yard\u0131mc\u0131 olabilmem i\u00e7in ki\u015fisel verilerin hakk\u0131nda bilgilendirme yapmam gerekiyor.

KVKK Ayd\u0131nlatma Metni: https://dolunay.ai/sozlesmeler/kvkk

Devam etmek i\u00e7in l\u00fctfen "Onayl\u0131yorum" yaz.`;

// Hosgeldin Mesaji
const WELCOME_MESSAGE = `Te\u015fekk\u00fcrler! \ud83d\ude4f Art\u0131k sana AI Factory hakk\u0131nda her konuda yard\u0131mc\u0131 olabilirim. Sormak istedi\u011fin bir \u015fey var m\u0131?`;

app.post('/webhook/message', async (req, res) => {
  // ManyChat webhook timeoutlari icin hemen 200 donulur
  res.status(200).send({ status: 'received' });
  
  try {
    const payload = req.body;
    const subscriberId = payload.kullanici_id;
    let messageContent = payload.last_text_input;
    const phoneNumber = payload.phone_number || '';

    if (!subscriberId || !messageContent) {
      log.warn(`[webhook] Eksik payload verisi.`, { subscriberId, messageContent: !!messageContent });
      return;
    }

    log.info(`[webhook] Yeni mesaj alindi.`, { subscriberId });

    // 1. Subscriber kontrolu
    let subscriber = await getSubscriber(subscriberId);
    if (!subscriber) {
      log.info(`[webhook] Yeni subscriber olusturuluyor...`, { subscriberId });
      subscriber = await createSubscriber(subscriberId, phoneNumber);
      
      // Yeni kullaniciya dogrudan KVKK mesaji gonder
      await setCustomField(subscriberId, FIELD_ID, KVKK_MESSAGE);
      await sendFlow(subscriberId, FLOW_ID);
      return;
    }

    // 2. KVKK kontrolu
    if (!subscriber.kvkk_accepted) {
      const lowerMsg = messageContent.toLowerCase().trim();
      const isAccepted = lowerMsg === 'onayliyorum' || lowerMsg === 'evet' || lowerMsg === 'kabul ediyorum' || lowerMsg === 'kabul';
      
      if (isAccepted) {
        log.info(`[webhook] Kullanici KVKK onayladi.`, { subscriberId });
        await acceptKVKK(subscriberId);
        
        await setCustomField(subscriberId, FIELD_ID, WELCOME_MESSAGE);
        await sendFlow(subscriberId, FLOW_ID);
      } else {
        log.info(`[webhook] Kullanici henuz KVKK onaylamadi, hatirlatma gonderiliyor.`, { subscriberId });
        await setCustomField(subscriberId, FIELD_ID, KVKK_MESSAGE);
        await sendFlow(subscriberId, FLOW_ID);
      }
      return;
    }

    // 3. Ses mesaji kontrolu ve transkripsiyon
    if (isAudioUrl(messageContent)) {
      log.info(`[webhook] Ses mesaji algilandi, transkribe ediliyor...`, { subscriberId });
      try {
        messageContent = await transcribeAudio(messageContent);
      } catch (err) {
        log.error(`[webhook] Ses mesaji cevrilemedi, kullaniciya bilgi veriliyor.`, err);
        await setCustomField(subscriberId, FIELD_ID, "Ozur dilerim, sesli mesajini su an dinleyemiyorum. Lutfen bana yazili olarak iletebilir misin?");
        await sendFlow(subscriberId, FLOW_ID);
        return;
      }
    }

    // Kullanici mesajini kaydet
    await saveMessage(subscriberId, 'user', messageContent);

    // 4. Dil algilama
    const detectedLanguage = await detectLanguage(messageContent);

    // 5. AI cevabi uret (RAG ve hafiza islemleri ai_engine icinde)
    const aiResponse = await generateResponse(subscriberId, messageContent, detectedLanguage);

    // AI cevabini kaydet
    await saveMessage(subscriberId, 'assistant', aiResponse);

    // 6. ManyChat'e gonder
    await setCustomField(subscriberId, FIELD_ID, aiResponse);
    await sendFlow(subscriberId, FLOW_ID);
    
    log.info(`[webhook] Islem basariyla tamamlandi.`, { subscriberId });

  } catch (error) {
    log.error(`[webhook] Beklenmeyen hata: ${error.message}`, error);
  }
});

app.get('/health', (req, res) => {
  res.status(200).json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Admin: RAG bilgi tabanini seed et
app.post('/admin/seed-knowledge', async (req, res) => {
  try {
    const fs = require('fs');
    const path = require('path');
    const OpenAI = require('openai');
    const { supabase } = require('./services/memory');
    const openai = new OpenAI({ apiKey: config.openaiApiKey });

    // Body'den markdown icerigi al, yoksa dosyadan oku
    let mdContent = req.body.markdown_content;
    if (!mdContent) {
      const mdPath = path.join(__dirname, 'ai-factory-asistan-bilgi-tabani-v2.md');
      if (!fs.existsSync(mdPath)) {
        return res.status(404).json({ error: 'Bilgi tabani dosyasi bulunamadi. Body ile markdown_content gonderin.' });
      }
      mdContent = fs.readFileSync(mdPath, 'utf8');
    }
    
    // Markdown'i chunk'lara ayir
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
        if (sectionMatch) {
          currentSection = sectionMatch[1].trim();
          currentTitle = titleText.substring(sectionMatch[0].length).trim();
        } else {
          currentTitle = titleText;
        }
      } else {
        currentContent.push(line);
      }
    }
    if (currentContent.length > 0 && currentTitle) {
      chunks.push({ section: currentSection || '0', section_title: currentTitle, content: currentContent.join('\n').trim() });
    }

    // Eski verileri temizle
    await supabase.from('knowledge_chunks').delete().neq('id', '00000000-0000-0000-0000-000000000000');

    let processedCount = 0;
    for (const chunk of chunks) {
      if (!chunk.content || chunk.content.trim() === '') continue;

      const embeddingResponse = await openai.embeddings.create({
        model: 'text-embedding-3-small',
        input: `[${chunk.section_title}]\n${chunk.content}`,
        dimensions: 1536
      });

      const embedding = embeddingResponse.data[0].embedding;

      const { error } = await supabase.from('knowledge_chunks').insert({
        section: chunk.section,
        section_title: chunk.section_title,
        content: chunk.content,
        embedding: embedding,
        metadata: { source: 'ai-factory-asistan-bilgi-tabani-v2' }
      });

      if (error) {
        log.error(`[seed] Kayit hatasi: ${chunk.section_title} - ${error.message}`);
      } else {
        processedCount++;
      }

      await new Promise(r => setTimeout(r, 200));
    }

    log.info(`[seed] ${processedCount} chunk kaydedildi.`);
    res.json({ status: 'ok', chunks_processed: processedCount, total_chunks: chunks.length });
  } catch (error) {
    log.error(`[seed] Seed hatasi: ${error.message}`, error);
    res.status(500).json({ error: error.message });
  }
});
// KB chunk listesi
app.get('/admin/kb/list', async (req, res) => {
  if (!process.env.ADMIN_SECRET || req.headers['x-admin-key'] !== process.env.ADMIN_SECRET) {
    return res.status(403).json({ error: 'Unauthorized' });
  }
  try {
    const { supabase } = require('./services/memory');
    const { data, error } = await supabase
      .from('knowledge_chunks')
      .select('id, section, section_title, content, created_at')
      .order('section');
      
    if (error) throw error;
    
    const formattedData = data.map(chunk => ({
      id: chunk.id,
      section: chunk.section,
      section_title: chunk.section_title,
      length: chunk.content ? chunk.content.length : 0,
      created_at: chunk.created_at
    }));
    
    res.json({ chunks: formattedData });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// KB chunk arama
app.get('/admin/kb/search', async (req, res) => {
  if (!process.env.ADMIN_SECRET || req.headers['x-admin-key'] !== process.env.ADMIN_SECRET) {
    return res.status(403).json({ error: 'Unauthorized' });
  }
  const query = req.query.q;
  if (!query) return res.status(400).json({ error: 'q parametresi gerekli' });
  
  try {
    const { supabase } = require('./services/memory');
    const { data, error } = await supabase
      .from('knowledge_chunks')
      .select('id, section, section_title, content')
      .ilike('content', `%${query}%`);
      
    if (error) throw error;
    res.json({ results: data });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// KB fiyat doğrulama
app.get('/admin/kb/validate', async (req, res) => {
  if (!process.env.ADMIN_SECRET || req.headers['x-admin-key'] !== process.env.ADMIN_SECRET) {
    return res.status(403).json({ error: 'Unauthorized' });
  }
  try {
    const { supabase } = require('./services/memory');
    const { data, error } = await supabase
      .from('knowledge_chunks')
      .select('content');
      
    if (error) throw error;
    
    const combinedContent = data.map(d => d.content).join('\n');
    const bannedPrices = ['$97', '$197', '$297', '$497', '$997', '$1997'];
    const foundBanned = [];
    
    bannedPrices.forEach(price => {
      const regex = new RegExp(`\\${price}\\b`);
      if (regex.test(combinedContent)) {
        foundBanned.push(price);
      }
    });

    res.json({ 
      valid: foundBanned.length === 0,
      banned_prices_found: foundBanned
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Tek chunk güncelleme
app.put('/admin/kb/update/:chunkId', async (req, res) => {
  if (!process.env.ADMIN_SECRET || req.headers['x-admin-key'] !== process.env.ADMIN_SECRET) {
    return res.status(403).json({ error: 'Unauthorized' });
  }
  const chunkId = req.params.chunkId;
  const { content } = req.body;
  if (!content) return res.status(400).json({ error: 'content gerekli' });
  
  try {
    const OpenAI = require('openai');
    const openai = new OpenAI({ apiKey: config.openaiApiKey });
    const { supabase } = require('./services/memory');
    
    const { data: chunkData, error: chunkErr } = await supabase
      .from('knowledge_chunks')
      .select('section_title')
      .eq('id', chunkId)
      .single();
      
    if (chunkErr || !chunkData) return res.status(404).json({ error: 'Chunk bulunamadı' });

    const embeddingResponse = await openai.embeddings.create({
      model: 'text-embedding-3-small',
      input: `[${chunkData.section_title}]\n${content}`,
      dimensions: 1536
    });

    const embedding = embeddingResponse.data[0].embedding;

    const { error: updateErr } = await supabase
      .from('knowledge_chunks')
      .update({ content, embedding })
      .eq('id', chunkId);

    if (updateErr) throw updateErr;

    res.json({ status: 'ok', message: 'Chunk başarıyla güncellendi' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.listen(config.port, () => {
  log.info(`[server] Whatsapp_Asistan ${config.port} portunda calisiyor.`);
});
