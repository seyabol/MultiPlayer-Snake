const express = require('express');
const http = require('http');
const socketIO = require('socket.io');
const cors = require('cors');

const { PORT } = require('./config');
const { initStore } = require('./storage');
const { RoomRegistry } = require('./game/roomRegistry');
const { registerRoutes } = require('./http/routes');
const { registerSockets } = require('./sockets');

async function main() {
  const store = await initStore();

  const app = express();
  const server = http.createServer(app);
  const io = socketIO(server, {
    cors: { origin: '*', methods: ['GET', 'POST'] },
  });

  app.use(cors());
  app.use(express.json());

  const rooms = new RoomRegistry();

  registerRoutes(app, { store, rooms });
  registerSockets(io, { store, rooms });

  server.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
  });
}

main().catch((err) => {
  console.error('Failed to start server:', err.message);
  process.exit(1);
});
