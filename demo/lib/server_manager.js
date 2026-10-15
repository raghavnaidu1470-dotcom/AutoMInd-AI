import { spawn } from 'child_process';
import http from 'http';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO_ROOT = path.resolve(__dirname, '../..');

export class ServerManager {
  constructor(options = {}) {
    this.backendPort = options.backendPort || 8000;
    this.frontendPort = options.frontendPort || 5173;
    this.backendUrl = `http://127.0.0.1:${this.backendPort}`;
    this.frontendUrl = `http://127.0.0.1:${this.frontendPort}`;
    this.spawnedProcesses = [];
    this.reusedBackend = false;
    this.reusedFrontend = false;
  }

  async checkUrl(url, timeoutMs = 1500) {
    return new Promise((resolve) => {
      try {
        const u = new URL(url);
        const req = http.get(
          {
            hostname: u.hostname,
            port: u.port,
            path: u.pathname + (u.search || ''),
            timeout: timeoutMs,
          },
          (res) => {
            resolve(res.statusCode >= 200 && res.statusCode < 400);
          }
        );
        req.on('error', () => resolve(false));
        req.on('timeout', () => {
          req.destroy();
          resolve(false);
        });
      } catch {
        resolve(false);
      }
    });
  }

  async waitForUrl(url, maxWaitMs = 25000, intervalMs = 400) {
    const start = Date.now();
    while (Date.now() - start < maxWaitMs) {
      const ok = await this.checkUrl(url);
      if (ok) return true;
      await new Promise((r) => setTimeout(r, intervalMs));
    }
    return false;
  }

  async startBackend() {
    const isHealthy = await this.checkUrl(`${this.backendUrl}/api/health`);
    if (isHealthy) {
      console.log(`[ServerManager] Existing Backend active at ${this.backendUrl} (reusing).`);
      this.reusedBackend = true;
      return;
    }

    console.log(`[ServerManager] Starting Backend via uvicorn on port ${this.backendPort}...`);
    const pythonBin = path.join(REPO_ROOT, 'backend/venv/bin/python');
    const child = spawn(
      pythonBin,
      ['-m', 'uvicorn', 'backend.api.main:app', '--port', String(this.backendPort)],
      {
        cwd: REPO_ROOT,
        stdio: ['ignore', 'pipe', 'pipe'],
      }
    );

    child.stdout.on('data', (d) => {
      const line = d.toString();
      if (process.env.DEBUG_SERVERS) console.log(`[backend stdout] ${line.trim()}`);
    });
    child.stderr.on('data', (d) => {
      const line = d.toString();
      if (process.env.DEBUG_SERVERS) console.error(`[backend stderr] ${line.trim()}`);
    });

    this.spawnedProcesses.push({ name: 'Backend', process: child });

    const ok = await this.waitForUrl(`${this.backendUrl}/api/health`, 20000);
    if (!ok) {
      throw new Error(`Backend failed to respond at ${this.backendUrl}/api/health within 20s`);
    }
    console.log(`[ServerManager] Backend ready at ${this.backendUrl}`);
  }

  async startFrontend() {
    const isHealthy = await this.checkUrl(this.frontendUrl);
    if (isHealthy) {
      console.log(`[ServerManager] Existing Frontend active at ${this.frontendUrl} (reusing).`);
      this.reusedFrontend = true;
      return;
    }

    console.log(`[ServerManager] Starting Frontend via Vite on port ${this.frontendPort}...`);
    const child = spawn(
      'npm',
      ['run', 'dev', '--', '--port', String(this.frontendPort)],
      {
        cwd: path.join(REPO_ROOT, 'frontend'),
        stdio: ['ignore', 'pipe', 'pipe'],
      }
    );

    child.stdout.on('data', (d) => {
      const line = d.toString();
      if (process.env.DEBUG_SERVERS) console.log(`[frontend stdout] ${line.trim()}`);
    });
    child.stderr.on('data', (d) => {
      const line = d.toString();
      if (process.env.DEBUG_SERVERS) console.error(`[frontend stderr] ${line.trim()}`);
    });

    this.spawnedProcesses.push({ name: 'Frontend', process: child });

    const ok = await this.waitForUrl(this.frontendUrl, 20000);
    if (!ok) {
      throw new Error(`Frontend failed to respond at ${this.frontendUrl} within 20s`);
    }
    console.log(`[ServerManager] Frontend ready at ${this.frontendUrl}`);
  }

  async ensureReady() {
    await this.startBackend();
    await this.startFrontend();
  }

  cleanup() {
    if (this.spawnedProcesses.length === 0) {
      return;
    }
    console.log(`[ServerManager] Cleaning up ${this.spawnedProcesses.length} spawned process(es)...`);
    for (const { name, process: proc } of this.spawnedProcesses) {
      try {
        console.log(`[ServerManager] Terminating ${name} (PID ${proc.pid})...`);
        proc.kill('SIGTERM');
      } catch (err) {
        console.warn(`[ServerManager] Error killing ${name}:`, err.message);
      }
    }
    this.spawnedProcesses = [];
  }
}
