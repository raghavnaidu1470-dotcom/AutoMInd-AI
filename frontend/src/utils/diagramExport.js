/**
 * Diagram Export Utility
 * =======================
 * Generates self-contained, high-resolution SVG and PNG exports of automata diagrams.
 * - Resolves all CSS variables to concrete hex values so standalone image viewers render correctly.
 * - Injects full embedded CSS styles and font-family rules.
 * - Computes generous unclipped viewBox and explicit dimensions independent of interactive zoom/pan.
 * - Renders high-DPI (3x) crisp canvas PNG with anti-aliasing and solid paper background.
 */

export const EXPORT_COLORS = {
  paperBg: '#f8f9fa',
  panelBg: '#ffffff',
  slateInk: '#1e293b',
  secondaryInk: '#475569',
  borderInk: '#cbd5e1',
  borderLight: '#e2e8f0',
  amberSignal: '#d97706',
  amberTint: '#fef3c7',
  greenAccept: '#15803d',
  redRisk: '#b91c1c',
};

/**
 * Builds standalone SVG string with embedded styles, concrete colors, and correct bounding box
 */
export function buildStandaloneSvgString(svgElement, layout, automaton, options = {}) {
  if (!svgElement || !layout) return '';

  const padding = options.padding !== undefined ? options.padding : 50;
  const showHeader = options.showHeader !== false;

  const headerHeight = showHeader ? 36 : 0;
  const viewBoxMinX = -padding;
  const viewBoxMinY = -(padding + headerHeight);
  const totalWidth = Math.max(700, layout.width + padding * 2);
  const totalHeight = Math.max(400, layout.height + padding * 2 + headerHeight);

  // Clone node so we don't modify the live interactive DOM
  const clone = svgElement.cloneNode(true);

  // Remove interactive transform from the clone
  clone.removeAttribute('style');
  clone.removeAttribute('class');
  clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
  clone.setAttribute('xmlns:xlink', 'http://www.w3.org/1999/xlink');
  clone.setAttribute('version', '1.1');
  clone.setAttribute('width', String(totalWidth));
  clone.setAttribute('height', String(totalHeight));
  clone.setAttribute('viewBox', `${viewBoxMinX} ${viewBoxMinY} ${totalWidth} ${totalHeight}`);

  // Serialize SVG safely across browser and Node.js environments
  let rawSvg = '';
  if (typeof XMLSerializer !== 'undefined') {
    rawSvg = new XMLSerializer().serializeToString(clone);
  } else if (clone && typeof clone.outerHTML === 'string') {
    rawSvg = clone.outerHTML;
  } else {
    rawSvg = '<svg xmlns="http://www.w3.org/2000/svg"><defs></defs></svg>';
  }
  // Replace any CSS variable references in attributes
  rawSvg = rawSvg
    .replace(/var\(--ink-slate\)/g, EXPORT_COLORS.slateInk)
    .replace(/var\(--paper-bg\)/g, EXPORT_COLORS.paperBg)
    .replace(/var\(--paper-panel\)/g, EXPORT_COLORS.panelBg)
    .replace(/var\(--amber-signal\)/g, EXPORT_COLORS.amberSignal)
    .replace(/var\(--amber-tint\)/g, EXPORT_COLORS.amberTint)
    .replace(/var\(--green-accept\)/g, EXPORT_COLORS.greenAccept)
    .replace(/var\(--red-risk\)/g, EXPORT_COLORS.redRisk)
    .replace(/var\(--ink-border\)/g, EXPORT_COLORS.borderInk)
    .replace(/var\(--ink-secondary\)/g, EXPORT_COLORS.secondaryInk);

  // Guarantee explicit unclipped viewBox, width, and height on root tag without duplicate xmlns
  rawSvg = rawSvg.replace(/<svg\b([^>]*)>/, (match, attrs) => {
    const cleanedAttrs = attrs
      .replace(/\s+xmlns="[^"]*"/g, '')
      .replace(/\s+xmlns:xlink="[^"]*"/g, '')
      .replace(/\s+viewBox="[^"]*"/g, '')
      .replace(/\s+width="[^"]*"/g, '')
      .replace(/\s+height="[^"]*"/g, '')
      .replace(/\s+style="[^"]*"/g, '');
    return `<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="${totalWidth}" height="${totalHeight}" viewBox="${viewBoxMinX} ${viewBoxMinY} ${totalWidth} ${totalHeight}"${cleanedAttrs}>`;
  });

  // Embedded self-contained stylesheet
  const embeddedStyles = `
    <style type="text/css">
      <![CDATA[
        text {
          font-family: 'JetBrains Mono', 'Courier New', Courier, monospace;
          text-rendering: geometricPrecision;
          -webkit-font-smoothing: antialiased;
        }
        .svg-edge-path {
          fill: none;
          stroke: ${EXPORT_COLORS.slateInk};
          stroke-width: 1.8px;
          stroke-linecap: round;
          stroke-linejoin: round;
        }
        .svg-edge-path.active {
          stroke: ${EXPORT_COLORS.amberSignal};
          stroke-width: 3.2px;
        }
        .svg-edge-label-bg {
          fill: ${EXPORT_COLORS.panelBg};
          stroke: ${EXPORT_COLORS.borderInk};
          stroke-width: 1px;
          rx: 3px;
        }
        .svg-edge-label-text {
          font-family: 'JetBrains Mono', monospace;
          font-size: 11px;
          font-weight: 600;
          fill: ${EXPORT_COLORS.slateInk};
          text-anchor: middle;
          dominant-baseline: central;
        }
        .svg-state-circle {
          fill: ${EXPORT_COLORS.panelBg};
          stroke: ${EXPORT_COLORS.slateInk};
          stroke-width: 2px;
        }
        .svg-state-group.active .svg-state-circle {
          stroke: ${EXPORT_COLORS.amberSignal};
          stroke-width: 3px;
          fill: ${EXPORT_COLORS.amberTint};
        }
        .svg-state-circle.accepting-outer {
          fill: none;
          stroke: ${EXPORT_COLORS.slateInk};
          stroke-width: 1.5px;
        }
        .svg-state-group.active .accepting-outer {
          stroke: ${EXPORT_COLORS.amberSignal};
        }
        .svg-state-label {
          font-family: 'JetBrains Mono', monospace;
          font-size: 12px;
          font-weight: 700;
          fill: ${EXPORT_COLORS.slateInk};
          text-anchor: middle;
          dominant-baseline: central;
        }
        .svg-start-arrow path {
          stroke: ${EXPORT_COLORS.slateInk};
          stroke-width: 2px;
        }
      ]]>
    </style>
  `;

  // Background rect and blueprint header bar
  const automatonTitle = automaton?.name || automaton?.type || 'Automaton Schematic';
  const stateCount = automaton?.states?.length || 0;
  const transCount = automaton?.transitions?.length || 0;
  const headerSubtitle = `${stateCount} states · ${transCount} transitions · AutoMind-AI`;

  const backgroundAndHeader = `
    <!-- Solid technical blueprint paper ground -->
    <rect x="${viewBoxMinX}" y="${viewBoxMinY}" width="${totalWidth}" height="${totalHeight}" fill="${EXPORT_COLORS.paperBg}" />
    <!-- Fine 20px grid lines for technical blueprint look -->
    <defs>
      <pattern id="export-grid" width="20" height="20" patternUnits="userSpaceOnUse">
        <path d="M 20 0 L 0 0 0 20" fill="none" stroke="${EXPORT_COLORS.borderLight}" stroke-width="0.75" />
      </pattern>
    </defs>
    <rect x="${viewBoxMinX}" y="${viewBoxMinY}" width="${totalWidth}" height="${totalHeight}" fill="url(#export-grid)" opacity="0.6" />
    
    ${showHeader ? `
    <!-- Blueprint Header -->
    <g id="export-header-group">
      <rect x="${viewBoxMinX + 16}" y="${viewBoxMinY + 12}" width="${totalWidth - 32}" height="32" rx="4" fill="${EXPORT_COLORS.panelBg}" stroke="${EXPORT_COLORS.borderInk}" stroke-width="1" />
      <text x="${viewBoxMinX + 28}" y="${viewBoxMinY + 32}" font-size="12" font-weight="700" fill="${EXPORT_COLORS.slateInk}">
        ${automatonTitle}
      </text>
      <text x="${viewBoxMinX + totalWidth - 28}" y="${viewBoxMinY + 32}" font-size="11" font-weight="500" fill="${EXPORT_COLORS.secondaryInk}" text-anchor="end">
        ${headerSubtitle}
      </text>
    </g>
    ` : ''}
  `;

  // Inject styles into <defs> and background right after <svg ...>
  let finalSvg = rawSvg.replace(
    /<defs>/,
    `<defs>${embeddedStyles}`
  );

  // Inject background rect right after opening <svg ...>
  const svgOpenTagMatch = finalSvg.match(/<svg[^>]*>/);
  if (svgOpenTagMatch) {
    const openTag = svgOpenTagMatch[0];
    const index = finalSvg.indexOf(openTag) + openTag.length;
    finalSvg = finalSvg.slice(0, index) + backgroundAndHeader + finalSvg.slice(index);
  }

  return finalSvg;
}

/**
 * Downloads SVG file
 */
export function exportSvgFile(svgElement, layout, automaton, filename = 'automaton.svg') {
  const svgString = buildStandaloneSvgString(svgElement, layout, automaton);
  if (!svgString) return;

  const blob = new Blob([svgString], { type: 'image/svg+xml;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Exports high-resolution PNG file via Canvas rasterization (3x retina scaling)
 */
export function exportPngFile(svgElement, layout, automaton, filename = 'automaton.png', scale = 3) {
  const svgString = buildStandaloneSvgString(svgElement, layout, automaton);
  if (!svgString) return;

  const padding = 50;
  const headerHeight = 36;
  const totalWidth = Math.max(700, layout.width + padding * 2);
  const totalHeight = Math.max(400, layout.height + padding * 2 + headerHeight);

  const canvas = document.createElement('canvas');
  canvas.width = Math.round(totalWidth * scale);
  canvas.height = Math.round(totalHeight * scale);

  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  ctx.imageSmoothingEnabled = true;
  ctx.imageSmoothingQuality = 'high';

  const img = new Image();
  const svgBlob = new Blob([svgString], { type: 'image/svg+xml;charset=utf-8' });
  const blobUrl = URL.createObjectURL(svgBlob);

  img.onload = () => {
    // Fill background first in case of transparent pixels
    ctx.fillStyle = EXPORT_COLORS.paperBg;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Draw rasterized SVG scaled up smoothly
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    URL.revokeObjectURL(blobUrl);

    try {
      const pngUrl = canvas.toDataURL('image/png');
      const link = document.createElement('a');
      link.href = pngUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (err) {
      console.error('Failed to export PNG from canvas:', err);
    }
  };

  img.onerror = (err) => {
    console.error('Failed to load SVG for PNG export:', err);
    URL.revokeObjectURL(blobUrl);
  };

  img.src = blobUrl;
}
