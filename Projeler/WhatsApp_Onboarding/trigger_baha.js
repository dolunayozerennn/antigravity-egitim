const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '../../_knowledge/credentials/master.env') });
// Explicitly map master.env values to the expected ones for this project
process.env.NOTION_API_KEY = process.env.NOTION_API_TOKEN;
process.env.NOTION_DATABASE_ID = '0a84f19d-8dd4-4c08-9226-71d9ce71411f'; // Database ID from notion.js comments

const notion = require('./services/notion');
const manychat = require('./services/manychat');
const { ONBOARDING_FLOWS } = require('./config/templates');

async function main() {
  console.log('Searching for Shahrud / Baha in Notion...');
  
  // Find Shahrud
  const shahrud = await notion.findByName('Shahrud');
  if (shahrud) {
    console.log(`Found Shahrud: ${JSON.stringify(shahrud)}`);
    if (shahrud.phone) {
      console.log(`Triggering WhatsApp flow for Shahrud (${shahrud.phone})...`);
      try {
        await manychat.ensureSubscriberAndSendFlow(shahrud.phone, shahrud.firstName, ONBOARDING_FLOWS[0].flow_id);
        console.log('Successfully triggered for Shahrud via WhatsApp.');
        
        await notion.updatePage(shahrud.id, {
          onboardingStatus: "whatsapp",
          onboardingChannel: "whatsapp",
          onboardingStep: 0,
          onboardingStartDate: new Date().toISOString().split('T')[0],
          notes: `[MANUAL TRIGGER] Flow manually triggered via script.`
        });
      } catch (err) {
        console.error('Error triggering Shahrud via WhatsApp:', err.message);
      }
    } else {
      console.log('Shahrud does not have a phone number. Trying email...');
      const resend = require('./services/resend');
      if (shahrud.email) {
        await resend.sendOnboardingEmail(shahrud.email, shahrud.firstName, 0);
        console.log('Triggered email for Shahrud.');
      } else {
        console.log('Shahrud has no email either.');
      }
    }
  } else {
    console.log('Shahrud not found.');
  }

  // Find Baha
  const baha = await notion.findByName('Baha');
  if (baha) {
    console.log(`Found Baha: ${JSON.stringify(baha)}`);
    if (baha.phone) {
      console.log(`Triggering WhatsApp flow for Baha (${baha.phone})...`);
      try {
        await manychat.ensureSubscriberAndSendFlow(baha.phone, baha.firstName, ONBOARDING_FLOWS[0].flow_id);
        console.log('Successfully triggered for Baha via WhatsApp.');
        
        await notion.updatePage(baha.id, {
          onboardingStatus: "whatsapp",
          onboardingChannel: "whatsapp",
          onboardingStep: 0,
          onboardingStartDate: new Date().toISOString().split('T')[0],
          notes: `[MANUAL TRIGGER] Flow manually triggered via script.`
        });
      } catch (err) {
        console.error('Error triggering Baha via WhatsApp:', err.message);
      }
    } else {
      console.log('Baha does not have a phone number. Trying email...');
      const resend = require('./services/resend');
      if (baha.email) {
        await resend.sendOnboardingEmail(baha.email, baha.firstName, 0);
        console.log('Triggered email for Baha.');
      } else {
        console.log('Baha has no email either.');
      }
    }
  } else {
    console.log('Baha not found.');
  }

  // Try combining names if they are the same person "Shahrud Baha"
  const shahrudBaha = await notion.findByName('Shahrud Baha');
  if (shahrudBaha) {
    console.log(`Found Shahrud Baha: ${JSON.stringify(shahrudBaha)}`);
    if (shahrudBaha.phone) {
      console.log(`Triggering WhatsApp flow for Shahrud Baha (${shahrudBaha.phone})...`);
      try {
        await manychat.ensureSubscriberAndSendFlow(shahrudBaha.phone, shahrudBaha.firstName, ONBOARDING_FLOWS[0].flow_id);
        console.log('Successfully triggered for Shahrud Baha via WhatsApp.');
        
        await notion.updatePage(shahrudBaha.id, {
          onboardingStatus: "whatsapp",
          onboardingChannel: "whatsapp",
          onboardingStep: 0,
          onboardingStartDate: new Date().toISOString().split('T')[0],
          notes: `[MANUAL TRIGGER] Flow manually triggered via script.`
        });
      } catch (err) {
        console.error('Error triggering Shahrud Baha via WhatsApp:', err.message);
      }
    }
  }
}

main().catch(console.error);
