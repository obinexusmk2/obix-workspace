/**
 * @obinexusltd/obix-state-minimizer
 *
 * Automaton state minimization, AST optimization, and Unicode structural
 * normalization (USCN) for the OBIX ecosystem.
 *
 * Author: Nnamdi Michael Okpala <support@obinexus.org>
 * Organisation: OBINexus Computing (obinexusmk2)
 * License: MIT
 */

// Types
export type {
  FSM,
  TransitionFn,
  TransitionTable,
  ASTNode,
  MinimizationResult,
  USCNResult,
  EncodingType,
} from './types';

// Minimizer
export { StateMinimizer, minimizeFSM } from './minimizer/StateMinimizer';
export { partitionRefinement } from './minimizer/PartitionRefinement';
export { ASTOptimizer, buildAST } from './minimizer/ASTOptimizer';

// Normalizer (USCN)
export {
  USCNormalizer,
  uscn,
  normalizeInput,
  isPathSafe,
} from './normalizer/USCNormalizer';

// Tennis reference implementation
export {
  TennisTrackerA,
  TennisTrackerB,
  buildTennisFSM,
  minimizeTennisFSM,
} from './tracker/TennisTracker';
export type {
  TennisScore,
  TennisEvent,
  MatchRecord,
} from './tracker/TennisTracker';
