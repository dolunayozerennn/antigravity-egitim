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
  'Content-Type': 'application/json',
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
};

let customFieldsCache = null;
let customFieldsFetchPromise = null; // Fix: Cache stampede önleme

// Fix: fetchWithRetry — 8s timeout + 1 retry
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

// Fix: Telefon numarası normalizasyonu
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

  // Fix: Cache stampede — aynı anda birden fazla çağrıyı engelle
  if (customFieldsFetchPromise) {
    await customFieldsFetchPromise;
    return customFieldsCache?.[fieldName] || null;
  }

  try {
    customFieldsFetchPromise = fetchWithRetry(`${API_URL}/page/getCustomFields`, {
      method: 'GET',
      headers
    });
    const response = await customFieldsFetchPromise;
    const contentType = response.headers.get('content-type') || '';
    
    if (!contentType.includes('application/json')) {
      const text = await response.text();
      throw new Error(`API JSON dönmedi (${response.status} ${response.statusText}). Content-Type: ${contentType}. Body: ${text.substring(0, 500)}`);
    }

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

/**
 * Ana fonksiyon: subscriber yoksa oluştur, custom field'ları set et, flow'u tetikle
 */
async function ensureSubscriberAndSendFlow(phoneNumber, firstName, flowId) {
  let subscriberId;
  // Fix: Telefon numarasını normalize et
  phoneNumber = normalizePhone(phoneNumber);
  const context = { phoneNumber, firstName, flowId };
  
  log.info(`[manychat:engine] Flow tetikleme işlemi başlatıldı.`, context);

  // 1. Subscriber'ı bulmaya çalış (custom field üzerinden)
  subscriberId = await findSubscriberByPhone(phoneNumber);

  // 2. Eğer custom field ile bulunamadıysa, system fields üzerinden ara (fallback)
  if (!subscriberId) {
    subscriberId = await findSubscriberBySystemPhone(phoneNumber);
  }
  
  // 2.5 Eğer system fields de bulamazsa name ile ara
  if (!subscriberId) {
    subscriberId = await findSubscriberByName(firstName, phoneNumber);
  }

  if (!subscriberId) {
    // 3. Hala yoksa oluştur
    log.info(`[manychat:engine] Subscriber bulunamadı, oluşturuluyor...`);
    subscriberId = await createSubscriber(phoneNumber, firstName);
  } else {
    log.info(`[manychat:engine] Mevcut subscriber bulundu: ${subscriberId}`);
  }

  if (!subscriberId) {
    const errMsg = `Subscriber ID alınamadı (ne yaratılabildi ne de bulunabildi). ManyChat API kısıtlaması nedeniyle WhatsApp atlanacak.`;
    log.warn(`[manychat:engine] WARN: ${errMsg}`, context);
    throw new Error(errMsg);
  }

  // 4. Custom field'ları güncelle (İsim ve Telefon her halükarda güncellenir)
  await setCustomFields(subscriberId, {
    whatsapp_phone_text: phoneNumber,
    phone_text: phoneNumber,
    last_name: "."
  });

  // 5. Flow'u tetikle
  await sendFlow(subscriberId, flowId);

  log.info(`[manychat:engine] Flow başarıyla tetiklendi.`, { subscriberId, flowId });
  return subscriberId;
}

async function createSubscriber(phoneNumber, firstName) {
  try {
    const cleanFirstName = firstName ? firstName.trim() : '';
    const payload = {
      first_name: cleanFirstName,
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

    // Fix: Subscriber conflict — zaten varsa bul
    log.warn(`[manychat:api] ⚠️ createSubscriber başarısız (büyük ihtimalle mevcut).`, { message: data.message });
    let existingId = await findSubscriberByPhone(phoneNumber);
    if (!existingId) {
      existingId = await findSubscriberBySystemPhone(phoneNumber);
    }
    if (!existingId) {
      existingId = await findSubscriberByName(firstName, phoneNumber);
    }
    if (existingId) {
      log.info(`[manychat:api] Conflict sonrası mevcut subscriber bulundu.`, { existingId });
      return existingId;
    }
    
    // Eğer yaratılamadıysa ve bulunamadıysa (gerçek bir API hatası olabilir, örn geçersiz telefon formatı)
    const errReason = data.message || JSON.stringify(data);
    log.error(`[manychat:api] Subscriber yaratılamadı ve aramalarda da bulunamadı. Sebep: ${errReason}`);
    throw new Error(`ManyChat API Hatası: ${errReason}`);

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

    let foundId = null;
    if (data.status === 'success' && data.data) {
      if (Array.isArray(data.data) && data.data.length > 0) {
        foundId = data.data[0].id;
      } else if (!Array.isArray(data.data) && data.data.id) {
        foundId = data.data.id;
      }
    }

    if (foundId) {
      log.info(`[manychat:api] ✅ Subscriber başarıyla bulundu.`, { id: foundId });
      return foundId;
    }

    // Try without '+' sign if not found
    if (!foundId && phoneNumber.startsWith('+')) {
      const phoneNoPlus = phoneNumber.substring(1);
      const urlNoPlus = `${API_URL}/subscriber/findByCustomField?field_id=${fieldId}&field_value=${encodeURIComponent(phoneNoPlus)}`;
      log.debug(`[manychat:api] findByCustomField (without +) isteği atılıyor.`, { url: urlNoPlus });
      
      const responseNoPlus = await fetchWithRetry(urlNoPlus, {
        method: 'GET',
        headers
      });

      const dataNoPlus = await responseNoPlus.json();
      log.debug(`[manychat:api] findByCustomField (without +) yanıtı.`, dataNoPlus);

      if (dataNoPlus.status === 'success' && dataNoPlus.data) {
        if (Array.isArray(dataNoPlus.data) && dataNoPlus.data.length > 0) {
          foundId = dataNoPlus.data[0].id;
        } else if (!Array.isArray(dataNoPlus.data) && dataNoPlus.data.id) {
          foundId = dataNoPlus.data.id;
        }
      }
    }

    if (foundId) {
      log.info(`[manychat:api] ✅ Subscriber başarıyla bulundu (without +).`, { id: foundId });
      return foundId;
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
    const searchFields = ['phone', 'whatsapp_phone'];
    let foundId = null;

    for (const field of searchFields) {
      if (foundId) break;

      // ManyChat system field araması GET isteği ile yapılır.
      // Telefon numaralarındaki artı işareti vb. encode edilmeli.
      let url = `${API_URL}/subscriber/findBySystemField?${field}=${encodeURIComponent(phoneNumber)}`;
      log.debug(`[manychat:api] findBySystemField (${field}) isteği atılıyor.`, { url });

      let response = await fetchWithRetry(url, {
        method: 'GET',
        headers
      });

      let data = await response.json();
      log.debug(`[manychat:api] findBySystemField (${field}) yanıtı.`, data);

      if (data.status === 'success' && data.data) {
        if (Array.isArray(data.data) && data.data.length > 0) {
          foundId = data.data[0].id;
        } else if (!Array.isArray(data.data) && data.data.id) {
          foundId = data.data.id;
        }
      }

      // Try without '+' sign if not found
      if (!foundId && phoneNumber.startsWith('+')) {
        const phoneNoPlus = phoneNumber.substring(1);
        url = `${API_URL}/subscriber/findBySystemField?${field}=${encodeURIComponent(phoneNoPlus)}`;
        log.debug(`[manychat:api] findBySystemField (${field} without +) isteği atılıyor.`, { url });
        
        response = await fetchWithRetry(url, {
          method: 'GET',
          headers
        });
        
        data = await response.json();
        log.debug(`[manychat:api] findBySystemField (${field} without +) yanıtı.`, data);
        
        if (data.status === 'success' && data.data) {
          if (Array.isArray(data.data) && data.data.length > 0) {
            foundId = data.data[0].id;
          } else if (!Array.isArray(data.data) && data.data.id) {
            foundId = data.data.id;
          }
        }
      }
    }

    if (foundId) {
      log.info(`[manychat:api] ✅ Subscriber system field üzerinden bulundu.`, { id: foundId });
      return foundId;
    }

    log.info(`[manychat:api] ℹ️ Subscriber system field ile bulunamadı.`);
    return null;
  } catch (error) {
    log.error(`[manychat:api] ❌ findBySystemField ağ hatası: ${error.message}`, error);
    return null;
  }
}

async function findSubscriberByName(name, phoneNumber) {
  if (!name) return null;
  const cleanName = name.trim();
  try {
    const url = `${API_URL}/subscriber/findByName?name=${encodeURIComponent(cleanName)}`;
    log.debug(`[manychat:api] findByName isteği atılıyor.`, { url });
    
    const response = await fetchWithRetry(url, {
      method: 'GET',
      headers
    });

    const data = await response.json();
    log.debug(`[manychat:api] findByName yanıtı.`, { status: data.status, count: data.data?.length });

    if (data.status === 'success' && data.data && Array.isArray(data.data)) {
      if (data.data.length === 0) {
        log.info(`[manychat:api] ℹ️ Subscriber isimden bulunamadı.`);
        return null;
      }
      
      const cleanTargetPhone = normalizePhone(phoneNumber);
      const cleanTargetPhoneNoPlus = cleanTargetPhone.startsWith('+') ? cleanTargetPhone.substring(1) : cleanTargetPhone;
      
      for (const sub of data.data) {
        const wp = sub.whatsapp_phone ? normalizePhone(sub.whatsapp_phone) : null;
        const ph = sub.phone ? normalizePhone(sub.phone) : null;
        
        if (wp === cleanTargetPhone || wp === cleanTargetPhoneNoPlus || ph === cleanTargetPhone || ph === cleanTargetPhoneNoPlus) {
           log.info(`[manychat:api] ✅ Subscriber isim ve telefon eşleşmesiyle bulundu.`, { id: sub.id });
           return sub.id;
        }
      }
      
      if (data.data.length === 1) {
         log.info(`[manychat:api] ✅ Subscriber sadece isim eşleşmesiyle bulundu (tek eşleşme).`, { id: data.data[0].id });
         return data.data[0].id;
      }
      
      log.warn(`[manychat:api] ⚠️ İsim eşleşmesi bulundu ama telefon tutmadı ve birden fazla kayıt var. Güvenlik için atlanıyor.`);
    }
    
    return null;
  } catch (error) {
    log.error(`[manychat:api] ❌ findByName ağ hatası: ${error.message}`, error);
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
      // Fallback: If ID not found, try sending with field_name
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
  findSubscriberByName,
  setCustomFields,
  sendFlow
};