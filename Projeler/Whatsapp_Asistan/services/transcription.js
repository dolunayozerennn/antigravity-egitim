// services/transcription.js
const { config } = require('../config/env');
const log = require('../utils/logger');
const fetch = require('node-fetch');
const FormData = require('form-data');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { pipeline } = require('stream/promises');

async function downloadFile(url, tempFilePath) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Dosya indirilemedi: ${response.statusText}`);
  await pipeline(response.body, fs.createWriteStream(tempFilePath));
}

async function transcribeAudio(audioUrl) {
  const tempFilePath = path.join(os.tmpdir(), `audio_${Date.now()}.mp4`);
  
  try {
    log.info(`[transcription] Ses dosyası indiriliyor...`);
    await downloadFile(audioUrl, tempFilePath);
    
    log.info(`[transcription] Groq Whisper API'ye gönderiliyor...`);
    const form = new FormData();
    form.append('file', fs.createReadStream(tempFilePath));
    form.append('model', 'whisper-large-v3-turbo');
    form.append('language', 'tr');
    
    const response = await fetch('https://api.groq.com/openai/v1/audio/transcriptions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${config.groqApiKey}`,
        ...form.getHeaders()
      },
      body: form
    });
    
    const data = await response.json();
    if (data.error) throw new Error(data.error.message);
    
    log.info(`[transcription] Ses başarıyla metne çevrildi.`);
    return data.text;
  } catch (error) {
    log.error(`[transcription] Transkripsiyon hatası: ${error.message}`, error);
    throw error;
  } finally {
    // Geçici dosyayı temizle
    if (fs.existsSync(tempFilePath)) {
      fs.unlinkSync(tempFilePath);
    }
  }
}

function isAudioUrl(url) {
  if (!url) return false;
  return url.includes('lookaside') || url.includes('manybot') || url.includes('fbsbx');
}

module.exports = {
  transcribeAudio,
  isAudioUrl
};
