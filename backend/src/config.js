require('dotenv').config();

const AUTH_MODE = (process.env.AUTH_MODE || 'dev').toLowerCase();
const PORT = Number(process.env.PORT || 3000);
const path = require('path');
const DATA_DIR = process.env.DATA_DIR || path.join(__dirname, '..', '..', 'data');
const MAX_PLAYERS = Number(process.env.MAX_PLAYERS || 4);

module.exports = {
  AUTH_MODE,
  PORT,
  DATA_DIR,
  MAX_PLAYERS,
};
