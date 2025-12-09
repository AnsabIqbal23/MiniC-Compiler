# main.py
import sys
from MiniC.lexer import tokenize
from MiniC.parser import Parser
from MiniC.semantic import SemanticAnalyzer
from MiniC.interpreter import Interpreter
from MiniC.ir_generator import IRGenerator
from MiniC.tac_printer import TACPrinter
from MiniC.optimizer import TACOptimizer
from MiniC.codegen import CodeGenerator

def compile_and_run(code: str, flags=None, run=True, filename=None):
    if flags is None:
        flags = {}
    toks = tokenize(code)
    if flags.get('tokens'):
        print("Tokens:")
        for tok in toks:
            print(f"  {tok}")
        print()

    p = Parser(toks)
    prog = p.parse()
    if flags.get('ast'):
        print("AST:")
        print(prog)
        print()

    sa = SemanticAnalyzer(prog)
    sa.analyze()
    if flags.get('symbol_table'):
        print("Functions:")
        for name, func in sa.functions.items():
            print(f"  {name}: {func.ret_type}({', '.join(f'{t} {n}' for t, n in func.params)})")
        print()

    ir_gen = IRGenerator()
    tac = ir_gen.generate(prog)
    if flags.get('tac'):
        print("TAC:")
        for instr in tac:
            print(f"  {instr}")
        print()

    optimizer = TACOptimizer(tac)
    optimized_tac = optimizer.optimize()
    if flags.get('optimized'):
        print("Optimized TAC:")
        for instr in optimized_tac:
            print(f"  {instr}")
        print()

    if flags.get('codegen'):
        codegen = CodeGenerator()
        assembly = codegen.generate(optimized_tac)
        print("Generated Assembly:")
        print(assembly)
        # Write to .out file
        out_file = filename.replace('.mc', '.out') if filename else 'output.out'
        with open(out_file, 'w') as f:
            f.write(assembly)
        print(f"Assembly written to {out_file}")

    if run:
        interp = Interpreter(prog)
        return interp.run()
    return prog

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='MiniC compiler (modular)')
    parser.add_argument('file', nargs='?', help='MiniC source file')
    parser.add_argument('--tokens', action='store_true', help='Print tokens')
    parser.add_argument('--ast', action='store_true', help='Print AST')
    parser.add_argument('--symbol-table', action='store_true', help='Print symbol table')
    parser.add_argument('--tac', action='store_true', help='Print TAC')
    parser.add_argument('--optimized', action='store_true', help='Print optimized TAC')
    parser.add_argument('--codegen', action='store_true', help='Generate and print assembly code')
    args = parser.parse_args()

    if args.file:
        with open(args.file, 'r') as f:
            code = f.read()
        flags = {
            'tokens': args.tokens,
            'ast': args.ast,
            'symbol_table': args.symbol_table,
            'tac': args.tac,
            'optimized': args.optimized,
            'codegen': args.codegen
        }
        try:
            compile_and_run(code, flags=flags, run=not any(flags.values()), filename=args.file)
        except Exception as e:
            print('Compilation/Runtime error:', e)
            raise
    else:
        print('No input file specified.')
