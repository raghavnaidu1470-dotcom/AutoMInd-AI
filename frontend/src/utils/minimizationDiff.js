/**
 * Minimization Diff Utility
 * =========================
 * Compares the DFA and Minimized DFA to explain Hopcroft's minimization:
 * - State reduction metrics
 * - Which DFA states merged into each Minimized state
 * - Plain-language explanation of why equivalence classes were formed
 */

export function computeMinimizationDiff(dfa, minDfa) {
  if (!dfa || !minDfa) return null;

  const originalCount = dfa.states?.length || 0;
  const minimizedCount = minDfa.states?.length || 0;
  const statesEliminated = Math.max(0, originalCount - minimizedCount);
  const reductionPercent = originalCount > 0 ? Math.round((statesEliminated / originalCount) * 100) : 0;

  // Map each minimized state to its merged DFA states
  const mergeGroups = [];
  const minStates = minDfa.states || [];

  for (const mState of minStates) {
    const mergedList = mState.metadata?.merged_states || [];
    const nfaSubset = mState.metadata?.nfa_subset || [];

    const isMerged = mergedList.length > 1;

    mergeGroups.push({
      minimizedId: mState.id,
      label: mState.label || mState.id,
      isStart: mState.is_start,
      isAccepting: mState.is_accepting,
      mergedDfaStates: mergedList.length > 0 ? mergedList : [mState.id],
      isMerged,
      nfaSubset,
      explanation: isMerged
        ? `States {${mergedList.join(', ')}} are language-equivalent (Myhill-Nerode): they share identical right-languages (for every continuation string w ∈ Σ*, transitions from either state yield identical accept/reject verdicts).`
        : `State ${mState.id} represents a distinct right-language equivalence class that cannot be merged with any other state.`,
    });
  }

  // Summary verdict
  let summary = '';
  if (statesEliminated === 0) {
    summary = 'The DFA is already minimal. Every state recognizes a distinct right-language (all Myhill-Nerode equivalence classes are singletons).';
  } else {
    summary = `Minimization eliminated ${statesEliminated} redundant state${statesEliminated > 1 ? 's' : ''} (${reductionPercent}% reduction) by merging language-equivalent state partitions (states with identical right-languages under the Myhill-Nerode theorem) into canonical equivalence classes without altering language acceptance.`;
  }

  return {
    originalCount,
    minimizedCount,
    statesEliminated,
    reductionPercent,
    mergeGroups,
    summary,
    alphabet: minDfa.alphabet || dfa.alphabet || [],
  };
}
