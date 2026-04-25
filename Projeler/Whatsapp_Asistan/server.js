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

// KVKK Aydınlatma Mesajı
const KVKK_MESSAGE = `Merhaba! 👋 Ben Dolunay Özeren'in yapay zekâ asistanıyım.

Sana yardımcı olabilmem için kişisel verilerin hakkında bilgilendirme yapmam gerekiyor.

KVKK Aydınlatma Metni: https://dolunay.ai/sozlesmeler/kvkk

Devam etmek için lütfen "Onaylıyorum" yaz.`;

// Hoşgeldin Mesajı
const WELCOME_MESSAGE = `Teşekkürler! 🙏 Artık sana AI Factory hakkında her konuda yardımcı olabilirim. Sormak istediğin bir şey var mı?`;

app.post('/webhook/message', async (req, res) => {
  // ManyChat webhook timeoutları için hemen 200 dönülür
  // Ancak arka planda işleme devam edilir
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

    log.info(`[webhook] Yeni mesaj alındı.`, { subscriberId });

    // 1. Subscriber kontrolü
    let subscriber = await getSubscriber(subscriberId);
    if (!subscriber) {
      log.info(`[webhook] Yeni subscriber oluşturuluyor...`, { subscriberId });
      subscriber = await createSubscriber(subscriberId, phoneNumber);
      
      // Yeni kullanıcıya doğrudan KVKK mesajı gönder
      await setCustomField(subscriberId, FIELD_ID, KVKK_MESSAGE);
      await sendFlow(subscriberId, FLOW_ID);
      return;
    }

    // 2. KVKK kontrolü
    if (!subscriber.kvkk_accepted) {
      const lowerMsg = messageContent.toLowerCase().trim();
      const isAccepted = lowerMsg === 'onaylıyorum' || lowerMsg === 'evet' || lowerMsg === 'kabul ediyorum' || lowerMsg === 'kabul';
      
      if (isAccepted) {
        log.info(`[webhook] Kullanıcı KVKK onayladı.`, { subscriberId });
        await acceptKVKK(subscriberId);
        
        await setCustomField(subscriberId, FIELD_ID, WELCOME_MESSAGE);
        await sendFlow(subscriberId, FLOW_ID);
      } else {
        log.info(`[webhook] Kullanıcı henüz KVKK onaylamadı, hatırlatma gönderiliyor.`, { subscriberId });
        await setCustomField(subscriberId, FIELD_ID, KVKK_MESSAGE);
        await sendFlow(subscriberId, FLOW_ID);
      }
      return;
    }

    // 3. Ses mesajı kontrolü ve transkripsiyon
    if (isAudioUrl(messageContent)) {
      log.info(`[webhook] Ses mesajı algılandı, transkribe ediliyor...`, { subscriberId });
      try {
        messageContent = await transcribeAudio(messageContent);
      } catch (err) {
        log.error(`[webhook] Ses mesajı çevrilemedi, kullanıcıya bilgi veriliyor.`, err);
        await setCustomField(subscriberId, FIELD_ID, "Özür dilerim, sesli mesajını şu an dinleyemiyorum. Lütfen bana yazılı olarak iletebilir misin?");
        await sendFlow(subscriberId, FLOW_ID);
        return;
      }
    }

    // Kullanıcı mesajını kaydet
    await saveMessage(subscriberId, 'user', messageContent);

    // 4. Dil algılama
    const detectedLanguage = await detectLanguage(messageContent);

    // 5. AI cevabı üret (RAG ve hafıza işlemleri ai_engine içinde)
    const aiResponse = await generateResponse(subscriberId, messageContent, detectedLanguage);

    // AI cevabını kaydet
    await saveMessage(subscriberId, 'assistant', aiResponse);

    // 6. ManyChat'e gönder
    await setCustomField(subscriberId, FIELD_ID, aiResponse);
    await sendFlow(subscriberId, FLOW_ID);
    
    log.info(`[webhook] İşlem başarıyla tamamlandı.`, { subscriberId });

  } catch (error) {
    log.error(`[webhook] Beklenmeyen hata: ${error.message}`, error);
  }
});

app.get('/health', (req, res) => {
  res.status(200).json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Admin: RAG bilgi tabanını seed et
app.post('/admin/seed-knowledge', async (req, res) => {
  try {
    const fs = require('fs');
    const path = require('path');
    const OpenAI = require('openai');
    const { supabase } = require('./services/memory');

    const openai = new OpenAI({ apiKey: config.openaiApiKey });

    // Body'den markdown içeriği al, yoksa dosyadan oku
    let mdContent = req.body.markdown_content;
    if (!mdContent) {
      const mdPath = path.join(__dirname, 'ai-factory-asistan-bilgi-tabani-v2.md');
      if (!fs.existsSync(mdPath)) {
        return res.status(404).json({ error: 'Bilgi tabanı dosyası bulunamadı. Body ile markdown_content gönderin.' });
      }
      mdContent = fs.readFileSync(mdPath, 'utf8');
    }
    
    // Markdown'ı chunk'lara ayır
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
        log.error(`[seed] Kayıt hatası: ${chunk.section_title} — ${error.message}`);
      } else {
        processedCount++;
      }

      await new Promise(r => setTimeout(r, 200));
    }

    log.info(`[seed] ✅ ${processedCount} chunk kaydedildi.`);
    res.json({ status: 'ok', chunks_processed: processedCount, total_chunks: chunks.length });
  } catch (error) {
    log.error(`[seed] Seed hatası: ${error.message}`, error);
    res.status(500).json({ error: error.message });
  }
});

app.listen(config.port, () => {
  log.info(`[server] Whatsapp_Asistan ${config.port} portunda çalışıyor.`);
});
