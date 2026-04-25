// services/manychat.js
const { config } = require('../config/env');
const log = require('../utils/logger');
const fetch = require('node-fetch');

const API_URL = "https://api.manychat.com/fb";
const headers = {
  'Authorization': `Bearer ${config.manychatApiToken}`,
  'Content-Type': 'application/json'
};

async function setCustomField(subscriberId, fieldId, value) {
  const payload = { subscriber_id: subscriberId, field_id: parseInt(fieldId), field_value: String(value) };
  log.debug(`[manychat] setCustomField isteği atılıyor.`, { subscriberId, fieldId });
  try {
    const response = await fetch(`${API_URL}/subscriber/setCustomField`, { method: 'POST', headers, body: JSON.stringify(payload) });
    const data = await response.json();
    if (data.status !== 'success') { log.warn(`[manychat] setCustomField başarısız/uyarı:`, data); return false; }
    log.info(`[manychat] Custom Field başarıyla güncellendi.`);
    return true;
  } catch (error) { log.error(`[manychat] setCustomField hatası: ${error.message}`, error); return false; }
}

async function sendFlow(subscriberId, flowId) {
  const payload = { subscriber_id: subscriberId, flow_ns: flowId };
  log.debug(`[manychat] sendFlow isteği atılıyor.`, { subscriberId, flowId });
  try {
    const response = await fetch(`${API_URL}/sending/sendFlow`, { method: 'POST', headers, body: JSON.stringify(payload) });
    const data = await response.json();
    if (data.status !== 'success') { log.error(`[manychat] sendFlow başarısız.`, data); throw new Error(`sendFlow hatası: ${JSON.stringify(data)}`); }
    log.info(`[manychat] sendFlow başarıyla tamamlandı.`);
    return data;
  } catch (error) { log.error(`[manychat] sendFlow hatası: ${error.message}`, error); throw error; }
}

module.exports = { setCustomField, sendFlow };
