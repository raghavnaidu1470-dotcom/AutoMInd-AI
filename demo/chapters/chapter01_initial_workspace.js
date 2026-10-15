/**
 * Chapter 1: Initial Workspace & Default Example
 * ===============================================
 * Demonstrates:
 * - Clean application load without errors
 * - Live FastAPI backend connection readout (Engine: connected)
 * - Default regular expression `(a|b)*abb` and candidate string `ababb`
 * - Layout structure: Command Bar, Learning Flow Rail, Drawing Canvas, Pinned Tape, Margin Column
 */

import path from 'path';

export async function runChapter01(runner) {
  const { page, overlay, report, options } = runner;
  const chapterName = 'CHAPTER 1 · INITIAL WORKSPACE';

  // 1.1 Page Title & Basic Shell
  await overlay.setCaption({
    chapter: chapterName,
    step: '1.1',
    title: 'Workspace Load & Page Title',
    action: 'Navigating to local frontend URL and checking document structure',
    expected: "Page title is 'AutoMind AI' and main dashboard elements are present",
  });

  const title = await page.title();
  if (title !== 'AutoMind AI') {
    throw new Error(`Expected title 'AutoMind AI', got '${title}'`);
  }
  await page.waitForSelector('#app-header');
  await page.waitForSelector('#command-bar');
  await page.waitForSelector('#stage-rail');
  await page.waitForSelector('#drawing-area');
  await page.waitForSelector('#tape-transport-bar');

  await overlay.markPass();
  await overlay.pauseForPresentation(1200);

  report.recordCheck({
    chapter: chapterName,
    step: '1.1',
    title: 'Page Title & UI Shell',
    action: 'Navigate to http://127.0.0.1:5173 and inspect core chrome',
    expected: "Title is 'AutoMind AI', top command bar, stage rail, canvas, and tape are mounted",
    observed: `Title: '${title}', all 5 primary regions detected`,
    status: 'PASS',
  });

  // 1.2 Backend Health Status Readout
  await overlay.setCaption({
    chapter: chapterName,
    step: '1.2',
    title: 'Backend Health Verification',
    action: 'Verifying live health polling connection with FastAPI backend',
    expected: "Engine status indicator displays 'Engine: connected' with green online dot",
  });

  await page.waitForSelector('#engine-status-text');
  const statusText = await page.locator('#engine-status-text').innerText();
  if (!statusText.includes('Engine: connected')) {
    throw new Error(`Expected 'Engine: connected', got '${statusText}'`);
  }
  const isOnlineDot = await page.locator('.status-dot.online').isVisible();
  if (!isOnlineDot) {
    throw new Error('Expected green .status-dot.online to be visible');
  }

  await overlay.markPass();
  await overlay.pauseForPresentation(1200);

  report.recordCheck({
    chapter: chapterName,
    step: '1.2',
    title: 'Backend Health Connection',
    action: 'Inspect status dot and engine health badge in app header',
    expected: "Engine status displays 'Engine: connected' with live status indicator",
    observed: `Engine status: '${statusText}', green online dot active`,
    status: 'PASS',
  });

  // 1.3 Default Pattern & Automata Model
  await overlay.setCaption({
    chapter: chapterName,
    step: '1.3',
    title: 'Default Language & Preloaded Automaton',
    action: "Inspecting pre-populated regex '(a|b)*abb' and candidate string 'ababb'",
    expected: 'Default regex is loaded, simulated on tape, and 4 states rendered on canvas',
  });

  const regexValue = await page.locator('#command-regex-input').inputValue();
  const stringValue = await page.locator('#command-string-input').inputValue();

  if (regexValue !== '(a|b)*abb') {
    throw new Error(`Expected default regex '(a|b)*abb', got '${regexValue}'`);
  }
  if (stringValue !== 'ababb') {
    throw new Error(`Expected default candidate string 'ababb', got '${stringValue}'`);
  }

  // Verify canvas contains states
  await page.waitForSelector('.svg-state-group');
  const stateCount = await page.locator('.svg-state-group').count();
  if (stateCount < 4) {
    throw new Error(`Expected at least 4 state nodes in minimized DFA, got ${stateCount}`);
  }

  // Capture Milestone Screenshot
  const screenshotPath = path.join(runner.artifactsDir, '01_initial_workspace.png');
  await page.screenshot({ path: screenshotPath });

  await overlay.markPass();
  await overlay.pauseForPresentation(1500);

  report.recordCheck({
    chapter: chapterName,
    step: '1.3',
    title: 'Default Example & Automaton State Count',
    action: "Verify regex input is '(a|b)*abb', candidate is 'ababb', and canvas has >= 4 states",
    expected: 'Default pattern loaded without user input, rendering minimal 4-state canonical DFA',
    observed: `Regex: '${regexValue}', String: '${stringValue}', Rendered states: ${stateCount}`,
    status: 'PASS',
    screenshot: screenshotPath,
  });
}
