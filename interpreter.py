# Emirhan Yakup Altuntaş, 2023400084
# Efe Dikilitaş, 2023400045
# Fill in the exact student ID before submission if needed.

# Interpreter implementation
# Evaluator uses Call-By-Value.
# Scoping mode: static lexical scoping by default, or dynamic scoping with --scope dynamic.
# Bonus: B1 (strings), B2 (while loops), B3 (lists), B4 (static/dynamic scoping flag)
import sys
import re

SCOPE_MODE = 'static'

# --- AST Nodes ---
class Node: pass

class NumberLit(Node):
    def __init__(self, value): self.value = value

class BoolLit(Node):
    def __init__(self, value): self.value = value

class StringLit(Node):
    def __init__(self, value): self.value = value  # str, escapes already resolved

class ListLit(Node):
    def __init__(self, elements): self.elements = elements

class Identifier(Node):
    def __init__(self, name): self.name = name

class BinOp(Node):
    def __init__(self, op, left, right):
        self.op, self.left, self.right = op, left, right

class UnaryOp(Node):
    def __init__(self, op, operand):
        self.op, self.operand = op, operand

class IfExpr(Node):
    def __init__(self, cond, then_branch, else_branch):
        self.cond, self.then_branch, self.else_branch = cond, then_branch, else_branch

class FunExpr(Node):
    def __init__(self, params, body):
        self.params, self.body = params, body

class CallExpr(Node):
    def __init__(self, func, args):
        self.func, self.args = func, args

class IndexExpr(Node):
    def __init__(self, collection, index):
        self.collection, self.index = collection, index

class LetStmt(Node):
    def __init__(self, name, value):
        self.name, self.value = name, value

class AssignStmt(Node):
    def __init__(self, name, value):
        self.name, self.value = name, value

class PrintStmt(Node):
    def __init__(self, expr):
        self.expr = expr

class WhileStmt(Node):
    def __init__(self, cond, body):
        self.cond, self.body = cond, body

class Block(Node):
    def __init__(self, statements, final_expr):
        self.statements, self.final_expr = statements, final_expr

# --- Lexer ---
KEYWORDS = {
    'let', 'fun', 'if', 'then', 'else', 'end',
    'and', 'or', 'not', 'true', 'false', 'print',
    'while', 'do', 'length', 'append'
}

BUILTINS = {'length', 'append'}
IDENTIFIER_RE = re.compile(r'[A-Za-z][A-Za-z0-9_]*')

def validate_identifier(name, context='identifier'):
    if not IDENTIFIER_RE.fullmatch(name):
        raise RuntimeError(f"Invalid {context}: '{name}'")
    if name in KEYWORDS:
        raise RuntimeError(f"Cannot use keyword '{name}' as {context}")
    return name

def decode_string(raw):
    """Decode escape sequences in a string literal without surrounding quotes."""
    result = []
    i = 0
    while i < len(raw):
        if raw[i] == '\\' and i + 1 < len(raw):
            c = raw[i + 1]
            if c == 'n':
                result.append('\n')
            elif c == 't':
                result.append('\t')
            elif c == '\\':
                result.append('\\')
            elif c == '"':
                result.append('"')
            else:
                result.append('\\')
                result.append(c)
            i += 2
        else:
            result.append(raw[i])
            i += 1
    return ''.join(result)

def lex(source_code):
    # Remove block comments (* ... *) - non-nested
    source_code = re.sub(r'\(\*.*?\*\)', '', source_code, flags=re.DOTALL)
    token_specification = [
        ('STRING',   r'"(?:[^"\\]|\\.)*"'),
        ('NUMBER',   r'\d+'),
        ('ID',       r'[A-Za-z][A-Za-z0-9_]*'),
        ('ARROW',    r'->'),
        ('OP2',      r'==|!=|<=|>='),
        ('OP1',      r'[+\-*/=<>(),;\[\]]'),
        ('SKIP',     r'[ \t\n\r]+'),
        ('MISMATCH', r'.'),
    ]
    tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specification)
    tokens = []
    for mo in re.finditer(tok_regex, source_code):
        kind, value = mo.lastgroup, mo.group()
        if kind == 'SKIP':
            continue
        if kind == 'MISMATCH':
            raise RuntimeError(f"Unexpected character: {repr(value)}")
        tokens.append(value)
    return tokens

# --- Parser ---
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def consume(self, expected=None):
        tok = self.peek()
        if expected is not None and tok != expected:
            raise RuntimeError(f"Expected '{expected}', got {repr(tok)}")
        if tok is None:
            raise RuntimeError('Unexpected end of input')
        self.pos += 1
        return tok

    def parse_program(self):
        block = self.parse_block()
        if self.peek() is not None:
            raise RuntimeError(f"Unexpected token at end: {repr(self.peek())}")
        return block

    def _consume_semi_if_present(self):
        if self.peek() == ';':
            self.consume(';')
        elif self.peek() not in (None, 'end', 'else'):
            raise RuntimeError(f"Expected ';', got {repr(self.peek())}")

    def parse_block(self):
        stmts = []
        final_expr = None

        while self.peek() and self.peek() not in ('end', 'else'):
            if self.peek() == 'let':
                stmts.append(self.parse_let())
                self._consume_semi_if_present()
            elif self.peek() == 'print':
                stmts.append(self.parse_print())
                self._consume_semi_if_present()
            elif self.peek() == 'while':
                stmts.append(self.parse_while())
                self._consume_semi_if_present()
            else:
                expr = self.parse_expr()

                if isinstance(expr, Identifier) and self.peek() == '=':
                    name = expr.name
                    self.consume('=')
                    val = self.parse_expr()
                    stmts.append(AssignStmt(name, val))
                    self._consume_semi_if_present()
                elif self.peek() == ';':
                    stmts.append(expr)
                    self.consume(';')
                else:
                    final_expr = expr
                    break

        return Block(stmts, final_expr)

    def parse_let(self):
        self.consume('let')
        name = validate_identifier(self.consume(), 'variable name')
        self.consume('=')
        val = self.parse_expr()
        return LetStmt(name, val)

    def parse_print(self):
        self.consume('print')
        self.consume('(')
        expr = self.parse_expr()
        self.consume(')')
        return PrintStmt(expr)

    def parse_while(self):
        self.consume('while')
        cond = self.parse_expr()
        self.consume('do')
        body = self.parse_block()
        self.consume('end')
        return WhileStmt(cond, body)

    def parse_expr(self):
        return self.parse_or()

    def parse_or(self):
        node = self.parse_and()
        while self.peek() == 'or':
            op = self.consume()
            node = BinOp(op, node, self.parse_and())
        return node

    def parse_and(self):
        node = self.parse_comp()
        while self.peek() == 'and':
            op = self.consume()
            node = BinOp(op, node, self.parse_comp())
        return node

    def parse_comp(self):
        node = self.parse_add()
        if self.peek() in ('==', '!=', '<', '>', '<=', '>='):
            op = self.consume()
            node = BinOp(op, node, self.parse_add())
        return node

    def parse_add(self):
        node = self.parse_mul()
        while self.peek() in ('+', '-'):
            op = self.consume()
            node = BinOp(op, node, self.parse_mul())
        return node

    def parse_mul(self):
        node = self.parse_unary()
        while self.peek() in ('*', '/'):
            op = self.consume()
            node = BinOp(op, node, self.parse_unary())
        return node

    def parse_unary(self):
        if self.peek() in ('not', '-'):
            op = self.consume()
            return UnaryOp(op, self.parse_unary())
        return self.parse_postfix()

    def parse_postfix(self):
        node = self.parse_primary()
        while True:
            if self.peek() == '(':
                self.consume('(')
                args = []
                if self.peek() != ')':
                    args.append(self.parse_expr())
                    while self.peek() == ',':
                        self.consume(',')
                        args.append(self.parse_expr())
                self.consume(')')
                node = CallExpr(node, args)
            elif self.peek() == '[':
                self.consume('[')
                index = self.parse_expr()
                self.consume(']')
                node = IndexExpr(node, index)
            else:
                break
        return node

    def parse_list_literal(self):
        self.consume('[')
        elements = []
        if self.peek() != ']':
            elements.append(self.parse_expr())
            while self.peek() == ',':
                self.consume(',')
                elements.append(self.parse_expr())
        self.consume(']')
        return ListLit(elements)

    def parse_primary(self):
        tok = self.peek()
        if tok is None:
            raise RuntimeError('Unexpected end of input')

        if tok.startswith('"'):
            self.consume()
            return StringLit(decode_string(tok[1:-1]))

        if re.fullmatch(r'\d+', tok):
            self.consume()
            return NumberLit(int(tok))

        if tok == 'true':
            self.consume()
            return BoolLit(True)

        if tok == 'false':
            self.consume()
            return BoolLit(False)

        if tok == '[':
            return self.parse_list_literal()

        if tok == 'if':
            self.consume()
            cond = self.parse_expr()
            self.consume('then')
            then_b = self.parse_block()
            self.consume('else')
            else_b = self.parse_block()
            self.consume('end')
            return IfExpr(cond, then_b, else_b)

        if tok == 'fun':
            self.consume()
            self.consume('(')
            params = []
            if self.peek() != ')':
                params.append(validate_identifier(self.consume(), 'parameter name'))
                while self.peek() == ',':
                    self.consume(',')
                    params.append(validate_identifier(self.consume(), 'parameter name'))
            if len(params) != len(set(params)):
                raise RuntimeError('Duplicate parameter name')
            self.consume(')')
            self.consume('->')
            body = self.parse_block()
            self.consume('end')
            return FunExpr(params, body)

        if tok == '(':
            self.consume()
            expr = self.parse_expr()
            self.consume(')')
            return expr

        # Identifiers and built-in functions.
        # Built-ins are reserved, but accepted only as direct call targets.
        if IDENTIFIER_RE.fullmatch(tok):
            if tok in KEYWORDS and tok not in BUILTINS:
                raise RuntimeError(f"Unexpected reserved keyword: '{tok}'")
            if tok in BUILTINS and not (self.pos + 1 < len(self.tokens) and self.tokens[self.pos + 1] == '('):
                raise RuntimeError(f"Built-in '{tok}' must be called")
            self.consume()
            return Identifier(tok)

        raise RuntimeError(f"Unexpected token: {repr(tok)}")

# --- Environment & Closure ---
class Environment:
    def __init__(self, parent=None):
        self.bindings = {}
        self.parent = parent

    def extend(self, name, value):
        self.bindings[name] = value

    def lookup(self, name):
        if name in self.bindings:
            return self.bindings[name]
        if self.parent:
            return self.parent.lookup(name)
        raise RuntimeError(f"Undefined variable: '{name}'")

    def update(self, name, value):
        if name in self.bindings:
            self.bindings[name] = value
            return
        if self.parent:
            self.parent.update(name, value)
            return
        raise RuntimeError(f"Assignment to undefined variable: '{name}'")

class Closure:
    def __init__(self, params, body, env):
        self.params = params
        self.body = body
        self.env = env

# --- Evaluator ---
def evaluate(node, env):
    if isinstance(node, NumberLit):
        return node.value

    if isinstance(node, BoolLit):
        return node.value

    if isinstance(node, StringLit):
        return node.value

    if isinstance(node, ListLit):
        return [evaluate(element, env) for element in node.elements]

    if isinstance(node, Identifier):
        return env.lookup(node.name)

    if isinstance(node, UnaryOp):
        val = evaluate(node.operand, env)
        if node.op == '-':
            if type(val) is not int:
                raise RuntimeError(f"Type error: unary '-' requires integer, got {type_name(val)}")
            return -val
        if node.op == 'not':
            if type(val) is not bool:
                raise RuntimeError(f"Type error: 'not' requires boolean, got {type_name(val)}")
            return not val
        raise RuntimeError(f"Unknown unary operator: {node.op}")

    if isinstance(node, BinOp):
        left = evaluate(node.left, env)
        right = evaluate(node.right, env)
        op = node.op
        if op == '+':
            if type(left) is str and type(right) is str:
                return left + right
            check_types(op, left, right, int)
            return left + right
        if op == '-':
            check_types(op, left, right, int)
            return left - right
        if op == '*':
            check_types(op, left, right, int)
            return left * right
        if op == '/':
            check_types(op, left, right, int)
            if right == 0:
                raise RuntimeError('Runtime error: division by zero')
            return int(left / right)  # truncate toward zero
        if op in ('==', '!='):
            return (left == right) if op == '==' else (left != right)
        if op in ('<', '>', '<=', '>='):
            check_types(op, left, right, int)
            if op == '<':  return left < right
            if op == '>':  return left > right
            if op == '<=': return left <= right
            if op == '>=': return left >= right
        if op == 'and':
            if type(left) is not bool or type(right) is not bool:
                raise RuntimeError("Type error: 'and' requires booleans")
            return left and right
        if op == 'or':
            if type(left) is not bool or type(right) is not bool:
                raise RuntimeError("Type error: 'or' requires booleans")
            return left or right
        raise RuntimeError(f"Unknown binary operator: {op}")

    if isinstance(node, IfExpr):
        cond = evaluate(node.cond, env)
        if type(cond) is not bool:
            raise RuntimeError(f"Type error: if condition must be boolean, got {type_name(cond)}")
        return evaluate(node.then_branch, env) if cond else evaluate(node.else_branch, env)

    if isinstance(node, FunExpr):
        return Closure(node.params, node.body, env)

    if isinstance(node, CallExpr):
        # Built-in: length(x), where x is a string or list.
        if isinstance(node.func, Identifier) and node.func.name == 'length':
            if len(node.args) != 1:
                raise RuntimeError('length() takes exactly 1 argument')
            val = evaluate(node.args[0], env)
            if type(val) is str or type(val) is list:
                return len(val)
            raise RuntimeError(f"Type error: length() requires string or list, got {type_name(val)}")

        # Built-in: append(lst, x). Mutates and returns the same list.
        if isinstance(node.func, Identifier) and node.func.name == 'append':
            if len(node.args) != 2:
                raise RuntimeError('append() takes exactly 2 arguments')
            lst = evaluate(node.args[0], env)
            x = evaluate(node.args[1], env)
            if type(lst) is not list:
                raise RuntimeError(f"Type error: append() requires list as first argument, got {type_name(lst)}")
            lst.append(x)
            return lst

        func = evaluate(node.func, env)
        if not isinstance(func, Closure):
            raise RuntimeError('Type error: called value is not a function')
        args = node.args
        if len(args) != len(func.params):
            raise RuntimeError(f"Arity mismatch: expected {len(func.params)} arguments, got {len(args)}")
        arg_vals = [evaluate(arg, env) for arg in args]

        parent_env = func.env if SCOPE_MODE == 'static' else env
        call_env = Environment(parent_env)
        for param, val in zip(func.params, arg_vals):
            call_env.extend(param, val)
        return evaluate(func.body, call_env)

    if isinstance(node, IndexExpr):
        collection = evaluate(node.collection, env)
        index = evaluate(node.index, env)
        if type(collection) is not list:
            raise RuntimeError(f"Type error: indexing requires list, got {type_name(collection)}")
        if type(index) is not int:
            raise RuntimeError(f"Type error: list index must be integer, got {type_name(index)}")
        if index < 0 or index >= len(collection):
            raise RuntimeError(f"Runtime error: list index out of bounds: {index}")
        return collection[index]

    if isinstance(node, LetStmt):
        env.extend(node.name, None)
        val = evaluate(node.value, env)
        env.update(node.name, val)
        return None

    if isinstance(node, AssignStmt):
        val = evaluate(node.value, env)
        env.update(node.name, val)
        return None

    if isinstance(node, PrintStmt):
        val = evaluate(node.expr, env)
        print(format_value(val))
        return None

    if isinstance(node, WhileStmt):
        while True:
            cond = evaluate(node.cond, env)
            if type(cond) is not bool:
                raise RuntimeError(f"Type error: while condition must be boolean, got {type_name(cond)}")
            if not cond:
                break
            evaluate(node.body, env)
        return None

    if isinstance(node, Block):
        for stmt in node.statements:
            evaluate(stmt, env)
        if node.final_expr is not None:
            return evaluate(node.final_expr, env)
        return None

    raise RuntimeError(f"Unknown AST node: {type(node).__name__}")

# --- Helpers ---
def type_name(val):
    if type(val) is bool:       return 'boolean'
    if type(val) is int:        return 'integer'
    if type(val) is str:        return 'string'
    if type(val) is list:       return 'list'
    if isinstance(val, Closure): return 'function'
    return type(val).__name__

def check_types(op, left, right, expected):
    if type(left) is not expected or type(right) is not expected:
        raise RuntimeError(
            f"Type error: operator '{op}' requires {expected.__name__} operands, "
            f"got {type_name(left)} and {type_name(right)}"
        )

def format_value(val, in_list=False):
    if type(val) is bool:
        return 'true' if val else 'false'
    if isinstance(val, Closure):
        return '<function>'
    if type(val) is str:
        return f'"{val}"' if in_list else val
    if type(val) is list:
        items = ', '.join(format_value(v, in_list=True) for v in val)
        return f'[{items}]'
    return str(val)

def parse_cli(argv):
    usage = 'Usage: python interpreter.py [--scope static|dynamic] <program.txt>\n'
    args = argv[1:]
    scope = 'static'

    if len(args) == 1:
        return args[0], scope

    if len(args) == 3 and args[0] == '--scope':
        if args[1] not in ('static', 'dynamic'):
            sys.stderr.write("Error: --scope must be 'static' or 'dynamic'\n")
            sys.stderr.write(usage)
            sys.exit(1)
        return args[2], args[1]

    sys.stderr.write(usage)
    sys.exit(1)

# --- Entry point ---
if __name__ == '__main__':
    filepath, SCOPE_MODE = parse_cli(sys.argv)

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()
    except FileNotFoundError:
        sys.stderr.write(f"Error: file not found: {filepath}\n")
        sys.exit(1)

    try:
        tokens = lex(code)
        parser = Parser(tokens)
        ast = parser.parse_program()
        global_env = Environment()
        evaluate(ast, global_env)
        sys.exit(0)
    except RuntimeError as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)
