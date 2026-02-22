const fs = require('fs');
const path = require('path');

function ensureDir(p) {
  fs.mkdirSync(p, { recursive: true });
}

function readJsonSafe(file, fallback) {
  try {
    if (!fs.existsSync(file)) return fallback;
    const raw = fs.readFileSync(file, 'utf8');
    return raw ? JSON.parse(raw) : fallback;
  } catch (e) {
    console.warn(`Failed to read ${file}:`, e);
    return fallback;
  }
}

function writeJsonSafe(file, data) {
  try {
    ensureDir(path.dirname(file));
    fs.writeFileSync(file, JSON.stringify(data, null, 2), 'utf8');
  } catch (e) {
    console.warn(`Failed to write ${file}:`, e);
  }
}

function createDevStore(dataDir) {
  const usersFile = path.join(dataDir, 'users.json');
  const gamesFile = path.join(dataDir, 'games.json');

  ensureDir(dataDir);
  if (!fs.existsSync(usersFile)) writeJsonSafe(usersFile, {});
  if (!fs.existsSync(gamesFile)) writeJsonSafe(gamesFile, []);

  function getAllUsers() {
    return readJsonSafe(usersFile, {});
  }

  function saveAllUsers(users) {
    writeJsonSafe(usersFile, users);
  }

  function getAllGames() {
    return readJsonSafe(gamesFile, []);
  }

  function saveAllGames(games) {
    writeJsonSafe(gamesFile, games);
  }

  return {
    mode: 'dev',

    async getUser(userId) {
      const users = getAllUsers();
      return users[userId] || null;
    },

    async upsertUser(userId, partial) {
      const users = getAllUsers();
      const existing = users[userId] || {
        username: partial.username || `player_${userId.slice(-4)}`,
        gamesPlayed: 0,
        wins: 0,
        totalScore: 0,
      };

      users[userId] = { ...existing, ...partial };
      saveAllUsers(users);
      return users[userId];
    },

    async incrementUserStats(userId, { gamesPlayed = 0, wins = 0, totalScore = 0 }) {
      const users = getAllUsers();
      const existing = users[userId] || {
        username: `player_${userId.slice(-4)}`,
        gamesPlayed: 0,
        wins: 0,
        totalScore: 0,
      };

      users[userId] = {
        ...existing,
        gamesPlayed: (existing.gamesPlayed || 0) + gamesPlayed,
        wins: (existing.wins || 0) + wins,
        totalScore: (existing.totalScore || 0) + totalScore,
      };

      saveAllUsers(users);
      return users[userId];
    },

    async addGame(gameRecord) {
      const games = getAllGames();
      games.unshift(gameRecord);
      saveAllGames(games);
      return gameRecord;
    },

    async listRecentGamesForUser(userId, limit = 20) {
      const games = getAllGames();
      return games
        .filter((g) => Array.isArray(g.players) && g.players.includes(userId))
        .slice(0, limit);
    },

    async listLeaderboard(limit = 10) {
      const users = getAllUsers();
      return Object.entries(users)
        .map(([id, u]) => ({ id, ...u }))
        .sort((a, b) => (b.totalScore || 0) - (a.totalScore || 0))
        .slice(0, limit);
    },
  };
}

module.exports = { createDevStore };
