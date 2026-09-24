import { spawn, spawnSync } from "node:child_process";
import path from "node:path";
import { setTimeout as delay } from "node:timers/promises";

const frontendEnv = { ...process.env, FRONTEND_PORT: "3211" };
const apiEnv = {
  ...process.env,
  DIAMANT_E2E_MODE: "1",
  DATABASE_URL: "sqlite:///tmp/e2e-runtime/diamant-id-e2e.sqlite3",
};
const children = [];
const frontendRoot = process.cwd();
const projectRoot = path.resolve(frontendRoot, "..");
const pythonExecutable = path.join(projectRoot, ".venv", "Scripts", "python.exe");
const gulpExecutable = path.join(frontendRoot, "node_modules", "gulp", "bin", "gulp.js");
const playwrightExecutable = path.join(frontendRoot, "node_modules", "@playwright", "test", "cli.js");
const staticServer = path.join(frontendRoot, "scripts", "serve-real-e2e.mjs");

function start(command, args, options) {
  const child = spawn(command, args, { stdio: "inherit", ...options });
  children.push(child);
  child.once("error", (error) => {
    console.error(`Не вдалося запустити E2E process: ${error.message}`);
    void stopChildren();
    process.exitCode = 1;
  });
  return child;
}

function run(command, args, options) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, { stdio: "inherit", ...options });
    child.once("error", reject);
    child.once("exit", (code) => (code === 0 ? resolve() : reject(new Error(`Command exited with ${code}`))));
  });
}

async function waitFor(url) {
  for (let attempt = 0; attempt < 240; attempt += 1) {
    try { if ((await fetch(url)).ok) return; } catch { /* server is starting */ }
    await delay(250);
  }
  throw new Error(`Timed out waiting for ${url}`);
}

async function stopChildren() {
  await Promise.all(children.map((child) => new Promise((resolve) => {
    if (child.exitCode !== null || child.killed) return resolve();
    child.once("exit", resolve);
    if (process.platform === "win32") {
      // BrowserSync can outlive the gulp CLI on Windows. The PID originates
      // from this runner, so killing its tree cannot affect an operator server.
      spawnSync("taskkill", ["/PID", String(child.pid), "/T", "/F"], { stdio: "ignore" });
    } else {
      child.kill();
    }
    setTimeout(resolve, 1000).unref();
  })));
}

try {
  await run(process.execPath, [gulpExecutable, "build"], { cwd: frontendRoot, env: frontendEnv });
  start(process.execPath, [staticServer], { cwd: frontendRoot, env: frontendEnv });
  start(pythonExecutable, ["-m", "uvicorn", "scripts.e2e_app:app", "--host", "127.0.0.1", "--port", "8010"], { cwd: projectRoot, env: apiEnv });
  await Promise.all([
    waitFor("http://127.0.0.1:8010/"),
    waitFor("http://127.0.0.1:3211/"),
  ]);
  const playwright = start(process.execPath, [playwrightExecutable, "test", "-c", "playwright.real.config.mjs"], {
    cwd: frontendRoot, env: { ...process.env, E2E_REAL_BASE_URL: "http://127.0.0.1:3211" },
  });
  process.exitCode = await new Promise((resolve) => playwright.once("exit", (code) => resolve(code ?? 1)));
} finally {
  await stopChildren();
}
