import { chromium } from 'playwright-core';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';
import { CaptionOverlay } from './caption_overlay.js';
import { ReportGenerator } from './report_generator.js';

import { runChapter01 } from '../chapters/chapter01_initial_workspace.js';
import { runChapter02 } from '../chapters/chapter02_walkthrough_and_syntax.js';
import { runChapter03 } from '../chapters/chapter03_view_modes_and_explainer.js';
import { runChapter04 } from '../chapters/chapter04_candidates_presets_history.js';
import { runChapter05 } from '../chapters/chapter05_automata_representations.js';
import { runChapter06 } from '../chapters/chapter06_graph_canvas_interactions.js';
import { runChapter07 } from '../chapters/chapter07_tape_playback_and_trace.js';
import { runChapter08 } from '../chapters/chapter08_redos_studio_and_presets.js';
import { runChapter09 } from '../chapters/chapter09_sidebars_modals_keyboard_mobile.js';
import { runChapter10 } from '../chapters/chapter10_file_exports_verification.js';
import { runChapter11 } from '../chapters/chapter11_robustness_and_edge_cases.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO_ROOT = path.resolve(__dirname, '../..');

export const CHAPTER_MAP = {
  1: { id: 'workspace', name: 'Initial Workspace & Health', fn: runChapter01 },
  2: { id: 'walkthrough', name: 'Walkthrough & Syntax Guide', fn: runChapter02 },
  3: { id: 'explainer', name: 'View Modes & Explainer', fn: runChapter03 },
  4: { id: 'candidates', name: 'Candidates, Presets & History', fn: runChapter04 },
  5: { id: 'automata', name: 'Automata Representations & Minimization', fn: runChapter05 },
  6: { id: 'canvas', name: 'Canvas Zoom & Pan Interactions', fn: runChapter06 },
  7: { id: 'tape', name: 'Tape Transport & Execution Trace', fn: runChapter07 },
  8: { id: 'redos', name: 'ReDoS Studio & Presets', fn: runChapter08 },
  9: { id: 'sidebars', name: 'Sidebars, Keyboard & Mobile', fn: runChapter09 },
  10: { id: 'exports', name: 'File Exports (SVG, PNG, JSON)', fn: runChapter10 },
  11: { id: 'robustness', name: 'Test Matrix & Robustness', fn: runChapter11 },
};

export class DemoRunner {
  constructor(options = {}) {
    this.options = {
      headed: options.headed !== false, // default true (visible browser)
      speed: options.speed !== undefined ? options.speed : 1, // default 1 (beginner presentation speed)
      fast: Boolean(options.fast),
      chapter: options.chapter || 'all',
      record: Boolean(options.record),
      frontendUrl: options.frontendUrl || 'http://127.0.0.1:5173',
      artifactsDir: options.artifactsDir || path.join(REPO_ROOT, 'demo/artifacts'),
      chromePath:
        options.chromePath || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
      ...options,
    };

    if (this.options.fast) {
      this.options.speed = 0;
      this.options.headed = false;
    }

    this.artifactsDir = this.options.artifactsDir;
    this.frontendUrl = this.options.frontendUrl;
    fs.mkdirSync(this.artifactsDir, { recursive: true });

    this.report = new ReportGenerator(this.artifactsDir);
    this.browser = null;
    this.context = null;
    this.page = null;
    this.overlay = null;
  }

  async initBrowser() {
    console.log(`[DemoRunner] Launching Chrome (headed=${this.options.headed}, speed=${this.options.speed}x)...`);

    const launchArgs = [
      '--window-size=1440,960',
      '--no-default-browser-check',
      '--disable-infobars',
    ];

    this.browser = await chromium.launch({
      executablePath: this.options.chromePath,
      headless: !this.options.headed,
      args: launchArgs,
    });

    const contextOptions = {
      viewport: { width: 1440, height: 920 },
      acceptDownloads: true,
    };

    if (this.options.record) {
      contextOptions.recordVideo = {
        dir: path.join(this.artifactsDir, 'recordings'),
        size: { width: 1440, height: 920 },
      };
      console.log(`[DemoRunner] Video recording enabled at: ${contextOptions.recordVideo.dir}`);
    }

    this.context = await this.browser.newContext(contextOptions);
    this.page = await this.context.newPage();

    this.overlay = new CaptionOverlay(this.page, {
      speed: this.options.speed,
    });
  }

  async run() {
    await this.initBrowser();

    console.log(`[DemoRunner] Navigating to ${this.frontendUrl}...`);
    await this.page.goto(this.frontendUrl);
    await this.page.waitForSelector('#command-bar', { timeout: 15000 });

    // Install Caption Overlay
    await this.overlay.install();

    // Determine chapters to run
    const selectedChapter = String(this.options.chapter).toLowerCase();
    const chapterKeys = Object.keys(CHAPTER_MAP).sort((a, b) => Number(a) - Number(b));

    for (const key of chapterKeys) {
      const ch = CHAPTER_MAP[key];
      const shouldRun =
        selectedChapter === 'all' ||
        selectedChapter === String(key) ||
        selectedChapter === ch.id ||
        selectedChapter === `chapter${key}` ||
        selectedChapter === `ch${key}`;

      if (!shouldRun) {
        continue;
      }

      console.log(`\n========================================================================`);
      console.log(`>>> RUNNING CHAPTER ${key}: ${ch.name}`);
      console.log(`========================================================================\n`);

      try {
        await ch.fn(this);
        console.log(`[DemoRunner] Chapter ${key} finished successfully.`);
      } catch (err) {
        console.error(`[DemoRunner] Error in Chapter ${key}:`, err);
        this.report.recordCheck({
          chapter: `CHAPTER ${key}`,
          step: `${key}.X`,
          title: ch.name,
          action: 'Execute chapter automation',
          expected: 'All chapter actions pass without unhandled exception',
          observed: `Exception: ${err.message}`,
          status: 'FAIL',
          error: err.message,
        });
        if (this.overlay) {
          await this.overlay.markFail(err.message);
        }
        throw err;
      }
    }

    // Write final reports
    const reportResult = this.report.writeReports();

    // If recording, close context to finalize video
    if (this.options.record && this.context) {
      await this.context.close();
      this.context = null;
      console.log(`[DemoRunner] Video recording saved.`);
    }

    return reportResult;
  }

  async close() {
    if (this.context) {
      await this.context.close();
      this.context = null;
    }
    if (this.browser) {
      await this.browser.close();
      this.browser = null;
    }
  }
}
