/**
 * Presentation Caption Overlay
 * ============================
 * Injects a small, non-intrusive live presentation overlay in the browser.
 * Shows:
 * - Current Chapter & Step number
 * - Action description (what the automation is doing)
 * - Expected result & formal theory note
 * - Live verification status (RUNNING, PASS, FAIL)
 * - Interactive Pause/Resume and Speed controls directly in the browser
 */

export class CaptionOverlay {
  constructor(page, options = {}) {
    this.page = page;
    this.speedMultiplier = options.speed !== undefined ? options.speed : 1; // 1 = normal beginner pace, 0 = fast/no pauses
  }

  async install() {
    await this.page.evaluate(() => {
      if (document.getElementById('automind-demo-overlay')) return;

      const overlay = document.createElement('div');
      overlay.id = 'automind-demo-overlay';
      overlay.innerHTML = `
        <div id="demo-overlay-header">
          <div id="demo-chapter-badge">LIVE DEMO · STARTING</div>
          <div id="demo-controls-row">
            <button id="demo-btn-pause" title="Pause or Resume presentation">⏸ Pause</button>
            <span id="demo-speed-label">1.0×</span>
          </div>
        </div>
        <div id="demo-step-title">Initializing Automated Demonstration...</div>
        <div id="demo-action-text">Preparing workspace, automata engines, and verification matrix.</div>
        <div id="demo-expected-box">
          <span id="demo-expected-label">Expected Result:</span>
          <span id="demo-expected-text">Application renders all views deterministically with zero mocked data.</span>
        </div>
        <div id="demo-status-bar">
          <span id="demo-status-badge">READY</span>
          <span id="demo-hint-text">Interactive: Click Pause or press 'P' to pause demo</span>
        </div>
      `;

      const style = document.createElement('style');
      style.id = 'automind-demo-overlay-style';
      style.textContent = `
        #automind-demo-overlay {
          position: fixed;
          top: 14px;
          right: 18px;
          width: 380px;
          max-width: calc(100vw - 36px);
          background: #ffffff;
          border: 2px solid #1e293b;
          border-radius: 6px;
          box-shadow: 0 8px 24px rgba(0, 0, 0, 0.16);
          padding: 10px 14px;
          z-index: 2147483647;
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
          font-size: 12px;
          color: #1e293b;
          pointer-events: auto;
          transition: transform 0.2s ease, opacity 0.2s ease;
        }
        #demo-overlay-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 6px;
          border-bottom: 1px solid #e2e8f0;
          padding-bottom: 4px;
        }
        #demo-chapter-badge {
          font-size: 10px;
          font-weight: 800;
          letter-spacing: 0.05em;
          text-transform: uppercase;
          background: #d97706;
          color: #ffffff;
          padding: 2px 6px;
          border-radius: 3px;
        }
        #demo-controls-row {
          display: flex;
          align-items: center;
          gap: 6px;
        }
        #demo-btn-pause {
          background: #f1f5f9;
          border: 1px solid #cbd5e1;
          border-radius: 3px;
          font-size: 11px;
          font-weight: 600;
          color: #1e293b;
          padding: 2px 8px;
          cursor: pointer;
        }
        #demo-btn-pause:hover {
          background: #e2e8f0;
        }
        #demo-speed-label {
          font-size: 11px;
          font-weight: 700;
          color: #475569;
        }
        #demo-step-title {
          font-size: 13px;
          font-weight: 700;
          color: #0f172a;
          margin-bottom: 4px;
        }
        #demo-action-text {
          font-size: 11.5px;
          color: #334155;
          line-height: 1.4;
          margin-bottom: 6px;
        }
        #demo-expected-box {
          background: #f8fafc;
          border: 1px solid #e2e8f0;
          border-radius: 4px;
          padding: 5px 8px;
          font-size: 11px;
          line-height: 1.35;
          margin-bottom: 6px;
        }
        #demo-expected-label {
          font-weight: 700;
          color: #15803d;
          display: block;
          margin-bottom: 2px;
        }
        #demo-expected-text {
          color: #334155;
        }
        #demo-status-bar {
          display: flex;
          justify-content: space-between;
          align-items: center;
          font-size: 10px;
          color: #64748b;
        }
        #demo-status-badge {
          font-weight: 800;
          text-transform: uppercase;
          padding: 1px 5px;
          border-radius: 2px;
          background: #f1f5f9;
          color: #475569;
        }
        #demo-status-badge.running {
          background: #fef3c7;
          color: #b45309;
        }
        #demo-status-badge.pass {
          background: #dcfce7;
          color: #15803d;
        }
        #demo-status-badge.fail {
          background: #fee2e2;
          color: #b91c1c;
        }
        #demo-hint-text {
          font-style: italic;
        }
      `;

      document.head.appendChild(style);
      document.body.appendChild(overlay);

      // State for user pause
      window.__AUTOMIND_DEMO_PAUSED = false;

      const pauseBtn = document.getElementById('demo-btn-pause');
      const togglePause = () => {
        window.__AUTOMIND_DEMO_PAUSED = !window.__AUTOMIND_DEMO_PAUSED;
        pauseBtn.textContent = window.__AUTOMIND_DEMO_PAUSED ? '▶ Resume' : '⏸ Pause';
        pauseBtn.style.background = window.__AUTOMIND_DEMO_PAUSED ? '#fef08a' : '#f1f5f9';
      };

      pauseBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        togglePause();
      });

      // Press 'P' to toggle pause (when not inside inputs)
      window.addEventListener('keydown', (e) => {
        const tag = document.activeElement?.tagName?.toLowerCase();
        if (tag === 'input' || tag === 'textarea' || tag === 'select') return;
        if (e.key === 'p' || e.key === 'P') {
          e.preventDefault();
          togglePause();
        }
      });
    });
  }

  async setCaption({ chapter, step, title, action, expected, status = 'RUNNING' }) {
    await this.page.evaluate(
      ({ chapter, step, title, action, expected, status, speed }) => {
        const badge = document.getElementById('demo-chapter-badge');
        const titleEl = document.getElementById('demo-step-title');
        const actionEl = document.getElementById('demo-action-text');
        const expectedEl = document.getElementById('demo-expected-text');
        const statusBadge = document.getElementById('demo-status-badge');
        const speedLabel = document.getElementById('demo-speed-label');

        if (badge) badge.textContent = chapter || 'AUTOMIND AI DEMO';
        if (titleEl) titleEl.textContent = `${step ? step + ' · ' : ''}${title || ''}`;
        if (actionEl) actionEl.textContent = action || '';
        if (expectedEl) expectedEl.textContent = expected || '';
        if (speedLabel) speedLabel.textContent = speed === 0 ? 'FAST' : `${speed.toFixed(1)}×`;

        if (statusBadge) {
          statusBadge.textContent = status;
          statusBadge.className = status.toLowerCase();
        }
      },
      { chapter, step, title, action, expected, status, speed: this.speedMultiplier }
    );
  }

  async markPass(message = 'Asserted successfully') {
    await this.page.evaluate((msg) => {
      const statusBadge = document.getElementById('demo-status-badge');
      if (statusBadge) {
        statusBadge.textContent = 'PASS ✓';
        statusBadge.className = 'pass';
      }
    }, message);
  }

  async markFail(message = 'Assertion failed') {
    await this.page.evaluate((msg) => {
      const statusBadge = document.getElementById('demo-status-badge');
      if (statusBadge) {
        statusBadge.textContent = 'FAIL ✕';
        statusBadge.className = 'fail';
      }
    }, message);
  }

  async pauseForPresentation(baseMs = 1500) {
    if (this.speedMultiplier === 0) return; // Fast mode skips presentation pauses

    const actualMs = Math.round(baseMs / this.speedMultiplier);
    const start = Date.now();

    while (Date.now() - start < actualMs) {
      // Check if paused by user
      const isPaused = await this.page.evaluate(() => Boolean(window.__AUTOMIND_DEMO_PAUSED));
      if (isPaused) {
        await this.page.waitForTimeout(200);
      } else {
        await this.page.waitForTimeout(Math.min(100, actualMs - (Date.now() - start)));
      }
    }
  }
}
