import ast
import re


# ═══════════════════════════════════════════════════════════════════════════════
#  PYTHON PATH  –  original AST-based extractor (unchanged)
# ═══════════════════════════════════════════════════════════════════════════════

class FeatureExtractor(ast.NodeVisitor):
    def __init__(self):
        self.thread_count       = 0
        self.lock_count         = 0
        self.queue_count        = 0
        self.class_count        = 0
        self.loop_count         = 0
        self.infinite_loop_count = 0
        self.if_count           = 0
        self.function_count     = 0
        self.async_count        = 0
        self.global_var_count   = 0
        self.memory_alloc_count = 0
        self.random_call_count  = 0

    # --------------------
    # Classes
    # --------------------
    def visit_ClassDef(self, node):
        self.class_count += 1
        for base in node.bases:
            base_name = ast.unparse(base).lower()
            if "thread" in base_name:
                self.thread_count += 1
        self.generic_visit(node)

    # --------------------
    # Functions
    # --------------------
    def visit_FunctionDef(self, node):
        self.function_count += 1
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self.function_count += 1
        self.async_count += 1
        self.generic_visit(node)

    # --------------------
    # Loops
    # --------------------
    def visit_For(self, node):
        self.loop_count += 1
        self.generic_visit(node)

    def visit_While(self, node):
        self.loop_count += 1
        if isinstance(node.test, ast.Constant) and node.test.value is True:
            self.infinite_loop_count += 1
        self.generic_visit(node)

    # --------------------
    # Branching
    # --------------------
    def visit_If(self, node):
        self.if_count += 1
        self.generic_visit(node)

    # --------------------
    # Globals
    # --------------------
    def visit_Global(self, node):
        self.global_var_count += len(node.names)
        self.generic_visit(node)

    # --------------------
    # Function Calls
    # --------------------
    def visit_Call(self, node):
        name = ast.unparse(node.func).lower()
        if "thread" in name:
            self.thread_count += 1
        if "lock" in name:
            self.lock_count += 1
        if "queue" in name:
            self.queue_count += 1
        if "bytearray" in name or "malloc" in name:
            self.memory_alloc_count += 1
        if "random" in name:
            self.random_call_count += 1
        self.generic_visit(node)


def extract_features(code: str):
    """Python AST-based feature extraction (original)."""
    tree = ast.parse(code)
    extractor = FeatureExtractor()
    extractor.visit(tree)
    loc = len(code.splitlines())
    return [
        extractor.thread_count,
        extractor.lock_count,
        extractor.queue_count,
        extractor.class_count,
        extractor.loop_count,
        extractor.infinite_loop_count,
        extractor.if_count,
        extractor.function_count,
        extractor.async_count,
        extractor.global_var_count,
        extractor.memory_alloc_count,
        extractor.random_call_count,
        loc
    ]


# ═══════════════════════════════════════════════════════════════════════════════
#  GENERIC PATH  –  regex-based extractor for JS / Java / C / C++
# ═══════════════════════════════════════════════════════════════════════════════

# ---------------------------------------------------------------------------
# Per-language regex patterns
# ---------------------------------------------------------------------------

# Threads: creation patterns per language
_THREAD_PATTERNS = {
    "javascript": [r'\bnew\s+Worker\b', r'\bsetInterval\b', r'\bsetTimeout\b'],
    "java":       [r'\bnew\s+Thread\b', r'\bExecutorService\b', r'\bForkJoinPool\b',
                   r'\bimplements\s+Runnable\b', r'\bextends\s+Thread\b'],
    "c":          [r'\bpthread_create\b', r'\bCreateThread\b'],
    "cpp":        [r'\bstd::thread\b', r'\bpthread_create\b', r'\bCreateThread\b'],
}

# Locks / mutexes
_LOCK_PATTERNS = {
    "javascript": [r'\bAsyncLock\b', r'\bMutex\b'],
    "java":       [r'\bsynchronized\b', r'\bReentrantLock\b', r'\bLock\b',
                   r'\b\.lock\(\)', r'\b\.unlock\(\)'],
    "c":          [r'\bpthread_mutex_lock\b', r'\bpthread_mutex_unlock\b', r'\bpthread_mutex_t\b'],
    "cpp":        [r'\bstd::mutex\b', r'\bstd::lock_guard\b', r'\bstd::unique_lock\b',
                   r'\bpthread_mutex_lock\b'],
}

# Queues
_QUEUE_PATTERNS = {
    "javascript": [r'\bQueue\b', r'\bDeque\b'],
    "java":       [r'\bQueue\b', r'\bDeque\b', r'\bArrayDeque\b', r'\bLinkedList\b',
                   r'\bBlockingQueue\b'],
    "c":          [r'\bqueue\b'],
    "cpp":        [r'\bstd::queue\b', r'\bstd::deque\b', r'\bstd::priority_queue\b'],
}

# Classes
_CLASS_PATTERNS = {
    "javascript": [r'\bclass\s+\w+'],
    "java":       [r'\bclass\s+\w+'],
    "c":          [],   # C has no classes
    "cpp":        [r'\bclass\s+\w+', r'\bstruct\s+\w+'],
}

# Loops: for / while / do-while
_LOOP_PATTERNS = {
    "javascript": [r'\bfor\s*\(', r'\bwhile\s*\(', r'\bdo\s*\{'],
    "java":       [r'\bfor\s*\(', r'\bwhile\s*\(', r'\bdo\s*\{'],
    "c":          [r'\bfor\s*\(', r'\bwhile\s*\(', r'\bdo\s*\{'],
    "cpp":        [r'\bfor\s*\(', r'\bwhile\s*\(', r'\bdo\s*\{'],
}

# Infinite loop heuristics
_INFINITE_LOOP_PATTERNS = {
    "javascript": [r'\bwhile\s*\(\s*true\s*\)', r'\bwhile\s*\(\s*1\s*\)', r'\bfor\s*\(\s*;\s*;\s*\)'],
    "java":       [r'\bwhile\s*\(\s*true\s*\)', r'\bwhile\s*\(\s*1\s*\)', r'\bfor\s*\(\s*;\s*;\s*\)'],
    "c":          [r'\bwhile\s*\(\s*1\s*\)', r'\bfor\s*\(\s*;\s*;\s*\)'],
    "cpp":        [r'\bwhile\s*\(\s*true\s*\)', r'\bwhile\s*\(\s*1\s*\)', r'\bfor\s*\(\s*;\s*;\s*\)'],
}

# If / else-if branches
_IF_PATTERNS = {
    "javascript": [r'\bif\s*\(', r'\belse\s+if\s*\('],
    "java":       [r'\bif\s*\(', r'\belse\s+if\s*\('],
    "c":          [r'\bif\s*\(', r'\belse\s+if\s*\('],
    "cpp":        [r'\bif\s*\(', r'\belse\s+if\s*\('],
}

# Functions / methods
_FUNCTION_PATTERNS = {
    # named function / arrow function / method shorthand
    "javascript": [
        r'\bfunction\s+\w+\s*\(',
        r'\bconst\s+\w+\s*=\s*\(',
        r'\bconst\s+\w+\s*=\s*async\s*\(',
        r'\b\w+\s*\([^)]*\)\s*\{',        # method shorthand in object/class
    ],
    # return-type method declarations (public/private/protected/static or bare type)
    "java": [
        r'(?:public|private|protected|static|\s)+[\w<>\[\]]+\s+\w+\s*\([^)]*\)\s*(?:throws\s+\w+\s*)?\{',
    ],
    # C function: return_type name(params) {
    "c": [
        r'^\s*[\w\*]+\s+\w+\s*\([^)]*\)\s*\{',
    ],
    # C++ same + constructor/destructor patterns
    "cpp": [
        r'^\s*[\w\*:<>]+\s+\w+\s*\([^)]*\)\s*(?:const\s*)?\{',
        r'^\s*\w+::\w+\s*\([^)]*\)\s*(?::\s*.+)?\{',  # constructor with init list
    ],
}

# Async keywords
_ASYNC_PATTERNS = {
    "javascript": [r'\basync\s+function\b', r'\basync\s*\(', r'\bawait\b'],
    "java":       [r'\bCompletableFuture\b', r'\bExecutorService\b', r'\bFuture\b'],
    "c":          [],
    "cpp":        [r'\bstd::future\b', r'\bstd::async\b', r'\bstd::promise\b'],
}

# Global / static variables
_GLOBAL_PATTERNS = {
    "javascript": [r'^\s*(?:var|let|const)\s+\w+',   # top-level declarations
                   r'\bwindow\.\w+\s*='],
    "java":       [r'\bstatic\s+(?!final\s+\w+\s+\w+\s*\()[\w<>\[\]]+\s+\w+\s*[=;]'],
    "c":          [r'^\s*(?:static\s+)?(?:int|float|double|char|long|unsigned)\s+\w+\s*[=;]'],
    "cpp":        [r'^\s*(?:static\s+)?(?:int|float|double|char|long|unsigned|auto)\s+\w+\s*[=;]',
                   r'^\s*\w+::\w+\s*='],
}

# Memory allocations
_MEMALLOC_PATTERNS = {
    "javascript": [r'\bnew\s+(?:ArrayBuffer|SharedArrayBuffer|Buffer|DataView)\b'],
    "java":       [r'\bnew\s+byte\[', r'\bnew\s+int\[', r'\bnew\s+char\[',
                   r'\bByteBuffer\.allocate\b', r'\bDirectByteBuffer\b'],
    "c":          [r'\bmalloc\s*\(', r'\bcalloc\s*\(', r'\brealloc\s*\(', r'\balloca\s*\('],
    "cpp":        [r'\bnew\s+\w', r'\bmalloc\s*\(', r'\bcalloc\s*\(', r'\brealloc\s*\('],
}

# Random calls
_RANDOM_PATTERNS = {
    "javascript": [r'\bMath\.random\b', r'\bcrypto\.getRandomValues\b'],
    "java":       [r'\bMath\.random\b', r'\bnew\s+Random\b', r'\bRandom\(\)'],
    "c":          [r'\brand\s*\(', r'\bsrand\s*\('],
    "cpp":        [r'\bstd::rand\b', r'\bstd::mt19937\b', r'\bstd::uniform_int_distribution\b',
                   r'\brand\s*\('],
}


def _count_patterns(code: str, patterns: list) -> int:
    """Count all (possibly overlapping) matches for a list of regex patterns."""
    total = 0
    for pat in patterns:
        total += len(re.findall(pat, code, re.MULTILINE))
    return total


def extract_features_generic(code: str, language: str) -> list:
    """
    Regex-based feature extraction for JavaScript, Java, C, and C++.
    Returns the same 13-element feature vector as the Python AST extractor.
    """
    lang = language.lower()

    threads       = _count_patterns(code, _THREAD_PATTERNS.get(lang, []))
    locks         = _count_patterns(code, _LOCK_PATTERNS.get(lang, []))
    queues        = _count_patterns(code, _QUEUE_PATTERNS.get(lang, []))
    classes       = _count_patterns(code, _CLASS_PATTERNS.get(lang, []))
    loops         = _count_patterns(code, _LOOP_PATTERNS.get(lang, []))
    infinite_loops = _count_patterns(code, _INFINITE_LOOP_PATTERNS.get(lang, []))
    ifs           = _count_patterns(code, _IF_PATTERNS.get(lang, []))
    functions     = _count_patterns(code, _FUNCTION_PATTERNS.get(lang, []))
    asyncs        = _count_patterns(code, _ASYNC_PATTERNS.get(lang, []))
    globals_      = _count_patterns(code, _GLOBAL_PATTERNS.get(lang, []))
    mem_allocs    = _count_patterns(code, _MEMALLOC_PATTERNS.get(lang, []))
    random_calls  = _count_patterns(code, _RANDOM_PATTERNS.get(lang, []))
    loc           = len(code.splitlines())

    return [
        threads, locks, queues, classes,
        loops, infinite_loops, ifs, functions,
        asyncs, globals_, mem_allocs, random_calls,
        loc
    ]