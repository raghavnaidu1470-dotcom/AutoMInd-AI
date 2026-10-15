#!/usr/bin/env node

/**
 * AutoMind AI - Automated Live Demonstration Launcher
 * ====================================================
 * Usage:
 *   node demo/run_live_demo.js                    # Full visible live demo in headed Chrome
 *   node demo/run_live_demo.js --fast             # Fast headless assertion verification
 *   node demo/run_live_demo.js --chapter 5        # Run single chapter (1 to 11)
 *   node demo/run_live_demo.js --record           # Record session video to disk
 *   node demo/run_live_demo.js --speed 2          # 2x faster visible demonstration pace
 */

import path from 'path';
import { fileURLToPath } from 'url';
import { ServerManager } from './lib/server_manager.js';
import { DemoRunner, CHAPTER_MAP } from './lib/demo_runner.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO_ROOT = path.resolve(__dirname, '..');

function parseArgs() {
  const args = process.argv.slice(2);
  const options = {
    headed: true,
    fast: false,
    speed: 1.0,
    chapter: 'all',
    record: false,
    autoStartServers: true,
    outDir: path.join(REPO_ROOT, 'demo/artifacts'),
  };

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg === '--headless') options.headed = false;
    else if (arg === '--headed') options.headed = true;
    else if (arg === '--fast') {
      options.fast = true;
      options.speed = 0;
      options.headed = false;
    } else if (arg === '--record') options.record = true;
    else if (arg === '--no-server-start') options.autoStartServers = false;
    else if (arg === '--speed' && i + 1 < args.length) {
      options.speed = parseFloat(args[++i]);
    } else if (arg === '--chapter' && i + 1 < args.length) {
      options.chapter = args[++i];
    } else if (arg === '--out-dir' && i + 1 < args.length) {
      options.outDir = path.resolve(process.cwd(), args[++i]);
    } else if (arg === '--help' || arg === '-h') {
      printHelp();
      process.exit(0);
    }
  }

  return options;
}

function printHelp() {
  console.log(`
AutoMind AI - Automated Live Demonstration CLI
==============================================
Commands:
  node demo/run_live_demo.js [options]
  npm run demo                  # Runs full headed live demo
  npm run demo:fast             # Fast assertion verification (headless)
  npm run demo:record           # Headed demo with WebM session video recording
  npm run demo:chapter -- 5     # Run specific chapter (1-11)

Options:
  --headed              Run visible browser (default: true)
  --headless            Run without browser window
  --fast                Fastest verification mode (headless, no presentation pauses)
  --speed <num>         Playback speed multiplier (e.g. 0.5, 1.0, 2.0; default: 1.0)
  --chapter <name|num>  Run specific chapter (1-11, or name like 'workspace', 'redos')
  --record              Record entire browser session to WebM video in artifacts/
  --out-dir <path>      Output directory for screenshots, reports, and downloads
  --no-server-start     Do not start backend or frontend (assumes already running)
  --help, -h            Show this help message

Available Chapters:
${Object.entries(CHAPTER_MAP)
  .map(([num, ch]) => `  ${num.padEnd(3)} : ${ch.name} (${ch.id})`)
  .join('\n')}
`);
}

async function main() {
  const options = parseArgs();

  console.log(`
========================================================================
  AutoMind AI — Theory of Computation Live Browser Demonstration
========================================================================
  Headed Mode:     ${options.headed ? 'VISIBLE (Google Chrome window)' : 'HEADLESS'}
  Playback Speed:  ${options.fast ? 'FAST (Verification mode)' : `${options.speed}x (Beginner pace)`}
  Target Chapter:  ${options.chapter}
  Record Session:  ${options.record ? 'YES (WebM video)' : 'NO'}
  Artifacts Dir:   ${options.outDir}
========================================================================
`);

  const serverManager = new ServerManager();
  let demoRunner = null;

  // Cleanup handler on exit or interrupt
  let cleaningUp = false;
  const handleExit = async (signal) => {
    if (cleaningUp) return;
    cleaningUp = true;
    console.log(`\n[Main] Received ${signal || 'exit'}, shutting down gracefully...`);
    try {
      if (demoRunner) await demoRunner.close();
    } catch {}
    serverManager.cleanup();
    process.exit(0);
  };

  process.on('SIGINT', () => handleExit('SIGINT'));
  process.on('SIGTERM', () => handleExit('SIGTERM'));

  try {
    if (options.autoStartServers) {
      console.log('[Main] Ensuring backend and frontend services are ready...');
      await serverManager.ensureReady();
    }

    demoRunner = new DemoRunner({
      headed: options.headed,
      speed: options.speed,
      fast: options.fast,
      chapter: options.chapter,
      record: options.record,
      artifactsDir: options.outDir,
    });

    const report = await demoRunner.run();

    console.log(`
========================================================================
  DEMONSTRATION & VERIFICATION COMPLETED SUCCESSFULLY!
========================================================================
  Total Checks:    ${report.summary.totalChecks}
  Passed Checks:   ${report.summary.passed} (${report.summary.passRate})
  Failed Checks:   ${report.summary.failed}
  Skipped Checks:  ${report.summary.skipped}
  Duration:        ${report.summary.totalDurationSec}s
  Markdown Report: ${report.mdPath}
  JSON Summary:    ${report.jsonPath}
========================================================================
`);

    await demoRunner.close();
    demoRunner = null;
    serverManager.cleanup();
    process.exit(0);
  } catch (err) {
    console.error(`\n[Main] Demonstration execution failed:`, err);
    if (demoRunner) await demoRunner.close();
    serverManager.cleanup();
    process.exit(1);
  }
}

main();
