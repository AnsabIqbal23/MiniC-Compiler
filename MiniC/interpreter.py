# interpreter.py
"""
Interpreter module for the MiniC compiler.

This module provides an interpreter to execute MiniC programs by evaluating
the AST nodes.
"""

from typing import Dict, Any, List
from MiniC.ast_nodes import *
from MiniC.semantic import SemanticError

class ReturnException(Exception):
    """Exception raised when a return statement is executed."""
    def __init__(self, value):
        self.value = value

class Interpreter:
    """
    Interpreter for executing MiniC programs.

    Attributes:
        program (Program): The AST of the program to interpret.
        functions (Dict[str, Function]): Mapping of function names to Function nodes.
    """

    def __init__(self, program: Program):
        self.program = program
        self.functions: Dict[str, Function] = {f.name: f for f in program.functions}

    def run(self, argv=None):
        """
        Run the program starting from the main function.

        Args:
            argv: Command line arguments (not used).

        Returns:
            The return value of the main function.

        Raises:
            Exception: If no main function is found.
        """
        if 'main' not in self.functions:
            raise Exception('No main function')
        mainf = self.functions['main']
        return self.exec_function(mainf, [])

    def exec_function(self, func: Function, args: List[Any]):
        """
        Execute a function with given arguments.

        Args:
            func (Function): The function to execute.
            args (List[Any]): Arguments to pass to the function.

        Returns:
            The return value of the function.
        """
        env: Dict[str, Any] = {}
        for (typ,name), val in zip(func.params, args):
            env[name] = val
        try:
            self.exec_block(func.body, env)
        except ReturnException as r:
            return r.value
        return None

    def exec_block(self, block: Block, env: Dict[str, Any]):
        """
        Execute a block of statements.

        Args:
            block (Block): The block to execute.
            env (Dict[str, Any]): The environment (variable bindings).
        """
        for stmt in block.statements:
            self.exec_stmt(stmt, env)

    def exec_stmt(self, stmt, env):
        """
        Execute a single statement.

        Args:
            stmt: The statement to execute.
            env (Dict[str, Any]): The environment.
        """
        if isinstance(stmt, VarDecl):
            val = None
            if stmt.init is not None:
                val = self.eval_expr(stmt.init, env)
            env[stmt.name] = val
            return

        if isinstance(stmt, Assignment):
            val = self.eval_expr(stmt.value, env)
            if stmt.target not in env:
                raise Exception(f"Assignment to undeclared variable {stmt.target}")
            env[stmt.target] = val
            return

        if isinstance(stmt, IfStmt):
            cond = self.eval_expr(stmt.cond, env)
            if cond:
                if isinstance(stmt.then_branch, Block):
                    self.exec_block(stmt.then_branch, env)
                else:
                    self.exec_stmt(stmt.then_branch, env)
            elif stmt.else_branch:
                if isinstance(stmt.else_branch, Block):
                    self.exec_block(stmt.else_branch, env)
                else:
                    self.exec_stmt(stmt.else_branch, env)
            return

        if isinstance(stmt, WhileStmt):
            while self.eval_expr(stmt.cond, env):
                if isinstance(stmt.body, Block):
                    self.exec_block(stmt.body, env)
                else:
                    self.exec_stmt(stmt.body, env)
            return

        if isinstance(stmt, ForStmt):
            if stmt.init:
                if isinstance(stmt.init, VarDecl):
                    self.exec_stmt(stmt.init, env)
                else:
                    self.exec_stmt(stmt.init, env)
            while True:
                if stmt.cond and not self.eval_expr(stmt.cond, env):
                    break
                if isinstance(stmt.body, Block):
                    self.exec_block(stmt.body, env)
                else:
                    self.exec_stmt(stmt.body, env)
                if stmt.update:
                    if isinstance(stmt.update, Assignment):
                        self.exec_stmt(stmt.update, env)
                    else:
                        self.eval_expr(stmt.update, env)
            return

        if isinstance(stmt, ReturnStmt):
            val = None
            if stmt.expr:
                val = self.eval_expr(stmt.expr, env)
            raise ReturnException(val)

        if isinstance(stmt, FuncCall):
            if stmt.name == 'print':
                vals = [self.eval_expr(a, env) for a in stmt.args]
                print(*vals)
                return
            if stmt.name == 'read':
                if not stmt.args or not isinstance(stmt.args[0], VarRef):
                    raise Exception('read expects a variable')
                name = stmt.args[0].name
                if name not in env:
                    raise Exception(f'read on undeclared variable {name}')
                v = input()
                try:
                    if '.' in v:
                        env[name] = float(v)
                    else:
                        env[name] = int(v)
                except:
                    env[name] = v
                return
            # user function
            f = self.functions.get(stmt.name)
            if not f:
                raise Exception(f'Call to undefined function {stmt.name}')
            argvals = [self.eval_expr(a, env) for a in stmt.args]
            return self.exec_function(f, argvals)

        if isinstance(stmt, Block):
            self.exec_block(stmt, env)
            return

        # expression statement
        if isinstance(stmt, (Expr, UnaryExpr, Literal, VarRef, FuncCall, Assignment)):
            self.eval_expr(stmt, env)
            return

        raise Exception(f'Unhandled statement in interpreter: {stmt}')

    def eval_expr(self, expr, env):
        """
        Evaluate an expression.

        Args:
            expr: The expression to evaluate.
            env (Dict[str, Any]): The environment.

        Returns:
            The value of the expression.
        """
        if isinstance(expr, Literal):
            return expr.value
        if isinstance(expr, VarRef):
            if expr.name not in env:
                raise Exception(f'Use of undeclared variable {expr.name}')
            return env[expr.name]
        if isinstance(expr, Assignment):
            val = self.eval_expr(expr.value, env)
            if expr.target not in env:
                raise Exception(f'Assignment to undeclared variable {expr.target}')
            env[expr.target] = val
            return val
        if isinstance(expr, UnaryExpr):
            v = self.eval_expr(expr.expr, env)
            if expr.op == '-':
                return -v
            if expr.op == '+':
                return +v
            if expr.op == '!':
                return not v
            return v
        if isinstance(expr, Expr):
            l = self.eval_expr(expr.left, env)
            r = self.eval_expr(expr.right, env)
            op = expr.op
            if op == '+': return l + r
            if op == '-': return l - r
            if op == '*': return l * r
            if op == '/': return l / r
            if op == '%': return l % r
            if op == '<': return l < r
            if op == '>': return l > r
            if op == '<=': return l <= r
            if op == '>=': return l >= r
            if op == '==': return l == r
            if op == '!=': return l != r
            if op == '&&': return l and r
            if op == '||': return l or r
            return None
        if isinstance(expr, FuncCall):
            if expr.name == 'print':
                vals = [self.eval_expr(a, env) for a in expr.args]
                print(*vals)
                return None
            if expr.name == 'read':
                if not expr.args or not isinstance(expr.args[0], VarRef):
                    raise Exception('read expects a variable')
                name = expr.args[0].name
                v = input()
                try:
                    if '.' in v:
                        return float(v)
                    else:
                        return int(v)
                except:
                    return v
            f = self.functions.get(expr.name)
            if not f:
                raise Exception(f'Call to undefined function {expr.name}')
            argvals = [self.eval_expr(a, env) for a in expr.args]
            return self.exec_function(f, argvals)
        raise Exception(f'Unhandled expression in interpreter: {expr}')
