-- ============================================
-- Whatsapp_Asistan — Supabase Kurulum SQL'i
-- Supabase Dashboard → SQL Editor → New Query → Yapıştır → Run
-- ============================================

-- 1. subscribers tablosu
CREATE TABLE subscribers (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  subscriber_id TEXT UNIQUE NOT NULL,
  phone_number TEXT,
  kvkk_accepted BOOLEAN DEFAULT FALSE,
  kvkk_accepted_at TIMESTAMPTZ,
  language TEXT DEFAULT 'tr',
  first_seen_at TIMESTAMPTZ DEFAULT NOW(),
  last_seen_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_subscribers_sid ON subscribers(subscriber_id);

-- 2. conversations tablosu
CREATE TABLE conversations (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  subscriber_id TEXT NOT NULL REFERENCES subscribers(subscriber_id),
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_conversations_subscriber ON conversations(subscriber_id, created_at DESC);

-- 3. pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 4. knowledge_chunks tablosu (RAG)
CREATE TABLE knowledge_chunks (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  section TEXT NOT NULL,
  section_title TEXT NOT NULL,
  content TEXT NOT NULL,
  embedding VECTOR(1536) NOT NULL,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_knowledge_embedding ON knowledge_chunks
  USING ivfflat (embedding vector_cosine_ops) WITH (lists = 20);

-- 5. Similarity Search Fonksiyonu
CREATE OR REPLACE FUNCTION match_knowledge_chunks(
  query_embedding VECTOR(1536),
  match_threshold FLOAT DEFAULT 0.7,
  match_count INT DEFAULT 5
)
RETURNS TABLE (
  id UUID,
  section TEXT,
  section_title TEXT,
  content TEXT,
  metadata JSONB,
  similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    kc.id,
    kc.section,
    kc.section_title,
    kc.content,
    kc.metadata,
    1 - (kc.embedding <=> query_embedding) AS similarity
  FROM knowledge_chunks kc
  WHERE 1 - (kc.embedding <=> query_embedding) > match_threshold
  ORDER BY kc.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
