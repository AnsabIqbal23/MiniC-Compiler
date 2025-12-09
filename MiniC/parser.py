# parser.py
from typing import List, Tuple, Any, Optional
from MiniC.lexer import Token
from MiniC.ast_nodes import *
from MiniC.lexer import tokenize

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
        init = None
        if not (self.peek().type=='SYM' and self.peek().value==';'):
            if self.peek().type in ('INT_KW','FLOAT_KW','CHAR_KW','BOOL_KW'):
                init = self.parse_vardecl()
            else:
                init = self.parse_expr_statement()
        else:
            self.expect('SYM',';')
        cond = None
        if not (self.peek().type=='SYM' and self.peek().value==';'):
            cond = self.parse_expression()
        self.expect('SYM',';')
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
        return FuncCall('read', [VarRef(var_tok.value)])

    def parse_expression(self, min_prec=0):
        tok = self.peek()
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
