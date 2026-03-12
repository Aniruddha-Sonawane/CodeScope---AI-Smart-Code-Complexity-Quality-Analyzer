import ast
import re

# ═══════════════════════════════════════════════════════════════════════════════
#  PYTHON PATH  –  original AST-based extractor (unchanged)
# ═══════════════════════════════════════════════════════════════════════════════

class FeatureExtractor(ast.NodeVisitor):
    def __init__(self):
        self.thread_count        = 0
        self.lock_count          = 0
        self.queue_count         = 0
        self.class_count         = 0
        self.loop_count          = 0
        self.infinite_loop_count = 0
        self.if_count            = 0
        self.function_count      = 0
        self.async_count         = 0
        self.global_var_count    = 0
        self.memory_alloc_count  = 0
        self.random_call_count   = 0

    def visit_ClassDef(self, node):
        self.class_count += 1
        for base in node.bases:
            if "thread" in ast.unparse(base).lower():
                self.thread_count += 1
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self.function_count += 1
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self.function_count += 1
        self.async_count += 1
        self.generic_visit(node)

    def visit_For(self, node):
        self.loop_count += 1
        self.generic_visit(node)

    def visit_While(self, node):
        self.loop_count += 1
        if isinstance(node.test, ast.Constant) and node.test.value is True:
            self.infinite_loop_count += 1
        self.generic_visit(node)

    def visit_If(self, node):
        self.if_count += 1
        self.generic_visit(node)

    def visit_Global(self, node):
        self.global_var_count += len(node.names)
        self.generic_visit(node)

    def visit_Call(self, node):
        name = ast.unparse(node.func).lower()
        if "thread"    in name: self.thread_count       += 1
        if "lock"      in name: self.lock_count         += 1
        if "queue"     in name: self.queue_count        += 1
        if "bytearray" in name or "malloc" in name: self.memory_alloc_count += 1
        if "random"    in name: self.random_call_count  += 1
        self.generic_visit(node)


def extract_features(code: str) -> list:
    """Python AST-based feature extraction."""
    tree = ast.parse(code)
    e    = FeatureExtractor()
    e.visit(tree)
    loc = len(code.splitlines())
    return [e.thread_count, e.lock_count, e.queue_count, e.class_count,
            e.loop_count, e.infinite_loop_count, e.if_count, e.function_count,
            e.async_count, e.global_var_count, e.memory_alloc_count,
            e.random_call_count, loc]


# ═══════════════════════════════════════════════════════════════════════════════
#  GENERIC PATH  –  regex-based extractor for all other lizard-supported languages
# ═══════════════════════════════════════════════════════════════════════════════

def _n(code, patterns):
    """Count all matches for a list of regex patterns."""
    return sum(len(re.findall(p, code, re.MULTILINE | re.IGNORECASE)) for p in patterns)

# ── Pattern tables per language ───────────────────────────────────────────────

_THREADS = {
    "javascript":  [r'\bnew\s+Worker\b', r'\bsetInterval\b', r'\bsetTimeout\b'],
    "typescript":  [r'\bnew\s+Worker\b', r'\bsetInterval\b', r'\bsetTimeout\b'],
    "java":        [r'\bnew\s+Thread\b', r'\bExecutorService\b', r'\bextends\s+Thread\b', r'\bimplements\s+Runnable\b'],
    "c":           [r'\bpthread_create\b', r'\bCreateThread\b'],
    "cpp":         [r'\bstd::thread\b', r'\bpthread_create\b', r'\bCreateThread\b'],
    "csharp":      [r'\bnew\s+Thread\b', r'\bTask\.Run\b', r'\bThreadPool\b', r'\basync\s+Task\b'],
    "go":          [r'\bgo\s+\w+\('],
    "rust":        [r'\bthread::spawn\b', r'\bstd::thread\b'],
    "swift":       [r'\bDispatchQueue\b', r'\bThread\b', r'\bOperationQueue\b'],
    "ruby":        [r'\bThread\.new\b', r'\bThread\.start\b'],
    "php":         [],
    "scala":       [r'\bFuture\s*\{', r'\bnew\s+Thread\b', r'\bActorSystem\b'],
    "kotlin":      [r'\bThread\s*\{', r'\bCoroutineScope\b', r'\blaunch\s*\{', r'\basync\s*\{'],
    "objectivec":  [r'\bNSThread\b', r'\bdispatch_async\b', r'\bdispatch_queue\b'],
    "lua":         [r'\bcoroutine\.create\b', r'\bcoroutine\.wrap\b'],
    "plsql":       [],
    "GDScript":    [r'\bThread\.new\b', r'\bstart\b'],
}

_LOCKS = {
    "javascript":  [r'\bMutex\b', r'\bAsyncLock\b'],
    "typescript":  [r'\bMutex\b', r'\bAsyncLock\b'],
    "java":        [r'\bsynchronized\b', r'\bReentrantLock\b', r'\.lock\(\)', r'\.unlock\(\)'],
    "c":           [r'\bpthread_mutex_lock\b', r'\bpthread_mutex_t\b'],
    "cpp":         [r'\bstd::mutex\b', r'\bstd::lock_guard\b', r'\bstd::unique_lock\b'],
    "csharp":      [r'\block\s*\(', r'\bMonitor\.(Enter|Exit)\b', r'\bMutex\b', r'\bSemaphore\b'],
    "go":          [r'\bsync\.Mutex\b', r'\b\.Lock\(\)', r'\b\.Unlock\(\)', r'\bsync\.RWMutex\b'],
    "rust":        [r'\bMutex::new\b', r'\bRwLock\b', r'\b\.lock\(\)'],
    "swift":       [r'\bNSLock\b', r'\bDispatchSemaphore\b', r'\bobjc_sync_enter\b'],
    "ruby":        [r'\bMutex\.new\b', r'\b\.synchronize\b'],
    "php":         [r'\bsem_acquire\b', r'\bflock\b'],
    "scala":       [r'\bsynchronized\b', r'\bReentrantLock\b'],
    "kotlin":      [r'\bsynchronized\b', r'\bReentrantLock\b', r'\bMutex\(\)'],
    "objectivec":  [r'\b@synchronized\b', r'\bNSLock\b', r'\bpthread_mutex_lock\b'],
    "lua":         [],
    "plsql":       [r'\bLOCK\s+TABLE\b', r'\bFOR\s+UPDATE\b'],
    "GDScript":    [],
}

_QUEUES = {
    "javascript":  [r'\bQueue\b'],
    "typescript":  [r'\bQueue\b'],
    "java":        [r'\bQueue\b', r'\bBlockingQueue\b', r'\bArrayDeque\b', r'\bLinkedList\b'],
    "c":           [r'\bqueue\b'],
    "cpp":         [r'\bstd::queue\b', r'\bstd::deque\b', r'\bstd::priority_queue\b'],
    "csharp":      [r'\bQueue<', r'\bConcurrentQueue\b'],
    "go":          [r'\bchan\b'],
    "rust":        [r'\bVecDeque\b', r'\bmpsc::channel\b'],
    "swift":       [r'\bDispatchQueue\b'],
    "ruby":        [r'\bQueue\.new\b', r'\bSizedQueue\b'],
    "php":         [],
    "scala":       [r'\bQueue\b', r'\bBlockingQueue\b'],
    "kotlin":      [r'\bArrayDeque\b', r'\bChannel\b', r'\bQueue\b'],
    "objectivec":  [r'\bNSOperationQueue\b'],
    "lua":         [],
    "plsql":       [],
    "GDScript":    [],
}

_CLASSES = {
    "javascript":  [r'\bclass\s+\w+'],
    "typescript":  [r'\bclass\s+\w+', r'\binterface\s+\w+'],
    "java":        [r'\bclass\s+\w+', r'\binterface\s+\w+', r'\benum\s+\w+'],
    "c":           [],
    "cpp":         [r'\bclass\s+\w+', r'\bstruct\s+\w+'],
    "csharp":      [r'\bclass\s+\w+', r'\binterface\s+\w+', r'\bstruct\s+\w+', r'\benum\s+\w+'],
    "go":          [r'\btype\s+\w+\s+struct\b', r'\btype\s+\w+\s+interface\b'],
    "rust":        [r'\bstruct\s+\w+', r'\benum\s+\w+', r'\btrait\s+\w+', r'\bimpl\s+\w+'],
    "swift":       [r'\bclass\s+\w+', r'\bstruct\s+\w+', r'\benum\s+\w+', r'\bprotocol\s+\w+'],
    "ruby":        [r'\bclass\s+\w+', r'\bmodule\s+\w+'],
    "php":         [r'\bclass\s+\w+', r'\binterface\s+\w+', r'\btrait\s+\w+'],
    "scala":       [r'\bclass\s+\w+', r'\bobject\s+\w+', r'\btrait\s+\w+', r'\bcase\s+class\s+\w+'],
    "kotlin":      [r'\bclass\s+\w+', r'\bobject\s+\w+', r'\binterface\s+\w+', r'\bdata\s+class\s+\w+'],
    "objectivec":  [r'\b@interface\b', r'\b@implementation\b'],
    "lua":         [],
    "plsql":       [r'\bCREATE\s+(OR\s+REPLACE\s+)?PACKAGE\b'],
    "GDScript":    [r'\bclass\s+\w+', r'\bclass_name\s+\w+'],
}

_LOOPS = {
    "javascript":  [r'\bfor\s*\(', r'\bwhile\s*\(', r'\bdo\s*\{', r'\bfor\s+\w+\s+of\b', r'\bfor\s+\w+\s+in\b'],
    "typescript":  [r'\bfor\s*\(', r'\bwhile\s*\(', r'\bdo\s*\{', r'\bfor\s+\w+\s+of\b', r'\bfor\s+\w+\s+in\b'],
    "java":        [r'\bfor\s*\(', r'\bwhile\s*\(', r'\bdo\s*\{'],
    "c":           [r'\bfor\s*\(', r'\bwhile\s*\(', r'\bdo\s*\{'],
    "cpp":         [r'\bfor\s*\(', r'\bwhile\s*\(', r'\bdo\s*\{'],
    "csharp":      [r'\bfor\s*\(', r'\bwhile\s*\(', r'\bdo\s*\{', r'\bforeach\s*\('],
    "go":          [r'\bfor\s+', r'\bfor\s*\{'],
    "rust":        [r'\bfor\s+\w+\s+in\b', r'\bwhile\s+', r'\bloop\s*\{'],
    "swift":       [r'\bfor\s+\w+\s+in\b', r'\bwhile\s+', r'\brepeat\s*\{'],
    "ruby":        [r'\bfor\b', r'\bwhile\b', r'\buntil\b', r'\b\.each\b', r'\b\.times\b', r'\b\.upto\b', r'\b\.loop\b'],
    "php":         [r'\bfor\s*\(', r'\bwhile\s*\(', r'\bforeach\s*\(', r'\bdo\s*\{'],
    "scala":       [r'\bfor\s*\(', r'\bfor\s*\{', r'\bwhile\s*\('],
    "kotlin":      [r'\bfor\s*\(', r'\bwhile\s*\(', r'\bdo\s*\{', r'\b\.forEach\b', r'\b\.repeat\b'],
    "objectivec":  [r'\bfor\s*\(', r'\bwhile\s*\(', r'\bdo\s*\{', r'\bfor\s*\(\s*\w+\s*\*\s*\w+\s+in\b'],
    "lua":         [r'\bfor\b', r'\bwhile\b', r'\brepeat\b'],
    "plsql":       [r'\bFOR\b', r'\bWHILE\b', r'\bLOOP\b'],
    "GDScript":    [r'\bfor\b', r'\bwhile\b'],
}

_INFINITE_LOOPS = {
    "javascript":  [r'\bwhile\s*\(\s*true\s*\)', r'\bwhile\s*\(\s*1\s*\)', r'\bfor\s*\(\s*;\s*;\s*\)'],
    "typescript":  [r'\bwhile\s*\(\s*true\s*\)', r'\bwhile\s*\(\s*1\s*\)', r'\bfor\s*\(\s*;\s*;\s*\)'],
    "java":        [r'\bwhile\s*\(\s*true\s*\)', r'\bwhile\s*\(\s*1\s*\)', r'\bfor\s*\(\s*;\s*;\s*\)'],
    "c":           [r'\bwhile\s*\(\s*1\s*\)', r'\bfor\s*\(\s*;\s*;\s*\)'],
    "cpp":         [r'\bwhile\s*\(\s*true\s*\)', r'\bwhile\s*\(\s*1\s*\)', r'\bfor\s*\(\s*;\s*;\s*\)'],
    "csharp":      [r'\bwhile\s*\(\s*true\s*\)', r'\bfor\s*\(\s*;\s*;\s*\)'],
    "go":          [r'\bfor\s*\{'],
    "rust":        [r'\bloop\s*\{'],
    "swift":       [r'\bwhile\s+true\b', r'\brepeat\s*\{.*\}\s*while\s+true\b'],
    "ruby":        [r'\bloop\s+do\b', r'\bwhile\s+true\b'],
    "php":         [r'\bwhile\s*\(\s*true\s*\)', r'\bfor\s*\(\s*;\s*;\s*\)'],
    "scala":       [r'\bwhile\s*\(\s*true\s*\)'],
    "kotlin":      [r'\bwhile\s*\(\s*true\s*\)', r'\bfor\s*\(\s*;\s*;\s*\)'],
    "objectivec":  [r'\bwhile\s*\(\s*YES\s*\)', r'\bwhile\s*\(\s*1\s*\)', r'\bfor\s*\(\s*;\s*;\s*\)'],
    "lua":         [r'\bwhile\s+true\b', r'\brepeat\b'],
    "plsql":       [r'\bLOOP\b(?!.*\bEND\s+LOOP\b)'],
    "GDScript":    [r'\bwhile\s+true\b'],
}

_IFS = {
    "javascript":  [r'\bif\s*\(', r'\belse\s+if\s*\('],
    "typescript":  [r'\bif\s*\(', r'\belse\s+if\s*\('],
    "java":        [r'\bif\s*\(', r'\belse\s+if\s*\('],
    "c":           [r'\bif\s*\(', r'\belse\s+if\s*\('],
    "cpp":         [r'\bif\s*\(', r'\belse\s+if\s*\('],
    "csharp":      [r'\bif\s*\(', r'\belse\s+if\s*\('],
    "go":          [r'\bif\s+', r'\belse\s+if\s+'],
    "rust":        [r'\bif\s+', r'\belse\s+if\s+', r'\bif\s+let\b', r'\bmatch\b'],
    "swift":       [r'\bif\s+', r'\belse\s+if\s+', r'\bguard\b', r'\bswitch\b'],
    "ruby":        [r'\bif\b', r'\belsif\b', r'\bunless\b', r'\bcase\b'],
    "php":         [r'\bif\s*\(', r'\belseif\s*\(', r'\belse\s+if\s*\('],
    "scala":       [r'\bif\s*\(', r'\belse\s+if\s*\(', r'\bmatch\b'],
    "kotlin":      [r'\bif\s*\(', r'\belse\s+if\s*\(', r'\bwhen\b'],
    "objectivec":  [r'\bif\s*\(', r'\belse\s+if\s*\('],
    "lua":         [r'\bif\b', r'\belseif\b'],
    "plsql":       [r'\bIF\b', r'\bELSIF\b', r'\bCASE\b'],
    "GDScript":    [r'\bif\b', r'\belif\b', r'\bmatch\b'],
}

_FUNCTIONS = {
    "javascript":  [r'\bfunction\s+\w+\s*\(', r'\bconst\s+\w+\s*=\s*(?:async\s*)?\(', r'\blet\s+\w+\s*=\s*(?:async\s*)?\('],
    "typescript":  [r'\bfunction\s+\w+\s*\(', r'\bconst\s+\w+\s*=\s*(?:async\s*)?\(', r'\b\w+\s*\([^)]*\)\s*:\s*\w+\s*\{'],
    "java":        [r'(?:public|private|protected|static|\s)+[\w<>\[\]]+\s+\w+\s*\([^)]*\)\s*(?:throws\s+[\w,\s]+)?\{'],
    "c":           [r'^\s*[\w\*]+\s+\w+\s*\([^)]*\)\s*\{'],
    "cpp":         [r'^\s*[\w\*:<>]+\s+\w+\s*\([^)]*\)\s*(?:const\s*)?\{', r'^\s*\w+::\w+\s*\([^)]*\)'],
    "csharp":      [r'(?:public|private|protected|static|virtual|override|async|\s)+[\w<>\[\]?]+\s+\w+\s*\([^)]*\)\s*\{'],
    "go":          [r'\bfunc\s+\w+\s*\(', r'\bfunc\s+\(\w+\s+\*?\w+\)\s+\w+\s*\('],
    "rust":        [r'\bfn\s+\w+\s*(?:<[^>]*>)?\s*\(', r'\bpub\s+fn\s+\w+\s*\(', r'\basync\s+fn\s+\w+\s*\('],
    "swift":       [r'\bfunc\s+\w+\s*\(', r'\bprivate\s+func\b', r'\bpublic\s+func\b', r'\binternal\s+func\b'],
    "ruby":        [r'\bdef\s+\w+'],
    "php":         [r'\bfunction\s+\w+\s*\(', r'\bpublic\s+function\b', r'\bprivate\s+function\b', r'\bprotected\s+function\b'],
    "scala":       [r'\bdef\s+\w+\s*(?:\([^)]*\))?\s*(?::\s*\w+)?\s*='],
    "kotlin":      [r'\bfun\s+\w+\s*\(', r'\bprivate\s+fun\b', r'\bpublic\s+fun\b', r'\bsuspend\s+fun\b'],
    "objectivec":  [r'[-+]\s*\([^)]+\)\s*\w+', r'[-+]\s*\([^)]+\)\s*\w+\s*:'],
    "lua":         [r'\bfunction\s+\w+\s*\(', r'\blocal\s+function\s+\w+\s*\(', r'\b\w+\s*=\s*function\s*\('],
    "plsql":       [r'\bCREATE\s+(?:OR\s+REPLACE\s+)?(?:FUNCTION|PROCEDURE)\b'],
    "GDScript":    [r'\bfunc\s+\w+\s*\('],
}

_ASYNCS = {
    "javascript":  [r'\basync\s+function\b', r'\basync\s*(?:\([^)]*\)|[^(=>\s]+)\s*=>', r'\bawait\b'],
    "typescript":  [r'\basync\s+function\b', r'\basync\s*(?:\([^)]*\)|[^(=>\s]+)\s*=>', r'\bawait\b'],
    "java":        [r'\bCompletableFuture\b', r'\bFuture\b', r'\bExecutorService\b'],
    "c":           [],
    "cpp":         [r'\bstd::future\b', r'\bstd::async\b', r'\bstd::promise\b'],
    "csharp":      [r'\basync\s+Task\b', r'\bawait\b', r'\bTask\.Run\b', r'\bValueTask\b'],
    "go":          [r'\bgo\s+\w+\('],
    "rust":        [r'\basync\s+fn\b', r'\b\.await\b', r'\btokio::spawn\b'],
    "swift":       [r'\basync\b', r'\bawait\b', r'\b@escaping\b', r'\bDispatchQueue\.async\b'],
    "ruby":        [r'\bAsync\b', r'\bFiber\.new\b'],
    "php":         [r'\bpromise\b', r'\basync\b'],
    "scala":       [r'\bFuture\s*\{', r'\bAwait\.result\b', r'\bpromise\b'],
    "kotlin":      [r'\bsuspend\s+fun\b', r'\blaunch\s*\{', r'\basync\s*\{', r'\bawait\(\)', r'\bCoroutineScope\b'],
    "objectivec":  [r'\bdispatch_async\b', r'\bdispatch_after\b', r'\bcompletion[Hh]andler\b'],
    "lua":         [r'\bcoroutine\.resume\b', r'\bcoroutine\.yield\b'],
    "plsql":       [r'\bDBMS_JOB\b', r'\bDBMS_SCHEDULER\b'],
    "GDScript":    [r'\byield\b', r'\bawait\b'],
}

_GLOBALS = {
    "javascript":  [r'^\s*(?:var|let|const)\s+\w+', r'\bwindow\.\w+\s*='],
    "typescript":  [r'^\s*(?:var|let|const)\s+\w+', r'\bglobal\.\w+\s*='],
    "java":        [r'\bstatic\s+(?!final\b)[\w<>\[\]]+\s+\w+\s*[=;]'],
    "c":           [r'^\s*(?:static\s+)?(?:int|float|double|char|long|short|unsigned|void\s*\*)\s+\w+\s*[=;]'],
    "cpp":         [r'^\s*(?:static\s+)?(?:int|float|double|char|long|auto|string)\s+\w+\s*[=;]', r'^\s*\w+::\w+\s*='],
    "csharp":      [r'\bstatic\s+(?!readonly\b)[\w<>\[\]?]+\s+\w+\s*[=;{]'],
    "go":          [r'^var\s+\w+', r'^[A-Z]\w*\s*='],
    "rust":        [r'\bstatic\s+(?:mut\s+)?\w+\s*:', r'\bstatic\s+\w+\s*:'],
    "swift":       [r'\bstatic\s+var\b', r'\bstatic\s+let\b', r'\bvar\s+\w+\s*=(?!=)'],
    "ruby":        [r'\$\w+', r'@@\w+'],
    "php":         [r'\bstatic\s+\$\w+', r'\bglobal\s+\$\w+'],
    "scala":       [r'\bobject\s+\w+', r'\bvar\s+\w+\s*='],
    "kotlin":      [r'\bcompanion\s+object\b', r'\bobject\s+\w+', r'\bvar\s+\w+\s*='],
    "objectivec":  [r'\bstatic\s+\w+\s+\w+', r'\bextern\s+\w+'],
    "lua":         [r'^\w+\s*=(?!=)'],
    "plsql":       [r'\bPACKAGE\s+BODY\b'],
    "GDScript":    [r'\bvar\s+\w+'],
}

_MEMALLOC = {
    "javascript":  [r'\bnew\s+(?:ArrayBuffer|SharedArrayBuffer|Buffer|DataView)\b'],
    "typescript":  [r'\bnew\s+(?:ArrayBuffer|SharedArrayBuffer|Buffer|DataView)\b'],
    "java":        [r'\bnew\s+byte\[', r'\bnew\s+int\[', r'\bnew\s+char\[', r'\bByteBuffer\.allocate\b'],
    "c":           [r'\bmalloc\s*\(', r'\bcalloc\s*\(', r'\brealloc\s*\(', r'\balloca\s*\('],
    "cpp":         [r'\bnew\s+\w', r'\bmalloc\s*\(', r'\bcalloc\s*\(', r'\brealloc\s*\('],
    "csharp":      [r'\bnew\s+\w+\[', r'\bMarshal\.AllocHGlobal\b', r'\bGCHandle\.Alloc\b'],
    "go":          [r'\bmake\s*\(', r'\bnew\s*\('],
    "rust":        [r'\bBox::new\b', r'\bVec::with_capacity\b', r'\bunsafe\s*\{'],
    "swift":       [r'\bUnsafeMutablePointer\b', r'\bUnsafePointer\b', r'\balloc\b'],
    "ruby":        [],
    "php":         [],
    "scala":       [r'\bnew\s+Array\b', r'\bArrayBuffer\b'],
    "kotlin":      [r'\bArrayOfNulls\b', r'\bByteArray\b', r'\bIntArray\b'],
    "objectivec":  [r'\bmalloc\s*\(', r'\bcalloc\s*\(', r'\balloc\]\s*init\b'],
    "lua":         [],
    "plsql":       [],
    "GDScript":    [],
}

_RANDOM = {
    "javascript":  [r'\bMath\.random\b', r'\bcrypto\.getRandomValues\b'],
    "typescript":  [r'\bMath\.random\b', r'\bcrypto\.getRandomValues\b'],
    "java":        [r'\bMath\.random\b', r'\bnew\s+Random\b', r'\bRandom\(\)', r'\bThreadLocalRandom\b'],
    "c":           [r'\brand\s*\(', r'\bsrand\s*\('],
    "cpp":         [r'\bstd::rand\b', r'\bstd::mt19937\b', r'\bstd::uniform_int_distribution\b'],
    "csharp":      [r'\bnew\s+Random\b', r'\bRandom\.Shared\b', r'\bRandomNumberGenerator\b'],
    "go":          [r'\brand\.Intn\b', r'\brand\.Float\b', r'\bcrypto/rand\b'],
    "rust":        [r'\bRng\b', r'\brand::random\b', r'\bthread_rng\b'],
    "swift":       [r'\bInt\.random\b', r'\bDouble\.random\b', r'\bSystemRandomNumberGenerator\b'],
    "ruby":        [r'\brand\b', r'\bRandom\b', r'\bSecureRandom\b'],
    "php":         [r'\brand\b', r'\bmt_rand\b', r'\brandom_int\b', r'\barray_rand\b'],
    "scala":       [r'\bRandom\b', r'\bscala\.util\.Random\b'],
    "kotlin":      [r'\bRandom\b', r'\bRandom\.nextInt\b', r'\bSecureRandom\b'],
    "objectivec":  [r'\barc4random\b', r'\brand\s*\('],
    "lua":         [r'\bmath\.random\b'],
    "plsql":       [r'\bDBMS_RANDOM\b'],
    "GDScript":    [r'\brandf\b', r'\brandi\b', r'\bRandomNumberGenerator\b'],
}


def extract_features_generic(code: str, language: str) -> list:
    """Regex-based feature extraction for all non-Python languages."""
    lang = language.lower()
    # GDScript key is case-sensitive in lizard but we normalise for pattern lookup
    if language == "GDScript": lang = "GDScript"

    threads       = _n(code, _THREADS.get(lang, []))
    locks         = _n(code, _LOCKS.get(lang, []))
    queues        = _n(code, _QUEUES.get(lang, []))
    classes       = _n(code, _CLASSES.get(lang, []))
    loops         = _n(code, _LOOPS.get(lang, []))
    infinite_loops = _n(code, _INFINITE_LOOPS.get(lang, []))
    ifs           = _n(code, _IFS.get(lang, []))
    functions     = _n(code, _FUNCTIONS.get(lang, []))
    asyncs        = _n(code, _ASYNCS.get(lang, []))
    globals_      = _n(code, _GLOBALS.get(lang, []))
    mem_allocs    = _n(code, _MEMALLOC.get(lang, []))
    random_calls  = _n(code, _RANDOM.get(lang, []))
    loc           = len(code.splitlines())

    return [threads, locks, queues, classes,
            loops, infinite_loops, ifs, functions,
            asyncs, globals_, mem_allocs, random_calls, loc]
