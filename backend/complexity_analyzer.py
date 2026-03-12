import ast
import re

# ═══════════════════════════════════════════════════════════════════════════════
#  PYTHON PATH  –  original AST-based estimator (unchanged)
# ═══════════════════════════════════════════════════════════════════════════════

class ComplexityVisitor(ast.NodeVisitor):
    def __init__(self):
        self.max_depth     = 0
        self.current_depth = 0
        self.functions     = set()
        self.calls         = []

    def visit_FunctionDef(self, node):
        self.functions.add(node.name)
        self.generic_visit(node)

    def visit_For(self, node):   self._enter_loop(node)
    def visit_While(self, node): self._enter_loop(node)

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
    try:
        tree = ast.parse(code)
    except Exception:
        return "Unknown"
    v = ComplexityVisitor()
    v.visit(tree)
    recursive = any(name in v.calls for name in v.functions)
    if recursive and v.max_depth >= 2: return "O(2^n) (Recursive)"
    if v.max_depth >= 3:               return "O(n³+)"
    if v.max_depth == 2:               return "O(n²)"
    if v.max_depth == 1:               return "O(n)"
    return "O(1)"


# ═══════════════════════════════════════════════════════════════════════════════
#  GENERIC PATH  –  works for all other languages
# ═══════════════════════════════════════════════════════════════════════════════

# Languages that use indentation instead of braces for block structure
_INDENT_BASED = {"python", "GDScript"}

# Loop keywords per language
_LOOP_KW: dict[str, re.Pattern] = {
    "javascript":  re.compile(r'\b(for|while|do)\b'),
    "typescript":  re.compile(r'\b(for|while|do)\b'),
    "java":        re.compile(r'\b(for|while|do)\b'),
    "c":           re.compile(r'\b(for|while|do)\b'),
    "cpp":         re.compile(r'\b(for|while|do)\b'),
    "csharp":      re.compile(r'\b(for|foreach|while|do)\b'),
    "go":          re.compile(r'\bfor\b'),
    "rust":        re.compile(r'\b(for|while|loop)\b'),
    "swift":       re.compile(r'\b(for|while|repeat)\b'),
    "ruby":        re.compile(r'\b(for|while|until|each|times|loop)\b'),
    "php":         re.compile(r'\b(for|foreach|while|do)\b'),
    "scala":       re.compile(r'\b(for|while)\b'),
    "kotlin":      re.compile(r'\b(for|while|do)\b'),
    "objectivec":  re.compile(r'\b(for|while|do)\b'),
    "lua":         re.compile(r'\b(for|while|repeat)\b'),
    "plsql":       re.compile(r'\b(FOR|WHILE|LOOP)\b', re.IGNORECASE),
    "GDScript":    re.compile(r'\b(for|while)\b'),
}

# Function name capture patterns per language (for recursion detection)
_FUNC_CAPTURE: dict[str, re.Pattern] = {
    "javascript":  re.compile(r'\bfunction\s+(\w+)\s*\('),
    "typescript":  re.compile(r'\bfunction\s+(\w+)\s*\('),
    "java":        re.compile(r'(?:public|private|protected|static|\s)+\w[\w<>\[\]]*\s+(\w+)\s*\([^)]*\)\s*\{'),
    "c":           re.compile(r'^\s*\w[\w\s\*]*\s+(\w+)\s*\([^)]*\)\s*\{', re.MULTILINE),
    "cpp":         re.compile(r'(?:\w+::)?(\w+)\s*\([^)]*\)\s*(?:const\s*)?\{'),
    "csharp":      re.compile(r'(?:public|private|protected|static|virtual|override|async|\s)+\w[\w<>\[\]?]*\s+(\w+)\s*\([^)]*\)\s*\{'),
    "go":          re.compile(r'\bfunc\s+(?:\(\w+\s+\*?\w+\)\s+)?(\w+)\s*\('),
    "rust":        re.compile(r'\bfn\s+(\w+)\s*(?:<[^>]*>)?\s*\('),
    "swift":       re.compile(r'\bfunc\s+(\w+)\s*\('),
    "ruby":        re.compile(r'\bdef\s+(\w+)'),
    "php":         re.compile(r'\bfunction\s+(\w+)\s*\('),
    "scala":       re.compile(r'\bdef\s+(\w+)\s*(?:\([^)]*\))?\s*(?::\s*\w+)?\s*='),
    "kotlin":      re.compile(r'\bfun\s+(\w+)\s*\('),
    "objectivec":  re.compile(r'[-+]\s*\([^)]+\)\s*(\w+)'),
    "lua":         re.compile(r'\bfunction\s+(\w+)\s*\('),
    "plsql":       re.compile(r'(?:FUNCTION|PROCEDURE)\s+(\w+)', re.IGNORECASE),
    "GDScript":    re.compile(r'\bfunc\s+(\w+)\s*\('),
}


def _strip_comments(code: str, language: str) -> str:
    """Remove single-line and block comments to avoid false positives."""
    lang = language.lower()
    # Block comments /* ... */
    if lang not in ("python", "ruby", "lua", "plsql", "GDScript"):
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
    # Single-line // comments
    if lang not in ("python", "ruby", "lua", "plsql", "GDScript"):
        code = re.sub(r'//[^\n]*', '', code)
    # Python/GDScript # comments
    if lang in ("python", "GDScript", "ruby"):
        code = re.sub(r'#[^\n]*', '', code)
    # Lua -- comments
    if lang == "lua":
        code = re.sub(r'--[^\n]*', '', code)
    # SQL -- comments
    if lang == "plsql":
        code = re.sub(r'--[^\n]*', '', code)
    # Strip string literals (simple)
    code = re.sub(r'"[^"\\]*(?:\\.[^"\\]*)*"', '""', code)
    code = re.sub(r"'[^'\\]*(?:\\.[^'\\]*)*'", "''", code)
    return code


def _max_nesting_brace(code: str, language: str) -> int:
    """
    Estimate max loop nesting for brace-delimited languages by tracking
    open brace depth at each loop keyword.
    """
    loop_re   = _LOOP_KW.get(language, re.compile(r'\b(for|while)\b'))
    brace_d   = 0
    loop_stack = []
    max_depth  = 0
    i = 0
    while i < len(code):
        # Try to match loop keyword at position i
        m = loop_re.match(code, i)
        if m:
            loop_stack.append(brace_d)
            max_depth = max(max_depth, len(loop_stack))
            i = m.end()
            continue
        ch = code[i]
        if ch == '{':
            brace_d += 1
        elif ch == '}':
            brace_d = max(0, brace_d - 1)
            while loop_stack and loop_stack[-1] >= brace_d:
                loop_stack.pop()
        i += 1
    return max_depth


def _max_nesting_indent(code: str) -> int:
    """
    Estimate max loop nesting for indent-based languages (Ruby, Lua, GDScript,
    PL/SQL) by tracking indentation level at loop keywords.
    """
    loop_words = re.compile(r'^\s*(for|while|until|loop|repeat)\b', re.IGNORECASE)
    end_words  = re.compile(r'^\s*(end|done|until)\b', re.IGNORECASE)
    depth = 0
    max_d = 0
    for line in code.splitlines():
        if loop_words.match(line):
            depth += 1
            max_d = max(max_d, depth)
        elif end_words.match(line) and depth > 0:
            depth -= 1
    return max_d


def _has_recursion(code: str, language: str) -> bool:
    """Detect likely recursion by checking if any function calls itself."""
    pat = _FUNC_CAPTURE.get(language)
    if not pat:
        return False
    names = set(pat.findall(code))
    for name in names:
        if len(re.findall(rf'\b{re.escape(name)}\s*\(', code)) >= 2:
            return True
    return False


def estimate_complexity_generic(code: str, language: str) -> str:
    """
    Heuristic time-complexity estimator for all non-Python lizard languages.
    """
    try:
        clean = _strip_comments(code, language)
        lang  = language.lower()

        indent_langs = {"ruby", "lua", "plsql", "GDScript"}
        if lang in indent_langs or language == "GDScript":
            max_depth = _max_nesting_indent(clean)
        else:
            max_depth = _max_nesting_brace(clean, language)

        recursive = _has_recursion(clean, language)

        if recursive and max_depth >= 2: return "O(2^n) (Recursive)"
        if max_depth >= 3:               return "O(n³+)"
        if max_depth == 2:               return "O(n²)"
        if max_depth == 1:               return "O(n)"
        return "O(1)"
    except Exception:
        return "Unknown"
