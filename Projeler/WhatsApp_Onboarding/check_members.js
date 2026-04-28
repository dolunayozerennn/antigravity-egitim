require('dotenv').config();
const { Client } = require('@notionhq/client');

const notion = new Client({ auth: process.env.NOTION_API_KEY });
const DATABASE_ID = process.env.NOTION_DATABASE_ID;

async function checkRecentMembers() {
  const threeDaysAgo = new Date();
  threeDaysAgo.setDate(threeDaysAgo.getDate() - 3);
  const dateStr = threeDaysAgo.toISOString().split('T')[0];

  try {
    const response = await notion.databases.query({
      database_id: DATABASE_ID,
      filter: {
        property: "Kayıt Tarihi",
        date: {
          on_or_after: dateStr
        }
      },
      sorts: [
        {
          property: "Kayıt Tarihi",
          direction: "descending"
        }
      ]
    });

    console.log(`Found ${response.results.length} recent members.`);
    response.results.forEach(page => {
      const firstName = page.properties["İsim"]?.title?.[0]?.text?.content || '';
      const lastName = page.properties["Soyisim"]?.rich_text?.[0]?.text?.content || '';
      const email = page.properties["Email"]?.email || '';
      const phone = page.properties["Telefon"]?.phone_number || '';
      const regDate = page.properties["Kayıt Tarihi"]?.date?.start || '';
      const status = page.properties["Onboarding Durumu"]?.select?.name || '';
      const step = page.properties["Onboarding Adımı"]?.number || 0;
      const channel = page.properties["Onboarding Kanalı"]?.select?.name || '';
      console.log(`- ${firstName} ${lastName} | Email: ${email} | Phone: ${phone} | Date: ${regDate} | Status: ${status} | Step: ${step} | Channel: ${channel} | ID: ${page.id}`);
    });
  } catch (err) {
    console.error("Error querying Notion:", err);
  }
}

checkRecentMembers();
