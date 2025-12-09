# lexer.py
import re
from dataclasses import dataclass
from typing import List, Optional

TokenSpec = [
    (r"[ \t\r\n]+",              None),        # whitespace
    (r"//[^\n]*",                None),  # safer: match everything until newline
    (r"/\*.*?\*/",               None),        # block comment (non-greedy)
    (r"\bint\b",                 'INT_KW'),
    (r"\bfloat\b",               'FLOAT_KW'),
    (r"\bchar\b",                'CHAR_KW'),
    (r"\bbool\b",                'BOOL_KW'),
    (r"\bif\b",                  'IF'),
    (r"\belse\b",                'ELSE'),
    (r"\bfor\b",                 'FOR'),
    (r"\bwhile\b",               'WHILE'),
    (r"\breturn\b",              'RETURN'),
    (r"\bvoid\b",                'VOID'),
    (r"\bprint\b",               'PRINT'),
    (r"\bread\b",                'READ'),
    (r"\btrue\b|\bfalse\b",      'BOOL_LIT'),
    (r"[0-9]+\.[0-9]+",          'FLOAT_LIT'),
    (r"[0-9]+",                  'INT_LIT'),
    (r"'([^'\\]|\\.)'",          'CHAR_LIT'),
    (r'\"([^"\\]|\\.)*\"',       'STRING_LIT'),
    (r"[A-Za-z_][A-Za-z0-9_]*",  'ID'),
    (r"\+|\-|\*|/|%",            'ARITH'),
    (r"<=|>=|==|!=|<|>",         'RELOP'),
    (r"&&|\|\||!",               'LOGIC'),
    (r"=",                      'ASSIGN'),
    (r";|,|\(|\)|\{|\}|\[|\]",   'SYM'),
]

master_pat = re.compile('|'.join('(?P<T%d>%s)' % (i, p[0]) for i, p in enumerate(TokenSpec)), re.S)

@dataclass
class Token:
    """Represents a lexical token with type, value, and position."""
    type: str
    value: str
    lineno: int
    col: int

def tokenize(code: str) -> List[Token]:
    """Tokenize the input MiniC code into a list of tokens."""
    tokens: List[Token] = []
    line_no = 1
    line_start = 0
    for m in master_pat.finditer(code):
        kind = None
        value = m.group(0)
        for i, spec in enumerate(TokenSpec):
            if m.lastgroup == f'T{i}':
                kind = spec[1]
                break
        if kind is None:
            pass
        else:
            col = m.start() - line_start + 1
            tokens.append(Token(kind, value, line_no, col))
        line_no += value.count('\n')
        if '\n' in value:
            line_start = m.end()
    tokens.append(Token('EOF', '', line_no, 1))
    return tokens
