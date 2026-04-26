// scripts/kb_manager.js
require('dotenv').config();
const fs = require('fs');
const path = require('path');
const { createClient } = require('@supabase/supabase-js');

// Ortam değişkenlerini kontrol et
const requiredEnvs = ['SUPABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY'];
for (const env of requiredEnvs) {
  if (!process.env[env]) {
    console.error(`EnvironmentError: Gerekli ortam değişkeni eksik: ${env}`);
    process.exit(1);
  }
}

const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY);
const mdPath = path.join(__dirname, '../ai-factory-asistan-bilgi-tabani-v2.md');

// seed_knowledge.js'deki parseMarkdown mantığının aynısı (diff için kullanıyoruz)
function parseMarkdown(content) {
  let initialChunks = [];
  const lines = content.split('\n');
  
  let currentSection = '';
  let currentTitle = '';
  let currentContent = [];

  for (const line of lines) {
    if (line.startsWith('## ') || line.startsWith('### ')) {
      if (currentContent.length > 0 && currentTitle) {
        initialChunks.push({
          section: currentSection || '0',
          section_title: currentTitle,
          content: currentContent.join('\n').trim()
        });
        currentContent = [];
      }
      
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

  if (currentContent.length > 0 && currentTitle) {
    initialChunks.push({
      section: currentSection || '0',
      section_title: currentTitle,
      content: currentContent.join('\n').trim()
    });
  }

  const mergedChunks = [];
  for (const chunk of initialChunks) {
    if (chunk.content.length < 50 && mergedChunks.length > 0) {
      mergedChunks[mergedChunks.length - 1].content += '\n\n' + `[${chunk.section_title}]\n${chunk.content}`;
    } else {
      mergedChunks.push({ ...chunk });
    }
  }

  const finalChunks = [];
  for (const chunk of mergedChunks) {
    if (chunk.content.length > 2000) {
      const paragraphs = chunk.content.split('\n\n');
      let currentPart = '';

      for (const p of paragraphs) {
        if (currentPart.length + p.length > 2000 && currentPart.length > 0) {
          finalChunks.push({
            section: chunk.section,
            section_title: chunk.section_title,
            content: currentPart.trim()
          });
          currentPart = p;
        } else {
          currentPart = currentPart ? currentPart + '\n\n' + p : p;
        }
      }
      
      if (currentPart) {
        finalChunks.push({
          section: chunk.section,
          section_title: chunk.section_title,
          content: currentPart.trim()
        });
      }
    } else {
      finalChunks.push(chunk);
    }
  }

  return finalChunks;
}

async function listChunks() {
  const { data, error } = await supabase
    .from('knowledge_chunks')
    .select('id, section, section_title, content, created_at')
    .order('section');

  if (error) {
    console.error('Hata:', error);
    return;
  }

  console.log(`Toplam Chunk: ${data.length}\n`);
  data.forEach(chunk => {
    console.log(`[${chunk.section}] ${chunk.section_title}`);
    console.log(`ID: ${chunk.id}`);
    console.log(`Uzunluk: ${chunk.content ? chunk.content.length : 0} karakter\n`);
  });
}

async function searchChunks(query) {
  if (!query) {
    console.log('Lütfen bir arama terimi girin: node scripts/kb_manager.js search "fiyat"');
    return;
  }

  const { data, error } = await supabase
    .from('knowledge_chunks')
    .select('id, section, section_title, content')
    .ilike('content', `%${query}%`);

  if (error) {
    console.error('Hata:', error);
    return;
  }

  console.log(`Arama: "${query}" - Bulunan Sonuç: ${data.length}\n`);
  data.forEach(chunk => {
    console.log(`[${chunk.section}] ${chunk.section_title}`);
    const idx = chunk.content.toLowerCase().indexOf(query.toLowerCase());
    const start = Math.max(0, idx - 40);
    const end = Math.min(chunk.content.length, idx + query.length + 40);
    console.log(`...${chunk.content.substring(start, end).replace(/\n/g, ' ')}...\n`);
  });
}

function validatePrices() {
  if (!fs.existsSync(mdPath)) {
    console.error(`Hata: Markdown dosyası bulunamadı: ${mdPath}`);
    return;
  }

  const content = fs.readFileSync(mdPath, 'utf8');
  
  const correctPrices = ['$39', '$59', '$129', '$156', '$236', '$516'];
  const bannedPrices = ['$97', '$197', '$297', '$497', '$997', '$1997'];

  let hasError = false;

  console.log('--- Fiyat Geçerlilik Kontrolü ---\n');

  console.log('✅ Doğru Fiyatlar Kontrol Ediliyor:');
  correctPrices.forEach(price => {
    const regex = new RegExp(`\\${price}\\b`);
    if (regex.test(content)) {
      console.log(`  Bulundu: ${price}`);
    } else {
      console.log(`  EKSİK: ${price}`);
      hasError = true;
    }
  });

  console.log('\n❌ Yasak Fiyatlar Kontrol Ediliyor:');
  bannedPrices.forEach(price => {
    const regex = new RegExp(`\\${price}\\b`);
    if (regex.test(content)) {
      console.log(`  BULUNDU (YASAKLI): ${price}`);
      hasError = true;
    } else {
      console.log(`  Temiz: ${price}`);
    }
  });

  console.log('\nSonuç:');
  if (hasError) {
    console.log('❌ Doğrulama Başarısız. Fiyatlarda sorun var.');
    process.exitCode = 1;
  } else {
    console.log('✅ Doğrulama Başarılı. Fiyatlar doğru.');
  }
}

async function stats() {
  const { data, error } = await supabase
    .from('knowledge_chunks')
    .select('content');

  if (error) {
    console.error('Hata:', error);
    return;
  }

  if (data.length === 0) {
    console.log('Hiç chunk bulunamadı.');
    return;
  }

  const lengths = data.map(d => d.content ? d.content.length : 0);
  const totalChunks = lengths.length;
  const totalLength = lengths.reduce((acc, curr) => acc + curr, 0);
  const avgLength = totalLength / totalChunks;
  const maxChunk = Math.max(...lengths);
  const minChunk = Math.min(...lengths);

  console.log(`--- KB İstatistikleri ---`);
  console.log(`Toplam Chunk: ${totalChunks}`);
  console.log(`Toplam Karakter: ${totalLength}`);
  console.log(`Ortalama Boyut: ${Math.round(avgLength)} karakter`);
  console.log(`En Uzun Chunk: ${maxChunk} karakter`);
  console.log(`En Kısa Chunk: ${minChunk} karakter`);
}

async function diff() {
  if (!fs.existsSync(mdPath)) {
    console.error(`Hata: Markdown dosyası bulunamadı: ${mdPath}`);
    return;
  }

  const mdContent = fs.readFileSync(mdPath, 'utf8');
  const localChunks = parseMarkdown(mdContent);
  const localCount = localChunks.length;

  const { count, error } = await supabase
    .from('knowledge_chunks')
    .select('*', { count: 'exact', head: true });

  if (error) {
    console.error('Hata:', error);
    return;
  }

  const dbCount = count;

  console.log(`--- KB Diff Kontrolü ---`);
  console.log(`Lokal MD Dosyası Chunk Sayısı: ${localCount}`);
  console.log(`Supabase (DB) Chunk Sayısı: ${dbCount}`);

  if (localCount === dbCount) {
    console.log('\n✅ Eşleşme başarılı. DB güncel.');
  } else {
    console.log('\n❌ EŞLEŞMEZ: MD dosyası ve DB arasında fark var. Seed işlemini çalıştırın.');
    process.exitCode = 1;
  }
}

const command = process.argv[2];
const arg = process.argv[3];

switch (command) {
  case 'list':
    listChunks();
    break;
  case 'search':
    searchChunks(arg);
    break;
  case 'validate':
    validatePrices();
    break;
  case 'stats':
    stats();
    break;
  case 'diff':
    diff();
    break;
  default:
    console.log('Kullanım: node scripts/kb_manager.js <list|search|validate|stats|diff> [arg]');
}
