import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const statePath = path.join(os.tmpdir(), "autotriage-e2e-state.json");

export default async function globalTeardown() {
  try {
    const raw = fs.readFileSync(statePath, { encoding: "utf-8" });
    const state = JSON.parse(raw) as { pid: number };
    try {
      process.kill(state.pid, "SIGTERM");
    } catch {
      // ignore
    }
    fs.unlinkSync(statePath);
  } catch {
    // ignore
  }
}
