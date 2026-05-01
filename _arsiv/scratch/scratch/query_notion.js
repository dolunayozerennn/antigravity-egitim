const { config } = require('../Projeler/Whatsapp_Onboarding/config/env');
const notion = require('../Projeler/Whatsapp_Onboarding/services/notion');

async function run() {
  console.log("Searching for Baha...");
  const baha = await notion.findByName("Baha");
  console.log(baha);
  
  console.log("Searching for Shahrud...");
  const shahrud = await notion.findByName("Shahrud");
  console.log(shahrud);
}

run().catch(console.error);
