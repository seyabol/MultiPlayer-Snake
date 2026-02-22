function registerRoutes(app, { store, rooms }) {
  app.get('/health', (req, res) => {
    res.json({ status: 'ok', authMode: store.mode, timestamp: Date.now() });
  });

  app.get('/api/stats/:userId', async (req, res) => {
    try {
      const userId = req.params.userId;
      const stats = await store.getUser(userId);
      if (!stats) return res.status(404).json({ error: 'User not found' });

      const recentGamesRaw = await store.listRecentGamesForUser(userId, 20);
      const recentGames = recentGamesRaw.map((g) => {
        const score = g.scores?.[userId] ?? 0;
        return {
          id: g.id,
          endTime: g.endTime,
          startTime: g.startTime,
          winner: g.winner,
          score,
          players: g.players,
        };
      });

      res.json({ stats, recentGames });
    } catch (e) {
      console.error('Error fetching stats:', e);
      res.status(500).json({ error: 'Internal server error' });
    }
  });

  app.get('/api/leaderboard', async (req, res) => {
    try {
      const limit = Math.min(50, Math.max(1, Number(req.query.limit || 10)));
      const leaderboard = await store.listLeaderboard(limit);
      res.json({ leaderboard });
    } catch (e) {
      console.error('Error fetching leaderboard:', e);
      res.status(500).json({ error: 'Internal server error' });
    }
  });

  app.get('/api/rooms', (req, res) => {
    res.json({ rooms: rooms.listJoinable() });
  });

  app.get('/api/games/active', (req, res) => {
    const active = rooms.listPublic({ includePlaying: true }).map((r) => ({
      id: r.id,
      playerCount: r.playerCount,
      state: r.state,
    }));

    res.json({ games: active });
  });
}

module.exports = { registerRoutes };
