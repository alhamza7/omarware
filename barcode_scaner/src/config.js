const path = require("path");

const ROOT = path.resolve(__dirname, "..");

module.exports = {
  ROOT,
  PORT: Number(process.env.PORT || 3000),
  JWT_SECRET: process.env.JWT_SECRET || "dev-secret-change-me",
  DB_PATH: process.env.DB_PATH || path.join(ROOT, "data", "app.sqlite"),
  EXCEL_PATH: process.env.EXCEL_PATH || path.join(ROOT, "items محمد دفان.xlsx"),
  SEED_ADMIN_USER: process.env.SEED_ADMIN_USER || "admin",
  SEED_ADMIN_PASS: process.env.SEED_ADMIN_PASS || "admin123",
};












