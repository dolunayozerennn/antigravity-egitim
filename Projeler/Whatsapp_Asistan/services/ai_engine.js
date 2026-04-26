// services/ai_engine.js
const OpenAI = require('openai');
const { config } = require('../config/env');
const log = require('../utils/logger');
const { queryKnowledge } = require('./knowledge_base');
const { getHistory } = require('./memory');

const openai = new OpenAI({ apiKey: config.openaiApiKey });

async function generateResponse(subscriberId, currentMessage, detectedLanguage) {
  try {
    log.info(`[ai_engine] AI cevabı üretiliyor...`, { subscriberId, language: detectedLanguage });
    
    // 1. RAG ile ilgili bilgileri çek
    const ragChunks = await queryKnowledge(currentMessage);
    
    // 2. Hafızadan geçmişi çek
    const history = await getHistory(subscriberId, 20);
    
    // 3. System prompt'u hazırla
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
Standard: $39/ay, $156/yıl
Premium: $59/ay, $236/yıl
VIP: $129/ay, $516/yıl
Yıllık = Aylık × 4 (4 ay öde, 8 ay bedava)
Bu fiyatlar dışında ($97, $197, $297, $497, $997, $1997 vb.) HİÇBİR rakam telaffuz etme. Bilgi tabanında farklı bir rakam görsen bile YUKARİDAKİ fiyatları kullan. Fiyatlar SABİTTİR.

[İTİRAZ YÖNETİMİ]
- Her itirazda sırayla: (1) duyguyu kabul et, (2) gerçek bilgiyle yanıtla, (3) kararı kişiye bırak. Baskı yapma.
- "Pahalı": Aylık $39 başlangıç ve yıllık (4 ay öde 8 bedava) avantajını hatırlat. KOBİ ise Ece ile görüşme öner.
- "Zamanım yok": Eğitimin kısa olduğunu (1-2 saat), kendi temposunda izleyeceğini belirt.
- "İndirim": İndirim YOK, fiyat sabit. Yıllık üyelikte avantaj olduğunu belirt.

[YÖNLENDİRME VE ESKALASYON KURALLARI]
- KOBİ Sinyali: Kişi KOBİ/İşletme sahibi ise, premium pakete ilgi duyuyorsa veya "detaylı konuşalım" diyorsa, Ece ile telefon görüşmesine yönlendir: "İstersen ekibimizden Ece seni arayıp detaylı anlatabilir, hangi numaradan ulaşalım?"
- Kayıt Linki: https://www.skool.com/yapay-zeka-factory/about (Asla erkenden paylaşma! Sadece açıkça istendiğinde veya olumlu sinyalde ver.)
- Dolunay'a Eskale Edilecekler: Para iadesi, şikayet, fatura sorunları, üyelik dondurma, manuel tier değişimi, sıradışı teknik sorular. Yönlendirme: "Bu konuyu Dolunay'a iletiyorum, en kısa sürede sana ulaşacak."
- Randevu (Premium/VIP): Kurulum desteği için Cal.com randevu linki verilir. AnyDesk ile bağlanılır.
- Onboarding (Yeni Üye): İlk iş "Buradan Başlayın" classroom'una yönlendir.

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

    // 4. API'ye gönderilecek mesaj listesini oluştur
    const messages = [
      { role: 'system', content: systemPrompt }
    ];

    // Geçmiş mesajları ekle
    for (const msg of history) {
      messages.push({ role: msg.role, content: msg.content });
    }

    // Mevcut mesajı ekle
    messages.push({ role: 'user', content: currentMessage });

    log.debug(`[ai_engine] OpenAI API'sine istek atılıyor...`);
    const response = await openai.chat.completions.create({
      model: 'gpt-4.1-mini',
      messages: messages,
      temperature: 0.3
    });

    const aiResponse = response.choices[0].message.content.trim();
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
