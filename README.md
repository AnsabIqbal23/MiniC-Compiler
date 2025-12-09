# MiniC Compiler

A simple compiler for MiniC, a subset of the C programming language, implemented in Python. This project demonstrates the key phases of compiler construction: lexical analysis, parsing, semantic analysis, intermediate representation generation, and interpretation.

## Features

- **Lexical Analysis**: Tokenizes MiniC source code into meaningful symbols.
- **Parsing**: Builds an Abstract Syntax Tree (AST) from tokens using recursive descent.
- **Semantic Analysis**: Performs type checking and ensures semantic correctness.
- **Intermediate Representation (IR)**: Generates Three-Address Code (TAC) for optimization and code generation.
- **Optimization**: Applies various TAC optimizations including constant folding, propagation, common subexpression elimination, and dead code elimination.
- **TAC Printing**: Outputs TAC in various formats (standard, quadruples, triples, postfix).
- **Code Generation**: Generates pseudo-assembly code from optimized TAC.
- **Interpretation**: Executes MiniC programs directly from the AST.
- **Supported Constructs**:
  - Data types: `int`, `float`, `char`, `bool`, `void`
  - Control structures: `if`, `while`, `for`
  - Functions with parameters and return values
  - Variable declarations and assignments
  - Arithmetic, relational, and logical operators
  - Built-in functions: `print()` and `read()`

## Project Structure

```
MiniC-Compiler/
├── main.py               # Main compiler driver with command-line interface
├── MiniC/
│   ├── ast_nodes.py      # AST node definitions
│   ├── lexer.py          # Lexical analyzer
│   ├── parser.py         # Parser for MiniC grammar
│   ├── semantic.py       # Semantic analyzer
│   ├── ir_generator.py   # Intermediate representation generator
│   ├── optimizer.py      # TAC optimizer
│   ├── dag_generator.py  # DAG generator for CSE
│   ├── tac_printer.py    # TAC output formatter
│   ├── codegen.py        # Code generator for pseudo-assembly
│   └── interpreter.py    # Interpreter for executing MiniC programs
├── test1.mc to test6.mc  # Sample MiniC programs
├── firstCode.mc          # Additional test file
├── Second.mc             # Another test file
└── README.md             # This file
```

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/AnsabIqbal23/MiniC-Compiler.git
   cd MiniC-Compiler
   ```

2. Ensure Python 3.6+ is installed on your system.

3. No additional dependencies are required beyond the Python standard library.

## Usage

### Command-Line Interface

The compiler includes a command-line interface via `main.py`. You can compile and run MiniC files with various options:

```bash
python main.py test1.mc --tokens --ast --tac --optimized --codegen
```

Available flags:
- `--tokens`: Print tokenized input
- `--ast`: Print abstract syntax tree
- `--symbol-table`: Print symbol table
- `--tac`: Print three-address code
- `--optimized`: Print optimized TAC
- `--codegen`: Generate and print assembly code

### Programmatic Usage

The compiler can be used programmatically by importing the modules. Here's a basic example:

```python
from main import compile_and_run

# Read and compile MiniC source code
with open('test1.mc', 'r') as f:
    source = f.read()

# Compile and run with flags
result = compile_and_run(source, flags={'tac': True, 'optimized': True})
```

### Generating TAC

To generate and print Three-Address Code:

```python
from MiniC.lexer import tokenize
from MiniC.parser import Parser
from MiniC.semantic import SemanticAnalyzer
from MiniC.ir_generator import IRGenerator
from MiniC.optimizer import TACOptimizer
from MiniC.tac_printer import TACPrinter

# Process source to TAC
toks = tokenize(source)
p = Parser(toks)
prog = p.parse()
sa = SemanticAnalyzer(prog)
sa.analyze()
ir_gen = IRGenerator()
tac = ir_gen.generate(prog)
optimizer = TACOptimizer(tac)
optimized_tac = optimizer.optimize()

# Print TAC
printer = TACPrinter()
print(printer.print_quadruples(optimized_tac))
```

## Examples

### Hello World

```c
int main() {
    print(42);
    return 0;
}
```

### Factorial

```c
int factorial(int n) {
    if (n <= 1) {
        return 1;
    }
    return n * factorial(n - 1);
}

int main() {
    int result = factorial(5);
    print(result);
    return 0;
}
```

### Input and Output

```c
int main() {
    int x;
    read(x);
    int y = x * 2;
    print(y);
    return 0;
}
```

## Testing

Run the provided test files to verify the compiler's functionality:

```bash
# Test all sample files
for file in test*.mc; do
    echo "Testing $file:"
    python main.py "$file"
    echo
done
```

Or test individual files with debugging flags:

```bash
python main.py test1.mc --tokens --ast --tac --optimized
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- This project was developed as part of a compiler construction course.
- Inspired by various compiler textbooks and online resources on language implementation.

