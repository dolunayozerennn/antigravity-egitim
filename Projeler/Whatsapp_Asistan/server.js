// server.js
const express = require('express');
const { config } = require('./config/env');
const log = require('./utils/logger');
const { getSubscriber, createSubscriber, acceptKVKK, saveMessage } = require('./services/memory');
const { setCustomField, sendFlow } = require('./services/manychat');
const { generateResponse } = require('./services/ai_engine');
const { detectLanguage } = require('./services/language_detector');
const { transcribeAudio, isAudioUrl } = require('./services/transcription');

const app = express();
app.use(express.json({ limit: '5mb' }));

// ============================================
// Health Check
// ============================================
app.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'whatsapp-asistan', timestamp: new Date().toISOString() });
});

// ============================================
// Ana Webhook Endpoint — ManyChat'ten gelen mesajlar
// ============================================
app.post('/webhook/message', async (req, res) => {
  const startTime = Date.now();
  
  try {
    const { subscriber_id, text, phone } = req.body;
    
    if (!subscriber_id) {
      log.warn('[webhook] subscriber_id eksik.');
      return res.status(400).json({ error: 'subscriber_id gerekli' });
    }

    const rawText = text || '';
    log.info(`[webhook] Mesaj alındı.`, { subscriber_id, textLength: rawText.length });

    // 1. Subscriber kontrolü (yoksa oluştur)
    let subscriber = await getSubscriber(subscriber_id);
    if (!subscriber) {
      subscriber = await createSubscriber(subscriber_id, phone || null);
      log.info(`[webhook] Yeni subscriber oluşturuldu.`, { subscriber_id });
    }

    // 2. KVKK kontrolü
    if (!subscriber.kvkk_accepted) {
      return await handleKVKK(subscriber, rawText, res);
    }

    // 3. Ses mesajı kontrolü
    let processedText = rawText;
    if (isAudioUrl(rawText)) {
      log.info(`[webhook] Ses mesajı tespit edildi, transkripsiyon başlıyor...`);
      try {
        processedText = await transcribeAudio(rawText);
        log.info(`[webhook] Transkripsiyon tamamlandı: ${processedText.substring(0, 50)}...`);
      } catch (e) {
        log.error(`[webhook] Transkripsiyon başarısız, metin olarak devam ediyor.`, e);
        processedText = rawText;
      }
    }

    // 4. Dil tespiti
    const detectedLanguage = await detectLanguage(processedText);

    // 5. Kullanıcı mesajını kaydet
    await saveMessage(subscriber_id, 'user', processedText);

    // 6. AI ile cevap üret
    const aiResponse = await generateResponse(subscriber_id, processedText, detectedLanguage);

    // 7. Cevabı kaydet
    await saveMessage(subscriber_id, 'assistant', aiResponse);

    // 8. ManyChat'e cevabı gönder (Custom Field üzerinden)
    const fieldSet = await setCustomField(subscriber_id, config.manychatFieldId, aiResponse);
    if (!fieldSet) {
      log.error(`[webhook] ManyChat Custom Field güncellenemedi!`);
    }

    // 9. ManyChat Flow'unu tetikle (cevabı göndermek için)
    await sendFlow(subscriber_id, config.manychatFlowId);

    const elapsed = Date.now() - startTime;
    log.info(`[webhook] İşlem tamamlandı`, { subscriber_id, elapsed_ms: elapsed });

    return res.json({ 
      status: 'ok', 
      response: aiResponse,
      elapsed_ms: elapsed 
    });

  } catch (error) {
    log.error(`[webhook] İşlem hatası: ${error.message}`, error);
    return res.status(500).json({ error: 'Sunucu hatası' });
  }
});

// ============================================
// KVKK Akışı
// ============================================
async function handleKVKK(subscriber, text, res) {
  const normalizedText = text.toLowerCase().trim();
  
  // "onay" veya "kabul" kelimelerini ara
  const isApproval = ['onay', 'kabul', 'onaylıyorum', 'kabul ediyorum', 'evet'].some(keyword => 
    normalizedText.includes(keyword)
  );

  if (isApproval) {
    await acceptKVKK(subscriber.subscriber_id);
    
    const approvalMessage = 'KVKK onayınız alınmıştır. Artık size yardımcı olabilirim! Nasıl yardımcı olabilirim?';
    await setCustomField(subscriber.subscriber_id, config.manychatFieldId, approvalMessage);
    await sendFlow(subscriber.subscriber_id, config.manychatFlowId);
    
    log.info(`[kvkk] KVKK onayı alındı.`, { subscriber_id: subscriber.subscriber_id });
    return res.json({ status: 'kvkk_accepted', response: approvalMessage });
  } else {
    const kvkkMessage = `Merhaba! AI Factory WhatsApp asistanı olarak size yardımcı olabilmem için kişisel verilerinizin işlenmesine ilişkin KVKK aydınlatma metnini onaylamanız gerekmektedir.\n\nOnaylamak için "Onay" yazın.`;
    await setCustomField(subscriber.subscriber_id, config.manychatFieldId, kvkkMessage);
    await sendFlow(subscriber.subscriber_id, config.manychatFlowId);
    
    log.info(`[kvkk] KVKK onay bekleniyor.`, { subscriber_id: subscriber.subscriber_id });
    return res.json({ status: 'kvkk_pending', response: kvkkMessage });
  }
}

// ============================================
// Admin: Bilgi Tabanını Seed Et
// ============================================
app.post('/admin/seed-knowledge', async (req, res) => {
  const authHeader = req.headers.authorization;
  if (!authHeader || authHeader !== `Bearer ${config.manychatApiToken}`) {
    return res.status(401).json({ error: 'Yetkisiz erişim' });
  }

  try {
    const { exec } = require('child_process');
    exec('node scripts/seed_knowledge.js', { cwd: __dirname }, (error, stdout, stderr) => {
      if (error) {
        log.error(`[admin] Seed başarısız: ${error.message}`);
        return res.status(500).json({ error: error.message });
      }
      log.info(`[admin] Seed tamamlandı.`);
      return res.json({ status: 'ok', output: stdout });
    });
  } catch (error) {
    log.error(`[admin] Seed hatası: ${error.message}`, error);
    return res.status(500).json({ error: error.message });
  }
});

// ============================================
// Sunucu Başlatma
// ============================================
app.listen(config.port, '0.0.0.0', () => {
  log.info(`[server] Whatsapp_Asistan çalışıyor`, { port: config.port });
});
