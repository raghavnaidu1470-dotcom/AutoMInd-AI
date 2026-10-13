/**
 * Edge Merging Utility for Automata Diagrams
 * ==========================================
 * Merges parallel transitions between identical source and target states,
 * combining their input symbols into clean comma-separated labels (e.g. "a, b").
 * Preserves importance metrics and active states.
 */

export function mergeParallelEdges(transitions = []) {
  if (!Array.isArray(transitions) || transitions.length === 0) {
    return [];
  }

  // Key by source and target state
  const edgeMap = new Map();

  for (const t of transitions) {
    if (!t || t.from_state === undefined || t.to_state === undefined) continue;

    const fromState = String(t.from_state);
    const toState = String(t.to_state);
    const key = `${fromState}->${toState}`;
    const symbol = t.symbol !== undefined && t.symbol !== null ? String(t.symbol) : 'ε';

    if (!edgeMap.has(key)) {
      edgeMap.set(key, {
        from_state: fromState,
        to_state: toState,
        isSelfLoop: fromState === toState,
        symbols: [symbol],
        importance: t.importance || 0,
        originalTransitions: [t],
      });
    } else {
      const existing = edgeMap.get(key);
      if (!existing.symbols.includes(symbol)) {
        existing.symbols.push(symbol);
      }
      if ((t.importance || 0) > existing.importance) {
        existing.importance = t.importance;
      }
      existing.originalTransitions.push(t);
    }
  }

  return Array.from(edgeMap.values()).map((edge) => {
    // Sort symbols alphabetically, putting epsilon last if present
    const sortedSymbols = [...edge.symbols].sort((a, b) => {
      if (a === 'ε') return 1;
      if (b === 'ε') return -1;
      return a.localeCompare(b);
    });

    return {
      from_state: edge.from_state,
      to_state: edge.to_state,
      isSelfLoop: edge.isSelfLoop,
      label: sortedSymbols.join(', '),
      symbols: sortedSymbols,
      importance: edge.importance,
      count: edge.symbols.length,
      originalTransitions: edge.originalTransitions,
    };
  });
}
