# ast_nodes.py
from dataclasses import dataclass
from typing import List, Optional, Any, Tuple

class ASTNode:
    """Base class for all AST nodes."""
    pass

@dataclass
class Program(ASTNode):
    """Represents the entire MiniC program with a list of functions."""
    functions: List[Any]

    def __str__(self):
        return '\n'.join(str(f) for f in self.functions)

@dataclass
class Function(ASTNode):
    """Represents a function definition with return type, name, parameters, and body."""
    ret_type: str
    name: str
    params: List[Tuple[str, str]]
    body: Any

    def __str__(self):
        params_str = ', '.join(f"{t} {n}" for t, n in self.params)
        return f"{self.ret_type} {self.name}({params_str}) {self.body}"

@dataclass
class Block(ASTNode):
    """Represents a block of statements."""
    statements: List[Any]

    def __str__(self):
        return '{\n' + '\n'.join(f"  {str(s)}" for s in self.statements) + '\n}'

@dataclass
class VarDecl(ASTNode):
    """Represents a variable declaration with optional initialization."""
    var_type: str
    name: str
    init: Optional[Any]

    def __str__(self):
        init_str = f" = {self.init}" if self.init else ""
        return f"{self.var_type} {self.name}{init_str};"

@dataclass
class Assignment(ASTNode):
    """Represents an assignment statement."""
    target: str
    value: Any

    def __str__(self):
        return f"{self.target} = {self.value};"

@dataclass
class IfStmt(ASTNode):
    """Represents an if statement with optional else branch."""
    cond: Any
    then_branch: Any
    else_branch: Optional[Any]

    def __str__(self):
        else_str = f" else {self.else_branch}" if self.else_branch else ""
        return f"if ({self.cond}) {self.then_branch}{else_str}"

@dataclass
class WhileStmt(ASTNode):
    """Represents a while loop."""
    cond: Any
    body: Any

    def __str__(self):
        return f"while ({self.cond}) {self.body}"

@dataclass
class ForStmt(ASTNode):
    """Represents a for loop with optional init, condition, and update."""
    init: Optional[Any]
    cond: Optional[Any]
    update: Optional[Any]
    body: Any

    def __str__(self):
        init_str = str(self.init) if self.init else ";"
        cond_str = str(self.cond) if self.cond else ""
        update_str = str(self.update) if self.update else ""
        return f"for ({init_str} {cond_str}; {update_str}) {self.body}"

@dataclass
class ReturnStmt(ASTNode):
    """Represents a return statement with optional expression."""
    expr: Optional[Any]

    def __str__(self):
        expr_str = f" {self.expr}" if self.expr else ""
        return f"return{expr_str};"

@dataclass
class Expr(ASTNode):
    """Represents a binary expression with operator and operands."""
    op: Optional[str]
    left: Any
    right: Any

    def __str__(self):
        return f"({self.left} {self.op} {self.right})"

@dataclass
class UnaryExpr(ASTNode):
    """Represents a unary expression with operator and operand."""
    op: str
    expr: Any

    def __str__(self):
        return f"({self.op}{self.expr})"

@dataclass
class Literal(ASTNode):
    """Represents a literal value with its type."""
    value: Any
    typ: str

    def __str__(self):
        return str(self.value)

@dataclass
class VarRef(ASTNode):
    """Represents a variable reference."""
    name: str

    def __str__(self):
        return self.name

@dataclass
class FuncCall(ASTNode):
    """Represents a function call with name and arguments."""
    name: str
    args: List[Any]

    def __str__(self):
        args_str = ', '.join(str(a) for a in self.args)
        return f"{self.name}({args_str})"
