const { MAX_PLAYERS } = require('../config');

function registerSockets(io, { store, rooms }) {
  const sockets = new Map();

  const broadcastRooms = () => {
    io.emit('rooms_update', { rooms: rooms.listJoinable() });
  };

  io.on('connection', (socket) => {
    console.log('Client connected:', socket.id);

    socket.on('authenticate', async (data, cb) => {
      try {
        const username = String(data?.username || '').trim() || 'Player';

        if (store.mode === 'firebase') {
          const idToken = data?.idToken;
          if (!idToken) {
            socket.emit('auth_error', { message: 'Missing idToken' });
            cb?.({ ok: false, error: 'Missing idToken' });
            return;
          }

          const decoded = await store.verifyIdToken(idToken);
          const userId = decoded.uid;

          sockets.set(socket.id, { userId, username });
          await store.upsertUser(userId, { username });

          socket.emit('authenticated', { userId, username });
          socket.emit('rooms_update', { rooms: rooms.listJoinable() });
          cb?.({ ok: true, userId, username });

          console.log(`Authenticated (firebase): ${username} (${userId})`);
          return;
        }

        const userId = (data?.userId && String(data.userId)) || `dev_${socket.id}`;
        sockets.set(socket.id, { userId, username });
        await store.upsertUser(userId, { username, lastLogin: Date.now() });

        socket.emit('authenticated', { userId, username });
        socket.emit('rooms_update', { rooms: rooms.listJoinable() });
        cb?.({ ok: true, userId, username });

        console.log(`Authenticated (dev): ${username} (${userId})`);
      } catch (err) {
        console.error('Authentication error:', err);
        socket.emit('auth_error', { message: 'Authentication failed' });
        cb?.({ ok: false, error: 'Authentication failed' });
      }
    });

    socket.on('list_rooms', (_, cb) => {
      cb?.({ ok: true, rooms: rooms.listJoinable() });
    });

    socket.on('create_room', (data, cb) => {
      const player = sockets.get(socket.id);
      if (!player) {
        cb?.({ ok: false, error: 'Not authenticated' });
        return;
      }

      const config = data?.config || {};
      const title = String(data?.title || '').trim();
      const color = data?.color || [0, 255, 0];

      const room = rooms.createRoom({
        hostId: player.userId,
        hostUsername: player.username,
        config,
        maxPlayers: MAX_PLAYERS,
        title,
      });

      room.addPlayer(player.userId, { username: player.username, color });

      socket.join(room.id);
      socket.emit('room_created', { roomId: room.id, game: room.getState() });

      broadcastRooms();
      cb?.({ ok: true, roomId: room.id });

      console.log(`Room created: ${room.id} by ${player.username}`);
    });

    socket.on('join_room', (data, cb) => {
      const player = sockets.get(socket.id);
      if (!player) {
        cb?.({ ok: false, error: 'Not authenticated' });
        return;
      }

      const roomId = data?.roomId;
      const color = data?.color || [0, 0, 255];

      const { ok, error, room } = rooms.join(roomId, {
        userId: player.userId,
        username: player.username,
        color,
      });

      if (!ok) {
        socket.emit('error', { message: error });
        cb?.({ ok: false, error });
        return;
      }

      socket.join(roomId);

      socket.emit('joined_room', { roomId, game: room.getState() });

      io.to(roomId).emit('player_joined', {
        playerId: player.userId,
        username: player.username,
        game: room.getState(),
      });

      broadcastRooms();
      cb?.({ ok: true, roomId });

      console.log(`Player joined: ${player.username} -> ${roomId}`);
    });

    socket.on('start_game', (data, cb) => {
      const player = sockets.get(socket.id);
      const roomId = data?.roomId;
      const room = rooms.get(roomId);

      if (!player || !room) {
        cb?.({ ok: false, error: 'Room not found' });
        return;
      }

      if (room.hostId !== player.userId) {
        socket.emit('error', { message: 'Only host can start' });
        cb?.({ ok: false, error: 'Only host can start' });
        return;
      }

      if (room.players.size < 2) {
        socket.emit('error', { message: 'Need at least 2 players' });
        cb?.({ ok: false, error: 'Need at least 2 players' });
        return;
      }

      room.state = 'playing';
      room.startTime = Date.now();

      io.to(roomId).emit('game_started', { game: room.getState() });
      broadcastRooms();
      cb?.({ ok: true });

      console.log(`Game started: ${roomId}`);
    });

    socket.on('game_update', (data) => {
      const player = sockets.get(socket.id);
      const roomId = data?.roomId;
      const room = rooms.get(roomId);
      if (!player || !room) return;
      if (room.state !== 'playing') return;

      const snakeData = data?.snakeData;
      const score = Number(data?.score || 0);

      if (snakeData) {
        room.updateSnake(player.userId, snakeData);
      }
      room.setScore(player.userId, score);
      room.turn += 1;

      io.to(roomId).emit('game_state', room.getState());
    });

    socket.on('player_died', async (data) => {
      const player = sockets.get(socket.id);
      const roomId = data?.roomId;
      const room = rooms.get(roomId);
      if (!player || !room) return;

      room.setAlive(player.userId, false);

      io.to(roomId).emit('player_died', {
        playerId: player.userId,
        username: player.username,
        game: room.getState(),
      });

      const alive = room.getAlivePlayers();
      if (alive.length > 1 || room.state !== 'playing') return;

      room.state = 'finished';
      room.endTime = Date.now();
      room.winner = alive.length === 1 ? alive[0].id : null;

      const scores = {};
      for (const [pid, pdata] of room.players.entries()) {
        scores[pid] = pdata.score || 0;
      }

      try {
        await store.addGame({
          id: room.id,
          players: Array.from(room.players.keys()),
          scores,
          winner: room.winner,
          startTime: room.startTime,
          endTime: room.endTime,
        });

        for (const [pid, pdata] of room.players.entries()) {
          await store.incrementUserStats(pid, {
            gamesPlayed: 1,
            wins: pid === room.winner ? 1 : 0,
            totalScore: pdata.score || 0,
          });
        }
      } catch (e) {
        console.error('Error saving game:', e);
      }

      io.to(roomId).emit('game_over', { winner: room.winner, finalState: room.getState() });
      broadcastRooms();

      setTimeout(() => {
        rooms.delete(roomId);
        broadcastRooms();
      }, 30_000);
    });

    socket.on('leave_room', (data, cb) => {
      const player = sockets.get(socket.id);
      const roomId = data?.roomId;
      if (!player || !roomId) {
        cb?.({ ok: false, error: 'Bad request' });
        return;
      }

      const result = rooms.leave(roomId, player.userId);
      socket.leave(roomId);

      io.to(roomId).emit('player_left', {
        playerId: player.userId,
        username: player.username,
        game: result.room ? result.room.getState() : null,
      });

      broadcastRooms();
      cb?.({ ok: true });
    });

    socket.on('disconnect', () => {
      const player = sockets.get(socket.id);
      console.log('Client disconnected:', socket.id);

      if (!player) return;

      for (const room of rooms.rooms.values()) {
        if (!room.players.has(player.userId)) continue;

        const result = rooms.leave(room.id, player.userId);
        io.to(room.id).emit('player_left', {
          playerId: player.userId,
          username: player.username,
          game: result.room ? result.room.getState() : null,
        });
      }

      sockets.delete(socket.id);
      broadcastRooms();
    });
  });
}

module.exports = { registerSockets };
