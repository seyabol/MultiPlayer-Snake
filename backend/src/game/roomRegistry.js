const { GameRoom } = require('./gameRoom');

function makeRoomId() {
  return `room_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
}

class RoomRegistry {
  constructor() {
    this.rooms = new Map();
  }

  createRoom({ hostId, hostUsername, config, maxPlayers, title }) {
    const id = makeRoomId();

    const room = new GameRoom({
      id,
      hostId,
      hostUsername,
      config,
      maxPlayers,
      title: title || `${hostUsername}'s room`,
    });

    this.rooms.set(id, room);
    return room;
  }

  get(roomId) {
    return this.rooms.get(roomId) || null;
  }

  delete(roomId) {
    this.rooms.delete(roomId);
  }

  listPublic({ includePlaying = true } = {}) {
    const out = [];

    for (const room of this.rooms.values()) {
      if (room.state === 'finished') continue;
      if (!includePlaying && room.state !== 'waiting') continue;
      out.push(room.toPublic());
    }

    out.sort((a, b) => b.createdAt - a.createdAt);
    return out;
  }

  listJoinable() {
    return this.listPublic({ includePlaying: false }).filter((r) => r.playerCount < r.maxPlayers);
  }

  join(roomId, { userId, username, color }) {
    const room = this.get(roomId);
    if (!room) return { ok: false, error: 'Room not found' };
    if (room.state !== 'waiting') return { ok: false, error: 'Game already started' };
    if (room.isFull()) return { ok: false, error: 'Room is full' };

    if (!room.players.has(userId)) {
      room.addPlayer(userId, { username, color });
    }

    return { ok: true, room };
  }

  leave(roomId, userId) {
    const room = this.get(roomId);
    if (!room) return { ok: false, error: 'Room not found' };

    const wasHost = room.hostId === userId;
    room.removePlayer(userId);

    if (room.players.size === 0) {
      this.delete(roomId);
      return { ok: true, deleted: true, room: null, wasHost };
    }

    if (wasHost) {
      const next = Array.from(room.players.values())[0];
      room.hostId = next.id;
      room.hostUsername = next.username;
      room.title = `${next.username}'s room`;
    }

    return { ok: true, deleted: false, room, wasHost };
  }
}

module.exports = { RoomRegistry };
