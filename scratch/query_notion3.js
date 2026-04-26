require('dotenv').config();
const notion = require('./services/notion');
const manychat = require('./services/manychat');

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
    
    const baha = await notion.findByName("Baha");
    console.log("Baha Notion Data:", baha);
    
    if (baha) {
      console.log("Triggering ManyChat flow for Baha...");
      await manychat.ensureSubscriberAndSendFlow(
        baha.phone,
        baha.firstName,
        "content20240905131920_768858" // Day 0 flow ID
      );
      
      console.log("Updating Notion to whatsapp channel...");
      await notion.updatePage(baha.id, {
        onboardingChannel: "whatsapp",
        onboardingStatus: "whatsapp",
        onboardingStep: 0,
        notes: "Manuel trigger yapıldı."
      });
      console.log("Done for Baha.");
    }

  } catch(e) {
    console.error(e);
  }
}

run().catch(console.error);
