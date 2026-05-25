import http from "http";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

import { config } from "./config.js";
import { createLogger } from "./logger.js";
import { toPublicError } from "./errors.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.resolve(__dirname, "..", "..", "..");

const logger = createLogger({ level: config.env === "development" ? "debug" : "info" });

function sendJson(res, status, obj) {
  const body = JSON.stringify(obj);
  res.writeHead(status, {
    "content-type": "application/json; charset=utf-8",
    "content-length": Buffer.byteLength(body)
  });
  res.end(body);
}

function getContentType(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  switch (ext) {
    case ".html":
      return "text/html; charset=utf-8";
    case ".css":
      return "text/css; charset=utf-8";
    case ".js":
      return "text/javascript; charset=utf-8";
    case ".json":
      return "application/json; charset=utf-8";
    case ".svg":
      return "image/svg+xml";
    case ".png":
      return "image/png";
    case ".jpg":
    case ".jpeg":
      return "image/jpeg";
    case ".ico":
      return "image/x-icon";
    default:
      return "application/octet-stream";
  }
}

function safeResolveStatic(requestPath) {
  const urlPath = decodeURIComponent(requestPath.split("?")[0] ?? "/");
  const normalized = path.posix.normalize(urlPath);
  const withoutTraversal = normalized.replace(/^(\.\.(\/|\\|$))+/, "");
  const rel = withoutTraversal === "/" ? "/index.html" : withoutTraversal;
  const abs = path.resolve(projectRoot, `.${rel}`);
  if (!abs.startsWith(projectRoot)) return null;
  return abs;
}

export function createServer() {
  return http.createServer((req, res) => {
    const start = Date.now();
    res.on("finish", () => {
      logger.info("request", {
        method: req.method,
        path: req.url,
        status: res.statusCode,
        durationMs: Date.now() - start
      });
    });

    try {
      if (req.method === "GET" && (req.url === "/health" || req.url?.startsWith("/health?"))) {
        sendJson(res, 200, { ok: true, env: config.env });
        return;
      }

      if (req.method !== "GET" && req.method !== "HEAD") {
        sendJson(res, 405, { ok: false, message: "Method not allowed" });
        return;
      }

      const filePath = safeResolveStatic(req.url ?? "/");
      if (!filePath) {
        sendJson(res, 400, { ok: false, message: "Bad request" });
        return;
      }

      fs.stat(filePath, (err, stat) => {
        if (err || !stat.isFile()) {
          sendJson(res, 404, { ok: false, message: "Not found" });
          return;
        }

        const contentType = getContentType(filePath);
        res.writeHead(200, { "content-type": contentType });
        if (req.method === "HEAD") {
          res.end();
          return;
        }
        fs.createReadStream(filePath).pipe(res);
      });
    } catch (err) {
      logger.error("unhandled_error", {
        message: err?.message ?? String(err),
        stack: err?.stack
      });
      const pub = toPublicError(err);
      sendJson(res, pub.status, pub);
    }
  });
}

export function startServer() {
  const server = createServer();

  process.on("unhandledRejection", (reason) => {
    logger.error("unhandled_rejection", { reason: String(reason) });
  });

  process.on("uncaughtException", (err) => {
    logger.error("uncaught_exception", { message: err.message, stack: err.stack });
    process.exitCode = 1;
  });

  server.listen(config.port, () => {
    logger.info("server_started", { port: config.port });
  });

  return server;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  startServer();
}

