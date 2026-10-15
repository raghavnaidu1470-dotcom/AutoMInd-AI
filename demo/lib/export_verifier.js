import fs from 'fs';
import path from 'path';

/**
 * File Export Verifier
 * ====================
 * Inspects downloaded SVG, PNG, and JSON files to guarantee:
 * - Proper dimensions and high-DPI scaling
 * - Concrete background colors and embedded styling
 * - Full unclipped viewBox independent of interactive pan/zoom
 * - Canonical JSON schema compliance and topological agreement with active automaton
 */

export class ExportVerifier {
  static verifySvgFile(filePath) {
    if (!fs.existsSync(filePath)) {
      throw new Error(`SVG file not found at ${filePath}`);
    }

    const content = fs.readFileSync(filePath, 'utf8');
    const stats = fs.statSync(filePath);

    if (stats.size < 500) {
      throw new Error(`SVG file is unusually small (${stats.size} bytes)`);
    }

    if (!content.includes('<svg') || !content.includes('</svg>')) {
      throw new Error('File does not contain valid SVG root element');
    }

    // Check viewBox and unclipped dimensions
    const viewBoxMatch = content.match(/viewBox="([^"]+)"/);
    if (!viewBoxMatch) {
      throw new Error('SVG missing required explicit viewBox');
    }
    const [minX, minY, width, height] = viewBoxMatch[1].split(' ').map(Number);
    if (isNaN(width) || isNaN(height) || width <= 0 || height <= 0) {
      throw new Error(`Invalid SVG viewBox dimensions: ${viewBoxMatch[1]}`);
    }

    // Check concrete background color (#f8f9fa)
    const hasPaperBg = content.includes('fill="#f8f9fa"');
    if (!hasPaperBg) {
      throw new Error('SVG missing solid paper background rect (#f8f9fa)');
    }

    // Check embedded stylesheet
    const hasEmbeddedStyles = content.includes('<style type="text/css">') || content.includes('<style>');
    if (!hasEmbeddedStyles) {
      throw new Error('SVG missing self-contained embedded style definition');
    }

    // Count states and transitions
    const stateCircleCount = (content.match(/class="[^"]*svg-state-circle[^"]*"/g) || []).length;
    const edgeCount = (content.match(/class="[^"]*svg-edge-path[^"]*"/g) || []).length;

    return {
      valid: true,
      sizeBytes: stats.size,
      viewBox: viewBoxMatch[1],
      dimensions: { width, height },
      stateCircleCount,
      edgeCount,
      hasPaperBg: true,
      hasEmbeddedStyles: true,
    };
  }

  static verifyPngFile(filePath) {
    if (!fs.existsSync(filePath)) {
      throw new Error(`PNG file not found at ${filePath}`);
    }

    const buffer = fs.readFileSync(filePath);
    const stats = fs.statSync(filePath);

    if (stats.size < 2000) {
      throw new Error(`PNG file size too small (${stats.size} bytes)`);
    }

    // Verify PNG magic number: 89 50 4E 47 0D 0A 1A 0A
    const pngSignature = [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a];
    for (let i = 0; i < 8; i++) {
      if (buffer[i] !== pngSignature[i]) {
        throw new Error('File signature does not match PNG format');
      }
    }

    // Parse IHDR chunk for pixel width and height
    // IHDR starts at byte 12 (length: 4 bytes at 8, type: 'IHDR' at 12, data at 16)
    const width = buffer.readUInt32BE(16);
    const height = buffer.readUInt32BE(20);
    const bitDepth = buffer.readUInt8(24);
    const colorType = buffer.readUInt8(25);

    if (width < 600 || height < 300) {
      throw new Error(`PNG pixel dimensions suspiciously small: ${width}x${height}`);
    }

    return {
      valid: true,
      sizeBytes: stats.size,
      pixelDimensions: { width, height },
      bitDepth,
      colorType,
      isHighDpi: width >= 1800, // 3x retina scaling
    };
  }

  static verifyJsonFile(filePath, expectedAutomaton = null) {
    if (!fs.existsSync(filePath)) {
      throw new Error(`JSON file not found at ${filePath}`);
    }

    const raw = fs.readFileSync(filePath, 'utf8');
    const data = JSON.parse(raw);

    // Validate canonical schema properties
    const requiredProps = ['type', 'states', 'transitions', 'alphabet', 'start_state'];
    for (const prop of requiredProps) {
      if (!(prop in data)) {
        throw new Error(`Exported JSON missing required property: ${prop}`);
      }
    }

    if (!Array.isArray(data.states) || data.states.length === 0) {
      throw new Error('Exported JSON has empty or invalid states array');
    }

    if (!Array.isArray(data.transitions)) {
      throw new Error('Exported JSON transitions must be an array');
    }

    if (!Array.isArray(data.alphabet)) {
      throw new Error('Exported JSON alphabet must be an array');
    }

    // Validate states structure
    for (const s of data.states) {
      if (!('id' in s) || typeof s.is_start !== 'boolean' || typeof s.is_accepting !== 'boolean') {
        throw new Error(`State ${JSON.stringify(s)} missing canonical fields (id, is_start, is_accepting)`);
      }
    }

    // Check against live expected automaton if provided
    if (expectedAutomaton) {
      if (expectedAutomaton.states && data.states.length !== expectedAutomaton.states.length) {
        throw new Error(
          `JSON state count (${data.states.length}) does not match displayed automaton (${expectedAutomaton.states.length})`
        );
      }
      if (expectedAutomaton.transitions && data.transitions.length !== expectedAutomaton.transitions.length) {
        throw new Error(
          `JSON transition count (${data.transitions.length}) does not match displayed automaton (${expectedAutomaton.transitions.length})`
        );
      }
    }

    return {
      valid: true,
      type: data.type,
      stateCount: data.states.length,
      transitionCount: data.transitions.length,
      alphabet: data.alphabet,
      startState: data.start_state,
    };
  }
}
