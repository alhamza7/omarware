const jwt = require("jsonwebtoken");
const { JWT_SECRET } = require("./config");

function signUser(user) {
  return jwt.sign(
    { sub: user.id, username: user.username, role: user.role },
    JWT_SECRET,
    { expiresIn: "12h" }
  );
}

function requireAuth(req, res, next) {
  const token = req.cookies && req.cookies.auth;
  if (!token) return res.redirect("/login");
  try {
    req.user = jwt.verify(token, JWT_SECRET);
    return next();
  } catch {
    res.clearCookie("auth");
    return res.redirect("/login");
  }
}

function requireAuthApi(req, res, next) {
  const header = req.headers && req.headers.authorization;
  const bearer =
    header && typeof header === "string" && header.toLowerCase().startsWith("bearer ")
      ? header.slice(7).trim()
      : null;
  const token = bearer || (req.cookies && req.cookies.auth);
  if (!token) return res.status(401).json({ error: "unauthorized" });
  try {
    req.user = jwt.verify(token, JWT_SECRET);
    return next();
  } catch {
    res.clearCookie("auth");
    return res.status(401).json({ error: "unauthorized" });
  }
}

function requireAdmin(req, res, next) {
  if (!req.user || req.user.role !== 'admin') {
    return res.status(403).json({ error: "admin_required", message: "This action requires administrator privileges" });
  }
  return next();
}

function requireAdminPage(req, res, next) {
  if (!req.user || req.user.role !== 'admin') {
    return res.status(403).send("Access Denied: Administrator privileges required");
  }
  return next();
}

module.exports = { signUser, requireAuth, requireAuthApi, requireAdmin, requireAdminPage };


