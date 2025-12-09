# MiniC Compiler

A simple compiler for MiniC, a subset of the C programming language, implemented in Python. This project demonstrates the key phases of compiler construction: lexical analysis, parsing, semantic analysis, intermediate representation generation, and interpretation.

## Features

- **Lexical Analysis**: Tokenizes MiniC source code into meaningful symbols.
- **Parsing**: Builds an Abstract Syntax Tree (AST) from tokens using recursive descent.
- **Semantic Analysis**: Performs type checking and ensures semantic correctness.
- **Intermediate Representation (IR)**: Generates Three-Address Code (TAC) for optimization and code generation.
- **TAC Printing**: Outputs TAC in various formats (standard, quadruples, triples, postfix).
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
├── MiniC/
│   ├── ast_nodes.py      # AST node definitions
│   ├── lexer.py          # Lexical analyzer
│   ├── parser.py         # Parser for MiniC grammar
│   ├── semantic.py       # Semantic analyzer
│   ├── ir_generator.py   # Intermediate representation generator
│   ├── tac_printer.py    # TAC output formatter
│   └── interpreter.py    # Interpreter for executing MiniC programs
├── test1.mc to test5.mc  # Sample MiniC programs
├── firstCode.mc          # Additional test file
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

### Running the Compiler

The compiler can be used programmatically by importing the modules. Here's a basic example:

```python
from MiniC.lexer import Lexer
from MiniC.parser import Parser
from MiniC.semantic import SemanticAnalyzer
from MiniC.interpreter import Interpreter

# Read MiniC source code
with open('test1.mc', 'r') as f:
    source = f.read()

# Lexical analysis
lexer = Lexer(source)
tokens = lexer.tokenize()

# Parsing
parser = Parser(tokens)
ast = parser.parse()

# Semantic analysis
analyzer = SemanticAnalyzer(ast)
analyzer.analyze()

# Interpretation
interpreter = Interpreter()
interpreter.interpret(ast)
```

### Generating TAC

To generate and print Three-Address Code:

```python
from MiniC.ir_generator import IRGenerator
from MiniC.tac_printer import print_tac

ir_gen = IRGenerator()
tac_instructions = ir_gen.generate(ast)
print(print_tac(tac_instructions, format_type='quadruples'))
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
python -c "
from MiniC.lexer import Lexer
from MiniC.parser import Parser
from MiniC.semantic import SemanticAnalyzer
from MiniC.interpreter import Interpreter

for i in range(1, 6):
    print(f'Testing test{i}.mc:')
    with open(f'test{i}.mc', 'r') as f:
        source = f.read()
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    analyzer = SemanticAnalyzer(ast)
    analyzer.analyze()
    interpreter = Interpreter()
    interpreter.interpret(ast)
    print()
"
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

