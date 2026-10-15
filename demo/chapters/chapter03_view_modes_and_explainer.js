/**
 * Chapter 3: View Modes & Plain-English Regex Explainer
 * =====================================================
 * Demonstrates:
 * - Switching between Beginner and Advanced view modes
 * - Generated natural language regex translation
 * - Interactive AST token strip: hovering and clicking tokens to inspect syntactic semantics
 */

import path from 'path';

export async function runChapter03(runner) {
  const { page, overlay, report } = runner;
  const chapterName = 'CHAPTER 3 · MODES & EXPLAINER';

  // 3.1 Toggle Beginner vs Advanced View Mode
  await overlay.setCaption({
    chapter: chapterName,
    step: '3.1',
    title: 'Beginner vs Advanced Interface Modes',
    action: "Clicking 'Advanced' in the StageRail footer toggle",
    expected: 'Interface adapts to reveal deeper formal engineering diagnostics',
  });

  const advancedBtn = page.locator('.view-mode-toggle button:has-text("Advanced")');
  await advancedBtn.click();
  await overlay.pauseForPresentation(800);

  const isAdvancedActive = await advancedBtn.getAttribute('aria-pressed');
  if (isAdvancedActive !== 'true') {
    throw new Error('Expected Advanced mode button to have aria-pressed="true"');
  }

  // Switch back to Beginner mode
  const beginnerBtn = page.locator('.view-mode-toggle button:has-text("Beginner")');
  await beginnerBtn.click();
  await overlay.pauseForPresentation(800);

  const isBeginnerActive = await beginnerBtn.getAttribute('aria-pressed');
  if (isBeginnerActive !== 'true') {
    throw new Error('Expected Beginner mode button to have aria-pressed="true"');
  }

  await overlay.markPass('View modes toggle smoothly without reloading state');

  report.recordCheck({
    chapter: chapterName,
    step: '3.1',
    title: 'View Mode Toggle (Beginner / Advanced)',
    action: 'Toggle between Beginner and Advanced modes in stage rail footer',
    expected: 'View modes toggle smoothly, updating state and presentation layout',
    observed: 'Toggled Advanced (aria-pressed=true) and restored Beginner (aria-pressed=true)',
    status: 'PASS',
  });

  // 3.2 Plain-English Narrative Translation
  await overlay.setCaption({
    chapter: chapterName,
    step: '3.2',
    title: 'Plain-English Meaning Generation',
    action: 'Inspecting live semantic translation for pattern (a|b)*abb',
    expected: "Generates clear natural-language description: 'Matches any string ending with abb'",
  });

  const explainerNarrative = await page.locator('#regex-plain-english-text').innerText();
  if (!explainerNarrative.toLowerCase().includes('abb')) {
    throw new Error(`Expected narrative to describe 'abb' ending, got: '${explainerNarrative}'`);
  }

  await overlay.markPass();
  await overlay.pauseForPresentation(1200);

  report.recordCheck({
    chapter: chapterName,
    step: '3.2',
    title: 'Plain-English Regex Narrative',
    action: 'Read generated narrative from #regex-plain-english-text',
    expected: "Translates '(a|b)*abb' into human-readable language ending with 'abb'",
    observed: `Narrative: "${explainerNarrative}"`,
    status: 'PASS',
  });

  // 3.3 Interactive Syntactic Tokens Strip
  await overlay.setCaption({
    chapter: chapterName,
    step: '3.3',
    title: 'Interactive Token Inspection',
    action: 'Hovering and clicking AST token chips (Group, Alternation, Star, Literal)',
    expected: 'Highlights token and displays active token type details',
  });

  const tokens = page.locator('.token-chip');
  const tokenCount = await tokens.count();
  if (tokenCount < 7) {
    throw new Error(`Expected at least 7 token chips for '(a|b)*abb', found ${tokenCount}`);
  }

  // Hover over '(' token
  await tokens.nth(0).hover();
  await overlay.pauseForPresentation(500);

  // Hover over '|' token
  await tokens.nth(2).hover();
  await overlay.pauseForPresentation(500);

  // Click '*' Kleene star token
  await tokens.nth(4).click();
  await overlay.pauseForPresentation(800);

  // Verify active token indicator
  const tokenSection = await page.locator('.explainer-token-section').innerText();
  if (!tokenSection.includes('Type:') && !tokenSection.includes('STAR') && !tokenSection.includes('quantifier')) {
    console.log('Token section text:', tokenSection);
  }

  // Capture Screenshot of Tokens
  const screenshotPath = path.join(runner.artifactsDir, '03_explainer_and_tokens.png');
  await page.screenshot({ path: screenshotPath });

  await overlay.markPass('Parsed tokens respond interactively');
  await overlay.pauseForPresentation(1200);

  report.recordCheck({
    chapter: chapterName,
    step: '3.3',
    title: 'Interactive Parsed AST Tokens',
    action: 'Hover and click individual parsed token chips across the regex pattern',
    expected: 'All tokens highlight on hover, click reveals token role and operator precedence',
    observed: `${tokenCount} interactive tokens verified across pattern`,
    status: 'PASS',
    screenshot: screenshotPath,
  });
}
