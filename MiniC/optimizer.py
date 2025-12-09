# optimizer.py
"""
Optimizer for MiniC Compiler TAC.

Implements various optimization passes on Three-Address Code:
- Constant Folding
- Dead Code Elimination
- Common Subexpression Elimination (CSE)
- Constant Propagation
"""

from typing import List, Dict, Set, Optional
from MiniC.ir_generator import TACInstruction
from MiniC.dag_generator import DAGGenerator

class TACOptimizer:
    """Optimizes TAC instructions."""

    def __init__(self, instructions: List[TACInstruction]):
        self.instructions = instructions
        self.constants: Dict[str, str] = {}  # var -> constant value
        self.live_vars: Set[str] = set()

    def optimize(self) -> List[TACInstruction]:
        """Run all optimization passes."""
        # Constant Propagation
        self.constant_propagation()
        # Constant Folding
        self.constant_folding()
        # Constant Propagation again
        self.constant_propagation()
        # Common Subexpression Elimination
        self.common_subexpression_elimination()
        # Dead Code Elimination
        self.dead_code_elimination()
        return self.instructions

    def constant_propagation(self):
        """Propagate constant values through assignments."""
        self.constants = {}
        for instr in self.instructions:
            if instr.op == 'assign' and instr.src1 and instr.src1.isdigit():
                self.constants[instr.dest] = instr.src1
            elif instr.op == 'assign' and instr.src1 in self.constants:
                self.constants[instr.dest] = self.constants[instr.src1]
            elif instr.op in ('binop', 'unop'):
                # If operands are constants, compute later in folding
                pass
            else:
                # Kill constants for dest
                if instr.dest in self.constants:
                    del self.constants[instr.dest]

        # Replace uses of constants
        for instr in self.instructions:
            if instr.src1:
                if isinstance(instr.src1, list):
                    instr.src1 = [self.constants.get(x, x) for x in instr.src1]
                elif instr.src1 in self.constants:
                    instr.src1 = self.constants[instr.src1]
            if instr.dest and instr.dest in self.constants:
                instr.dest = self.constants[instr.dest]
            if instr.src2 and ' ' in instr.src2:
                parts = instr.src2.split(' ', 1)
                if parts[1] in self.constants:
                    instr.src2 = f"{parts[0]} {self.constants[parts[1]]}"

    def constant_folding(self):
        """Fold constant expressions."""
        new_instructions = []
        for instr in self.instructions:
            if instr.op == 'binop':
                parts = instr.src2.split(' ', 1)
                op = parts[0]
                right = parts[1]
                if instr.src1 and instr.src1.isdigit() and right.isdigit():
                    result = self.compute_constant(op, int(instr.src1), int(right))
                    new_instr = TACInstruction('assign', dest=instr.dest, src1=str(result))
                    new_instructions.append(new_instr)
                else:
                    new_instructions.append(instr)
            elif instr.op == 'unop':
                if instr.src2 and instr.src2.isdigit():
                    if instr.src1 == '-':
                        result = -int(instr.src2)
                    elif instr.src1 == '!':
                        result = 0 if int(instr.src2) else 1
                    new_instr = TACInstruction('assign', dest=instr.dest, src1=str(result))
                    new_instructions.append(new_instr)
                else:
                    new_instructions.append(instr)
            else:
                new_instructions.append(instr)
        self.instructions = new_instructions

    def compute_constant(self, op: str, left: int, right: int) -> int:
        """Compute constant binary operation."""
        if op == '+':
            return left + right
        elif op == '-':
            return left - right
        elif op == '*':
            return left * right
        elif op == '/':
            return left // right  # Integer division
        elif op == '%':
            return left % right
        elif op == '&&':
            return 1 if left and right else 0
        elif op == '||':
            return 1 if left or right else 0
        elif op == '<':
            return 1 if left < right else 0
        elif op == '>':
            return 1 if left > right else 0
        elif op == '<=':
            return 1 if left <= right else 0
        elif op == '>=':
            return 1 if left >= right else 0
        elif op == '==':
            return 1 if left == right else 0
        elif op == '!=':
            return 1 if left != right else 0
        else:
            return 0  # Default

    def common_subexpression_elimination(self):
        """Eliminate common subexpressions using DAG."""
        dag_gen = DAGGenerator()
        dag_gen.build_dag(self.instructions)
        cse_map = dag_gen.detect_cse()

        # For each CSE, replace later uses with the first temp
        for node, temps in cse_map.items():
            if len(temps) > 1:
                first_temp = temps[0]
                for temp in temps[1:]:
                    # Replace assignments to temp with assignments to first_temp
                    for instr in self.instructions:
                        if instr.dest == temp:
                            instr.dest = first_temp
                        if instr.src1 == temp:
                            instr.src1 = first_temp
                        if instr.src2 and temp in instr.src2:
                            instr.src2 = instr.src2.replace(temp, first_temp)

    def dead_code_elimination(self):
        """Remove dead code (unused assignments)."""
        # Compute live variables
        self.compute_live_variables()

        # Remove instructions that assign to dead variables
        new_instructions = []
        for instr in self.instructions:
            if instr.op in ('assign', 'binop', 'unop', 'call') and instr.dest not in self.live_vars:
                continue  # Skip dead assignment
            new_instructions.append(instr)
        self.instructions = new_instructions

    def compute_live_variables(self):
        """Compute which variables are live (used later)."""
        self.live_vars = set()
        # Backward pass
        for instr in reversed(self.instructions):
            if instr.op == 'return' and instr.dest:
                self.live_vars.add(instr.dest)
            elif instr.op == 'cjump':
                self.live_vars.add(instr.dest)
            elif instr.op == 'assign':
                if instr.dest in self.live_vars:
                    self.live_vars.add(instr.src1)
                self.live_vars.discard(instr.dest)  # dest is killed
            elif instr.op == 'binop':
                if instr.dest in self.live_vars:
                    self.live_vars.add(instr.src1)
                    parts = instr.src2.split(' ', 1)
                    if len(parts) > 1:
                        self.live_vars.add(parts[1])
                self.live_vars.discard(instr.dest)
            elif instr.op == 'unop':
                if instr.dest in self.live_vars:
                    self.live_vars.add(instr.src2)
                self.live_vars.discard(instr.dest)
            elif instr.op == 'call':
                if instr.dest in self.live_vars:
                    if instr.src1:
                        self.live_vars.update(instr.src1)
                self.live_vars.discard(instr.dest)
            elif instr.op == 'param':
                self.live_vars.add(instr.dest)