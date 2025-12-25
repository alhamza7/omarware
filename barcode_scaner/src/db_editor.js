const { openDb } = require("./db");
const bcrypt = require("bcryptjs");
const readline = require("readline");

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
});

function question(query) {
  return new Promise((resolve) => rl.question(query, resolve));
}

async function listUsers(db) {
  const users = db.prepare("SELECT id, username, role, warehouse_id, created_at FROM users ORDER BY id").all();
  console.log("\n=== USERS ===");
  console.table(users);
}

async function listItems(db, limit = 20) {
  const items = db
    .prepare("SELECT id, item_code, item_name FROM items ORDER BY id LIMIT ?")
    .all(limit);
  console.log(`\n=== ITEMS (showing first ${limit}) ===`);
  console.table(items);
}

async function listCounts(db, limit = 20) {
  const counts = db
    .prepare(
      `
      SELECT c.id, c.item_id, c.user_id, c.warehouse_id, c.qty, c.note, c.created_at,
             u.username, i.item_code
      FROM counts c
      JOIN users u ON u.id = c.user_id
      JOIN items i ON i.id = c.item_id
      ORDER BY c.id DESC
      LIMIT ?
    `
    )
    .all(limit);
  console.log(`\n=== COUNTS (showing last ${limit}) ===`);
  console.table(counts);
}

async function addUser(db) {
  const username = await question("Username: ");
  const password = await question("Password: ");
  const role = (await question("Role (user/admin) [user]: ")) || "user";
  const warehouse_id = parseInt((await question("Warehouse ID (1-18) [1]: ")) || "1");

  if (!username || !password) {
    console.log("Username and password are required!");
    return;
  }

  const password_hash = await bcrypt.hash(password, 10);
  try {
    db.prepare("INSERT INTO users (username, password_hash, role, warehouse_id) VALUES (?, ?, ?, ?)").run(
      username,
      password_hash,
      role,
      warehouse_id
    );
    console.log(`✓ User ${username} created successfully!`);
  } catch (err) {
    console.log(`✗ Error: ${err.message}`);
  }
}

async function updateUser(db) {
  const userId = await question("User ID to update: ");
  const user = db.prepare("SELECT id, username, role, warehouse_id FROM users WHERE id = ?").get(userId);
  if (!user) {
    console.log("User not found!");
    return;
  }

  console.log("\nCurrent user:", user);
  const newUsername = await question(`New username [${user.username}]: `);
  const newRole = await question(`New role (user/admin) [${user.role}]: `);
  const newWarehouse = await question(`New warehouse ID (1-18) [${user.warehouse_id}]: `);
  const newPassword = await question("New password (leave empty to keep current): ");

  const updates = [];
  const values = [];

  if (newUsername && newUsername !== user.username) {
    updates.push("username = ?");
    values.push(newUsername);
  }
  if (newRole && newRole !== user.role) {
    updates.push("role = ?");
    values.push(newRole);
  }
  if (newWarehouse && parseInt(newWarehouse) !== user.warehouse_id) {
    updates.push("warehouse_id = ?");
    values.push(parseInt(newWarehouse));
  }
  if (newPassword) {
    const password_hash = await bcrypt.hash(newPassword, 10);
    updates.push("password_hash = ?");
    values.push(password_hash);
  }

  if (updates.length === 0) {
    console.log("No changes made.");
    return;
  }

  values.push(userId);
  const sql = `UPDATE users SET ${updates.join(", ")} WHERE id = ?`;
  try {
    db.prepare(sql).run(...values);
    console.log("✓ User updated successfully!");
  } catch (err) {
    console.log(`✗ Error: ${err.message}`);
  }
}

async function deleteUser(db) {
  const userId = await question("User ID to delete: ");
  const user = db.prepare("SELECT id, username FROM users WHERE id = ?").get(userId);
  if (!user) {
    console.log("User not found!");
    return;
  }

  const confirm = await question(`Are you sure you want to delete user '${user.username}'? (yes/no): `);
  if (confirm.toLowerCase() !== "yes") {
    console.log("Cancelled.");
    return;
  }

  try {
    db.prepare("DELETE FROM users WHERE id = ?").run(userId);
    console.log("✓ User deleted successfully!");
  } catch (err) {
    console.log(`✗ Error: ${err.message}`);
  }
}

async function runQuery(db) {
  const sql = await question("Enter SQL query: ");
  if (!sql) return;

  try {
    const result = db.prepare(sql).all();
    console.log("\n=== QUERY RESULT ===");
    console.table(result);
  } catch (err) {
    console.log(`✗ Error: ${err.message}`);
  }
}

async function showMenu() {
  console.log("\n=== DATABASE EDITOR ===");
  console.log("1. List users");
  console.log("2. List items");
  console.log("3. List counts");
  console.log("4. Add user");
  console.log("5. Update user");
  console.log("6. Delete user");
  console.log("7. Run custom SQL query");
  console.log("8. Exit");
  console.log("======================");
}

async function main() {
  const db = openDb();

  console.log("Database editor started!");
  console.log("Database path:", require("./config").DB_PATH);

  while (true) {
    await showMenu();
    const choice = await question("\nSelect an option: ");

    switch (choice) {
      case "1":
        await listUsers(db);
        break;
      case "2":
        const limit = await question("How many items to show? [20]: ");
        await listItems(db, parseInt(limit) || 20);
        break;
      case "3":
        const countLimit = await question("How many counts to show? [20]: ");
        await listCounts(db, parseInt(countLimit) || 20);
        break;
      case "4":
        await addUser(db);
        break;
      case "5":
        await updateUser(db);
        break;
      case "6":
        await deleteUser(db);
        break;
      case "7":
        await runQuery(db);
        break;
      case "8":
        console.log("Goodbye!");
        db.close();
        rl.close();
        process.exit(0);
      default:
        console.log("Invalid option!");
    }
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});








