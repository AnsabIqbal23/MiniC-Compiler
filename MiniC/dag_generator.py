# dag_generator.py
"""
DAG Generator for Expression Optimization in MiniC Compiler.

This module builds a Directed Acyclic Graph (DAG) for expressions
to facilitate Common Subexpression Elimination (CSE) and other optimizations.
"""

from typing import Dict, List, Tuple, Any
from MiniC.ir_generator import TACInstruction

class DAGNode:
    """Represents a node in the expression DAG."""
    def __init__(self, op: str, left: Any = None, right: Any = None, value: Any = None):
        self.op = op  # 'const', 'var', or operator like '+', '-', etc.
        self.left = left  # Left child
        self.right = right  # Right child
        self.value = value  # For constants or variables
        self.users: List[DAGNode] = []  # Nodes that use this node
        self.temp_var = None  # Assigned temporary variable

    def __eq__(self, other):
        if not isinstance(other, DAGNode):
            return False
        return (self.op == other.op and
                self.left == other.left and
                self.right == other.right and
                self.value == other.value)

    def __hash__(self):
        return hash((self.op, self.left, self.right, self.value))

    def __str__(self):
        if self.op == 'const':
            return str(self.value)
        elif self.op == 'var':
            return self.value
        elif self.op in ('+', '-', '*', '/', '%', '&&', '||', '<', '>', '<=', '>=', '==', '!='):
            return f"({self.left} {self.op} {self.right})"
        elif self.op in ('-', '!'):
            return f"({self.op} {self.left})"
        else:
            return f"{self.op}({self.left}, {self.right})"

class DAGGenerator:
    """Generates DAG from TAC instructions for expression optimization."""

    def __init__(self):
        self.nodes: Dict[Tuple, DAGNode] = {}  # Map from (op, left, right) to node
        self.var_to_node: Dict[str, DAGNode] = {}  # Variable to its current node
        self.node_list: List[DAGNode] = []

    def build_dag(self, instructions: List[TACInstruction]) -> List[DAGNode]:
        """Build DAG from TAC instructions."""
        self.nodes = {}
        self.var_to_node = {}
        self.node_list = []

        for instr in instructions:
            self.process_instruction(instr)

        return self.node_list

    def process_instruction(self, instr: TACInstruction):
        """Process a single TAC instruction and add to DAG."""
        if instr.op == 'assign':
            # dest = src1
            if instr.src1 in self.var_to_node:
                node = self.var_to_node[instr.src1]
            else:
                # Assume src1 is a constant or variable
                node = self.get_or_create_node('var', value=instr.src1)
            self.var_to_node[instr.dest] = node
            node.temp_var = instr.dest

        elif instr.op == 'binop':
            # dest = src1 op src2
            parts = instr.src2.split(' ', 1)
            op = parts[0]
            right_operand = parts[1]
            left_node = self.get_operand_node(instr.src1)
            right_node = self.get_operand_node(right_operand)
            node = self.get_or_create_node(op, left_node, right_node)
            self.var_to_node[instr.dest] = node
            node.temp_var = instr.dest

        elif instr.op == 'unop':
            # dest = op src2
            operand_node = self.get_operand_node(instr.src2)
            node = self.get_or_create_node(instr.src1, operand_node)  # op is src1
            self.var_to_node[instr.dest] = node
            node.temp_var = instr.dest

        # For control flow, labels, jumps, etc., we can skip or handle differently
        # For now, focus on expressions

    def get_operand_node(self, operand: str) -> DAGNode:
        """Get the DAG node for an operand (variable or constant)."""
        if operand in self.var_to_node:
            return self.var_to_node[operand]
        else:
            # Assume it's a constant or new variable
            return self.get_or_create_node('var', value=operand)

    def get_or_create_node(self, op: str, left: DAGNode = None, right: DAGNode = None, value: Any = None) -> DAGNode:
        """Get existing node or create new one."""
        key = (op, left, right, value)
        if key in self.nodes:
            return self.nodes[key]
        node = DAGNode(op, left, right, value)
        self.nodes[key] = node
        self.node_list.append(node)
        if left:
            left.users.append(node)
        if right:
            right.users.append(node)
        return node

    def detect_cse(self) -> Dict[DAGNode, List[str]]:
        """Detect common subexpressions by finding nodes with multiple users."""
        cse = {}
        for node in self.node_list:
            if len(node.users) > 1 and node.temp_var:
                cse[node] = [node.temp_var] + [u.temp_var for u in node.users if u.temp_var]
        return cse

def print_dag(self) -> str:
    """Print the DAG structure."""
    lines = []
    for i, node in enumerate(self.node_list):
        lines.append(f"Node {i}: {node}")
        if node.temp_var:
            lines.append(f"  Assigned to: {node.temp_var}")
        if node.users:
            users = [str(u) for u in node.users]
            lines.append(f"  Used by: {', '.join(users)}")
    return '\n'.join(lines)