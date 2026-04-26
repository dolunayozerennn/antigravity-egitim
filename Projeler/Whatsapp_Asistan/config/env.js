// config/env.js
require('dotenv').config();

const requiredEnvs = [
  'MANYCHAT_API_TOKEN',
  'MANYCHAT_FIELD_ID',
  'MANYCHAT_FLOW_ID',
  'OPENAI_API_KEY',
  'GROQ_API_KEY',
  'SUPABASE_URL',
  'SUPABASE_SERVICE_ROLE_KEY'
];

for (const env of requiredEnvs) {
  if (!process.env[env]) {
    throw new Error(`EnvironmentError: Gerekli ortam degiskeni eksik: ${env}`);
  }
}

const config = {
  manychatApiToken: process.env.MANYCHAT_API_TOKEN,
  manychatFieldId: process.env.MANYCHAT_FIELD_ID,
  manychatFlowId: process.env.MANYCHAT_FLOW_ID,
  openaiApiKey: process.env.OPENAI_API_KEY,
  groqApiKey: process.env.GROQ_API_KEY,
  supabaseUrl: process.env.SUPABASE_URL,
  supabaseServiceRoleKey: process.env.SUPABASE_SERVICE_ROLE_KEY,
  port: process.env.PORT || 3456,
  resendApiKey: process.env.RESEND_API_KEY || null,
  escalationEmail: process.env.ESCALATION_EMAIL || 'dolunay@dolunay.ai'
};

module.exports = { config };
