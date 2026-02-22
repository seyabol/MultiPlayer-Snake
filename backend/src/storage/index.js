const { AUTH_MODE, DATA_DIR } = require('../config');
const { createDevStore } = require('./devStore');
const { createFirebaseStore } = require('./firebaseStore');

async function initStore() {
  if (AUTH_MODE === 'firebase') {
    const store = await createFirebaseStore();
    console.log('Auth/storage: Firebase mode');
    return store;
  }

  const store = createDevStore(DATA_DIR);
  console.log('Auth/storage: DEV mode (no Firebase required)');
  return store;
}

module.exports = { initStore };
