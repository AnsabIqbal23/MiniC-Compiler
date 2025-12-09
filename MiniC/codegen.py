# codegen.py
"""
Code Generator for MiniC Compiler.

Converts optimized TAC to pseudo-assembly code.
Outputs to a .out file.
"""

from typing import List
from MiniC.ir_generator import TACInstruction

class CodeGenerator:
    """Generates pseudo-assembly from TAC."""

    def __init__(self):
        self.assembly: List[str] = []
        self.temp_stack = []  # For stack-based operations

    def generate(self, instructions: List[TACInstruction]) -> str:
        """Generate assembly code from TAC."""
        self.assembly = []
        for instr in instructions:
            self.generate_instruction(instr)
        return '\n'.join(self.assembly)

    def generate_instruction(self, instr: TACInstruction):
        """Generate assembly for a single TAC instruction."""
        if instr.op == 'assign':
            # dest = src1
            self.assembly.append(f"LOAD {instr.src1}")
            self.assembly.append(f"STORE {instr.dest}")
        elif instr.op == 'binop':
            # dest = src1 op src2
            parts = instr.src2.split(' ', 1)
            op = parts[0]
            right = parts[1]
            self.assembly.append(f"LOAD {instr.src1}")
            self.assembly.append(f"LOAD {right}")
            if op == '+':
                self.assembly.append("ADD")
            elif op == '-':
                self.assembly.append("SUB")
            elif op == '*':
                self.assembly.append("MUL")
            elif op == '/':
                self.assembly.append("DIV")
            elif op == '%':
                self.assembly.append("MOD")
            elif op == '&&':
                self.assembly.append("AND")
            elif op == '||':
                self.assembly.append("OR")
            elif op == '<':
                self.assembly.append("LT")
            elif op == '>':
                self.assembly.append("GT")
            elif op == '<=':
                self.assembly.append("LE")
            elif op == '>=':
                self.assembly.append("GE")
            elif op == '==':
                self.assembly.append("EQ")
            elif op == '!=':
                self.assembly.append("NE")
            self.assembly.append(f"STORE {instr.dest}")
        elif instr.op == 'unop':
            # dest = op src2
            self.assembly.append(f"LOAD {instr.src2}")
            if instr.src1 == '-':
                self.assembly.append("NEG")
            elif instr.src1 == '!':
                self.assembly.append("NOT")
            self.assembly.append(f"STORE {instr.dest}")
        elif instr.op == 'jump':
            self.assembly.append(f"JMP {instr.label}")
        elif instr.op == 'cjump':
            self.assembly.append(f"LOAD {instr.dest}")
            self.assembly.append(f"JTRUE {instr.label}")
        elif instr.op == 'label':
            self.assembly.append(f"{instr.label}:")
        elif instr.op == 'call':
            # For simplicity, assume functions are handled separately
            args = instr.src1 or []
            for arg in args:
                self.assembly.append(f"PUSH {arg}")
            self.assembly.append(f"CALL {instr.src2}")
            if instr.dest:
                self.assembly.append(f"STORE {instr.dest}")
        elif instr.op == 'return':
            if instr.dest:
                self.assembly.append(f"LOAD {instr.dest}")
            self.assembly.append("RET")
        elif instr.op == 'param':
            self.assembly.append(f"PUSH {instr.dest}")
        # Skip other instructions or add as comments
        else:
            self.assembly.append(f"; {instr}")

def write_to_file(self, instructions: List[TACInstruction], filename: str):
    """Write the generated assembly to a file."""
    code = self.generate(instructions)
    with open(filename, 'w') as f:
        f.write(code)