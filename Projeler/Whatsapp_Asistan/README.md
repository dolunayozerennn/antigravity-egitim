# Whatsapp_Asistan

AI Factory'nin WhatsApp hattında gelen müşteri mesajlarını yapay zeka ile yanıtlayan, ManyChat üzerinden çalışan tam otonom asistan.

## Özellikler
- KVKK Onay Akışı (LLM tabanlı akıllı niyet tespiti)
- ManyChat entegrasyonu (Custom fields & Flow triggering)
- OpenAI GPT-4o-mini (GPT-4.1-mini) akıllı yanıt motoru
- Sesli mesaj desteği (Groq Whisper)
- RAG bilgi tabanı entegrasyonu (Supabase pgvector)
- Otomatik dil tespiti (Türkçe, İngilizce, Almanca vb.)
- Supabase Conversation Memory (son 20 mesaj)

## Kurulum
1. `npm install`
2. `.env.example` dosyasını `.env` olarak kopyalayın ve içerisindeki değerleri doldurun
3. `npm start`
