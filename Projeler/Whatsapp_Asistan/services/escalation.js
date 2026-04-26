const { config } = require('../config/env');
const log = require('../utils/logger');

// XSS korumasi icin HTML escape fonksiyonu
function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

/**
 * WhatsApp Asistanı Eskalasyon Maili Gönderir
 * @param {Object} params
 * @param {string} params.type - "hassas_konu" veya "bilinmeyen_soru"
 * @param {string} params.subscriberId - ManyChat subscriber ID
 * @param {string} [params.phoneNumber] - Telefon numarası
 * @param {string} params.reason - Eskalasyon sebebi (LLM açıklaması)
 * @param {Array} params.recentMessages - Son 5 mesaj ({ role, content })
 */
async function sendEscalationEmail({ type, subscriberId, phoneNumber, reason, recentMessages }) {
  if (!config.resendApiKey) {
    log.warn(`[escalation] RESEND_API_KEY yok — email gönderilmedi: ${type}`);
    return false;
  }

  const escalationTypeStr = type === 'hassas_konu' ? 'HASSAS' : 'BİLİNMEYEN';
  const shortReason = reason.length > 60 ? reason.substring(0, 60) + '...' : reason;
  const subject = `[${escalationTypeStr}] WhatsApp Eskalasyon — ${shortReason}`;
  const toEmail = config.escalationEmail;
  const fromAddress = `WhatsApp Asistan <${toEmail}>`;

  // İstanbul saati ile zaman damgası
  const dateStr = new Date().toLocaleString('tr-TR', { timeZone: 'Europe/Istanbul' });

  // Son mesajları HTML'e çevir
  let messagesHtml = '';
  if (recentMessages && recentMessages.length > 0) {
    messagesHtml = recentMessages.map(m => {
      const roleName = m.role === 'user' ? 'Kullanıcı' : 'Asistan';
      const color = m.role === 'user' ? '#2563EB' : '#16A34A';
      return `<div style="margin-bottom: 12px;">
        <strong style="color: ${color};">${roleName}:</strong>
        <div style="margin-top: 4px; background: #f9fafb; padding: 10px; border-radius: 6px; border: 1px solid #e5e7eb; white-space: pre-wrap; font-family: system-ui, sans-serif; font-size: 14px;">${escapeHtml(m.content)}</div>
      </div>`;
    }).join('');
  } else {
    messagesHtml = '<p style="color: #6b7280; font-style: italic;">Son konuşma bulunamadı.</p>';
  }

  const html = `
    <div style="font-family: system-ui, -apple-system, sans-serif; color: #111827; max-width: 600px; margin: 0 auto; border: 1px solid #e5e7eb; border-radius: 8px; padding: 24px;">
      <h2 style="margin-top: 0; color: #dc2626; border-bottom: 2px solid #fee2e2; padding-bottom: 12px;">🚨 WhatsApp Eskalasyon Bildirimi</h2>
      
      <table border="0" cellpadding="10" cellspacing="0" style="width: 100%; border-collapse: collapse; margin-bottom: 24px;">
        <tr>
          <td style="background: #f3f4f6; width: 120px; border-bottom: 1px solid #e5e7eb;"><strong>Tarih (TSİ)</strong></td>
          <td style="border-bottom: 1px solid #e5e7eb;">${dateStr}</td>
        </tr>
        <tr>
          <td style="background: #f3f4f6; border-bottom: 1px solid #e5e7eb;"><strong>Kişi Bilgileri</strong></td>
          <td style="border-bottom: 1px solid #e5e7eb;">
            Telefon: ${escapeHtml(phoneNumber || 'Bilinmiyor')}<br>
            Subscriber ID: ${escapeHtml(subscriberId)}
          </td>
        </tr>
        <tr>
          <td style="background: #f3f4f6; border-bottom: 1px solid #e5e7eb;"><strong>Kategori</strong></td>
          <td style="border-bottom: 1px solid #e5e7eb;">
            <span style="background: #fee2e2; color: #991b1b; padding: 2px 8px; border-radius: 9999px; font-size: 13px; font-weight: 500;">
              ${escapeHtml(type)}
            </span>
          </td>
        </tr>
        <tr>
          <td style="background: #f3f4f6; border-bottom: 1px solid #e5e7eb;"><strong>Sebep</strong></td>
          <td style="border-bottom: 1px solid #e5e7eb;">${escapeHtml(reason)}</td>
        </tr>
      </table>

      <h3 style="margin-top: 0; margin-bottom: 16px; font-size: 18px;">Son Konuşma Özeti</h3>
      <div style="background: #ffffff;">
        ${messagesHtml}
      </div>
    </div>
  `;

  try {
    const response = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${config.resendApiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        from: fromAddress,
        to: [toEmail],
        subject: subject,
        html: html
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      log.error(`[escalation] Resend API hatası: HTTP ${response.status} - ${errorText}`);
      return false;
    }

    const data = await response.json();
    log.info(`[escalation] E-mail başarıyla gönderildi: ${type} (${data.id})`);
    return true;

  } catch (error) {
    log.error(`[escalation] Beklenmeyen hata: ${error.message}`, error);
    return false;
  }
}

module.exports = {
  sendEscalationEmail
};
