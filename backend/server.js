const express = require('express');
const http = require('http');
const socketIO = require('socket.io');
const cors = require('cors');
const admin = require('firebase-admin');
require('dotenv').config();

const app = express();
const server = http.createServer(app);
const io = socketIO(server, {
  cors: {
    origin: "*",
    methods: ["GET", "POST"]
  }
});

// Middleware
app.use(cors());
app.use(express.json());

// Firebase Admin initialization
const serviceAccount = {
  projectId: process.env.FIREBASE_PROJECT_ID,
  privateKey: process.env.FIREBASE_PRIVATE_KEY?.replace(/\\n/g, '\n'),
  clientEmail: process.env.FIREBASE_CLIENT_EMAIL,
};

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount)
});

const db = admin.firestore();

// Game state management
const games = new Map();
const players = new Map();

class GameRoom {
  constructor(id, hostId, config) {
    this.id = id;
    this.hostId = hostId;
    this.players = new Map();
    this.snakes = new Map();
    this.fruits = [];
    this.state = 'waiting';
    this.config = config;
    this.turn = 0;
    this.startTime = null;
    this.endTime = null;
    this.winner = null;
  }

  addPlayer(playerId, playerData) {
    this.players.set(playerId, {
      id: playerId,
      username: playerData.username,
      color: playerData.color,
      score: 0,
      alive: true
    });
  }

  removePlayer(playerId) {
    this.players.delete(playerId);
    this.snakes.delete(playerId);
  }

  updateSnake(playerId, snakeData) {
    this.snakes.set(playerId, snakeData);
  }

  getState() {
    return {
      id: this.id,
      players: Array.from(this.players.values()),
      snakes: Array.from(this.snakes.entries()),
      fruits: this.fruits,
      state: this.state,
      turn: this.turn
    };
  }
}

// REST API Endpoints
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: Date.now() });
});

app.get('/api/stats/:userId', async (req, res) => {
  try {
    const userId = req.params.userId;
    const statsDoc = await db.collection('users').doc(userId).get();
    
    if (!statsDoc.exists) {
      return res.status(404).json({ error: 'User not found' });
    }

    const gamesSnapshot = await db.collection('games')
      .where('players', 'array-contains', userId)
      .orderBy('endTime', 'desc')
      .limit(20)
      .get();

    const games = [];
    gamesSnapshot.forEach(doc => {
      games.push({ id: doc.id, ...doc.data() });
    });

    res.json({
      stats: statsDoc.data(),
      recentGames: games
    });
  } catch (error) {
    console.error('Error fetching stats:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

app.get('/api/leaderboard', async (req, res) => {
  try {
    const limit = parseInt(req.query.limit) || 10;
    const usersSnapshot = await db.collection('users')
      .orderBy('totalScore', 'desc')
      .limit(limit)
      .get();

    const leaderboard = [];
    usersSnapshot.forEach(doc => {
      leaderboard.push({ id: doc.id, ...doc.data() });
    });

    res.json({ leaderboard });
  } catch (error) {
    console.error('Error fetching leaderboard:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

app.get('/api/games/active', (req, res) => {
  const activeGames = [];
  games.forEach((game, id) => {
    if (game.state !== 'finished') {
      activeGames.push({
        id: game.id,
        playerCount: game.players.size,
        state: game.state
      });
    }
  });
  res.json({ games: activeGames });
});

// Socket.IO Events
io.on('connection', (socket) => {
  console.log('New client connected:', socket.id);

  socket.on('authenticate', async (data) => {
    try {
      const { idToken, username } = data;
      const decodedToken = await admin.auth().verifyIdToken(idToken);
      const userId = decodedToken.uid;

      players.set(socket.id, {
        userId,
        username,
        socketId: socket.id
      });

      await db.collection('users').doc(userId).set({
        username,
        lastLogin: admin.firestore.FieldValue.serverTimestamp()
      }, { merge: true });

      socket.emit('authenticated', { userId, username });
      console.log(`User authenticated: ${username} (${userId})`);
    } catch (error) {
      console.error('Authentication error:', error);
      socket.emit('auth_error', { message: 'Authentication failed' });
    }
  });

  socket.on('create_room', (data) => {
    const player = players.get(socket.id);
    if (!player) {
      socket.emit('error', { message: 'Not authenticated' });
      return;
    }

    const roomId = `room_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const game = new GameRoom(roomId, player.userId, data.config || {});
    game.addPlayer(player.userId, {
      username: player.username,
      color: data.color || [0, 255, 0]
    });

    games.set(roomId, game);
    socket.join(roomId);

    socket.emit('room_created', {
      roomId,
      game: game.getState()
    });

    console.log(`Room created: ${roomId} by ${player.username}`);
  });

  socket.on('join_room', (data) => {
    const player = players.get(socket.id);
    if (!player) {
      socket.emit('error', { message: 'Not authenticated' });
      return;
    }

    const { roomId } = data;
    const game = games.get(roomId);

    if (!game) {
      socket.emit('error', { message: 'Room not found' });
      return;
    }

    if (game.state !== 'waiting') {
      socket.emit('error', { message: 'Game already started' });
      return;
    }

    if (game.players.size >= 4) {
      socket.emit('error', { message: 'Room is full' });
      return;
    }

    game.addPlayer(player.userId, {
      username: player.username,
      color: data.color || [0, 0, 255]
    });

    socket.join(roomId);

    io.to(roomId).emit('player_joined', {
      playerId: player.userId,
      username: player.username,
      game: game.getState()
    });

    console.log(`${player.username} joined room: ${roomId}`);
  });

  socket.on('start_game', (data) => {
    const { roomId } = data;
    const game = games.get(roomId);
    const player = players.get(socket.id);

    if (!game || !player) {
      socket.emit('error', { message: 'Invalid game or player' });
      return;
    }

    if (game.hostId !== player.userId) {
      socket.emit('error', { message: 'Only host can start the game' });
      return;
    }

    if (game.players.size < 2) {
      socket.emit('error', { message: 'Need at least 2 players' });
      return;
    }

    game.state = 'playing';
    game.startTime = Date.now();

    io.to(roomId).emit('game_started', {
      game: game.getState()
    });

    console.log(`Game started in room: ${roomId}`);
  });

  socket.on('game_update', (data) => {
    const { roomId, snakeData, score } = data;
    const game = games.get(roomId);
    const player = players.get(socket.id);

    if (!game || !player) return;

    game.updateSnake(player.userId, snakeData);
    
    const playerData = game.players.get(player.userId);
    if (playerData) {
      playerData.score = score;
    }

    game.turn++;

    io.to(roomId).emit('game_state', game.getState());
  });

  socket.on('player_died', async (data) => {
    const { roomId } = data;
    const game = games.get(roomId);
    const player = players.get(socket.id);

    if (!game || !player) return;

    const playerData = game.players.get(player.userId);
    if (playerData) {
      playerData.alive = false;
    }

    io.to(roomId).emit('player_died', {
      playerId: player.userId,
      username: player.username
    });

    const alivePlayers = Array.from(game.players.values()).filter(p => p.alive);
    if (alivePlayers.length <= 1) {
      game.state = 'finished';
      game.endTime = Date.now();
      
      if (alivePlayers.length === 1) {
        game.winner = alivePlayers[0].id;
      }

      try {
        const gameData = {
          roomId: game.id,
          players: Array.from(game.players.values()).map(p => ({
            userId: p.id,
            username: p.username,
            score: p.score,
            alive: p.alive
          })),
          winner: game.winner,
          startTime: game.startTime,
          endTime: game.endTime,
          duration: game.endTime - game.startTime
        };

        await db.collection('games').add(gameData);

        for (const [playerId, playerData] of game.players) {
          await db.collection('users').doc(playerId).set({
            gamesPlayed: admin.firestore.FieldValue.increment(1),
            totalScore: admin.firestore.FieldValue.increment(playerData.score),
            wins: playerId === game.winner ? admin.firestore.FieldValue.increment(1) : admin.firestore.FieldValue.increment(0)
          }, { merge: true });
        }
      } catch (error) {
        console.error('Error saving game:', error);
      }

      io.to(roomId).emit('game_over', {
        winner: game.winner,
        finalState: game.getState()
      });

      setTimeout(() => {
        games.delete(roomId);
      }, 30000);
    }
  });

  socket.on('leave_room', (data) => {
    const { roomId } = data;
    const game = games.get(roomId);
    const player = players.get(socket.id);

    if (!game || !player) return;

    game.removePlayer(player.userId);
    socket.leave(roomId);

    io.to(roomId).emit('player_left', {
      playerId: player.userId,
      username: player.username
    });

    if (game.players.size === 0) {
      games.delete(roomId);
    }
  });

  socket.on('disconnect', () => {
    const player = players.get(socket.id);
    console.log('Client disconnected:', socket.id);

    if (player) {
      games.forEach((game, roomId) => {
        if (game.players.has(player.userId)) {
          game.removePlayer(player.userId);
          io.to(roomId).emit('player_left', {
            playerId: player.userId,
            username: player.username
          });

          if (game.players.size === 0) {
            games.delete(roomId);
          }
        }
      });

      players.delete(socket.id);
    }
  });
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});