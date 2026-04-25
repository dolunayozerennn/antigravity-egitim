// scripts/seed_knowledge.js
require('dotenv').config();
const fs = require('fs');
const path = require('path');
const OpenAI = require('openai');
const { createClient } = require('@supabase/supabase-js');
const log = require('../utils/logger');

const requiredEnvs = ['OPENAI_API_KEY', 'SUPABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY'];
for (const env of requiredEnvs) {
  if (!process.env[env]) {
    throw new Error(`EnvironmentError: Gerekli ortam değişkeni eksik: ${env}`);
  }
}

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY);

function parseMarkdown(content) {
  const chunks = [];
  const lines = content.split('\n');
  
  let currentSection = '';
  let currentTitle = '';
  let currentContent = [];

  // Basit bir markdown parser (## ve ### başlıklarına göre ayırır)
  for (const line of lines) {
    if (line.startsWith('## ') || line.startsWith('### ')) {
      // Önceki chunk'ı kaydet
      if (currentContent.length > 0 && currentTitle) {
        chunks.push({
          section: currentSection || '0',
          section_title: currentTitle,
          content: currentContent.join('\n').trim()
        });
        currentContent = [];
      }
      
      // Başlıktan numarayı (varsa) ve başlığı ayıkla
      const titleText = line.replace(/^#+\s/, '');
      const sectionMatch = titleText.match(/^([\d.]+)\s*/);
      
      if (sectionMatch) {
        currentSection = sectionMatch[1].trim();
        currentTitle = titleText.substring(sectionMatch[0].length).trim();
      } else {
        currentTitle = titleText;
      }
    } else {
      currentContent.push(line);
    }
  }

  // Son chunk'ı kaydet
  if (currentContent.length > 0 && currentTitle) {
    chunks.push({
      section: currentSection || '0',
      section_title: currentTitle,
      content: currentContent.join('\n').trim()
    });
  }

  return chunks;
}

async function seed() {
  try {
    const mdPath = path.join(__dirname, '../ai-factory-asistan-bilgi-tabani-v2.md');
    if (!fs.existsSync(mdPath)) {
      log.error(`Markdown dosyası bulunamadı: ${mdPath}`);
      return;
    }

    const mdContent = fs.readFileSync(mdPath, 'utf8');
    const chunks = parseMarkdown(mdContent);
    
    log.info(`[seed] Toplam ${chunks.length} chunk ayrıştırıldı. İşlem başlatılıyor...`);

    // Mevcut tüm chunk'ları sil (Opsiyonel - isterseniz yoruma alabilirsiniz)
    log.info(`[seed] Eski veriler siliniyor...`);
    await supabase.from('knowledge_chunks').delete().neq('id', '00000000-0000-0000-0000-000000000000'); // Tüm kayıtları silmenin güvenli bir yolu

    let processedCount = 0;
    
    // Chunk'ları embedding'e dönüştür ve Supabase'e kaydet
    for (const chunk of chunks) {
      if (!chunk.content || chunk.content.trim() === '') continue;

      log.info(`[seed] İşleniyor: ${chunk.section_title}...`);
      
      const embeddingResponse = await openai.embeddings.create({
        model: 'text-embedding-3-small',
        input: `[${chunk.section_title}]\n${chunk.content}`,
        dimensions: 1536
      });
      
      const embedding = embeddingResponse.data[0].embedding;

      const { error } = await supabase.from('knowledge_chunks').insert({
        section: chunk.section,
        section_title: chunk.section_title,
        content: chunk.content,
        embedding: embedding,
        metadata: { source: 'ai-factory-asistan-bilgi-tabani-v2' }
      });

      if (error) {
        log.error(`[seed] Supabase kayıt hatası (${chunk.section_title}): ${error.message}`);
      } else {
        processedCount++;
      }
      
      // Rate limit'e takılmamak için kısa bekleme
      await new Promise(r => setTimeout(r, 200));
    }

    log.info(`[seed] ✅ İşlem tamamlandı. ${processedCount} adet chunk kaydedildi.`);
  } catch (error) {
    log.error(`[seed] Seed işlemi başarısız: ${error.message}`, error);
  }
}

seed();
