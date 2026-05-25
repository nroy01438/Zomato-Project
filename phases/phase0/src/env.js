import fs from "fs";
import path from "path";

function parseEnvLine(line) {
  const trimmed = line.trim();
  if (!trimmed || trimmed.startsWith("#")) return null;

  const eq = trimmed.indexOf("=");
  if (eq === -1) return null;

  const key = trimmed.slice(0, eq).trim();
  let value = trimmed.slice(eq + 1).trim();

  if (
    (value.startsWith('"') && value.endsWith('"')) ||
    (value.startsWith("'") && value.endsWith("'"))
  ) {
    value = value.slice(1, -1);
  }

  return { key, value };
}

export function loadEnvFile({ filePath }) {
  try {
    const raw = fs.readFileSync(filePath, "utf8");
    for (const line of raw.split(/\r?\n/)) {
      const parsed = parseEnvLine(line);
      if (!parsed) continue;
      if (process.env[parsed.key] === undefined) {
        process.env[parsed.key] = parsed.value;
      }
    }
    return { loaded: true };
  } catch (err) {
    if (err && typeof err === "object" && "code" in err && err.code === "ENOENT") {
      return { loaded: false };
    }
    throw err;
  }
}

export function loadEnvFromProjectRoot({ projectRoot }) {
  const envPath = path.join(projectRoot, ".env");
  return loadEnvFile({ filePath: envPath });
}

