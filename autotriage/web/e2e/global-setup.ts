import { spawn } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import * as net from "node:net";
import { setTimeout as sleep } from "node:timers/promises";
import { request as pwRequest } from "@playwright/test";
import { fileURLToPath } from "node:url";

const baseUrl = "http://127.0.0.1:18080";
const statePath = path.join(os.tmpdir(), "autotriage-e2e-state.json");
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.resolve(__dirname, "..", "..");

function pythonCmd(): string {
  const venvPython = path.join(projectRoot, ".venv", "bin", "python");
  return fs.existsSync(venvPython) ? venvPython : process.platform === "win32" ? "python" : "python3";
}

async function waitReady() {
  const req = await pwRequest.newContext({ baseURL: baseUrl });
  for (let i = 0; i < 120; i++) {
    try {
      const r = await req.get("/readyz");
      if (r.status() === 200) return;
    } catch {
      // ignore
    }
    await sleep(250);
  }
  throw new Error("backend did not become ready");
}

function portInUse(host: string, port: number): Promise<boolean> {
  return new Promise((resolve) => {
    const socket = net.connect({ host, port });
    socket.once("connect", () => {
      socket.end();
      resolve(true);
    });
    socket.once("error", () => resolve(false));
  });
}

function tryKillPid(pid: number): void {
  try {
    process.kill(pid, "SIGTERM");
  } catch {
    // ignore
  }
}

function cleanupStaleState(): void {
  try {
    const raw = fs.readFileSync(statePath, { encoding: "utf-8" });
    const state = JSON.parse(raw) as { pid: number };
    tryKillPid(state.pid);
    fs.unlinkSync(statePath);
  } catch {
    // ignore
  }
}

async function ingestSamples() {
  const req = await pwRequest.newContext({ baseURL: baseUrl });
  const payloads = [
    {
      vendor: "vendor_a",
      time: "2025-01-01T00:00:01Z",
      rule: "R-LOGIN-001",
      severity: 7,
      src_ip: "1.2.3.4",
      user: "alice",
      host: "workstation-1",
      title: "Suspicious login"
    },
    {
      vendor: "vendor_a",
      time: "2025-01-01T00:01:05Z",
      rule: "R-LOGIN-001",
      severity: 7,
      src_ip: "1.2.3.4",
      user: "alice",
      host: "workstation-1",
      title: "Suspicious login"
    }
  ];
  for (let i = 0; i < payloads.length; i++) {
    const r = await req.post("/webhook/alerts", {
      headers: { "Idempotency-Key": `e2e-${i}` },
      data: payloads[i]
    });
    if (r.status() !== 202) throw new Error(`ingest failed: ${r.status()}`);
  }
}

async function waitCases() {
  const req = await pwRequest.newContext({ baseURL: baseUrl });
  for (let i = 0; i < 120; i++) {
    const r = await req.get("/api/cases");
    if (r.status() === 200) {
      const body = await r.json();
      if ((body?.items?.length ?? 0) > 0) return;
    }
    await sleep(250);
  }
  throw new Error("cases did not appear");
}

export default async function globalSetup() {
  cleanupStaleState();
  if (await portInUse("127.0.0.1", 18080)) {
    throw new Error("port 18080 already in use (stale server?). Stop it and re-run Playwright.");
  }
  const dbPath = path.join(os.tmpdir(), `autotriage-e2e-${process.pid}-${Date.now()}.db`);

  const child = spawn(
    pythonCmd(),
    ["-m", "autotriage.cli.main", "run", "--mode", "all", "--host", "127.0.0.1", "--port", "18080"],
    {
      cwd: projectRoot,
      env: { ...process.env, AUTOTRIAGE_DB_PATH: dbPath, AUTOTRIAGE_LOG_LEVEL: "ERROR" },
      stdio: "inherit"
    }
  );

  await waitReady();
  await ingestSamples();
  await waitCases();

  fs.writeFileSync(statePath, JSON.stringify({ pid: child.pid, dbPath, baseUrl }), { encoding: "utf-8" });
}
