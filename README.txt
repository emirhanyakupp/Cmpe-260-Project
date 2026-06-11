CmpE 260 - Project 1
Mini Programming Language Interpreter
======================================

Author(s):
  Emirhan Yakup Altuntaş, 2023400084
  Efe Dikilitaş, 2023400045

--------------------------------------
HOW TO RUN
--------------------------------------

Requirements: Python 3.8 or higher. No external libraries required.

Default static scoping:
  python interpreter.py <program.txt>

Explicit static scoping:
  python interpreter.py --scope static <program.txt>

Dynamic scoping:
  python interpreter.py --scope dynamic <program.txt>

Examples:
  python interpreter.py examples/basics.txt
  python interpreter.py examples/recursion.txt
  python interpreter.py examples/closures.txt
  python interpreter.py examples/scope.txt
  python interpreter.py examples/higher_order.txt
  python interpreter.py examples/lists.txt
  python interpreter.py --scope static examples/dynamic_scope.txt
  python interpreter.py --scope dynamic examples/dynamic_scope.txt

Exit codes:
  0  - success
  1  - runtime or syntax error (error message printed to stderr)

--------------------------------------
DELIVERABLES
--------------------------------------

  grammar.txt          - BNF grammar (D1)
  ast.txt              - AST node design (D2)
  interpreter.py       - Interpreter source (D3)
  examples/
    basics.txt         - Variable declarations, arithmetic, comparisons
    recursion.txt      - Recursive factorial and fibonacci
    closures.txt       - Closures with captured variables
    scope.txt          - Static scoping demonstration
    higher_order.txt   - Higher-order functions
    lists.txt          - B3 lists, indexing, length, append
    dynamic_scope.txt  - B4 static vs dynamic scoping behavior
  report.pdf           - Design report (D5)
  README.txt           - This file

--------------------------------------
IMPLEMENTATION NOTES
--------------------------------------

  Evaluation: Call-by-value / eager evaluation
  Scoping:    Static lexical by default; dynamic available with --scope dynamic
  Language:   Python 3

  The interpreter follows the pipeline:
    Source -> Lexer -> Token list -> Parser -> AST -> Evaluator -> Output

--------------------------------------
IMPLEMENTED BONUS FEATURES
--------------------------------------

  B1 Strings
    - Double-quoted string literals
    - Escape sequences: \n, \t, \\, \" 
    - String concatenation with + when both operands are strings
    - length(s) built-in for strings

  B2 While loops
    - Syntax: while condition do block end
    - Condition must evaluate to a boolean

  B3 Lists
    - List literals: [], [1, 2, 3]
    - Nested lists are supported
    - Indexing: xs[0], xs[length(xs) - 1]
    - length(xs) returns the number of list elements
    - append(xs, value) mutates xs and returns the same list

  B4 Static/Dynamic scoping
    - Default: static lexical scoping
    - --scope static uses closure definition-time environment
    - --scope dynamic uses call-site environment
