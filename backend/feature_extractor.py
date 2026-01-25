import ast


class FeatureExtractor(ast.NodeVisitor):
    def __init__(self):
        self.thread_count = 0
        self.lock_count = 0
        self.queue_count = 0
        self.class_count = 0
        self.loop_count = 0
        self.infinite_loop_count = 0
        self.if_count = 0
        self.function_count = 0
        self.async_count = 0
        self.global_var_count = 0
        self.memory_alloc_count = 0
        self.random_call_count = 0

    # --------------------
    # Classes
    # --------------------
    def visit_ClassDef(self, node):
        self.class_count += 1

        # Detect inheritance from Thread
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

        # Detect infinite loop: while True
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
