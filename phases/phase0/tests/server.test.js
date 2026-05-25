import test from "node:test";
import assert from "node:assert/strict";

import { createServer } from "../src/server.js";

test("GET /health returns ok:true", async () => {
  const server = createServer();
  await new Promise((resolve) => server.listen(0, resolve));
  const { port } = server.address();

  try {
    const res = await fetch(`http://127.0.0.1:${port}/health`);
    assert.equal(res.status, 200);
    const body = await res.json();
    assert.equal(body.ok, true);
    assert.ok(typeof body.env === "string");
  } finally {
    await new Promise((resolve) => server.close(resolve));
  }
});

