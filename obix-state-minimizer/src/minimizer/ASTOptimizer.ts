/**
 * ASTOptimizer — reflects minimized FSM structure into an Abstract Syntax Tree.
 *
 * Steps:
 *  1. Build an AST from the original (or minimized) FSM via BFS from q₀.
 *  2. Prune nodes that map to removed (merged) states.
 *  3. Return the optimized tree rooted at the initial state node.
 *
 * Based on: Okpala, N.M. (2024). Automaton State Minimization and AST
 *           Optimization. OBINexus Computing Technical Report.
 */

import type { FSM, ASTNode, MinimizationResult } from '../types';

export class ASTOptimizer<S extends string, A extends string> {
  constructor(
    private readonly fsm: FSM<S, A>,
    private readonly result: MinimizationResult<S, A>
  ) {}

  /**
   * Build and return an optimized AST rooted at the minimized initial state.
   * Cycles are handled by tracking visited nodes — back-edges are not followed.
   */
  buildOptimizedAST(): ASTNode<string, A> {
    const { minimized } = this.result;
    const visited = new Map<string, ASTNode<string, A>>();
    return this.buildNode(minimized.initialState, minimized, visited);
  }

  private buildNode(
    state: string,
    fsm: FSM<string, A>,
    visited: Map<string, ASTNode<string, A>>
  ): ASTNode<string, A> {
    if (visited.has(state)) {
      // Return the already-built node (handles cycles)
      return visited.get(state)!;
    }

    const node: ASTNode<string, A> = {
      state,
      children: new Map(),
      accepting: fsm.acceptingStates.has(state),
    };
    visited.set(state, node);

    for (const symbol of fsm.alphabet) {
      const next = fsm.transition(state, symbol);
      if (next !== undefined) {
        const child = this.buildNode(next, fsm, visited);
        node.children.set(symbol, child);
      }
    }

    return node;
  }

  /** Serialize the AST as an indented string (for debugging / display). */
  static serialize<S extends string, A extends string>(
    node: ASTNode<S, A>,
    indent = 0,
    seen = new Set<S>()
  ): string {
    const prefix = '  '.repeat(indent);
    const marker = node.accepting ? ' [ACCEPT]' : '';
    let out = `${prefix}[${node.state}]${marker}\n`;

    if (seen.has(node.state)) {
      return out + `${prefix}  <cycle>\n`;
    }
    seen.add(node.state);

    for (const [sym, child] of node.children) {
      out += `${prefix}  --${sym}--> \n`;
      out += ASTOptimizer.serialize(child, indent + 2, new Set(seen));
    }

    return out;
  }
}

/** Convenience factory */
export function buildAST<S extends string, A extends string>(
  fsm: FSM<S, A>,
  result: MinimizationResult<S, A>
): ASTNode<string, A> {
  return new ASTOptimizer(fsm, result).buildOptimizedAST();
}
