# Multiplayer Snake 

This repo is split into **backend** (Node + Socket.IO) and **frontend** (Python + Pygame).

- Backend runs out-of-the-box in **DEV mode** (no Firebase required).
- Frontend supports **Firebase Auth** if you add a real `frontend/firebase_config.json`, but it also works in **local auth mode** automatically.

---

## Project structure

```
.
├─ backend/      # Node/Express + Socket.IO server
├─ frontend/     # Python/Pygame client
└─ docker-compose.yml
```

---

## 1) Run the backend (recommended: Docker)

From the repo root:

```bash
docker compose up --build
```

Backend:
- `http://localhost:3000`
- Health check: `http://localhost:3000/health`

### Where data is stored (DEV mode)
In DEV mode, users + games are saved to JSON files in:
- `backend/data/users.json`
- `backend/data/games.json`

---

## 2) Run the frontend (Python)

Open a new terminal:

```bash
cd frontend
python -m venv .venv

# macOS/Linux
source .venv/bin/activate

# Windows (PowerShell)
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt
python main.py
```

---

## First run: account required

On the first run (local auth mode), the game will ask you to **create an account** before entering the lobby.

Accounts are saved locally on your machine in `frontend/users_local.json`.

---

## Multiplayer (2 players)

Run **two instances** of the client (two terminals):

1) Create an account / Sign in
2) Player A creates a room (`C`)
3) Player B will see it in the room list and can select it with ↑/↓ and press `ENTER` to join
4) Host starts the game in the waiting room (`S`)

Lobby shortcuts:
- `C` Create room
- `ENTER` Join selected room
- `R` Refresh list
- `S` Stats
- `L` Leaderboard

---

## Controls + leveling

In-game controls:
- **Arrows** or **WASD**
- `ESC` leave the game

Food gives different points (shown as emoji), and your **level** increases with score.
The game starts slower and speeds up a bit as you level up.

---

## Optional: enable Firebase auth + Firestore stats

### Backend (Firebase mode)
Edit `backend/.env`:

```env
AUTH_MODE=firebase
FIREBASE_PROJECT_ID=...
FIREBASE_CLIENT_EMAIL=...
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
```

Then restart docker compose.

### Frontend (Firebase mode)
Edit `frontend/firebase_config.json`:

```json
{
  "project_id": "YOUR_FIREBASE_PROJECT_ID",
  "api_key": "YOUR_FIREBASE_WEB_API_KEY"
}
```

---
