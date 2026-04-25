// services/memory.js
const { createClient } = require('@supabase/supabase-js');
const { config } = require('../config/env');
const log = require('../utils/logger');

const supabase = createClient(config.supabaseUrl, config.supabaseServiceRoleKey);

async function getHistory(subscriberId, limit = 20) {
  try {
    const { data, error } = await supabase
      .from('conversations')
      .select('role, content')
      .eq('subscriber_id', subscriberId)
      .order('created_at', { ascending: false })
      .limit(limit);

    if (error) throw error;
    return data.reverse();
  } catch (error) {
    log.error(`[memory] getHistory hatası: ${error.message}`, error);
    return [];
  }
}

async function saveMessage(subscriberId, role, content) {
  try {
    const { error } = await supabase
      .from('conversations')
      .insert({ subscriber_id: subscriberId, role: role, content: content });
    if (error) throw error;
    log.debug(`[memory] Mesaj kaydedildi`, { subscriberId, role });
  } catch (error) {
    log.error(`[memory] saveMessage hatası: ${error.message}`, error);
  }
}

async function getSubscriber(subscriberId) {
  try {
    const { data, error } = await supabase
      .from('subscribers')
      .select('*')
      .eq('subscriber_id', subscriberId)
      .single();
    if (error && error.code !== 'PGRST116') throw error;
    return data;
  } catch (error) {
    log.error(`[memory] getSubscriber hatası: ${error.message}`, error);
    return null;
  }
}

async function createSubscriber(subscriberId, phoneNumber) {
  try {
    const { data, error } = await supabase
      .from('subscribers')
      .insert({ subscriber_id: subscriberId, phone_number: phoneNumber, kvkk_accepted: false })
      .select()
      .single();
    if (error) throw error;
    return data;
  } catch (error) {
    log.error(`[memory] createSubscriber hatası: ${error.message}`, error);
    return null;
  }
}

async function acceptKVKK(subscriberId) {
  try {
    const { error } = await supabase
      .from('subscribers')
      .update({ kvkk_accepted: true, kvkk_accepted_at: new Date().toISOString() })
      .eq('subscriber_id', subscriberId);
    if (error) throw error;
    log.info(`[memory] KVKK kabul edildi`, { subscriberId });
  } catch (error) {
    log.error(`[memory] acceptKVKK hatası: ${error.message}`, error);
  }
}

module.exports = { getHistory, saveMessage, getSubscriber, createSubscriber, acceptKVKK, supabase };
