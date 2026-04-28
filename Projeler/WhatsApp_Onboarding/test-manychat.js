require('dotenv').config({ path: '/Users/dolunayozeren/Desktop/Antigravity/_knowledge/credentials/master.env' });
const fetch = require('node-fetch');

async function test() {
  const token = process.env.MANYCHAT_API_TOKEN || process.env.MANYCHAT_TOKEN;
  if (!token) throw new Error("No token");
  
  const headers = { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };
  
  const url = `https://api.manychat.com/fb/subscriber/findBySystemField?whatsapp_phone=905537027572`;
  const res = await fetch(url, { headers });
  console.log("whatsapp_phone (without +):", await res.json());

  const url2 = `https://api.manychat.com/fb/subscriber/findBySystemField?whatsapp_phone=%2B905537027572`;
  const res2 = await fetch(url2, { headers });
  console.log("whatsapp_phone (with +):", await res2.json());

  const url3 = `https://api.manychat.com/fb/subscriber/findBySystemField?phone=905537027572`;
  const res3 = await fetch(url3, { headers });
  console.log("phone (without +):", await res3.json());
}
test().catch(console.error);
