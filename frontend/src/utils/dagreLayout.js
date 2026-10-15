/**
 * Hierarchical Automata Layout using Dagre
 * ==========================================
 * Computes layered left-to-right coordinates for states and edges.
 * Generates smooth bezier curves, merged parallel transitions,
 * and handles large graphs (>60 states) with safety warnings and simplified rendering.
 */

import dagre from 'dagre';
import { mergeParallelEdges } from './edgeMerging.js';

export const LARGE_INPUT_THRESHOLD = 60;

/**
 * Builds layout geometry for an automaton
 */
export function buildAutomatonLayout(automaton, { nodeRadius = 22, simplified = false } = {}) {
  const states = automaton?.states || [];
  const rawTransitions = automaton?.transitions || [];
  const mergedEdges = mergeParallelEdges(rawTransitions);

  const isLarge = states.length >= LARGE_INPUT_THRESHOLD;
  const shouldSimplify = simplified || isLarge;

  if (states.length === 0) {
    return {
      coords: {},
      edges: [],
      width: 600,
      height: 400,
      nodeRadius,
      isLarge: false,
    };
  }

  // If simplified rendering is active for massive graphs, compute fast algorithmic positions
  if (shouldSimplify) {
    const cols = Math.ceil(Math.sqrt(states.length * 1.5));
    const cellWidth = 90;
    const cellHeight = 80;
    const padding = 60;
    const coords = {};

    states.forEach((s, idx) => {
      const col = idx % cols;
      const row = Math.floor(idx / cols);
      coords[s.id] = {
        x: padding + col * cellWidth,
        y: padding + row * cellHeight,
      };
    });

    const width = Math.max(700, padding * 2 + cols * cellWidth);
    const rows = Math.ceil(states.length / cols);
    const height = Math.max(400, padding * 2 + rows * cellHeight);

    const edges = mergedEdges.map((edge) => {
      const u = coords[edge.from_state];
      const v = coords[edge.to_state];
      return {
        ...edge,
        from: edge.from_state,
        to: edge.to_state,
        points: u && v ? [u, v] : [],
        isSelfLoop: edge.from_state === edge.to_state,
      };
    });

    return {
      coords,
      edges,
      width,
      height,
      nodeRadius: 18,
      isLarge: true,
      stateCount: states.length,
    };
  }

  // Standard hierarchical left-to-right layout via Dagre
  const g = new dagre.graphlib.Graph({ multigraph: false });
  g.setGraph({
    rankdir: 'LR',
    nodesep: 45,
    ranksep: 75,
    marginx: 60,
    marginy: 60,
  });
  g.setDefaultEdgeLabel(() => ({}));

  const nodeDim = nodeRadius * 2 + 10;
  states.forEach((s) => {
    g.setNode(String(s.id), {
      width: nodeDim,
      height: nodeDim,
      label: s.label || s.id,
    });
  });

  mergedEdges.forEach((edge) => {
    if (edge.from_state !== edge.to_state) {
      g.setEdge(String(edge.from_state), String(edge.to_state));
    }
  });

  dagre.layout(g);

  const coords = {};
  states.forEach((s) => {
    const node = g.node(String(s.id));
    if (node) {
      coords[s.id] = {
        x: Math.round(node.x),
        y: Math.round(node.y),
      };
    } else {
      coords[s.id] = { x: 80, y: 80 };
    }
  });

  const graphBounds = g.graph();
  const width = Math.max(680, Math.round(graphBounds?.width || 680) + 120);
  const height = Math.max(380, Math.round(graphBounds?.height || 380) + 100);

  // Compute curved paths and control points for edges
  const edges = mergedEdges.map((edge) => {
    const u = coords[edge.from_state];
    const v = coords[edge.to_state];
    const dagreEdge = g.edge(String(edge.from_state), String(edge.to_state));

    let points = [];
    if (dagreEdge && Array.isArray(dagreEdge.points) && dagreEdge.points.length > 0) {
      points = dagreEdge.points.map((p) => ({ x: Math.round(p.x), y: Math.round(p.y) }));
    } else if (u && v) {
      points = [u, v];
    }

    return {
      ...edge,
      from: edge.from_state,
      to: edge.to_state,
      points,
      isSelfLoop: edge.from_state === edge.to_state,
    };
  });

  return {
    coords,
    edges,
    width,
    height,
    nodeRadius,
    isLarge: false,
    stateCount: states.length,
  };
}
