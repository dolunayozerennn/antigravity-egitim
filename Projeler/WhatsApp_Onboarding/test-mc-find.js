const { config } = require('./config/env');
const token = config.manychatApiToken;

async function testFind() {
  const phone = '+905537027572';
  const url = `https://api.manychat.com/fb/subscriber/findBySystemField?phone=${encodeURIComponent(phone)}`;
  const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
  const data = await res.json();
  console.log('findBySystemField phone:', JSON.stringify(data));
  
  const urlWA = `https://api.manychat.com/fb/subscriber/findBySystemField?whatsapp_phone=${encodeURIComponent(phone)}`;
  const resWA = await fetch(urlWA, { headers: { Authorization: `Bearer ${token}` } });
  const dataWA = await resWA.json();
  console.log('findBySystemField whatsapp_phone:', JSON.stringify(dataWA));
  
  const phoneNoPlus = '905537027572';
  const urlNoPlus = `https://api.manychat.com/fb/subscriber/findBySystemField?phone=${encodeURIComponent(phoneNoPlus)}`;
  const resNoPlus = await fetch(urlNoPlus, { headers: { Authorization: `Bearer ${token}` } });
  const dataNoPlus = await resNoPlus.json();
  console.log('findBySystemField phone no plus:', JSON.stringify(dataNoPlus));
}
testFind();
