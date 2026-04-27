// ============================================================
// server.js — Ana Express Uygulaması
// ============================================================
// Express sunucusunu ayağa kaldırır, webhook endpoint'lerini tanımlar.
// ============================================================

const express = require('express');
const cors = require('cors');
const { config } = require('./config/env');
const manychat = require('./services/manychat');
const notion = require('./services/notion');
const ai = require('./services/ai');
const resend = require('./services/resend');
const log = require('./utils/logger');
const { ONBOARDING_FLOWS } = require('./config/templates');

const app = express();
app.use(cors());

// Webhook payload loglama (debug)
app.use(express.json({
  verify: (req, res, buf) => {
    req.rawBody = buf;
  }
}));

// ==========================================
// YARDIMCI FONKSİYONLAR
// ==========================================

function adminAuth(req, res, next) {
  if (!config.adminSecret) {
    log.warn('[security] ADMIN_SECRET tanımlı değil — auth atlanıyor');
    return next();
  }
  const authHeader = req.headers['authorization'] || '';
  const token = authHeader.replace(/^Bearer\s+/i, '').trim() || req.query.secret;
  if (token !== config.adminSecret) {
    log.warn(`[security] Admin auth başarısız — IP: ${req.ip}`);
    return res.status(401).json({ error: 'Unauthorized' });
  }
  next();
}

// ─────────────────────────────────────────────────────────────
// GET /health — Liveness/Readiness Check
// ─────────────────────────────────────────────────────────────
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'ok', timestamp: new Date().toISOString() });
});

// ==========================================
// MANYCHAT WEBHOOK ENDPOINT'LERİ
// ==========================================

// ... (ve diğer route'lar ama dosyanın tamamını okuyamadığım için push_files kullanamam!)
