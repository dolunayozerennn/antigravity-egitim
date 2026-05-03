require('dotenv').config();
const token = process.env.MANYCHAT_API_TOKEN;
const API_URL = "https://api.manychat.com/fb";

async function test() {
  const response = await fetch(`${API_URL}/page/getCustomFields`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  const text = await response.text();
  console.log("Status:", response.status);
  console.log("Response:", text.substring(0, 500));
}
test();
