// ============================================================
// server.js — WhatsApp Onboarding Express Server
// ============================================================
// Webhook endpoints + Health check + Cron initialization
//
// Endpoints:
//   POST /webhook/new-paid-member    — Zapier Zap #1
//   POST /webhook/membership-questions — Zapier Zap #2
//   POST /webhook/wa-optin           — ManyChat WhatsApp Opt-in (Hibrit Fallback)
//   POST /webhook/wa-failed          — ManyChat Fallback
//   GET  /health                     — Monitoring
// ============================================================

// 1. Fail-Fast: env doğrulama (boot time)
const { validateEnv, config } = require('./config/env');
validateEnv();

const express = require('express');
const app = express();
const moment = require('moment-timezone');

app.use(express.json());

const { ONBOARDING_FLOWS } = require('./config/templates');
const notion = require('./services/notion');
const manychat = require('./services/manychat');
const { validatePhone } = require('./services/phoneValidator');
const resend = require('./services/resend');
const log = require('./utils/logger');

// POST /webhook/new-paid-member
app.post('/webhook/new-paid-member', async (req, res) => {
  try {
    const { transaction_id, first_name, last_name, email, date } = req.body;

    log.info(`[new-paid-member] Gelen veri: ${JSON.stringify(req.body)}`);

    if (!transaction_id || !first_name) {
      log.warn('[new-paid-member] Eksik veri, atlanıyor');
      return res.status(400).json({ error: 'transaction_id ve first_name zorunlu' });
    }

    const existing = await notion.findByTransactionId(transaction_id);

    if (existing) {
      await notion.updatePage(existing.id, {
        email: email || null,
        lastName: last_name || null
      });
      log.info(`[new-paid-member] Mevcut kayıt güncellendi: ${transaction_id}`);
    } else {
      await notion.createMember({
        firstName: first_name,
        lastName: last_name || '',
        email: email || '',
        transactionId: transaction_id,
        registrationDate: date || moment().tz('Europe/Istanbul').format('YYYY-MM-DD'),
        onboardingStatus: "bekliyor"
      });
      log.info(`[new-paid-member] Yeni kayıt: ${first_name} ${last_name} (${email})`);
    }

    res.status(200).json({ success: true });
  } catch (error) {
    log.error(`[new-paid-member] HATA: ${error.message}`, error.stack);
    res.status(500).json({ error: error.message });
  }
});

// POST /webhook/membership-questions
app.post('/webhook/membership-questions', async (req, res) => {
  try {
    const { transaction_id, first_name, last_name, answer_1, email } = req.body;

    log.info(`[membership-questions] Gelen veri: ${JSON.stringify(req.body)}`);

    if (!answer_1) {
      log.warn('[membership-questions] answer_1 boş, atlanıyor');
      return res.status(400).json({ error: 'answer_1 zorunlu' });
    }

    // 0. Eski üye kontrolü
    const isEmailValid = email && email !== "No data" && email.trim() !== "";
    if (isEmailValid) {
      const existingByEmail = await notion.findByEmail(email.trim());
      if (existingByEmail && existingByEmail.onboardingStatus === 'atlandı') {
        log.info(`[membership-questions] Eski üye atlanıyor (email eşleşmesi): ${email}`);
        return res.status(200).json({ success: true, skipped: true, reason: 'eski_uye' });
      }
    } else {
      if (first_name && first_name !== "No data") {
        const existingByName = await notion.findByName(first_name, last_name);
        if (existingByName && existingByName.onboardingStatus === 'atlandı') {
          log.info(`[membership-questions] Eski üye atlanıyor (isim eşleşmesi): ${first_name} ${last_name}`);
          return res.status(200).json({ success: true, skipped: true, reason: 'eski_uye' });
        }
      }
    }

    // 1. Telefon numarasını valide et
    const phoneResult = await validatePhone(answer_1);
    log.info(`[membership-questions] Validasyon sonucu: ${JSON.stringify(phoneResult)}`);

    // 2. Notion'da kaydı bul
    let member = await notion.findByTransactionId(transaction_id);

    if (!member) {
      member = await notion.createMember({
        firstName: first_name,
        lastName: last_name || '',
        transactionId: transaction_id,
        onboardingStatus: "bekliyor"
      });
      log.info(`[membership-questions] Kayıt oluşturuldu (new-paid-member henüz gelmemiş)`);
    }

    // 3. Deduplication kontrolü
    const skipStatuses = ['whatsapp', 'email', 'tamamlandı', 'error'];
    if (skipStatuses.includes(member.onboardingStatus)) {
      log.info(`[membership-questions] Zaten onboarding'de veya tamamlanmış, atlanıyor: ${transaction_id}`);
      return res.status(200).json({ success: true, skipped: true });
    }

    if (phoneResult.valid && phoneResult.confidence >= 0.5) {
      // 4a. Telefon numarası ile deduplication
      const existingPhone = await notion.findByPhone(phoneResult.normalized);
      if (existingPhone && existingPhone.id !== member.id) {
        log.warn(`[membership-questions] Bu numara başka hesapta kayıtlı: ${phoneResult.normalized}`);
        await notion.updatePage(member.id, {
          notes: `Telefon ${phoneResult.normalized} başka hesapta mevcut — dedup`,
          onboardingStatus: "atlandı"
        });
        return res.status(200).json({ success: true, skipped: true });
      }

      // 5. ManyChat'te subscriber oluştur + Gün 0 flow'unu tetikle
      await manychat.ensureSubscriberAndSendFlow(
        phoneResult.normalized,
        first_name,
        ONBOARDING_FLOWS[0].flow_id
      );

      // 6. Notion'ı güncelle
      const nowWa = moment().tz('Europe/Istanbul');
      const startDateWa = nowWa.hour() < 6
        ? nowWa.clone().subtract(1, 'day').format('YYYY-MM-DD')
        : nowWa.format('YYYY-MM-DD');
      
      await notion.updatePage(member.id, {
        phone: phoneResult.normalized,
        onboardingStatus: "whatsapp",
        onboardingChannel: "whatsapp",
        onboardingStep: 0,
        onboardingStartDate: startDateWa
      });

      log.info(`[membership-questions] WhatsApp onboarding başlatıldı: ${first_name} → ${phoneResult.normalized} (Güven: ${phoneResult.confidence})`);

    } else {
      // 4b. Geçersiz numara veya Düşük Güven Skoru → Email fallback
      const failReason = !phoneResult.valid ? phoneResult.reason : "Düşük güven skoru";
      const confidenceStr = phoneResult.confidence !== undefined ? phoneResult.confidence : 'N/A';
      
      const nowEmail = moment().tz('Europe/Istanbul');
      const startDateEmail = nowEmail.hour() < 6
        ? nowEmail.clone().subtract(1, 'day').format('YYYY-MM-DD')
        : nowEmail.format('YYYY-MM-DD');

      if (member.email) {
        await resend.sendOnboardingEmail(member.email, first_name, 0);
      }

      await notion.updatePage(member.id, {
        onboardingStatus: "email",
        onboardingChannel: "email",
        onboardingStep: 0,
        onboardingStartDate: startDateEmail,
        notes: `Telefon cevabı: "${answer_1}" — Sebep: ${failReason} (Güven: ${confidenceStr})`
      });

      log.info(`[membership-questions] Email fallback: ${first_name} — ${phoneResult.reason}`);
    }

    res.status(200).json({ success: true });
  } catch (error) {
    log.error(`[membership-questions] HATA: ${error.message}`, error.stack);
    res.status(500).json({ error: error.message });
  }
});

// POST /webhook/wa-optin
app.post('/webhook/wa-optin', async (req, res) => {
  try {
    const { phone: rawPhone, first_name } = req.body;
    const phone = rawPhone ? rawPhone.replace(/^\+/, '') : null;

    log.info(`[wa-optin] Gelen veri: ${JSON.stringify(req.body)}`);

    if (!phone) {
      log.warn('[wa-optin] phone eksik, atlanıyor');
      return res.status(400).json({ error: 'phone zorunlu' });
    }

    const member = await notion.findByPhone(phone);
    if (!member) {
      log.warn(`[wa-optin] Notion'da kullanıcı bulunamadı: ${phone}`);
      return res.status(404).json({ error: 'Kullanıcı bulunamadı' });
    }

    if (member.onboardingStatus !== 'email') {
      log.info(`[wa-optin] Statü "email" değil (${member.onboardingStatus}), atlanıyor: ${phone}`);
      return res.status(200).json({ success: true, skipped: true, reason: `Statü: ${member.onboardingStatus}` });
    }

    const currentNotes = member.notes ? `${member.notes}\n` : '';
    const newNote = `${currentNotes}[WA-OPTIN] Kullanıcı email'den WhatsApp'a geçiş yaptı — ${new Date().toISOString()}`;
    const currentStep = member.onboardingStep || 0;

    if (currentStep >= 6) {
      await notion.updatePage(member.id, {
        onboardingStatus: "tamamlandı",
        onboardingChannel: "whatsapp",
        notes: newNote
      });
      log.info(`[wa-optin] Step >= 6, onboarding tamamlandı olarak işaretlendi: ${member.firstName} (${phone})`);
    } else {
      const nextStep = currentStep + 1;
      const nextFlow = ONBOARDING_FLOWS[nextStep];

      if (nextFlow && nextFlow.flow_id) {
        await manychat.ensureSubscriberAndSendFlow(
          phone,
          first_name || member.firstName,
          nextFlow.flow_id
        );
        log.info(`[wa-optin] ManyChat flow tetiklendi: Step ${nextStep} → ${nextFlow.flow_id}`);
      }

      await notion.updatePage(member.id, {
        onboardingStatus: "whatsapp",
        onboardingChannel: "whatsapp",
        onboardingStep: nextStep,
        notes: newNote
      });
      log.info(`[wa-optin] Email'den WhatsApp'a geçiş tamamlandı: ${member.firstName} (${phone}), Step: ${currentStep} → ${nextStep}`);
    }

    res.status(200).json({ success: true });
  } catch (error) {
    log.error(`[wa-optin] HATA: ${error.message}`, error.stack);
    res.status(500).json({ error: error.message });
  }
});

// POST /webhook/wa-failed
app.post('/webhook/wa-failed', async (req, res) => {
  try {
    const { phone: rawPhone, reason } = req.body;
    const phone = rawPhone ? rawPhone.replace(/^\+/, '') : null;

    log.info(`[wa-failed] Gelen veri: ${JSON.stringify(req.body)}`);

    if (!phone) {
      log.warn('[wa-failed] phone eksik, atlanıyor');
      return res.status(400).json({ error: 'phone zorunlu' });
    }

    const member = await notion.findByPhone(phone);
    if (!member) {
      log.warn(`[wa-failed] Notion'da kullanıcı bulunamadı: ${phone}`);
      return res.status(404).json({ error: 'Kullanıcı bulunamadı' });
    }

    const currentNotes = member.notes ? `${member.notes}\n` : '';
    const newNote = `${currentNotes}[WA-FAILED] Sebep: ${reason || 'Bilinmiyor'} — Email'e yönlendirildi.`;

    await notion.updatePage(member.id, {
      onboardingStatus: "email",
      onboardingChannel: "email",
      notes: newNote
    });

    log.info(`[wa-failed] Notion güncellendi, email kanalına alındı: ${member.firstName} (${phone})`);

    if (member.email) {
      try {
        await resend.sendHybridFallbackEmail(member.email, member.firstName, member.onboardingStep || 0, config.waBusinessPhone);
        log.info(`[wa-failed] Hibrit fallback email tetiklendi: ${member.email}`);
      } catch (emailErr) {
        log.error(`[wa-failed] Email gönderme hatası: ${emailErr.message}`, emailErr.stack);
      }
    } else {
      log.warn(`[wa-failed] Kullanıcının emaili yok, email atılamadı: ${member.firstName}`);
    }

    res.status(200).json({ success: true });
  } catch (error) {
    log.error(`[wa-failed] HATA: ${error.message}`, error.stack);
    res.status(500).json({ error: error.message });
  }
});

// POST /admin/trigger-flow
app.post('/admin/trigger-flow', async (req, res) => {
  try {
    const { phone, first_name, flow_step } = req.body;

    log.info(`[admin/trigger-flow] Gelen istek: ${JSON.stringify(req.body)}`);

    if (!phone || !first_name) {
      return res.status(400).json({ error: 'phone ve first_name zorunlu' });
    }

    const step = flow_step !== undefined ? flow_step : 0;
    const flowConfig = ONBOARDING_FLOWS[step];

    if (!flowConfig || !flowConfig.flow_id) {
      return res.status(400).json({ error: `Geçersiz flow_step: ${step}` });
    }

    const subscriberId = await manychat.ensureSubscriberAndSendFlow(
      phone,
      first_name,
      flowConfig.flow_id
    );

    log.info(`[admin/trigger-flow] ✅ Başarılı: ${first_name} → Step ${step} (${flowConfig.description})`);

    res.status(200).json({
      success: true,
      subscriberId,
      flow: {
        step,
        flow_id: flowConfig.flow_id,
        description: flowConfig.description
      }
    });
  } catch (error) {
    log.error(`[admin/trigger-flow] HATA: ${error.message}`, error.stack);
    res.status(500).json({ error: error.message });
  }
});

// GET /health
app.get('/health', async (req, res) => {
  try {
    const members = await notion.getActiveOnboardingMembers();
    res.json({
      status: 'ok',
      timestamp: new Date().toISOString(),
      timezone: config.cronTimezone,
      activeOnboardings: members.length,
      services: {
        notion: 'connected',
        groq: config.groqApiKey ? 'configured' : 'missing',
        manychat: config.manychatApiToken ? 'configured' : 'missing',
        resend: config.resendApiKey ? 'configured' : 'not_configured'
      }
    });
  } catch (error) {
    res.status(500).json({ status: 'error', error: error.message });
  }
});

require('./cron');

const PORT = config.port;
app.listen(PORT, '0.0.0.0', () => {
  log.info(`WhatsApp Onboarding server başlatıldı: 0.0.0.0:${PORT}`);
  log.info(`Webhook URL'ler:`);
  log.info(`  POST /webhook/new-paid-member`);
  log.info(`  POST /webhook/membership-questions`);
  log.info(`  POST /webhook/wa-optin`);
  log.info(`  POST /webhook/wa-failed`);
  log.info(`  POST /admin/trigger-flow`);
  log.info(`  GET  /health`);
});
