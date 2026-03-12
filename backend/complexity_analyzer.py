import ast
import re


# ═══════════════════════════════════════════════════════════════════════════════
#  PYTHON PATH  –  original AST-based complexity estimator (unchanged)
# ═══════════════════════════════════════════════════════════════════════════════

class ComplexityVisitor(ast.NodeVisitor):
    def __init__(self):
        self.max_depth      = 0
        self.current_depth  = 0
        self.recursive_calls = 0
        self.functions      = set()
        self.calls          = []

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
    Heuristic time-complexity estimator for Python based on AST loop depth
    and recursion.
    """
    try:
        tree = ast.parse(code)
    except Exception:
        return "Unknown"

    visitor = ComplexityVisitor()
    visitor.visit(tree)

    recursive = any(name in visitor.calls for name in visitor.functions)

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


# ═══════════════════════════════════════════════════════════════════════════════
#  GENERIC PATH  –  regex / brace-counting estimator for JS / Java / C / C++
# ═══════════════════════════════════════════════════════════════════════════════

# Regex that matches any loop keyword opener for C-style languages
_CSTYLE_LOOP_RE = re.compile(r'\b(for|while|do)\s*[\(\{]')

# Function definition patterns per language (used for recursion detection)
_FUNC_NAME_PATTERNS = {
    "javascript": re.compile(r'\bfunction\s+(\w+)\s*\('),
    "java":       re.compile(
        r'(?:public|private|protected|static|\s)+[\w<>\[\]]+\s+(\w+)\s*\([^)]*\)\s*(?:throws\s+\w+\s*)?\{'
    ),
    "c":          re.compile(r'^\s*[\w\*]+\s+(\w+)\s*\([^)]*\)\s*\{', re.MULTILINE),
    "cpp":        re.compile(r'(?:\w+::)?(\w+)\s*\([^)]*\)\s*(?:const\s*)?\{'),
}

# Pattern to detect a self-call (recursion): `name(` somewhere in body
def _has_recursion(code: str, language: str) -> bool:
    pattern = _FUNC_NAME_PATTERNS.get(language)
    if not pattern:
        return False
    names = set(pattern.findall(code))
    for name in names:
        # Count how many times the function name appears followed by '('
        calls = len(re.findall(rf'\b{re.escape(name)}\s*\(', code))
        if calls >= 2:   # at least definition + one call inside itself
            return True
    return False


def _max_loop_nesting_cstyle(code: str) -> int:
    """
    Estimate maximum loop nesting depth for C-style (brace-delimited) languages
    by walking the code character-by-character and tracking brace depth at
    each loop keyword.
    """
    # Strip single-line and block comments to avoid false positives
    code = re.sub(r'//[^\n]*', '', code)
    code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
    # Strip string literals (simple heuristic)
    code = re.sub(r'"[^"\\]*(?:\\.[^"\\]*)*"', '""', code)
    code = re.sub(r"'[^'\\]*(?:\\.[^'\\]*)*'", "''", code)

    brace_depth    = 0   # current { } nesting
    loop_stack     = []  # brace_depth values where loops started
    max_loop_depth = 0

    i = 0
    while i < len(code):
        # Detect loop keyword
        m = _CSTYLE_LOOP_RE.match(code, i)
        if m:
            loop_stack.append(brace_depth)
            max_loop_depth = max(max_loop_depth, len(loop_stack))
            i = m.end()
            continue

        ch = code[i]
        if ch == '{':
            brace_depth += 1
        elif ch == '}':
            brace_depth -= 1
            brace_depth = max(brace_depth, 0)
            # Pop any loops whose brace context has closed
            while loop_stack and loop_stack[-1] >= brace_depth:
                loop_stack.pop()
        i += 1

    return max_loop_depth


def estimate_complexity_generic(code: str, language: str) -> str:
    """
    Heuristic time-complexity estimator for JavaScript, Java, C, and C++.
    Uses brace-aware loop nesting counting and a simple recursion heuristic.
    """
    try:
        max_depth = _max_loop_nesting_cstyle(code)
        recursive = _has_recursion(code, language)

        if recursive and max_depth >= 2:
            return "O(2^n) (Recursive)"
        elif max_depth >= 3:
            return "O(n³+)"
        elif max_depth == 2:
            return "O(n²)"
        elif max_depth == 1:
            return "O(n)"
        else:
            return "O(1)"
    except Exception:
        return "Unknown"