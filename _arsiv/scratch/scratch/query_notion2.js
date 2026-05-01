require('dotenv').config({ path: '../Projeler/Whatsapp_Onboarding/.env' });
const notion = require('../Projeler/Whatsapp_Onboarding/services/notion');
const manychat = require('../Projeler/Whatsapp_Onboarding/services/manychat');

async function run() {
  try {
    const shahrud = await notion.findByName("Shahrud");
    console.log("Shahrud Notion Data:", shahrud);
    
    if (shahrud) {
      console.log("Triggering ManyChat flow for Shahrud...");
      await manychat.ensureSubscriberAndSendFlow(
        shahrud.phone,
        shahrud.firstName,
        "content20240905131920_768858" // Day 0 flow ID
      );
      
      console.log("Updating Notion to whatsapp channel...");
      await notion.updatePage(shahrud.id, {
        onboardingChannel: "whatsapp",
        onboardingStatus: "whatsapp",
        onboardingStep: 0,
        notes: "Manuel trigger yapıldı."
      });
      console.log("Done for Shahrud.");
    }
  } catch(e) {
    console.error(e);
  }
}

run().catch(console.error);
