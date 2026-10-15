/**
 * Chapter 2: Beginner Walkthrough & Formal Syntax Guide
 * ======================================================
 * Demonstrates:
 * - Opening interactive beginner tutorial via "Walk me through this"
 * - Stepping through all 6 pedagogical automata theory concepts
 * - Focus trapping and Escape key dismissal
 * - Opening and inspecting the Formal Syntax Guide modal
 * - Reviewing supported operators and documented regular language limitations
 */

import path from 'path';

export async function runChapter02(runner) {
  const { page, overlay, report } = runner;
  const chapterName = 'CHAPTER 2 · WALKTHROUGH & SYNTAX';

  // 2.1 Launch Beginner Walkthrough Modal
  await overlay.setCaption({
    chapter: chapterName,
    step: '2.1',
    title: 'Interactive Beginner Walkthrough',
    action: "Clicking 'Walk me through this' button in the navigation rail",
    expected: 'Walkthrough dialog opens with Step 1: Formal Language Specification',
  });

  const walkthroughBtn = page.locator('#btn-walk-me-through');
  await walkthroughBtn.waitFor({ state: 'visible' });
  await walkthroughBtn.click();

  await page.waitForSelector('.modal-backdrop');
  await page.waitForSelector('.modal-card');
  const modalTitle = await page.locator('.modal-header h3').innerText();

  if (!modalTitle.includes('Regular Expression')) {
    throw new Error(`Expected modal title with 'Regular Expression', got '${modalTitle}'`);
  }

  await overlay.markPass();
  await overlay.pauseForPresentation(1200);

  report.recordCheck({
    chapter: chapterName,
    step: '2.1',
    title: 'Beginner Walkthrough Modal Launch',
    action: "Click #btn-walk-me-through in sidebar",
    expected: "Modal dialog opens, focus transfers to modal, step 1 rendered",
    observed: `Modal opened with header: '${modalTitle}'`,
    status: 'PASS',
  });

  // 2.2 Step Through Educational Concepts (Steps 1 through 6)
  await overlay.setCaption({
    chapter: chapterName,
    step: '2.2',
    title: 'Navigating Core Automata Concepts',
    action: 'Stepping through Thompson NFA, Subset DFA, Hopcroft Minimization, and ReDoS immunity',
    expected: 'Step indicators increment smoothly and explain theoretical milestones',
  });

  // Step 2: NFA
  const nextBtn = page.locator('.modal-footer button:has-text("Next")');
  await nextBtn.click();
  await page.waitForSelector('text=Thompson');
  await overlay.pauseForPresentation(800);

  // Step 3: DFA
  await nextBtn.click();
  await page.waitForSelector('text=Subset');
  await overlay.pauseForPresentation(800);

  // Step 4: Minimization
  await nextBtn.click();
  await page.waitForSelector('text=Hopcroft');
  await overlay.pauseForPresentation(800);

  // Step 5: Tape Simulator
  await nextBtn.click();
  await page.waitForSelector('text=Tape Transport');
  await overlay.pauseForPresentation(800);

  // Step 6: ReDoS Immunity Guarantee
  await nextBtn.click();
  await page.waitForSelector('text=Automata Immunity Guarantee');
  await overlay.pauseForPresentation(1200);

  // Capture screenshot of educational modal
  const screenshotPath = path.join(runner.artifactsDir, '02_walkthrough_modal.png');
  await page.screenshot({ path: screenshotPath });

  // Close modal via Escape key (testing keyboard a11y)
  await page.keyboard.press('Escape');
  await page.waitForSelector('.modal-backdrop', { state: 'detached' });

  await overlay.markPass('Walkthrough completed and dismissed via Escape');
  await overlay.pauseForPresentation(1000);

  report.recordCheck({
    chapter: chapterName,
    step: '2.2',
    title: 'Pedagogical Concepts & Escape Dismissal',
    action: 'Traverse 6 walkthrough steps and dismiss via keyboard Escape',
    expected: 'All 6 theoretical steps render correct educational cards; Escape closes modal cleanly',
    observed: 'Steps 1-6 verified (NFA, DFA, Minimization, Tape, ReDoS), modal closed with Escape',
    status: 'PASS',
    screenshot: screenshotPath,
  });

  // 2.3 Formal Syntax Guide Inspection
  await overlay.setCaption({
    chapter: chapterName,
    step: '2.3',
    title: 'Formal Syntax Reference Guide',
    action: "Opening 'Formal Syntax Guide' modal from plain-English explainer header",
    expected: 'Displays supported syntax table and documented regular language limits',
  });

  const syntaxBtn = page.locator('button:has-text("Formal Syntax Guide")');
  await syntaxBtn.waitFor({ state: 'visible' });
  await syntaxBtn.click();

  await page.waitForSelector('.syntax-table');
  const tableRowsCount = await page.locator('.syntax-table tbody tr').count();
  if (tableRowsCount < 8) {
    throw new Error(`Expected at least 8 syntax reference rows, got ${tableRowsCount}`);
  }

  // Verify documented unsupported constructs notice
  const unsupportedNotice = await page.locator('.modal-body').innerText();
  if (!unsupportedNotice.includes('Backreferences') || !unsupportedNotice.includes('Lookaround')) {
    throw new Error('Expected syntax guide to explicitly document non-regular constructs (Backreferences, Lookaround)');
  }

  // Close via close button
  const closeSyntaxBtn = page.locator('.modal-header button[aria-label="Close syntax guide"]');
  await closeSyntaxBtn.click();
  await page.waitForSelector('.modal-backdrop', { state: 'detached' });

  await overlay.markPass('Syntax guide inspected and closed');
  await overlay.pauseForPresentation(1200);

  report.recordCheck({
    chapter: chapterName,
    step: '2.3',
    title: 'Formal Syntax Guide & Unsupported Features',
    action: "Open 'Formal Syntax Guide' modal, verify operator rows and unsupported feature warnings",
    expected: 'Supported table lists concatenation, alternation, star/plus/opt, classes, escapes; notes backreference limits',
    observed: `${tableRowsCount} syntax rules documented, non-regular construct limits confirmed, modal closed`,
    status: 'PASS',
  });
}
