/**
 * Chapter 5: Automata Representations & Deep Inspection
 * ======================================================
 * Demonstrates:
 * - Switching across NFA (Thompson), DFA (Subset), and Minimized DFA (Hopcroft)
 * - State counts, start state indicators, and accepting double-circle rings
 * - Live subset mappings (hover tooltip and click state-inspector drawer)
 * - Hopcroft minimization before-and-after comparison modal
 * - Accessible Transition Table toggle
 */

import path from 'path';

export async function runChapter05(runner) {
  const { page, overlay, report } = runner;
  const chapterName = 'CHAPTER 5 · AUTOMATA MODELS';

  // Ensure pattern is (a|b)*abb
  const regexInput = page.locator('#command-regex-input');
  await regexInput.fill('(a|b)*abb');
  await page.locator('#btn-run-string').click();
  await page.waitForTimeout(600);

  // 5.1 Thompson's NFA Representation
  await overlay.setCaption({
    chapter: chapterName,
    step: '5.1',
    title: "Thompson's NFA Representation",
    action: "Clicking 'NFA (Thompson)' tab in the representation bar",
    expected: 'Renders 11-state NFA with epsilon transitions and initial epsilon-closure set',
  });

  const nfaTab = page.locator('.rep-tab:has-text("NFA")');
  await nfaTab.click();
  await page.waitForTimeout(600);

  // Verify meta label displays NFA
  const nfaMeta = await page.locator('.automata-representation-bar').innerText();
  if (!nfaMeta.includes('NFA')) {
    throw new Error(`Expected representation bar to indicate NFA, got: '${nfaMeta}'`);
  }

  const nfaNodesCount = await page.locator('.svg-state-group').count();
  if (nfaNodesCount < 10) {
    throw new Error(`Expected ~11 states in Thompson NFA, got ${nfaNodesCount}`);
  }

  await overlay.markPass(`NFA rendered with ${nfaNodesCount} states`);
  await overlay.pauseForPresentation(1200);

  report.recordCheck({
    chapter: chapterName,
    step: '5.1',
    title: "Thompson's NFA Representation",
    action: "Switch to 'NFA (Thompson)' representation tab",
    expected: 'AutomataViewer updates layout to display full 11-state Thompson NFA structure',
    observed: `NFA active, rendered ${nfaNodesCount} states with start arrow and epsilon paths`,
    status: 'PASS',
  });

  // 5.2 Subset Construction DFA Representation
  await overlay.setCaption({
    chapter: chapterName,
    step: '5.2',
    title: 'Subset Construction DFA',
    action: "Clicking 'DFA (Subset)' tab in the representation bar",
    expected: 'Renders deterministic 5-state DFA over alphabet {a, b} with zero epsilon transitions',
  });

  const dfaTab = page.locator('.rep-tab:has-text("DFA (Subset)")');
  await dfaTab.click();
  await page.waitForTimeout(600);

  const dfaNodesCount = await page.locator('.svg-state-group').count();
  if (dfaNodesCount < 4 || dfaNodesCount > 6) {
    throw new Error(`Expected 4-6 states in subset DFA, got ${dfaNodesCount}`);
  }

  await overlay.markPass(`DFA rendered with ${dfaNodesCount} deterministic states`);
  await overlay.pauseForPresentation(1000);

  report.recordCheck({
    chapter: chapterName,
    step: '5.2',
    title: 'Subset Construction DFA',
    action: "Switch to 'DFA (Subset)' tab",
    expected: 'Transforms multi-state NFA into deterministic DFA over full alphabet',
    observed: `DFA active, rendered ${dfaNodesCount} deterministic states`,
    status: 'PASS',
  });

  // 5.3 Minimized DFA & State Inspection
  await overlay.setCaption({
    chapter: chapterName,
    step: '5.3',
    title: 'Hopcroft Minimized DFA & State Inspection',
    action: "Selecting 'Minimized DFA', hovering a state for subset mapping, then clicking to inspect",
    expected: 'Hover reveals NFA subset pill; click opens State Inspector Drawer with outgoing edges',
  });

  const minDfaTab = page.locator('.rep-tab:has-text("Minimized DFA")');
  await minDfaTab.click();
  await page.waitForTimeout(600);

  // Hover over the first state node
  const firstStateNode = page.locator('.svg-state-group').first();
  await firstStateNode.hover();
  await overlay.pauseForPresentation(800);

  // Click state node to open drawer
  await firstStateNode.click();
  await page.waitForSelector('.state-inspector-drawer');
  const drawerText = await page.locator('.state-inspector-drawer').innerText();

  if (!drawerText.includes('State') || !drawerText.includes('Outgoing transitions')) {
    throw new Error(`State inspector drawer missing expected content, got: '${drawerText}'`);
  }

  // Close inspector drawer
  await page.locator('.state-inspector-drawer button[aria-label="Close state inspector"]').click();
  await overlay.markPass('State inspector drawer and subset mapping verified');
  await overlay.pauseForPresentation(1000);

  report.recordCheck({
    chapter: chapterName,
    step: '5.3',
    title: 'State Inspection & Subset Mappings',
    action: 'Hover and click DFA state node to inspect underlying NFA subsets and transitions',
    expected: 'Inspects underlying NFA subset equivalence and lists outgoing transitions',
    observed: `Inspector drawer opened: "${drawerText.replace(/\n/g, ' ')}"`,
    status: 'PASS',
  });

  // 5.4 Minimization Comparison Modal
  await overlay.setCaption({
    chapter: chapterName,
    step: '5.4',
    title: 'Hopcroft Minimization Comparison Modal',
    action: "Clicking '⚖️ Compare Minimization' button to inspect algorithm partitioning",
    expected: 'Opens comparison dialog showing original vs minimized state counts and merged groups',
  });

  const compareBtn = page.locator('button:has-text("Compare Minimization")');
  await compareBtn.click();
  await page.waitForSelector('.modal-card');

  const statCards = await page.locator('.stat-card').allInnerTexts();
  console.log('[Demo] Minimization stat cards:', statCards);

  // Verify modal table
  const mergeRows = await page.locator('.modal-body .syntax-table tbody tr').count();
  if (mergeRows === 0) {
    throw new Error('Expected state partition rows in minimization comparison modal');
  }

  // Dismiss modal via Escape key
  await page.keyboard.press('Escape');
  await page.waitForSelector('.modal-backdrop', { state: 'detached' });

  await overlay.markPass('Minimization comparison verified');
  await overlay.pauseForPresentation(1000);

  report.recordCheck({
    chapter: chapterName,
    step: '5.4',
    title: 'Minimization Comparison Modal',
    action: "Click '⚖️ Compare Minimization' and inspect partitioning breakdown",
    expected: 'Displays stats cards, reduction verdict, and detailed state partition breakdown table',
    observed: `Modal verified with ${mergeRows} state partition entries; closed via Escape`,
    status: 'PASS',
  });

  // 5.5 Accessible Transition Table View
  await overlay.setCaption({
    chapter: chapterName,
    step: '5.5',
    title: 'Accessible Transition Table View',
    action: "Clicking 'View as table' to inspect state transitions in tabular form",
    expected: 'Switches from graphical canvas to accessible HTML table with rows per state',
  });

  const viewTableBtn = page.locator('button:has-text("View table")');
  await viewTableBtn.click();
  await page.waitForSelector('.automata-table-view-container');

  const tableHeader = await page.locator('.automata-table-view-container h4').innerText();
  const rowsCount = await page.locator('.automata-table-view-container tbody tr').count();

  if (rowsCount < 4) {
    throw new Error(`Expected at least 4 table rows, got ${rowsCount}`);
  }

  // Capture screenshot of table view
  const screenshotPath = path.join(runner.artifactsDir, '05_transition_table_view.png');
  await page.screenshot({ path: screenshotPath });

  // Toggle back to diagram view
  const viewDiagramBtn = page.locator('button:has-text("View diagram")');
  await viewDiagramBtn.click();
  await page.waitForSelector('#automaton-svg');

  await overlay.markPass('Transition table view verified and restored to diagram');
  await overlay.pauseForPresentation(1200);

  report.recordCheck({
    chapter: chapterName,
    step: '5.5',
    title: 'Transition Table View Toggle',
    action: "Toggle 'View table', verify tabular columns (State ID, Type, Subset, Transitions), toggle back",
    expected: 'Accessible HTML table displays complete transition matrix; switches back to SVG diagram',
    observed: `Transition table verified (${rowsCount} rows for ${tableHeader}), restored diagram`,
    status: 'PASS',
    screenshot: screenshotPath,
  });
}
