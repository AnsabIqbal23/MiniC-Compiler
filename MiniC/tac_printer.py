# tac_printer.py
"""
TAC Printer for MiniC Compiler.

This module provides functions to print Three-Address Code (TAC)
in different formats: Quadruples, Triples, and Postfix (RPN).
"""

from typing import List
from MiniC.ir_generator import TACInstruction

class TACPrinter:
    """Handles printing TAC in various formats."""

    @staticmethod
    def print_quadruples(instructions: List[TACInstruction]) -> str:
        """Print TAC as quadruples: (op, arg1, arg2, result)"""
        lines = []
        for i, instr in enumerate(instructions, 1):
            if instr.op == 'assign':
                lines.append(f"({i}) ({instr.op}, {instr.src1}, -, {instr.dest})")
            elif instr.op == 'binop':
                # src2 is "op right", so parse it
                parts = instr.src2.split(' ', 1)
                op = parts[0]
                arg2 = parts[1] if len(parts) > 1 else '-'
                lines.append(f"({i}) ({op}, {instr.src1}, {arg2}, {instr.dest})")
            elif instr.op == 'unop':
                lines.append(f"({i}) ({instr.src1}, {instr.src2}, -, {instr.dest})")
            elif instr.op == 'jump':
                lines.append(f"({i}) (goto, -, -, {instr.label})")
            elif instr.op == 'cjump':
                lines.append(f"({i}) (if, {instr.dest}, -, {instr.label})")
            elif instr.op == 'label':
                lines.append(f"({i}) (label, -, -, {instr.label})")
            elif instr.op == 'call':
                args_str = ', '.join(instr.src1) if instr.src1 else '-'
                lines.append(f"({i}) (call, {args_str}, {instr.src2}, {instr.dest})")
            elif instr.op == 'return':
                lines.append(f"({i}) (return, {instr.dest or '-'}, -, -)")
            elif instr.op == 'param':
                lines.append(f"({i}) (param, {instr.dest}, -, -)")
            else:
                lines.append(f"({i}) ({instr.op}, {instr.src1 or '-'}, {instr.src2 or '-'}, {instr.dest or '-'})")
        return '\n'.join(lines)

    @staticmethod
    def print_triples(instructions: List[TACInstruction]) -> str:
        """Print TAC as triples: (op, arg1, arg2) with implicit result as index"""
        lines = []
        for i, instr in enumerate(instructions, 1):
            if instr.op == 'assign':
                lines.append(f"({i}) ({instr.op}, {instr.src1}, -)")
            elif instr.op == 'binop':
                parts = instr.src2.split(' ', 1)
                op = parts[0]
                arg2 = parts[1] if len(parts) > 1 else '-'
                lines.append(f"({i}) ({op}, {instr.src1}, {arg2})")
            elif instr.op == 'unop':
                lines.append(f"({i}) ({instr.src1}, {instr.src2}, -)")
            elif instr.op == 'jump':
                lines.append(f"({i}) (goto, -, {instr.label})")
            elif instr.op == 'cjump':
                lines.append(f"({i}) (if, {instr.dest}, {instr.label})")
            elif instr.op == 'label':
                lines.append(f"({i}) (label, -, {instr.label})")
            elif instr.op == 'call':
                args_str = ', '.join(instr.src1) if instr.src1 else '-'
                lines.append(f"({i}) (call, {args_str}, {instr.src2})")
            elif instr.op == 'return':
                lines.append(f"({i}) (return, {instr.dest or '-'}, -)")
            elif instr.op == 'param':
                lines.append(f"({i}) (param, {instr.dest}, -)")
            else:
                lines.append(f"({i}) ({instr.op}, {instr.src1 or '-'}, {instr.src2 or '-'})")
        return '\n'.join(lines)

    @staticmethod
    def print_postfix(instructions: List[TACInstruction]) -> str:
        """Print TAC in postfix (RPN) notation for expressions."""
        # For simplicity, convert each instruction to RPN form
        lines = []
        for instr in instructions:
            if instr.op == 'assign':
                lines.append(f"{instr.src1} {instr.dest} =")
            elif instr.op == 'binop':
                parts = instr.src2.split(' ', 1)
                op = parts[0]
                arg2 = parts[1] if len(parts) > 1 else ''
                lines.append(f"{instr.src1} {arg2} {op} {instr.dest} =")
            elif instr.op == 'unop':
                lines.append(f"{instr.src2} {instr.src1} {instr.dest} =")
            elif instr.op == 'jump':
                lines.append(f"goto {instr.label}")
            elif instr.op == 'cjump':
                lines.append(f"{instr.dest} if goto {instr.label}")
            elif instr.op == 'label':
                lines.append(f"{instr.label}:")
            elif instr.op == 'call':
                args_str = ' '.join(instr.src1) if instr.src1 else ''
                lines.append(f"{args_str} {instr.src2} call {instr.dest} =")
            elif instr.op == 'return':
                lines.append(f"{instr.dest or ''} return")
            elif instr.op == 'param':
                lines.append(f"{instr.dest} param")
            else:
                lines.append(str(instr))
        return '\n'.join(lines)

@staticmethod
def print_tac(instructions: List[TACInstruction], format_type: str = 'standard') -> str:
    """Print TAC in the specified format."""
    if format_type == 'quadruples':
        return TACPrinter.print_quadruples(instructions)
    elif format_type == 'triples':
        return TACPrinter.print_triples(instructions)
    elif format_type == 'postfix':
        return TACPrinter.print_postfix(instructions)
    else:
        # Standard TAC
        return '\n'.join(str(instr) for instr in instructions)