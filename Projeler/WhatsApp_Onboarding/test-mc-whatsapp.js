const { config } = require('./config/env');
const fetch = require('node-fetch'); // we can use global fetch in Node 18+

async function test() {
  const url = `https://api.manychat.com/fb/subscriber/findBySystemField?whatsapp_phone=905343023726`;
  console.log("Fetching:", url);
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${config.manychatApiToken}`,
      'Content-Type': 'application/json'
    }
  });
  const data = await response.json();
  console.log("Response:", JSON.stringify(data, null, 2));
}

test();
