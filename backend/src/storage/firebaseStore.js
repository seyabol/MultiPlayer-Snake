const fs = require('fs');

async function createFirebaseStore() {
  const admin = require('firebase-admin');

  let credential;
  if (process.env.FIREBASE_SERVICE_ACCOUNT_JSON) {
    const saPath = process.env.FIREBASE_SERVICE_ACCOUNT_JSON;
    if (!fs.existsSync(saPath)) {
      throw new Error(`FIREBASE_SERVICE_ACCOUNT_JSON points to missing file: ${saPath}`);
    }
    const sa = JSON.parse(fs.readFileSync(saPath, 'utf8'));
    credential = admin.credential.cert(sa);
  } else {
    const projectId = process.env.FIREBASE_PROJECT_ID;
    const clientEmail = process.env.FIREBASE_CLIENT_EMAIL;
    const privateKey = process.env.FIREBASE_PRIVATE_KEY?.replace(/\\n/g, '\n');

    if (!projectId || !clientEmail || !privateKey) {
      throw new Error(
        'Firebase mode requires FIREBASE_PROJECT_ID, FIREBASE_CLIENT_EMAIL, FIREBASE_PRIVATE_KEY (or FIREBASE_SERVICE_ACCOUNT_JSON).'
      );
    }

    credential = admin.credential.cert({ projectId, clientEmail, privateKey });
  }

  admin.initializeApp({ credential });
  const db = admin.firestore();

  return {
    mode: 'firebase',
    admin,
    db,

    async verifyIdToken(idToken) {
      return admin.auth().verifyIdToken(idToken);
    },

    async getUser(userId) {
      const doc = await db.collection('users').doc(userId).get();
      return doc.exists ? doc.data() : null;
    },

    async upsertUser(userId, partial) {
      await db.collection('users').doc(userId).set(
        {
          ...partial,
          lastLogin: admin.firestore.FieldValue.serverTimestamp(),
        },
        { merge: true }
      );
      return this.getUser(userId);
    },

    async incrementUserStats(userId, { gamesPlayed = 0, wins = 0, totalScore = 0 }) {
      await db.collection('users').doc(userId).set(
        {
          gamesPlayed: admin.firestore.FieldValue.increment(gamesPlayed),
          wins: admin.firestore.FieldValue.increment(wins),
          totalScore: admin.firestore.FieldValue.increment(totalScore),
        },
        { merge: true }
      );
      return this.getUser(userId);
    },

    async addGame(gameRecord) {
      const doc = await db.collection('games').add({
        ...gameRecord,
        endTime: admin.firestore.Timestamp.fromMillis(gameRecord.endTime || Date.now()),
        startTime: gameRecord.startTime ? admin.firestore.Timestamp.fromMillis(gameRecord.startTime) : null,
      });
      return { id: doc.id, ...gameRecord };
    },

    async listRecentGamesForUser(userId, limit = 20) {
      const snap = await db
        .collection('games')
        .where('players', 'array-contains', userId)
        .orderBy('endTime', 'desc')
        .limit(limit)
        .get();

      const games = [];
      snap.forEach((d) => games.push({ id: d.id, ...d.data() }));
      return games;
    },

    async listLeaderboard(limit = 10) {
      const snap = await db.collection('users').orderBy('totalScore', 'desc').limit(limit).get();
      const out = [];
      snap.forEach((d) => out.push({ id: d.id, ...d.data() }));
      return out;
    },
  };
}

module.exports = { createFirebaseStore };
