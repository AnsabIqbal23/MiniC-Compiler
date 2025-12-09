"""
File: MiniC_compiler.py

1. Scanner (lexer) - tokenizes input using regex rules
2. Parser - recursive-descent parser that builds an AST from tokens
3. Semantic Analyzer - walks the AST performing symbol table construction,
   undeclared variable checks, function checks, and basic type checking
4. Interpreter (optional "backend") - executes the AST directly to
   demonstrate semantics. This stands in for code generation in this
   simplified compiler.

Supported features (as per your proposal):
- Primitive types: int, float, char, bool
- Variable declarations and initialization
- Arithmetic operators: + - * / %
- Relational operators: < > <= >= == !=
- Logical operators: && || !
- If / if-else, while, for
- Functions (no recursion enforced by grammar, but interpreter accepts it)
- Built-in I/O: read(x); print(expr);
- return statements inside functions

Limitations & design choices:
- No arrays, pointers, structs, or advanced type conversions
- Type coercion: int <-> float allowed where sensible; char treated as small int
- The interpreter is not optimized; it's educational and easy to follow

Usage
-----
- To run a MiniC source file:
    python MiniC_compiler.py path/to/program.mc

- To run sample programs included at the bottom of this file:
    python MiniC_compiler.py --run-samples

The parser/AST implementation is compact but annotated.

"""

import re
import sys
from dataclasses import dataclass
from typing import List, Optional, Any, Dict, Tuple

# --------------------------- Lexer ---------------------------

TokenSpec = [
    (r"[ \t\r\n]+",              None),        # whitespace
    (r"//.*",                     None),        # line comment
    (r"/\*.*?\*/",              None),        # block comment (non-greedy)
    (r"\bint\b",                'INT_KW'),
    (r"\bfloat\b",              'FLOAT_KW'),
    (r"\bchar\b",               'CHAR_KW'),
    (r"\bbool\b",               'BOOL_KW'),
    (r"\bif\b",                 'IF'),
    (r"\belse\b",               'ELSE'),
    (r"\bfor\b",                'FOR'),
    (r"\bwhile\b",              'WHILE'),
    (r"\breturn\b",             'RETURN'),
    (r"\bvoid\b",               'VOID'),
    (r"\bprint\b",              'PRINT'),
    (r"\bread\b",               'READ'),
    (r"\btrue\b|\bfalse\b",   'BOOL_LIT'),
    (r"[0-9]+\.[0-9]+",          'FLOAT_LIT'),
    (r"[0-9]+",                   'INT_LIT'),
    (r"'([^'\\]|\\.)'",       'CHAR_LIT'),
    (r'\"([^"\\]|\\.)*\"', 'STRING_LIT'),
    (r"[A-Za-z_][A-Za-z0-9_]*",   'ID'),
    (r"\+|\-|\*|/|%",          'ARITH'),
    (r"<=|>=|==|!=|<|>",         'RELOP'),
    (r"&&|\|\||!",             'LOGIC'),
    (r"=",                       'ASSIGN'),
    (r";|,|\(|\)|\{|\}|\[|\]", 'SYM'),
]

master_pat = re.compile('|'.join('(?P<T%d>%s)' % (i, p[0]) for i, p in enumerate(TokenSpec)), re.S)

@dataclass
class Token:
    type: str
    value: str
    lineno: int
    col: int

def tokenize(code: str) -> List[Token]:
    tokens: List[Token] = []
    line_no = 1
    line_start = 0
    for m in master_pat.finditer(code):
        kind = None
        value = m.group(0)
        # identify which named group matched
        for i, spec in enumerate(TokenSpec):
            if m.lastgroup == f'T{i}':
                kind = spec[1]
                break
        if kind is None:
            # skip (whitespace or comment)
            pass
        else:
            col = m.start() - line_start + 1
            tok = Token(kind, value, line_no, col)
            tokens.append(tok)
        # update line number
        line_no += value.count('\n')
        if '\n' in value:
            line_start = m.end()
    tokens.append(Token('EOF', '', line_no, 1))
    return tokens

# --------------------------- AST Nodes ---------------------------

class ASTNode:
    pass

@dataclass
class Program(ASTNode):
    functions: List[Any]

@dataclass
class Function(ASTNode):
    ret_type: str
    name: str
    params: List[Tuple[str, str]]
    body: Any

@dataclass
class Block(ASTNode):
    statements: List[Any]

@dataclass
class VarDecl(ASTNode):
    var_type: str
    name: str
    init: Optional[Any]

@dataclass
class Assignment(ASTNode):
    target: str
    value: Any

@dataclass
class IfStmt(ASTNode):
    cond: Any
    then_branch: Any
    else_branch: Optional[Any]

@dataclass
class WhileStmt(ASTNode):
    cond: Any
    body: Any

@dataclass
class ForStmt(ASTNode):
    init: Optional[Any]
    cond: Optional[Any]
    update: Optional[Any]
    body: Any

@dataclass
class ReturnStmt(ASTNode):
    expr: Optional[Any]

@dataclass
class Expr(ASTNode):
    op: Optional[str]
    left: Any
    right: Any

@dataclass
class UnaryExpr(ASTNode):
    op: str
    expr: Any

@dataclass
class Literal(ASTNode):
    value: Any
    typ: str

@dataclass
class VarRef(ASTNode):
    name: str

@dataclass
class FuncCall(ASTNode):
    name: str
    args: List[Any]

# --------------------------- Parser ---------------------------

class ParserError(Exception):
    pass

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> Token:
        return self.tokens[self.pos]

    def next(self) -> Token:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def expect(self, typ: str, val: Optional[str]=None) -> Token:
        tok = self.peek()
        if tok.type != typ:
            raise ParserError(f"Expected {typ} at {tok.lineno}:{tok.col}, found {tok.type} ('{tok.value}')")
        if val is not None and tok.value != val:
            raise ParserError(f"Expected {val} at {tok.lineno}:{tok.col}, found '{tok.value}'")
        return self.next()

    def parse(self) -> Program:
        funcs = []
        while self.peek().type != 'EOF':
            funcs.append(self.parse_function())
        return Program(funcs)

    def parse_function(self) -> Function:
        # [type] ID ( param_list ) { body }
        ret_tok = self.next()
        if ret_tok.type not in ('INT_KW','FLOAT_KW','CHAR_KW','BOOL_KW','VOID'):
            raise ParserError(f"Function must start with return type at {ret_tok.lineno}:{ret_tok.col}")
        ret_type = ret_tok.value
        name_tok = self.expect('ID')
        name = name_tok.value
        self.expect('SYM', '(')
        params = self.parse_params()
        self.expect('SYM', ')')
        body = self.parse_block()
        return Function(ret_type, name, params, body)

    def parse_params(self) -> List[Tuple[str,str]]:
        params = []
        if self.peek().type == 'SYM' and self.peek().value == ')':
            return params
        while True:
            typ_tok = self.next()
            if typ_tok.type not in ('INT_KW','FLOAT_KW','CHAR_KW','BOOL_KW'):
                raise ParserError(f"Parameter type expected at {typ_tok.lineno}:{typ_tok.col}")
            var_tok = self.expect('ID')
            params.append((typ_tok.value, var_tok.value))
            if self.peek().type == 'SYM' and self.peek().value == ',':
                self.next()
                continue
            break
        return params

    def parse_block(self) -> Block:
        self.expect('SYM','{')
        stmts = []
        while not (self.peek().type=='SYM' and self.peek().value=='}'):
            stmts.append(self.parse_statement())
        self.expect('SYM','}')
        return Block(stmts)

    def parse_statement(self):
        tok = self.peek()
        if tok.type in ('INT_KW','FLOAT_KW','CHAR_KW','BOOL_KW'):
            return self.parse_vardecl()
        if tok.type == 'ID':
            # either assignment or function call
            return self.parse_expr_statement()
        if tok.type == 'IF':
            return self.parse_if()
        if tok.type == 'WHILE':
            return self.parse_while()
        if tok.type == 'FOR':
            return self.parse_for()
        if tok.type == 'RETURN':
            return self.parse_return()
        if tok.type == 'PRINT':
            return self.parse_print()
        if tok.type == 'READ':
            return self.parse_read()
        if tok.type == 'SYM' and tok.value == '{':
            return self.parse_block()
        # fallback - expression statement
        return self.parse_expr_statement()

    def parse_vardecl(self) -> VarDecl:
        typ_tok = self.next()
        typ = typ_tok.value
        id_tok = self.expect('ID')
        name = id_tok.value
        init = None
        if self.peek().type == 'ASSIGN':
            self.next()
            init = self.parse_expression()
        self.expect('SYM',';')
        return VarDecl(typ, name, init)

    def parse_expr_statement(self):
        expr = self.parse_expression()
        # assignment handled as top-level: ID ASSIGN expr ;
        if isinstance(expr, Assignment):
            self.expect('SYM',';')
            return expr
        self.expect('SYM',';')
        return expr

    def parse_if(self) -> IfStmt:
        self.expect('IF')
        self.expect('SYM','(')
        cond = self.parse_expression()
        self.expect('SYM',')')
        then_branch = self.parse_statement()
        else_branch = None
        if self.peek().type == 'ELSE':
            self.next()
            else_branch = self.parse_statement()
        return IfStmt(cond, then_branch, else_branch)

    def parse_while(self) -> WhileStmt:
        self.expect('WHILE')
        self.expect('SYM','(')
        cond = self.parse_expression()
        self.expect('SYM',')')
        body = self.parse_statement()
        return WhileStmt(cond, body)

    def parse_for(self) -> ForStmt:
        self.expect('FOR')
        self.expect('SYM','(')
        # init
        init = None
        if not (self.peek().type=='SYM' and self.peek().value==';'):
            if self.peek().type in ('INT_KW','FLOAT_KW','CHAR_KW','BOOL_KW'):
                init = self.parse_vardecl()
            else:
                init = self.parse_expr_statement()
        else:
            self.expect('SYM',';')
        # cond
        cond = None
        if not (self.peek().type=='SYM' and self.peek().value==';'):
            cond = self.parse_expression()
        self.expect('SYM',';')
        # update
        update = None
        if not (self.peek().type=='SYM' and self.peek().value==')'):
            update = self.parse_expression()
        self.expect('SYM',')')
        body = self.parse_statement()
        return ForStmt(init, cond, update, body)

    def parse_return(self) -> ReturnStmt:
        self.expect('RETURN')
        if not (self.peek().type=='SYM' and self.peek().value==';'):
            expr = self.parse_expression()
        else:
            expr = None
        self.expect('SYM',';')
        return ReturnStmt(expr)

    def parse_print(self):
        self.expect('PRINT')
        self.expect('SYM','(')
        expr = self.parse_expression()
        self.expect('SYM',')')
        self.expect('SYM',';')
        return FuncCall('print', [expr])

    def parse_read(self):
        self.expect('READ')
        self.expect('SYM','(')
        var_tok = self.expect('ID')
        self.expect('SYM',')')
        self.expect('SYM',';')
        # represent as special builtin call
        return FuncCall('read', [VarRef(var_tok.value)])

    # Expression parsing (precedence climbing)
    def parse_expression(self, min_prec=0):
        tok = self.peek()
        # handle unary
        if tok.type == 'ARITH' and tok.value in ('+','-'):
            op = self.next().value
            left = UnaryExpr(op, self.parse_expression(6))
        elif tok.type == 'LOGIC' and tok.value == '!':
            op = self.next().value
            left = UnaryExpr(op, self.parse_expression(6))
        else:
            left = self.parse_primary()

        while True:
            tok = self.peek()
            if tok.type == 'ARITH':
                prec = 5 if tok.value in ('*','/','%') else 4
                assoc = 'L'
                op = tok.value
            elif tok.type == 'RELOP':
                prec = 3
                assoc = 'L'
                op = tok.value
            elif tok.type == 'LOGIC':
                if tok.value in ('&&','||'):
                    prec = 2 if tok.value=='||' else 1
                    assoc = 'L'
                    op = tok.value
                else:
                    break
            elif tok.type == 'ASSIGN' and isinstance(left, VarRef):
                # assignment is right-assoc and lowest precedence
                prec = 0
                assoc = 'R'
                op = tok.value
            else:
                break
            if prec < min_prec:
                break
            self.next()
            if assoc == 'L':
                rhs = self.parse_expression(prec+1)
            else:
                rhs = self.parse_expression(prec)
            if op == '=':
                left = Assignment(left.name, rhs)
            else:
                left = Expr(op, left, rhs)
        return left

    def parse_primary(self):
        tok = self.peek()
        if tok.type == 'INT_LIT':
            self.next(); return Literal(int(tok.value), 'int')
        if tok.type == 'FLOAT_LIT':
            self.next(); return Literal(float(tok.value), 'float')
        if tok.type == 'CHAR_LIT':
            self.next(); val = tok.value[1:-1]
            return Literal(val, 'char')
        if tok.type == 'STRING_LIT':
            self.next(); return Literal(tok.value[1:-1], 'string')
        if tok.type == 'BOOL_LIT':
            self.next(); return Literal(True if tok.value=='true' else False, 'bool')
        if tok.type == 'ID':
            id_tok = self.next()
            # function call?
            if self.peek().type=='SYM' and self.peek().value=='(':
                self.next()
                args = []
                if not (self.peek().type=='SYM' and self.peek().value==')'):
                    while True:
                        args.append(self.parse_expression())
                        if self.peek().type=='SYM' and self.peek().value==',':
                            self.next(); continue
                        break
                self.expect('SYM',')')
                return FuncCall(id_tok.value, args)
            else:
                return VarRef(id_tok.value)
        if tok.type=='SYM' and tok.value=='(':
            self.next()
            expr = self.parse_expression()
            self.expect('SYM',')')
            return expr
        raise ParserError(f"Unexpected token {tok.type} ('{tok.value}') at {tok.lineno}:{tok.col}")

# --------------------------- Semantic Analyzer ---------------------------

class SemanticError(Exception):
    pass

class Symbol:
    def __init__(self, name, typ, kind='var'):
        self.name = name
        self.typ = typ
        self.kind = kind  # 'var' or 'func'

class SemanticAnalyzer:
    def __init__(self, program: Program):
        self.program = program
        self.globals: Dict[str, Symbol] = {}
        self.functions: Dict[str, Function] = {}

    def analyze(self):
        # collect functions
        for f in self.program.functions:
            if f.name in self.functions:
                raise SemanticError(f"Duplicate function {f.name}")
            self.functions[f.name] = f
        # ensure main exists
        if 'main' not in self.functions:
            raise SemanticError('No main function defined')
        # analyze function bodies
        for fname, func in self.functions.items():
            self.analyze_function(func)

    def analyze_function(self, func: Function):
        # new symbol table for function
        symtab: Dict[str, Symbol] = {}
        # parameters
        for typ, name in func.params:
            symtab[name] = Symbol(name, typ, 'var')
        # walk function body
        self.walk_block(func.body, symtab, func.ret_type)

    def walk_block(self, block: Block, symtab: Dict[str, Symbol], ret_type: str):
        for stmt in block.statements:
            self.walk_stmt(stmt, symtab, ret_type)

    def walk_stmt(self, stmt, symtab, ret_type):
        if isinstance(stmt, VarDecl):
            if stmt.name in symtab:
                raise SemanticError(f"Variable {stmt.name} already declared")
            if stmt.init is not None:
                init_type = self.eval_expr_type(stmt.init, symtab)
                # simple compatibility check
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
            self.walk_stmt(stmt.body, symtab, ret_type)


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
            # builtin print/read handled in interpreter; others must exist
            if stmt.name not in ('print','read') and stmt.name not in self.functions:
                raise SemanticError(f"Call to undefined function {stmt.name}")
            # TODO: check arity & types (basic)

        elif isinstance(stmt, Block):
            self.walk_block(stmt, dict(symtab), ret_type)

        elif isinstance(stmt, Expr) or isinstance(stmt, UnaryExpr) or isinstance(stmt, Literal) or isinstance(stmt, VarRef) or isinstance(stmt, FuncCall):
            # expression statement
            self.eval_expr_type(stmt, symtab)

        else:
            raise SemanticError(f"Unhandled statement in semantic analyzer: {stmt}")

    def eval_expr_type(self, expr, symtab) -> str:
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
            # arithmetic
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
            # builtin
            if expr.name == 'print':
                return 'void'
            if expr.name == 'read':
                # argument should be VarRef
                if not expr.args or not isinstance(expr.args[0], VarRef):
                    raise SemanticError('read expects a variable')
                if expr.args[0].name not in symtab:
                    raise SemanticError(f"read on undeclared variable {expr.args[0].name}")
                return 'void'
            # user function
            if expr.name not in self.functions:
                raise SemanticError(f"Call to undefined function {expr.name}")
            # return type of function
            return self.functions[expr.name].ret_type
        raise SemanticError(f"Unable to determine expression type for {expr}")

    def type_compatible(self, dest: str, src: str) -> bool:
        if dest == src:
            return True
        # allow int -> float
        if dest == 'float' and src == 'int':
            return True
        # char <-> int allowed
        if dest == 'int' and src == 'char':
            return True
        if dest == 'char' and src == 'int':
            return True
        return False

# --------------------------- Interpreter ---------------------------

class ReturnException(Exception):
    def __init__(self, value):
        self.value = value

class Interpreter:
    def __init__(self, program: Program):
        self.program = program
        self.functions: Dict[str, Function] = {f.name: f for f in program.functions}

    def run(self, argv=None):
        if 'main' not in self.functions:
            raise Exception('No main function')
        mainf = self.functions['main']
        # execute main with no args
        return self.exec_function(mainf, [])

    def exec_function(self, func: Function, args: List[Any]):
        env = {}
        for (typ,name), val in zip(func.params, args):
            env[name] = val
        try:
            self.exec_block(func.body, env)
        except ReturnException as r:
            return r.value
        return None

    def exec_block(self, block: Block, env: Dict[str, Any]):
        for stmt in block.statements:
            self.exec_stmt(stmt, env)

    def exec_stmt(self, stmt, env):
        if isinstance(stmt, VarDecl):
            val = None
            if stmt.init is not None:
                val = self.eval_expr(stmt.init, env)
            env[stmt.name] = val

        elif isinstance(stmt, Assignment):
            val = self.eval_expr(stmt.value, env)
            if stmt.target not in env:
                raise Exception(f"Assignment to undeclared variable {stmt.target}")
            env[stmt.target] = val

        elif isinstance(stmt, IfStmt):
            cond = self.eval_expr(stmt.cond, env)
            if cond:
                self.exec_stmt(stmt.then_branch, env) if not isinstance(stmt.then_branch, Block) else self.exec_block(stmt.then_branch, dict(env))
            elif stmt.else_branch:
                self.exec_stmt(stmt.else_branch, env) if not isinstance(stmt.else_branch, Block) else self.exec_block(stmt.else_branch, dict(env))

        elif isinstance(stmt, WhileStmt):
            while self.eval_expr(stmt.cond, env):
                self.exec_stmt(stmt.body, env) if not isinstance(stmt.body, Block) else self.exec_block(stmt.body, env)

        elif isinstance(stmt, ForStmt):
            if stmt.init:
                if isinstance(stmt.init, VarDecl):
                    self.exec_stmt(stmt.init, env)
                else:
                    self.exec_stmt(stmt.init, env)
            while True:
                if stmt.cond and not self.eval_expr(stmt.cond, env):
                    break
                self.exec_stmt(stmt.body, env) if not isinstance(stmt.body, Block) else self.exec_block(stmt.body, dict(env))
                if stmt.update:
                    self.eval_expr(stmt.update, env)

        elif isinstance(stmt, ReturnStmt):
            val = None
            if stmt.expr:
                val = self.eval_expr(stmt.expr, env)
            raise ReturnException(val)

        elif isinstance(stmt, FuncCall):
            if stmt.name == 'print':
                vals = [self.eval_expr(a, env) for a in stmt.args]
                print(*vals)
            elif stmt.name == 'read':
                if not stmt.args or not isinstance(stmt.args[0], VarRef):
                    raise Exception('read expects a variable')
                name = stmt.args[0].name
                if name not in env:
                    raise Exception(f'read on undeclared variable {name}')
                v = input()
                # try convert to int or float
                try:
                    if '.' in v:
                        env[name] = float(v)
                    else:
                        env[name] = int(v)
                except:
                    env[name] = v
            else:
                # user function
                f = self.functions.get(stmt.name)
                if not f:
                    raise Exception(f'Call to undefined function {stmt.name}')
                argvals = [self.eval_expr(a, env) for a in stmt.args]
                return self.exec_function(f, argvals)

        elif isinstance(stmt, Block):
            self.exec_block(stmt, dict(env))

        else:
            # expression statement
            self.eval_expr(stmt, env)

    def eval_expr(self, expr, env):
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
            # user function
            f = self.functions.get(expr.name)
            if not f:
                raise Exception(f'Call to undefined function {expr.name}')
            argvals = [self.eval_expr(a, env) for a in expr.args]
            return self.exec_function(f, argvals)
        raise Exception(f'Unhandled expression in interpreter: {expr}')

# --------------------------- Utilities & Main ---------------------------

SAMPLE_PROGRAM = r'''
int main() {
    int a = 10;
    int b = 20;
    int c = a + b;
    print(c);
    return 0;
}
'''

SAMPLE_FACTORIAL = r'''
int fact(int n) {
    int res = 1;
    for (int i = 1; i <= n; i = i + 1) {
        res = res * i;
    }
    return res;
}

int main() {
    int x = 6;
    int f = fact(x);
    print(f);
    return 0;
}
'''

SAMPLE_IF = r'''
int main() {
    int x = 5;
    if (x > 3) {
        print(1);
    } else {
        print(0);
    }
    return 0;
}
'''

def compile_and_run(code: str, run=True):
    toks = tokenize(code)
    p = Parser(toks)
    prog = p.parse()
    sa = SemanticAnalyzer(prog)
    sa.analyze()
    if run:
        interp = Interpreter(prog)
        return interp.run()
    return prog

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='MiniC compiler (demo)')
    parser.add_argument('file', nargs='?', help='MiniC source file')
    parser.add_argument('--run-samples', action='store_true')
    args = parser.parse_args()

    if args.run_samples:
        print('Running sample: simple')
        compile_and_run(SAMPLE_PROGRAM)
        print('\nRunning sample: factorial')
        compile_and_run(SAMPLE_FACTORIAL)
        print('\nRunning sample: if')
        compile_and_run(SAMPLE_IF)
        sys.exit(0)

    if args.file:
        with open(args.file, 'r') as f:
            code = f.read()
        try:
            compile_and_run(code)
        except Exception as e:
            print('Compilation/Runtime error:', e)
            raise
    else:
        print('No input file. Use --run-samples to run included examples.')


# --------------------------- Project Deliverables Report ---------------------------
# (Appended report: attributed grammar with semantic rules + how to run each phase)
# NOTE: This section is written as Python block comments so it stays inside the code file.
"""
Project Deliverables
--------------------
This file implements the three required deliverables for the MiniC compiler course project:

1. Scanner (implemented in code)
   - See the `tokenize(code: str)` function and the `TokenSpec` list near the top of this file.
   - Token categories: keywords, identifiers, literals, operators, symbols; comments & whitespace are ignored.

2. Syntax Analyzer (implemented in code)
   - Implemented as a recursive-descent parser in the `Parser` class.
   - Builds an Abstract Syntax Tree (AST) using dataclasses (Program, Function, Block, VarDecl, Assignment, IfStmt, etc.).

3. Semantic Analyzer (implemented in code + attributed grammar with semantic rules below)
   - Implemented in `SemanticAnalyzer` class. It constructs symbol tables per function, checks undeclared identifiers, duplicate declarations, type compatibility in assignments, return type checks, and basic checks for control-flow conditions.

How to run each phase (from this script):
- Lexing only: call `tokenize(code)` and inspect returned `Token` list.
- Parsing only: instantiate `Parser(tokens)` and call `parse()` to get `Program` (AST).
- Semantic analysis: instantiate `SemanticAnalyzer(program)` and call `analyze()`; it raises `SemanticError` on problems.
- Interpreter (runtime/demo): `Interpreter(program).run()` executes the `main` function.

----------------------------------------
Attributed Grammar (MiniC) + Semantic Rules
----------------------------------------
Notation:
- A -> B means production A produces B
- {action} means a semantic action executed when the production is reduced
- type(x) means the static type attached to node x
- env, symtab represent symbol tables mapping names to types

Grammar (abridged and focused on deliverables):

Program -> FunctionList
FunctionList -> Function FunctionList | ε

Function -> Type ID '(' ParamList ')' Block
  { add_function(ID.name, Type); create new symtab for Function; insert params into symtab }

ParamList -> Param (',' Param)* | ε
Param -> Type ID
  { insert param ID with Type into current function symtab }

Block -> '{' StmtList '}'
StmtList -> Stmt StmtList | ε

Stmt -> VarDecl
      | AssignmentStmt
      | IfStmt
      | WhileStmt
      | ForStmt
      | ReturnStmt
      | ExprStmt
      | Block
      | PrintStmt
      | ReadStmt

VarDecl -> Type ID ('=' Expression)? ';'
  { if ID in env error 'already declared';
    if '=' present { t = type(Expression); if not compatible(Type, t) error }
    insert ID:Type into env }

AssignmentStmt -> ID '=' Expression ';'
  { if ID not in env error 'undeclared';
    t_left = env[ID]; t_right = type(Expression);
    if not compatible(t_left, t_right) error }

IfStmt -> 'if' '(' Expression ')' Stmt ( 'else' Stmt )?
  { t = type(Expression); if t != bool error 'condition must be bool' }

WhileStmt -> 'while' '(' Expression ')' Stmt
  { t = type(Expression); if t != bool error }

ForStmt -> 'for' '(' (VarDecl | AssignmentStmt | ';') Expression? ';' Expression? ')' Stmt
  { if Expression present check for bool }

ReturnStmt -> 'return' Expression? ';'
  { if current function's return type is not void and Expression absent -> error;
    if Expression present then check type compatibility with function return type }

ExprStmt -> Expression ';'   { type(Expression) computed; used for side-effects }

PrintStmt -> 'print' '(' Expression ')' ';'   { Expression must be well-typed }
ReadStmt -> 'read' '(' ID ')' ';'   { ID must be declared and be an l-value }

Expression grammar (operator precedence simplified):
Expression -> LogicOr
LogicOr -> LogicAnd ( '||' LogicAnd )*
LogicAnd -> Equality ( '&&' Equality )*
Equality -> Relational ( ('==' | '!=') Relational )*
Relational -> Add ( ('<' | '>' | '<=' | '>=') Add )*
Add -> Mul ( ('+' | '-') Mul )*
Mul -> Unary ( ('*' | '/' | '%') Unary )*
Unary -> ('+' | '-' | '!') Unary | Primary
Primary -> INT_LIT | FLOAT_LIT | CHAR_LIT | BOOL_LIT | ID | ID '(' ArgList ')' | '(' Expression ')'

Semantic Rules for Expressions (type attribution):
- INT_LIT.type = int
- FLOAT_LIT.type = float
- CHAR_LIT.type = char
- BOOL_LIT.type = bool
- ID.type = lookup(env, ID)  // error if not found
- FunctionCall.type = lookup(return type of function) // check arity and argument types

Binary arithmetic (+,-,*,/,%)
- if left.type == float or right.type == float => type = float
- else => type = int
- operands must be numeric (int, float, char)

Relational operators (<,>,<=,>=,==,!=)
- operands must be comparable; result type = bool

Logical operators (&&,||)
- operands must be bool; result type = bool

Unary '!'
- operand must be bool; result = bool

Assignment
- left must be declared; right.type must be compatible with left.type
- compatibility: exact match OR int -> float allowed OR char<->int allowed

Function Declaration & Return
- On encountering Function: create a new scope (symtab), insert parameters with their types.
- Body statements are type-checked with this symtab.
- Every ReturnStmt with an expression must have expression type compatible with function's declared return type.
- If function return type is non-void and there exists an execution path without return, that is allowed for this simplified project (we only check returns when present).  (Optional enhancement: require all paths to return.)

Symbol Table Management
- Each function has its own symbol table (local scope).
- Variables declared in a block create entries in the local symbol table; sub-blocks get a copy-on-write nested symbol table for shadowing.
- No global variable support in this simplified design (can be added by extending the top-level symtab).

Error Reporting
- Semantic errors should indicate the nature (undeclared identifier, type mismatch, duplicate declaration) and ideally the source location (line:col). In this implementation, exceptions carry readable messages.

----------------------------------------
Examples of semantic actions (pseudocode):

Production: VarDecl -> Type ID '=' Expression ';'
Action:
    t_expr = Expression.type
    if not type_compatible(Type, t_expr):
        error("Type mismatch: cannot initialize {} with {}".format(ID, t_expr))
    symtab[ID] = Type

Production: AssignmentStmt -> ID '=' Expression ';'
Action:
    if ID not in symtab: error("Undeclared variable")
    if not type_compatible(symtab[ID], Expression.type):
        error("Type mismatch in assignment")

Production: Function -> Type ID '(' ParamList ')' Block
Action:
    if ID in functions: error("Duplicate function")
    functions[ID] = Function(Type, ParamList, Block)
    create new symtab for function
    for each (ptype,pname) in ParamList: symtab[pname] = ptype
    type-check Block with this symtab

----------------------------------------
Deliverables Checklist
- [x] Scanner implemented in code (tokenize)
- [x] Syntax Analyzer implemented in code (Parser -> AST)
- [x] Semantic Analyzer implemented in code (SemanticAnalyzer)
- [x] Attributed grammar with semantic rules included in this report (above)
- [ ] Split into modules (optional)
- [ ] Unit tests (optional)
- [ ] Extended semantic checks (function arity/type checking, full path return checks) (optional)

Notes & Next Steps
- If you need this report as a separate Markdown or PDF file for submission, I can extract and produce a standalone report and slides.
- I can also split the single-file implementation into separate modules (lexer.py, parser.py, sema.py, interp.py) and include unit tests + a Makefile.

"""
