# ir_generator.py
"""
Intermediate Representation Generator for MiniC Compiler.

This module generates Three-Address Code (TAC) from the AST.
TAC is a linear representation of the program where each instruction
has at most three operands: two sources and one destination.
"""

from typing import List, Dict, Any, Optional
from MiniC.ast_nodes import *

class TACInstruction:
    """Represents a single TAC instruction."""
    def __init__(self, op: str, dest: Optional[str] = None, src1: Optional[str] = None,
                 src2: Optional[str] = None, label: Optional[str] = None):
        self.op = op  # Operation: 'assign', 'binop', 'unop', 'jump', 'cjump', 'label', 'call', 'return', 'param'
        self.dest = dest  # Destination operand
        self.src1 = src1  # First source operand
        self.src2 = src2  # Second source operand
        self.label = label  # Label for jumps

    def __str__(self):
        if self.op == 'label':
            return f"{self.label}:"
        elif self.op == 'assign':
            return f"{self.dest} = {self.src1}"
        elif self.op == 'binop':
            return f"{self.dest} = {self.src1} {self.src2}"
        elif self.op == 'unop':
            return f"{self.dest} = {self.src1} {self.src2}"
        elif self.op == 'jump':
            return f"goto {self.label}"
        elif self.op == 'cjump':
            return f"if {self.dest} goto {self.label}"
        elif self.op == 'call':
            args_str = ', '.join(self.src1) if self.src1 else ''
            return f"{self.dest} = call {self.src2}({args_str})"
        elif self.op == 'return':
            return f"return {self.dest}" if self.dest else "return"
        elif self.op == 'param':
            return f"param {self.dest}"
        else:
            return f"{self.op} {self.dest} {self.src1} {self.src2}"

class IRGenerator:
    """Generates TAC from AST."""

    def __init__(self):
        self.instructions: List[TACInstruction] = []
        self.temp_count = 0
        self.label_count = 0
        self.symbol_table: Dict[str, str] = {}  # var name to type

    def new_temp(self) -> str:
        """Generate a new temporary variable."""
        self.temp_count += 1
        return f"t{self.temp_count}"

    def new_label(self) -> str:
        """Generate a new label."""
        self.label_count += 1
        return f"L{self.label_count}"

    def generate(self, program: Program) -> List[TACInstruction]:
        """Generate TAC for the entire program."""
        self.instructions = []
        self.temp_count = 0
        self.label_count = 0
        for func in program.functions:
            self.generate_function(func)
        return self.instructions

    def generate_function(self, func: Function):
        """Generate TAC for a function."""
        # Function label
        self.instructions.append(TACInstruction('label', label=func.name))
        # Parameters
        for typ, name in func.params:
            self.symbol_table[name] = typ
        # Body
        self.generate_statement(func.body)
        # Implicit return if void
        if func.ret_type == 'void':
            self.instructions.append(TACInstruction('return'))

    def generate_statement(self, stmt):
        """Generate TAC for a statement."""
        if isinstance(stmt, Block):
            for s in stmt.statements:
                self.generate_statement(s)
        elif isinstance(stmt, VarDecl):
            if stmt.init:
                temp = self.generate_expression(stmt.init)
                self.instructions.append(TACInstruction('assign', dest=stmt.name, src1=temp))
            self.symbol_table[stmt.name] = stmt.var_type
        elif isinstance(stmt, Assignment):
            temp = self.generate_expression(stmt.value)
            self.instructions.append(TACInstruction('assign', dest=stmt.target, src1=temp))
        elif isinstance(stmt, IfStmt):
            cond_temp = self.generate_expression(stmt.cond)
            else_label = self.new_label()
            end_label = self.new_label()
            self.instructions.append(TACInstruction('cjump', dest=cond_temp, label=else_label))
            self.generate_statement(stmt.then_branch)
            self.instructions.append(TACInstruction('jump', label=end_label))
            self.instructions.append(TACInstruction('label', label=else_label))
            if stmt.else_branch:
                self.generate_statement(stmt.else_branch)
            self.instructions.append(TACInstruction('label', label=end_label))
        elif isinstance(stmt, WhileStmt):
            start_label = self.new_label()
            end_label = self.new_label()
            self.instructions.append(TACInstruction('label', label=start_label))
            cond_temp = self.generate_expression(stmt.cond)
            self.instructions.append(TACInstruction('cjump', dest=cond_temp, label=end_label))
            self.generate_statement(stmt.body)
            self.instructions.append(TACInstruction('jump', label=start_label))
            self.instructions.append(TACInstruction('label', label=end_label))
        elif isinstance(stmt, ForStmt):
            if stmt.init:
                self.generate_statement(stmt.init)
            start_label = self.new_label()
            end_label = self.new_label()
            self.instructions.append(TACInstruction('label', label=start_label))
            if stmt.cond:
                cond_temp = self.generate_expression(stmt.cond)
                self.instructions.append(TACInstruction('cjump', dest=cond_temp, label=end_label))
            self.generate_statement(stmt.body)
            if stmt.update:
                self.generate_expression(stmt.update)  # For side effects
            self.instructions.append(TACInstruction('jump', label=start_label))
            self.instructions.append(TACInstruction('label', label=end_label))
        elif isinstance(stmt, ReturnStmt):
            if stmt.expr:
                temp = self.generate_expression(stmt.expr)
                self.instructions.append(TACInstruction('return', dest=temp))
            else:
                self.instructions.append(TACInstruction('return'))
        elif isinstance(stmt, FuncCall):
            self.generate_func_call(stmt)
        elif isinstance(stmt, Expr):
            self.generate_expression(stmt)  # For side effects

    def generate_expression(self, expr) -> str:
        """Generate TAC for an expression and return the temp holding the result."""
        if isinstance(expr, Literal):
            temp = self.new_temp()
            self.instructions.append(TACInstruction('assign', dest=temp, src1=str(expr.value)))
            return temp
        elif isinstance(expr, VarRef):
            return expr.name
        elif isinstance(expr, UnaryExpr):
            src_temp = self.generate_expression(expr.expr)
            temp = self.new_temp()
            self.instructions.append(TACInstruction('unop', dest=temp, src1=expr.op, src2=src_temp))
            return temp
        elif isinstance(expr, Expr):
            left_temp = self.generate_expression(expr.left)
            right_temp = self.generate_expression(expr.right)
            temp = self.new_temp()
            self.instructions.append(TACInstruction('binop', dest=temp, src1=left_temp, src2=f"{expr.op} {right_temp}"))
            return temp
        elif isinstance(expr, Assignment):
            value_temp = self.generate_expression(expr.value)
            self.instructions.append(TACInstruction('assign', dest=expr.target, src1=value_temp))
            return expr.target
        elif isinstance(expr, FuncCall):
            return self.generate_func_call(expr)
        else:
            raise ValueError(f"Unsupported expression type: {type(expr)}")

    def generate_func_call(self, call: FuncCall) -> str:
        """Generate TAC for a function call."""
        # Push parameters
        arg_temps = []
        for arg in call.args:
            arg_temp = self.generate_expression(arg)
            arg_temps.append(arg_temp)
            self.instructions.append(TACInstruction('param', dest=arg_temp))
        # Call
        temp = self.new_temp()
        self.instructions.append(TACInstruction('call', dest=temp, src2=call.name, src1=arg_temps))
        return temp