import ast

class ComplexityVisitor(ast.NodeVisitor):
    def __init__(self):
        self.max_depth = 0
        self.current_depth = 0
        self.recursive_calls = 0
        self.functions = set()
        self.calls = []

    def visit_FunctionDef(self, node):
        self.functions.add(node.name)
        self.generic_visit(node)

    def visit_For(self, node):
        self._enter_loop(node)

    def visit_While(self, node):
        self._enter_loop(node)

    def _enter_loop(self, node):
        self.current_depth += 1
        self.max_depth = max(self.max_depth, self.current_depth)
        self.generic_visit(node)
        self.current_depth -= 1

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            self.calls.append(node.func.id)
        self.generic_visit(node)


def estimate_complexity(code: str) -> str:
    """
    Heuristic time-complexity estimator based on AST loop depth and recursion.
    """

    try:
        tree = ast.parse(code)
    except Exception:
        return "Unknown"

    visitor = ComplexityVisitor()
    visitor.visit(tree)

    # Detect recursion
    recursive = any(name in visitor.calls for name in visitor.functions)

    # Heuristic classification
    if recursive and visitor.max_depth >= 2:
        return "O(2^n) (Recursive)"
    elif visitor.max_depth >= 3:
        return "O(n³+)"
    elif visitor.max_depth == 2:
        return "O(n²)"
    elif visitor.max_depth == 1:
        return "O(n)"
    else:
        return "O(1)"
