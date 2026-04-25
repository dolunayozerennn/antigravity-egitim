// config/env.js
require('dotenv').config();

const requiredEnvs = [
  'MANYCHAT_API_TOKEN',
  'OPENAI_API_KEY',
  'GROQ_API_KEY',
  'SUPABASE_URL',
  'SUPABASE_SERVICE_ROLE_KEY'
];

for (const env of requiredEnvs) {
  if (!process.env[env]) {
    throw new Error(`EnvironmentError: Gerekli ortam değişkeni eksik: ${env}`);
  }
}

const config = {
  port: process.env.PORT || 3456,
  manychatApiToken: process.env.MANYCHAT_API_TOKEN,
  manychatFieldId: process.env.MANYCHAT_FIELD_ID || '13424657',
  manychatFlowId: process.env.MANYCHAT_FLOW_ID || 'content20250823101653_898847',
  openaiApiKey: process.env.OPENAI_API_KEY,
  groqApiKey: process.env.GROQ_API_KEY,
  supabaseUrl: process.env.SUPABASE_URL,
  supabaseServiceRoleKey: process.env.SUPABASE_SERVICE_ROLE_KEY
};

module.exports = { config };
