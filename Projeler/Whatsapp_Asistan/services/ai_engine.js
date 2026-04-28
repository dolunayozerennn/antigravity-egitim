// services/ai_engine.js
const OpenAI = require('openai');
const { config } = require('../config/env');
const log = require('../utils/logger');
const { queryKnowledge } = require('./knowledge_base');
const { getHistory } = require('./memory');
const { sendEscalationEmail } = require('./escalation');

const openai = new OpenAI({ apiKey: config.openaiApiKey });

const escalationTools = [{
  type: 'function',
  function: {
    name: 'escalate_to_dolunay',
    description: 'Konusmayi Dolunay Ozeren\'e eskale et ve email bildirimi gonder. Su durumlarda MUTLAKA cagir: (1) HASSAS KONU: Para iadesi talebi, sikayet, fatura sorunu, uyelik dondurma, tier degisimi, kizgin veya uzgun ton algiladiginda. (2) BILINMEYEN SORU: Bilgi tabaninda cevabi olmayan, RAG ile bulamadigi, guvensiz hissettigi sorular veya alisilmadik teknik konular.',
    parameters: {
      type: 'object',
      properties: {
        type: {
          type: 'string',
          enum: ['hassas_konu', 'bilinmeyen_soru'],
          description: 'hassas_konu: para iadesi, sikayet, fatura, uyelik dondurma, kizgin ton. bilinmeyen_soru: bilgi tabaninda cevabi yok veya guvenle cevaplayamiyorsun.'
        },
        reason: {
          type: 'string',
          description: 'Eskalasyonun sebebini kisa ve net acikla (Turkce). Ornek: Kullanici para iadesi istiyor veya Kullanici Antigravity ile mobil uygulama yapilip yapilamayacagini soruyor, bilgi tabaninda bu konu yok.'
        }
      },
      required: ['type', 'reason']
    }
  }
}];

async function generateResponse(subscriberId, currentMessage, detectedLanguage, subscriberInfo) {
  try {
    log.info(`[ai_engine] AI cevabı üretiliyor...`, { subscriberId, language: detectedLanguage });
    
    const ragChunks = await queryKnowledge(currentMessage);
    const history = await getHistory(subscriberId, 20);
    const todayDate = new Date().toLocaleDateString('tr-TR', { day: 'numeric', month: 'long', year: 'numeric' });
    
    const systemPrompt = `
[ROL]
Sen, Dolunay Özeren'in yapay zekâ asistanısın. AI Factory hakkında sorularını yanıtlamak için buradasın. ${detectedLanguage} dilinde cevap üret. Karşındaki kişi üye adayı veya mevcut üye olabilir.

[İLETİŞİM KURALLARI VE TON]
- Kısa ve öz yaz. İdeal 2-4 cümle, maksimum 6-8 cümle. Uzarsa parçalara böl.
- Özel biçimlendirme kullanma (*, **, \`, #, > gibi). Sadece düz metin yaz.
- Emoji çok az veya hiç kullanma.
- Sade Türkçe kullan, jargondan uzak dur. Samimi ol, "sen" dili kullan. (İstisna: VIP üye ile ilk temas "siz" olabilir).
- Empatik ol, satışçı veya robotik olma.
- Asla "bilgim yok", "elimde bilgi yok" deme. RAG bilgisinde yoksa "Bu konuyu Dolunay'a iletiyorum" diyerek geçiştir.
- Liste gerekiyorsa tire (—) ile ayrılmış kısa satırlar kullan.
- Kullanıcı arka arkaya birden fazla mesaj gönderirse, hepsine topluca tek cevap ver.

[SABİT FİYATLANDIRMA — ASLA DEĞİŞMEZ]
Standard (Girisimci Paketi): $39/ay
Premium (Isletme Paketi): $129/ay
VIP (Kurumsal Paket): $1.499/ay
Yillik uyelik mevcuttur, detaylar Skool ayarlarindan: https://www.skool.com/settings?t=communities
Bu fiyatlar dışında ($59, $236, $516, $97, $197, $297, $497, $997, $1997 vb.) HİÇBİR rakam telaffuz etme. Bilgi tabanindaki fiyat bilgisini kullan. Asagidaki fiyatlar referans icin verilmistir. Fiyatlar SABİTTİR.

[İTİRAZ YÖNETİMİ]
- Her itirazda sırayla: (1) duyguyu kabul et, (2) gerçek bilgiyle yanıtla, (3) kararı kişiye bırak. Baskı yapma.
- "Pahalı": Aylık $39 başlangıç ve yıllık (4 ay öde 8 bedava) avantajını hatırlat. KOBİ ise doğrudan yatırımın geri dönüşü (ROI) üzerine odaklan, fiyat indirimi yapma.
- "Zamanım yok": Eğitimin kısa olduğunu (1-2 saat), kendi temposunda izleyeceğini belirt.
- "İndirim": İndirim YOK, fiyat sabit. Yıllık üyelikte avantaj olduğunu belirt.

[YÖNLENDİRME VE ESKALASYON KURALLARI]
- KOBİ Sinyali: Kişi KOBİ/İşletme sahibi ise veya "detaylı konuşalım" diyorsa, telefon numarası ASLA İSTEME. Sadece AI Factory üzerinden tüm soruları yazılı yanıtlayabileceğini belirt.
- Kayıt Linki: https://www.skool.com/yapay-zeka-factory/plans (Kayıt linkini veya paket önerdiğinde MUHAKKAK bu linki mesaja ekle. Sadece paketleri önerdiğinde veya açıkça istendiğinde ver.)
- Dolunay'a Eskale Edilecekler: Para iadesi, şikayet, fatura sorunları, üyelik dondurma, manuel tier değişimi, sıradışı teknik sorular. Yönlendirme: "Bu konuyu Dolunay'a iletiyorum, en kısa sürede sana ulaşacak."
- Randevu: Kurulum desteği veya randevu SADECE satın alım tamamlandıktan sonra Skool topluluğu içinde Premium/VIP üyelere verilir. WhatsApp üzerinden asla randevu ayarlama veya telefon numarası isteme.
- Onboarding (Yeni Üye): İlk iş "Buradan Başlayın" classroom'una yönlendir.

[ESKALASYON — ZORUNLU TOOL KULLANIMI]
Asagidaki durumlarda escalate_to_dolunay tool'unu MUTLAKA cagir:
1. HASSAS KONU: Para iadesi, sikayet, fatura sorunlari, uyelik dondurma, tier degisimi, kizgin/uzgun ton algiladiginda.
2. BILINMEYEN SORU: Bilgi tabaninda cevabi olmayan, guvensiz hissettigin sorular, alisildik olmayan teknik konular.
Tool'u cagirdiktan sonra kullaniciya kisa ve empatik bir yanit ver. Ornegin: Bu konuyu Dolunay'a iletiyorum, en kisa surede sana ulasacak.
UNUTMA: Eskalasyonu KACIRILMASI, yanlis bilgi vermekten DAHA KOTUDUR. Suphede kalirsan, eskale et.

[KRİTİK YASAKLAR]
- Fiyatları USD/$ olarak koru. TL yazma veya dönüştürme.
- İndirim sözü VERME, özel kampanya uydurma.
- Para iadesini KENDİN onaylama veya reddetme ("Skool'un standart iade politikası geçerli" de ve Dolunay'a yönlendir).
- Garanti, kesin gelir vaadi veya sertifika sözü verme.
- Yapay zeka olduğunu İNKAR ETME. Sorulursa dürüstçe söyle.
- Ses mesajı, görsel veya sticker YANITLAMA, yazıyla dön.
- Tier kilitli içerik linkini veya başka üyelerin bilgisini SIZDIRMA.

[BUGÜNÜN TARİHİ]
${todayDate}

[İLGİLİ BİLGİLER]
${ragChunks}
    `.trim();

    const messages = [
      { role: 'system', content: systemPrompt }
    ];

    for (const msg of history) {
      messages.push({ role: msg.role, content: msg.content });
    }

    messages.push({ role: 'user', content: currentMessage });

    log.debug(`[ai_engine] OpenAI API'sine istek atılıyor...`);
    const response = await openai.chat.completions.create({
      model: 'gpt-4.1-mini',
      messages: messages,
      tools: escalationTools,
      tool_choice: 'auto',
      temperature: 0.3
    });

    const responseMessage = response.choices[0].message;

    if (responseMessage.tool_calls && responseMessage.tool_calls.length > 0) {
      for (const tool_call of responseMessage.tool_calls) {
        if (tool_call.function.name === 'escalate_to_dolunay') {
          try {
            const args = JSON.parse(tool_call.function.arguments);
            const { type, reason } = args;
            
            const recentMessages = history.slice(-5);
            
            sendEscalationEmail({
              type,
              subscriberId: subscriberInfo.subscriberId,
              phoneNumber: subscriberInfo.phoneNumber,
              reason,
              recentMessages
            }).catch(err => log.error(`[ai_engine] sendEscalationEmail hatası: ${err.message}`, err));
            
            messages.push(responseMessage);
            messages.push({
              role: 'tool',
              tool_call_id: tool_call.id,
              content: 'Eskalasyon emaili gonderildi.'
            });
            
          } catch (e) {
            log.error(`[ai_engine] Tool parse hatasi: ${e.message}`);
          }
        }
      }
      
      const secondResponse = await openai.chat.completions.create({
        model: 'gpt-4.1-mini',
        messages: messages,
        temperature: 0.3
      });
      
      const aiResponse = secondResponse.choices[0].message.content.trim();
      log.info(`[ai_engine] AI cevabı (eskalasyon sonrasi) başarıyla üretildi.`);
      return aiResponse;
    }

    const aiResponse = responseMessage.content.trim();
    log.info(`[ai_engine] AI cevabı başarıyla üretildi.`);
    
    return aiResponse;
  } catch (error) {
    log.error(`[ai_engine] generateResponse hatası: ${error.message}`, error);
    throw error;
  }
}

module.exports = {
  generateResponse
};
