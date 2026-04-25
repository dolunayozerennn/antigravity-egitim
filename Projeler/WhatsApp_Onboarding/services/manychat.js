// ============================================================
// services/manychat.js — ManyChat WhatsApp API
// ============================================================
// KRİTİK: WhatsApp business-initiated mesaj için sendFlow kullanılır.
// sendContent KULLANILMAZ — template mesajlar flow içinde tetiklenir.
// ============================================================

const { config } = require('../config/env');
const log = require('../utils/logger');

const API_URL = "https://api.manychat.com/fb";
const headers = {
  'Authorization': `Bearer ${config.manychatApiToken}`,
  'Content-Type': 'application/json'
};

let customFieldsCache = null;
let customFieldsFetchPromise = null;

async function fetchWithRetry(url, options, retries = 1) {
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const response = await fetch(url, {
        ...options,
        signal: AbortSignal.timeout(8000)
      });
      return response;
    } catch (err) {
      if (attempt < retries && (err.name === 'TimeoutError' || err.name === 'AbortError')) {
        log.warn(`[manychat:retry] Timeout, tekrar deneniyor... (${attempt + 1}/${retries})`);
        continue;
      }
      throw err;
    }
  }
}

function normalizePhone(phone) {
  if (!phone) return phone;
  let cleaned = phone.replace(/[\s\-()]/g, '');
  if (!cleaned.startsWith('+')) cleaned = '+' + cleaned;
  return cleaned;
}

async function getCustomFieldId(fieldName) {
  if (customFieldsCache && customFieldsCache[fieldName]) {
    return customFieldsCache[fieldName];
  }

  if (customFieldsFetchPromise) {
    await customFieldsFetchPromise;
    return customFieldsCache?.[fieldName] || null;
  }

  try {
    customFieldsFetchPromise = fetchWithRetry(`${API_URL}/subscriber/getCustomFields`, {
      method: 'GET',
      headers
    });
    const response = await customFieldsFetchPromise;
    const data = await response.json();
    if (data.status === 'success' && data.data) {
      customFieldsCache = {};
      for (const field of data.data) {
        customFieldsCache[field.name] = field.id;
      }
      return customFieldsCache[fieldName] || null;
    }
  } catch (error) {
    log.error(`[manychat:api] getCustomFields hatası: ${error.message}`, error);
  } finally {
    customFieldsFetchPromise = null;
  }
  return null;
}

async function ensureSubscriberAndSendFlow(phoneNumber, firstName, flowId) {
  let subscriberId;
  phoneNumber = normalizePhone(phoneNumber);
  const context = { phoneNumber, firstName, flowId };
  
  log.info(`[manychat:engine] Flow tetikleme işlemi başlatıldı.`, context);

  subscriberId = await findSubscriberByPhone(phoneNumber);
  log.debug(`[manychat:engine] Arama sonucu (Custom Field):`, { subscriberId });

  if (!subscriberId) {
    subscriberId = await findSubscriberBySystemPhone(phoneNumber);
    log.debug(`[manychat:engine] Arama sonucu (System Field):`, { subscriberId });
  }

  if (!subscriberId) {
    log.info(`[manychat:engine] Subscriber bulunamadı, oluşturuluyor...`);
    subscriberId = await createSubscriber(phoneNumber, firstName);
  } else {
    log.info(`[manychat:engine] Mevcut subscriber bulundu, oluşturma adımı atlanıyor.`);
  }

  if (!subscriberId) {
    const errMsg = `Subscriber ID alınamadı (ne yaratılabildi ne de bulunabildi).`;
    log.error(`[manychat:engine] FATAL: ${errMsg}`, context);
    throw new Error(errMsg);
  }

  log.debug(`[manychat:engine] Custom fields güncelleniyor...`, { subscriberId });
  await setCustomFields(subscriberId, {
    onboarding_name: firstName,
    whatsapp_phone_text: phoneNumber
  });

  log.info(`[manychat:engine] Flow gönderimi çağrılıyor...`, { subscriberId, flowId });
  const flowResult = await sendFlow(subscriberId, flowId);

  log.info(`[manychat:engine] ✅ Flow gönderimi başarıyla tamamlandı.`, { 
    subscriberId, 
    flowId, 
    manychatStatus: flowResult.status 
  });
  
  return subscriberId;
}

async function createSubscriber(phoneNumber, firstName) {
  try {
    const payload = {
      first_name: firstName,
      whatsapp_phone: phoneNumber,
      consent_phrase: "onboarding"
    };
    
    log.debug(`[manychat:api] createSubscriber isteği atılıyor.`, payload);
    
    const response = await fetchWithRetry(`${API_URL}/subscriber/createSubscriber`, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload)
    });

    const data = await response.json();
    log.debug(`[manychat:api] createSubscriber yanıtı.`, data);

    if (data.status === 'success') {
      log.info(`[manychat:api] ✅ Yeni subscriber oluşturuldu: ${phoneNumber}`, { id: data.data.id });
      return data.data.id;
    }

    log.warn(`[manychat:api] ⚠️ createSubscriber başarısız (büyük ihtimalle mevcut).`, { message: data.message });
    let existingId = await findSubscriberByPhone(phoneNumber);
    if (!existingId) {
      existingId = await findSubscriberBySystemPhone(phoneNumber);
    }
    if (existingId) {
      log.info(`[manychat:api] Conflict sonrası mevcut subscriber bulundu.`, { existingId });
    }
    return existingId;

  } catch (error) {
    log.error(`[manychat:api] ❌ createSubscriber ağ hatası: ${error.message}`, error);
    throw error;
  }
}

async function findSubscriberByPhone(phoneNumber) {
  try {
    const fieldId = await getCustomFieldId('whatsapp_phone_text');
    if (!fieldId) {
      log.warn(`[manychat:api] whatsapp_phone_text custom field ID alınamadı.`);
      return null;
    }

    const url = `${API_URL}/subscriber/findByCustomField?field_id=${fieldId}&field_value=${encodeURIComponent(phoneNumber)}`;
    
    log.debug(`[manychat:api] findByCustomField isteği atılıyor.`, { url });
    
    const response = await fetchWithRetry(url, {
      method: 'GET',
      headers
    });

    const data = await response.json();
    log.debug(`[manychat:api] findByCustomField yanıtı.`, data);

    if (data.status === 'success' && data.data) {
      log.info(`[manychat:api] ✅ Subscriber başarıyla bulundu.`, { id: data.data.id });
      return data.data.id;
    }

    log.info(`[manychat:api] ℹ️ Subscriber bulunamadı.`);
    return null;
  } catch (error) {
    log.error(`[manychat:api] ❌ findByCustomField ağ hatası: ${error.message}`, error);
    return null;
  }
}

async function findSubscriberBySystemPhone(phoneNumber) {
  try {
    const url = `${API_URL}/subscriber/findBySystemField?phone=${encodeURIComponent(phoneNumber)}`;
    log.debug(`[manychat:api] findBySystemField (phone) isteği atılıyor.`, { url });

    const response = await fetchWithRetry(url, {
      method: 'GET',
      headers
    });

    const data = await response.json();
    log.debug(`[manychat:api] findBySystemField (phone) yanıtı.`, data);

    let foundId = null;
    if (data.status === 'success' && data.data) {
      if (Array.isArray(data.data) && data.data.length > 0) {
        foundId = data.data[0].id;
      } else if (!Array.isArray(data.data) && data.data.id) {
        foundId = data.data.id;
      }
    }

    if (foundId) {
      log.info(`[manychat:api] ✅ Subscriber system field üzerinden bulundu.`, { id: foundId });
      return foundId;
    }

    log.info(`[manychat:api] ℹ️ Subscriber system field ile bulunamadı.`);
    return null;
  } catch (error) {
    log.error(`[manychat:api] ❌ findBySystemField (phone) ağ hatası: ${error.message}`, error);
    return null;
  }
}

async function setCustomFields(subscriberId, fields) {
  const fieldArray = [];
  for (const [name, value] of Object.entries(fields)) {
    const fieldId = await getCustomFieldId(name);
    if (fieldId) {
      fieldArray.push({
        field_id: fieldId,
        field_value: String(value)
      });
    } else {
      fieldArray.push({
        field_name: name,
        field_value: String(value)
      });
    }
  }

  const payload = {
    subscriber_id: subscriberId,
    fields: fieldArray
  };

  log.debug(`[manychat:api] setCustomFields isteği atılıyor.`, payload);

  const response = await fetchWithRetry(`${API_URL}/subscriber/setCustomFields`, {
    method: 'POST',
    headers,
    body: JSON.stringify(payload)
  });

  const data = await response.json();
  log.debug(`[manychat:api] setCustomFields yanıtı.`, data);

  if (data.status !== 'success') {
    log.warn(`[manychat:api] ⚠️ setCustomFields başarısız/uyarı:`, data);
  } else {
    log.info(`[manychat:api] ✅ Custom Fields güncellendi.`);
  }
}

async function sendFlow(subscriberId, flowId) {
  const payload = {
    subscriber_id: subscriberId,
    flow_ns: flowId
  };
  
  log.debug(`[manychat:api] sendFlow isteği atılıyor.`, payload);

  const response = await fetchWithRetry(`${API_URL}/sending/sendFlow`, {
    method: 'POST',
    headers,
    body: JSON.stringify(payload)
  });

  const data = await response.json();
  log.debug(`[manychat:api] sendFlow yanıtı.`, data);

  if (data.status !== 'success') {
    log.error(`[manychat:api] ❌ sendFlow başarısız.`, data);
    throw new Error(`sendFlow hatası: ${JSON.stringify(data)}`);
  }

  return data;
}

module.exports = {
  ensureSubscriberAndSendFlow,
  createSubscriber,
  findSubscriberByPhone,
  findSubscriberBySystemPhone,
  setCustomFields,
  sendFlow
};
