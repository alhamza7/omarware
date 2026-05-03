const bcrypt = require("bcryptjs");
const { openDb, migrate } = require("./db");
const { EXCEL_PATH, SEED_ADMIN_USER, SEED_ADMIN_PASS } = require("./config");
const { readItemsFromExcel, upsertItems, upsertBarcodes } = require("./excel_import");

async function main() {
  const db = openDb();
  migrate(db);

  const adminExists = db
    .prepare("SELECT id FROM users WHERE username = ?")
    .get(SEED_ADMIN_USER);
  if (!adminExists) {
    const password_hash = await bcrypt.hash(SEED_ADMIN_PASS, 10);
    db.prepare(
      "INSERT INTO users (username, password_hash, role) VALUES (?, ?, 'admin')"
    ).run(SEED_ADMIN_USER, password_hash);
    console.log(`Seeded admin user: ${SEED_ADMIN_USER}`);
  } else {
    console.log(`Admin user already exists: ${SEED_ADMIN_USER}`);
  }

  // Add 12 users with numbers 1-12
  const roles = ['user', 'user', 'user', 'user', 'user', 'user', 'user', 'user', 'user', 'user', 'user', 'admin'];
  const insertUser = db.prepare(
    "INSERT OR IGNORE INTO users (username, password_hash, role, warehouse_id) VALUES (?, ?, ?, ?)"
  );
  
  for (let i = 1; i <= 12; i++) {
    const username = `user${i}`;
    const password = `user${i}123`; // Simple password for each user
    const password_hash = await bcrypt.hash(password, 10);
    // Random warehouse_id between 1 and 18
    const warehouse_id = Math.floor(Math.random() * 18) + 1;
    // Random role (mostly 'user', but one might be 'admin')
    const role = roles[Math.floor(Math.random() * roles.length)];
    
    try {
      insertUser.run(username, password_hash, role, warehouse_id);
      console.log(`Seeded user: ${username} (role: ${role}, warehouse: ${warehouse_id})`);
    } catch (err) {
      if (err.message.includes('UNIQUE constraint')) {
        console.log(`User ${username} already exists, skipping...`);
      } else {
        throw err;
      }
    }
  }

  console.log(`Reading Excel: ${EXCEL_PATH}`);
  const { items, barcodes } = await readItemsFromExcel(EXCEL_PATH);
  const n = upsertItems(db, items);
  const b = upsertBarcodes(db, barcodes);
  console.log(`Imported/updated items: ${n}`);
  console.log(`Imported/updated barcodes: ${b}`);

  db.close();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});


