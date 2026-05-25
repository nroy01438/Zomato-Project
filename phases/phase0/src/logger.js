const levelOrder = ["debug", "info", "warn", "error"];

function nowIso() {
  return new Date().toISOString();
}

function shouldLog(currentLevel, msgLevel) {
  const currentIdx = levelOrder.indexOf(currentLevel);
  const msgIdx = levelOrder.indexOf(msgLevel);
  if (currentIdx === -1 || msgIdx === -1) return true;
  return msgIdx >= currentIdx;
}

export function createLogger({ level = "info" } = {}) {
  function log(msgLevel, message, meta) {
    if (!shouldLog(level, msgLevel)) return;
    const payload = {
      time: nowIso(),
      level: msgLevel,
      message,
      ...(meta && typeof meta === "object" ? { meta } : {})
    };
    console.log(JSON.stringify(payload));
  }

  return {
    debug: (message, meta) => log("debug", message, meta),
    info: (message, meta) => log("info", message, meta),
    warn: (message, meta) => log("warn", message, meta),
    error: (message, meta) => log("error", message, meta)
  };
}

