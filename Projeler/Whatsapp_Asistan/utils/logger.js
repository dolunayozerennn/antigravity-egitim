// utils/logger.js
const log = {
  info: (msg, meta = {}) => console.log(JSON.stringify({ level: 'INFO', msg, timestamp: new Date().toISOString(), ...meta })),
  error: (msg, error) => console.error(JSON.stringify({ level: 'ERROR', msg, error: error?.message || error, timestamp: new Date().toISOString() })),
  warn: (msg, meta = {}) => console.warn(JSON.stringify({ level: 'WARN', msg, timestamp: new Date().toISOString(), ...meta })),
  debug: (msg, meta = {}) => {
    if (process.env.NODE_ENV !== 'production') {
      console.debug(JSON.stringify({ level: 'DEBUG', msg, timestamp: new Date().toISOString(), ...meta }));
    }
  }
};

module.exports = log;
