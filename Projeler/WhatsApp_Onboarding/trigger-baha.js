const { config } = require('./config/env');
const notion = require('./services/notion');
const manychat = require('./services/manychat');
const { ONBOARDING_FLOWS } = require('./config/templates');

async function run() {
  try {
    console.log("Shahrud veya Baha aranıyor...");
    const queries = ['Shahrud', 'Baha', 'Shahrud Baha', 'Aghayev'];
    let targetUser = null;
    for (const q of queries) {
      const user = await notion.findByName(q);
      if (user) {
        targetUser = user;
        console.log(`Kullanıcı bulundu: ${user.firstName} ${user.lastName} | Phone: ${user.phone} | Email: ${user.email} (Query: ${q})`);
        break;
      }
    }

    if (!targetUser) {
      console.log("Hiçbiri bulunamadı.");
      return;
    }

    if (targetUser.phone) {
      console.log(`ManyChat tetikleniyor: ${targetUser.phone}`);
      const subscriberId = await manychat.ensureSubscriberAndSendFlow(targetUser.phone, targetUser.firstName, ONBOARDING_FLOWS[0].flow_id);
      console.log("Başarılı, Subscriber ID:", subscriberId);

      await notion.updatePage(targetUser.id, {
        onboardingStatus: "whatsapp",
        onboardingChannel: "whatsapp",
        onboardingStep: 0,
        notes: `[MANUAL TRIGGER] Flow manuel olarak başlatıldı.`
      });
      console.log("Notion güncellendi.");
    } else if (targetUser.email) {
      console.log(`Telefon yok, Email üzerinden tetikleniyor: ${targetUser.email}`);
      const resend = require('./services/resend');
      await resend.sendOnboardingEmail(targetUser.email, targetUser.firstName, 0);
      console.log("Email gönderildi.");

      await notion.updatePage(targetUser.id, {
        onboardingStatus: "email",
        onboardingChannel: "email",
        onboardingStep: 0,
        notes: `[MANUAL TRIGGER] Email flow manuel olarak başlatıldı.`
      });
      console.log("Notion güncellendi.");
    } else {
      console.log("Telefon veya email bulunamadı.");
    }
  } catch (err) {
    console.error("HATA:", err);
  }
}

run();
