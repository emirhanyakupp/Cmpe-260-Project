# Interpreter implementation
# Evaluator uses Call-By-Value and Static Scoping
import sys
import re

# --- AST Nodes  ---
class Node: pass
class NumberLit(Node):
    def __init__(self, value): self.value = value
class BoolLit(Node):
    def __init__(self, value): self.value = value
class Identifier(Node):
    def __init__(self, name): self.name = name
class BinOp(Node):
    def __init__(self, op, left, right): self.op, self.left, self.right = op, left, right
class UnaryOp(Node):
    def __init__(self, op, operand): self.op, self.operand = op, operand
class IfExpr(Node):
    def __init__(self, cond, then_branch, else_branch): self.cond, self.then_branch, self.else_branch = cond, then_branch, else_branch
class FunExpr(Node):
    def __init__(self, params, body): self.params, self.body = params, body
class CallExpr(Node):
    def __init__(self, func, args): self.func, self.args = func, args
class LetStmt(Node):
    def __init__(self, name, value): self.name, self.value = name, value
class AssignStmt(Node):
    def __init__(self, name, value): self.name, self.value = name, value
class PrintStmt(Node):
    def __init__(self, expr): self.expr = expr
class Block(Node):
    def __init__(self, statements, final_expr): self.statements, self.final_expr = statements, final_expr

# --- Lexer  ---
def lex(source_code):
    source_code = re.sub(r'\(\*.*?\*\)', '', source_code, flags=re.DOTALL) # Remove comments 
    token_specification = [
        ('NUMBER',   r'\d+'),
        ('ID',       r'[A-Za-z][A-Za-z0-9_]*'),
        ('ARROW',    r'->'),            
        ('OP2',      r'==|!=|<=|>='),
        ('OP1',      r'[+\-*/=<>(),;]'),
        ('SKIP',     r'[ \t\n\r]+'),
        ('MISMATCH', r'.'),
    ]
    tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specification)
    tokens = []
    for mo in re.finditer(tok_regex, source_code):
        kind, value = mo.lastgroup, mo.group()
        if kind == 'SKIP': continue
        elif kind == 'MISMATCH': raise RuntimeError(f"Unexpected token: {value}")
        tokens.append(value)
    return tokens

# --- Parser  ---
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def consume(self, expected=None):
        if expected and self.peek() != expected:
            raise RuntimeError(f"Expected {expected}, got {self.peek()}")
        val = self.peek()
        self.pos += 1
        return val

    def parse_program(self):
        return self.parse_block()

    def parse_block(self):
        stmts = []
        final_expr = None
        while self.peek() and self.peek() not in ('end', 'else'):
            if self.peek() == 'let':
                stmts.append(self.parse_let())
                self.consume(';')
            elif self.peek() == 'print':
                stmts.append(self.parse_print())
                self.consume(';')
            else:
                expr = self.parse_expr()
                if self.peek() == ';':
                    # It's an expression statement or assignment 
                    if isinstance(expr, Identifier) and self.peek() == '=': # Assignment 
                        self.pos -= 1 # backtrack
                        stmts.append(self.parse_assign())
                    else:
                        stmts.append(expr)
                    self.consume(';')
                elif isinstance(expr, Identifier) and self.peek() == '=':
                    name = expr.name
                    self.consume('=')
                    val = self.parse_expr()
                    stmts.append(AssignStmt(name, val))
                    self.consume(';')
                else:
                    final_expr = expr # Final expression of block 
                    break
        return Block(stmts, final_expr)

    def parse_let(self):
        self.consume('let')
        name = self.consume()
        self.consume('=')
        val = self.parse_expr()
        return LetStmt(name, val)

    def parse_print(self):
        self.consume('print')
        self.consume('(')
        expr = self.parse_expr()
        self.consume(')')
        return PrintStmt(expr)

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
        return self.parse_call()

    def parse_call(self):
        node = self.parse_primary()
        while self.peek() == '(':
            self.consume('(')
            args = []
            if self.peek() != ')':
                args.append(self.parse_expr())
                while self.peek() == ',':
                    self.consume(',')
                    args.append(self.parse_expr())
            self.consume(')')
            node = CallExpr(node, args)
        return node

    def parse_primary(self):
        tok = self.consume()
        if tok.isdigit(): return NumberLit(int(tok))
        elif tok in ('true', 'false'): return BoolLit(tok == 'true')
        elif tok == 'if':
            cond = self.parse_expr()
            self.consume('then')
            then_b = self.parse_block()
            self.consume('else')
            else_b = self.parse_block()
            self.consume('end')
            return IfExpr(cond, then_b, else_b)
        elif tok == 'fun':
            self.consume('(')
            params = []
            if self.peek() != ')':
                params.append(self.consume())
                while self.peek() == ',':
                    self.consume(',')
                    params.append(self.consume())
            self.consume(')')
            self.consume('->')
            body = self.parse_block()
            self.consume('end')
            return FunExpr(params, body)
        elif tok == '(':
            expr = self.parse_expr()
            self.consume(')')
            return expr
        else:
            return Identifier(tok)

# --- Environment & Closure  ---
class Environment:
    def __init__(self, parent=None):
        self.bindings = {}
        self.parent = parent # Static scope link 

    def extend(self, name, value):
        self.bindings[name] = value 

    def lookup(self, name):
        if name in self.bindings: return self.bindings[name]
        if self.parent: return self.parent.lookup(name)
        raise RuntimeError(f"Undefined variable: {name}") 

    def update(self, name, value):
        if name in self.bindings:
            self.bindings[name] = value 
            return
        if self.parent:
            self.parent.update(name, value) 
            return
        raise RuntimeError(f"Undefined variable: {name}")

class Closure:
    def __init__(self, params, body, env):
        self.params = params
        self.body = body
        self.env = env # Capturing the defining environment 

# --- Evaluator 
def evaluate(node, env):
    if isinstance(node, NumberLit): return node.value
    if isinstance(node, BoolLit): return node.value
    if isinstance(node, Identifier): return env.lookup(node.name)
    if isinstance(node, UnaryOp):
        val = evaluate(node.operand, env)
        if node.op == '-': return -val
        if node.op == 'not': return not val
    if isinstance(node, BinOp):
        left = evaluate(node.left, env)
        right = evaluate(node.right, env)
        if node.op == '+': return left + right
        if node.op == '-': return left - right
        if node.op == '*': return left * right
        if node.op == '/':
            if right == 0: raise RuntimeError("Division by zero") 
            return int(left / right) # Truncate towards zero 
        if node.op == '==': return left == right
        if node.op == '!=': return left != right
        if node.op == '<': return left < right
        if node.op == '>': return left > right
        if node.op == '<=': return left <= right
        if node.op == '>=': return left >= right
        if node.op == 'and': return left and right
        if node.op == 'or': return left or right
    if isinstance(node, IfExpr):
        cond = evaluate(node.cond, env)
        if cond: return evaluate(node.then_branch, env)
        else: return evaluate(node.else_branch, env) 
    if isinstance(node, FunExpr):
        return Closure(node.params, node.body, env) 
    if isinstance(node, CallExpr):
        func = evaluate(node.func, env)
        if not isinstance(func, Closure): raise RuntimeError("Not a function")
        if len(args := node.args) != len(func.params): raise RuntimeError("Arity mismatch")
        
        # Call-by-value: Evaluate args fully before function execution 
        arg_vals = [evaluate(arg, env) for arg in args]
        
        call_env = Environment(func.env) # Link to captured environment 
        for param, val in zip(func.params, arg_vals):
            call_env.extend(param, val)
        return evaluate(func.body, call_env)
    
    if isinstance(node, LetStmt):
        # Placeholder for implicitly recursive functions 
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
        if isinstance(val, bool): print("true" if val else "false") 
        elif isinstance(val, Closure): print("<function>") 
        else: print(val)
        return None
    if isinstance(node, Block):
        for stmt in node.statements:
            evaluate(stmt, env)
        if node.final_expr:
            return evaluate(node.final_expr, env) 
        return None

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python interpreter.py <program.txt>")
        sys.exit(1)
    
    with open(sys.argv[1], 'r') as f:
        code = f.read()
    
    try:
        tokens = lex(code)
        parser = Parser(tokens)
        ast = parser.parse_program()
        global_env = Environment()
        evaluate(ast, global_env)
    except Exception as e:
        sys.stderr.write(f"Error: {e}\n") 
        sys.exit(1)