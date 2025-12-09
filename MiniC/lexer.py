# lexer.py
"""
Lexer module for the MiniC compiler.

This module defines the token specifications and provides a tokenize function
to convert MiniC source code into a list of tokens.
"""

import re
from dataclasses import dataclass
from typing import List, Optional

# Token specifications: each tuple is (regex pattern, token type)
# Patterns that match None are ignored (whitespace, comments)
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

# Compile the master regex pattern from TokenSpec
master_pat = re.compile('|'.join('(?P<T%d>%s)' % (i, p[0]) for i, p in enumerate(TokenSpec)), re.S)

@dataclass
class Token:
    """Represents a token with type, value, line number, and column."""
    type: str
    value: str
    lineno: int
    col: int

def tokenize(code: str) -> List[Token]:
    """
    Tokenize the given MiniC source code into a list of Token objects.

    Args:
        code (str): The source code to tokenize.

    Returns:
        List[Token]: A list of tokens, ending with an EOF token.
    """
    tokens: List[Token] = []
    line_no = 1
    line_start = 0
    for m in master_pat.finditer(code):
        kind = None
        value = m.group(0)
        # Find which token spec matched
        for i, spec in enumerate(TokenSpec):
            if m.lastgroup == f'T{i}':
                kind = spec[1]
                break
        if kind is None:
            pass  # Skip ignored tokens (whitespace, comments)
        else:
            col = m.start() - line_start + 1
            tokens.append(Token(kind, value, line_no, col))
        # Update line number and line start position
        line_no += value.count('\n')
        if '\n' in value:
            line_start = m.end()
    # Add EOF token
    tokens.append(Token('EOF', '', line_no, 1))
    return tokens
