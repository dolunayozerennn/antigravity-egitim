const { config } = require('./config/env');
const fetch = require('node-fetch');

const API_URL = "https://api.manychat.com/fb";
const headers = {
  'Authorization': `Bearer ${config.manychatApiToken}`,
  'Content-Type': 'application/json'
};

async function test() {
  const phone = '+905343023726';
  
  // 1. try findBySystemField phone
  let res = await fetch(`${API_URL}/subscriber/findBySystemField?phone=${encodeURIComponent(phone)}`, { headers });
  console.log("findBySystemField phone:", await res.json());

  // 2. try findBySystemField whatsapp_phone
  res = await fetch(`${API_URL}/subscriber/findBySystemField?whatsapp_phone=${encodeURIComponent(phone)}`, { headers });
  console.log("findBySystemField whatsapp_phone:", await res.json());

  // 3. try findBySystemField whatsapp
  res = await fetch(`${API_URL}/subscriber/findBySystemField?whatsapp=${encodeURIComponent(phone)}`, { headers });
  console.log("findBySystemField whatsapp:", await res.json());

  // 4. try findSubscriberByName ? (We only have phone)
  
  // 5. Let's see if we can get subscriber by something else?
}
test();
