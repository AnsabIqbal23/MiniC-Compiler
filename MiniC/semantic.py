# semantic.py
from typing import Dict, Any
from MiniC.ast_nodes import *
class SemanticError(Exception):
    """Exception raised for semantic analysis errors in the MiniC compiler."""
    pass

class Symbol:
    """Represents a symbol in the symbol table with name, type, and kind."""
    def __init__(self, name, typ, kind='var'):
        """Initialize a symbol with name, type, and kind (default 'var')."""
        self.name = name
        self.typ = typ
        self.kind = kind

class SemanticAnalyzer:
    """Performs semantic analysis on the MiniC program AST."""
    def __init__(self, program: Program):
        """Initialize the semantic analyzer with the program AST."""
        self.program = program
        self.globals: Dict[str, Symbol] = {}
        self.functions: Dict[str, Function] = {}

    def analyze(self):
        """Analyze the entire program for semantic errors."""
        for f in self.program.functions:
            if f.name in self.functions:
                raise SemanticError(f"Duplicate function {f.name}")
            self.functions[f.name] = f
        if 'main' not in self.functions:
            raise SemanticError('No main function defined')
        for fname, func in self.functions.items():
            self.analyze_function(func)

    def analyze_function(self, func: Function):
        """Analyze a single function for semantic errors."""
        symtab: Dict[str, Symbol] = {}
        for typ, name in func.params:
            symtab[name] = Symbol(name, typ, 'var')
        self.walk_block(func.body, symtab, func.ret_type)

    def walk_block(self, block: Block, symtab: Dict[str, Symbol], ret_type: str):
        """Walk through the statements in a block."""
        for stmt in block.statements:
            self.walk_stmt(stmt, symtab, ret_type)

    def walk_stmt(self, stmt, symtab, ret_type):
        """Walk through a statement and perform semantic checks."""
        if isinstance(stmt, VarDecl):
            if stmt.name in symtab:
                raise SemanticError(f"Variable {stmt.name} already declared")
            if stmt.init is not None:
                init_type = self.eval_expr_type(stmt.init, symtab)
                if not self.type_compatible(stmt.var_type, init_type):
                    raise SemanticError(f"Type mismatch initializing {stmt.name}: {stmt.var_type} <- {init_type}")
            symtab[stmt.name] = Symbol(stmt.name, stmt.var_type)

        elif isinstance(stmt, Assignment):
            if stmt.target not in symtab:
                raise SemanticError(f"Assignment to undeclared variable {stmt.target}")
            ttype = symtab[stmt.target].typ
            vtype = self.eval_expr_type(stmt.value, symtab)
            if not self.type_compatible(ttype, vtype):
                raise SemanticError(f"Type mismatch in assignment to {stmt.target}: {ttype} <- {vtype}")

        elif isinstance(stmt, IfStmt):
            condt = self.eval_expr_type(stmt.cond, symtab)
            if condt != 'bool':
                raise SemanticError(f"Condition in if must be bool, got {condt}")
            self.walk_stmt(stmt.then_branch, dict(symtab), ret_type) if isinstance(stmt.then_branch, Block) else self.walk_stmt(stmt.then_branch, symtab, ret_type)
            if stmt.else_branch:
                self.walk_stmt(stmt.else_branch, dict(symtab), ret_type) if isinstance(stmt.else_branch, Block) else self.walk_stmt(stmt.else_branch, symtab, ret_type)

        elif isinstance(stmt, WhileStmt):
            condt = self.eval_expr_type(stmt.cond, symtab)
            if condt != 'bool':
                raise SemanticError(f"Condition in while must be bool, got {condt}")
            # semantic checking of body (use copy to prevent accidental symbol leakage)
            self.walk_stmt(stmt.body, dict(symtab), ret_type) if isinstance(stmt.body, Block) else self.walk_stmt(stmt.body, symtab, ret_type)

        elif isinstance(stmt, ForStmt):
            if stmt.init:
                self.walk_stmt(stmt.init, symtab, ret_type) if not isinstance(stmt.init, VarDecl) else self.walk_stmt(stmt.init, symtab, ret_type)
            if stmt.cond:
                condt = self.eval_expr_type(stmt.cond, symtab)
                if condt != 'bool':
                    raise SemanticError(f"Condition in for must be bool, got {condt}")
            if stmt.body:
                self.walk_stmt(stmt.body, dict(symtab), ret_type) if isinstance(stmt.body, Block) else self.walk_stmt(stmt.body, symtab, ret_type)

        elif isinstance(stmt, ReturnStmt):
            if stmt.expr is None:
                if ret_type != 'void':
                    raise SemanticError(f"Missing return value for non-void function")
            else:
                et = self.eval_expr_type(stmt.expr, symtab)
                if not self.type_compatible(ret_type, et):
                    raise SemanticError(f"Return type mismatch: expected {ret_type}, got {et}")

        elif isinstance(stmt, FuncCall):
            if stmt.name not in ('print','read') and stmt.name not in self.functions:
                raise SemanticError(f"Call to undefined function {stmt.name}")

        elif isinstance(stmt, Block):
            self.walk_block(stmt, dict(symtab), ret_type)

        elif isinstance(stmt, (Expr, UnaryExpr, Literal, VarRef, FuncCall)):
            self.eval_expr_type(stmt, symtab)

        else:
            raise SemanticError(f"Unhandled statement in semantic analyzer: {stmt}")

    def eval_expr_type(self, expr, symtab) -> str:
        """Evaluate the type of an expression."""
        if isinstance(expr, Literal):
            return expr.typ
        if isinstance(expr, VarRef):
            if expr.name not in symtab:
                raise SemanticError(f"Use of undeclared variable {expr.name}")
            return symtab[expr.name].typ
        if isinstance(expr, Assignment):
            if expr.target not in symtab:
                raise SemanticError(f"Assignment to undeclared variable {expr.target}")
            rtype = self.eval_expr_type(expr.value, symtab)
            if not self.type_compatible(symtab[expr.target].typ, rtype):
                raise SemanticError(f"Type mismatch in assignment to {expr.target}: {symtab[expr.target].typ} <- {rtype}")
            return symtab[expr.target].typ
        if isinstance(expr, UnaryExpr):
            et = self.eval_expr_type(expr.expr, symtab)
            if expr.op == '!':
                if et != 'bool':
                    raise SemanticError(f"'!' operator needs bool, got {et}")
                return 'bool'

            return et
        if isinstance(expr, Expr):
            lt = self.eval_expr_type(expr.left, symtab)
            rt = self.eval_expr_type(expr.right, symtab)
            if expr.op in ('+','-','*','/','%'):
                if lt == 'float' or rt == 'float':
                    return 'float'
                return 'int'
            if expr.op in ('<','>','<=','>=','==','!='):
                return 'bool'
            if expr.op in ('&&','||'):
                return 'bool'
            return 'int'
        if isinstance(expr, FuncCall):
            if expr.name == 'print':
                return 'void'
            if expr.name == 'read':
                if not expr.args or not isinstance(expr.args[0], VarRef):
                    raise SemanticError('read expects a variable')
                if expr.args[0].name not in symtab:
                    raise SemanticError(f"read on undeclared variable {expr.args[0].name}")
                return 'void'
            if expr.name not in self.functions:
                raise SemanticError(f"Call to undefined function {expr.name}")
            return self.functions[expr.name].ret_type
        raise SemanticError(f"Unable to determine expression type for {expr}")

    def type_compatible(self, dest: str, src: str) -> bool:
        """Check if source type is compatible with destination type."""
        if dest == src:
            return True
        if dest == 'float' and src == 'int':
            return True
        if dest == 'int' and src == 'char':
            return True
        if dest == 'char' and src == 'int':
            return True
        return False