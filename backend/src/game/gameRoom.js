class GameRoom {
  constructor({ id, hostId, hostUsername, config, maxPlayers, title }) {
    this.id = id;
    this.hostId = hostId;
    this.hostUsername = hostUsername;
    this.title = title;

    this.players = new Map();
    this.snakes = new Map();
    this.fruits = [];

    this.state = 'waiting';
    this.config = config || {};
    this.maxPlayers = maxPlayers;

    this.turn = 0;
    this.createdAt = Date.now();

    this.startTime = null;
    this.endTime = null;
    this.winner = null;
  }

  addPlayer(userId, { username, color }) {
    this.players.set(userId, {
      id: userId,
      username,
      color,
      score: 0,
      alive: true,
    });
  }

  removePlayer(userId) {
    this.players.delete(userId);
    this.snakes.delete(userId);
  }

  updateSnake(userId, snakeData) {
    this.snakes.set(userId, snakeData);
  }

  setScore(userId, score) {
    const p = this.players.get(userId);
    if (p) p.score = score;
  }

  setAlive(userId, alive) {
    const p = this.players.get(userId);
    if (p) p.alive = alive;
  }

  getAlivePlayers() {
    return Array.from(this.players.values()).filter((p) => p.alive);
  }

  isFull() {
    return this.players.size >= this.maxPlayers;
  }

  toPublic() {
    return {
      id: this.id,
      title: this.title,
      host: { id: this.hostId, username: this.hostUsername },
      state: this.state,
      playerCount: this.players.size,
      maxPlayers: this.maxPlayers,
      createdAt: this.createdAt,
    };
  }

  getState() {
    return {
      id: this.id,
      players: Array.from(this.players.values()),
      snakes: Array.from(this.snakes.entries()),
      fruits: this.fruits,
      state: this.state,
      turn: this.turn,
      hostId: this.hostId,
    };
  }
}

module.exports = { GameRoom };
