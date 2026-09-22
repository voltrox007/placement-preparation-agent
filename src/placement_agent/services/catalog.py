"""Agent-authored starter content reviewed by Jiya-garg08 on 2026-09-22.

These items support development and demonstrations, not certified assessment.
"""

SKILLS = {
    "python": "Python fundamentals",
    "dsa": "Data structures and algorithms",
    "sql": "SQL and databases",
    "engineering": "Software engineering",
}

# (prompt, options, correct option index, explanation)
ITEMS = {
    "python": [
        (
            "Which Python collection enforces unique elements?",
            ["list", "tuple", "set", "str"],
            2,
            "A set stores distinct hashable elements.",
        ),
        (
            "What does len([1, 2, 3]) return?",
            ["2", "3", "4", "None"],
            1,
            "The list contains three elements.",
        ),
        (
            "Which Python type is immutable?",
            ["list", "dict", "set", "tuple"],
            3,
            "A tuple cannot have its element references reassigned.",
        ),
        (
            "Which construct handles an exception?",
            ["try/except", "if/then", "switch", "repeat"],
            0,
            "An except clause handles a matching raised exception.",
        ),
        (
            "What does a function return when execution reaches its end without return?",
            ["0", "False", "None", "An empty string"],
            2,
            "Python functions implicitly return None.",
        ),
        (
            "Which expression makes a shallow copy of list a?",
            ["a = a", "list(a)", "id(a)", "len(a)"],
            1,
            "list(a) creates a new outer list while retaining references to its elements.",
        ),
        (
            "What is the result of 7 // 2?",
            ["3", "3.5", "4", "1"],
            0,
            "Floor division rounds the quotient down to an integer here.",
        ),
        (
            "Which keyword creates a generator function when used in its body?",
            ["async", "yield", "global", "pass"],
            1,
            "yield produces a value and suspends the generator.",
        ),
        (
            "Which value is a safe default for an optional list argument?",
            ["[]", "list() in the signature", "None", "A shared global list"],
            2,
            "Use None and construct a fresh list inside the function.",
        ),
        (
            "What does 'x' in {'x': 1} test?",
            ["Value membership", "Key membership", "Object identity", "Dictionary length"],
            1,
            "Dictionary membership checks keys.",
        ),
    ],
    "dsa": [
        (
            "Which structure implements FIFO behavior?",
            ["Stack", "Queue", "Set", "Heap"],
            1,
            "A queue removes the earliest enqueued item first.",
        ),
        (
            "Which structure implements LIFO behavior?",
            ["Queue", "Stack", "Graph", "Hash map"],
            1,
            "A stack removes the most recently pushed item first.",
        ),
        (
            "What precondition does ordinary binary search require?",
            ["Distinct elements", "Sorted data", "Positive integers", "An even length"],
            1,
            "Binary search relies on an ordered search space.",
        ),
        (
            "What is binary search's worst-case comparison complexity?",
            ["O(1)", "O(log n)", "O(n)", "O(n squared)"],
            1,
            "Each comparison reduces the remaining interval by roughly half.",
        ),
        (
            "Which traversal finds shortest paths by edge count in an unweighted graph?",
            ["DFS", "BFS", "Inorder", "Random walk"],
            1,
            "BFS explores vertices in increasing distance layers.",
        ),
        (
            "Which data structure is normally used for BFS?",
            ["Queue", "Stack", "Sorted array only", "Recursion only"],
            0,
            "A queue preserves the layer-by-layer frontier order.",
        ),
        (
            "What is the worst-case time of scanning every element of a list once?",
            ["O(1)", "O(log n)", "O(n)", "O(n factorial)"],
            2,
            "One visit per element scales linearly.",
        ),
        (
            "What is a necessary base case property in recursion?",
            [
                "Always calls itself",
                "Stops further recursive calls for some input",
                "Uses a global variable",
                "Returns zero",
            ],
            1,
            "A base case terminates recursion for a defined condition.",
        ),
        (
            "What does a min-heap expose at its root?",
            ["Largest value", "Median", "Smallest value", "Most recent value"],
            2,
            "The heap-order invariant places a minimum at the root.",
        ),
        (
            "What technique stores overlapping subproblem results for reuse?",
            ["Memoization", "Randomization", "Linear search", "Serialization"],
            0,
            "Memoization caches computed subproblem results.",
        ),
    ],
    "sql": [
        (
            "Which clause filters rows before grouping?",
            ["HAVING", "WHERE", "ORDER BY", "SELECT"],
            1,
            "WHERE filters source rows before GROUP BY.",
        ),
        (
            "Which clause filters groups after aggregation?",
            ["WHERE", "HAVING", "FROM", "LIMIT"],
            1,
            "HAVING applies conditions to grouped results.",
        ),
        (
            "Which expression tests for a missing SQL value?",
            ["= NULL", "IS NULL", "== NULL", "NULL = NULL"],
            1,
            "SQL uses IS NULL because ordinary NULL comparisons produce unknown.",
        ),
        (
            "Which JOIN retains all left-side rows?",
            ["INNER JOIN", "LEFT JOIN", "CROSS JOIN only", "No join"],
            1,
            "LEFT JOIN retains unmatched left rows with NULL right columns.",
        ),
        (
            "What does COUNT(*) count?",
            ["Only non-null values in one column", "Rows", "Distinct values only", "Columns"],
            1,
            "COUNT(*) counts rows regardless of NULL column values.",
        ),
        (
            "What does a primary key identify?",
            ["A unique row", "The largest row", "Every index", "The database user"],
            0,
            "A primary key uniquely identifies a row and cannot be NULL.",
        ),
        (
            "What protects a transaction from being partially committed?",
            ["Atomicity", "Sorting", "Denormalization", "Pagination"],
            0,
            "Atomicity gives all-or-nothing transaction effects.",
        ),
        (
            "Which technique prevents SQL injection in value parameters?",
            ["String concatenation", "Parameterized queries", "Removing spaces", "Uppercasing SQL"],
            1,
            "Bound parameters keep values separate from SQL syntax.",
        ),
        (
            "What does a foreign key primarily enforce?",
            ["Output order", "Referential integrity", "Fast sorting", "User authentication"],
            1,
            "A foreign key constrains references to valid related rows.",
        ),
        (
            "Which keyword removes duplicate result rows?",
            ["DISTINCT", "UNIQUE BY", "ONLY", "FIRST"],
            0,
            "SELECT DISTINCT eliminates duplicate result rows.",
        ),
    ],
    "engineering": [
        (
            "What does an HTTP 404 response normally indicate?",
            ["Success", "Resource not found", "Rate limit", "Server restart"],
            1,
            "404 indicates the requested resource was not found.",
        ),
        (
            "What is the main purpose of a unit test?",
            [
                "Deploy the app",
                "Check a focused behavior in isolation",
                "Replace requirements",
                "Measure revenue",
            ],
            1,
            "Unit tests check small, focused behaviors.",
        ),
        (
            "Where should production API secrets be stored?",
            [
                "Public Git repository",
                "Secret manager or protected environment",
                "Browser HTML",
                "Issue comments",
            ],
            1,
            "Secrets belong in protected runtime configuration.",
        ),
        (
            "What does idempotency mean for a request?",
            [
                "It never fails",
                "Repeated application has the same intended effect",
                "It is always fast",
                "It uses HTTP GET",
            ],
            1,
            "Repeating an idempotent operation does not add further intended effects.",
        ),
        (
            "What should a code review primarily assess?",
            [
                "Only line count",
                "Correctness, maintainability and risks",
                "Author popularity",
                "Only formatting",
            ],
            1,
            "Review examines behavior, clarity, maintainability and risks.",
        ),
        (
            "Which Git operation records staged changes locally?",
            ["fetch", "commit", "clone", "status"],
            1,
            "git commit creates a local commit from staged content.",
        ),
        (
            "What is authentication?",
            [
                "Deciding permissions",
                "Verifying identity",
                "Encrypting a database",
                "Sorting users",
            ],
            1,
            "Authentication verifies identity; authorization decides permissions.",
        ),
        (
            "What should happen if one database operation in a transaction fails?",
            [
                "Commit all previous operations unconditionally",
                "Roll back the transaction",
                "Ignore it",
                "Delete the database",
            ],
            1,
            "Rollback prevents partial transaction effects.",
        ),
        (
            "Why add a timeout to an external request?",
            [
                "Guarantee success",
                "Bound how long the application waits",
                "Remove authentication",
                "Prevent all retries",
            ],
            1,
            "A timeout bounds waiting when a dependency stalls.",
        ),
        (
            "What distinguishes a mock from a live integration test?",
            [
                "A mock uses a controlled replacement",
                "Mocks always call production",
                "Live tests need no credentials",
                "They are identical",
            ],
            0,
            "Mocks replace dependencies with controlled behavior.",
        ),
    ],
}

RESOURCES = {
    "python": "https://docs.python.org/3/tutorial/",
    "dsa": "https://opendatastructures.org/",
    "sql": "https://www.sqlite.org/lang.html",
    "engineering": "https://git-scm.com/book/en/v2",
}

INTERVIEW = [
    (
        "engineering",
        "Describe a project you contributed to. Separate your contribution from the team's work.",
    ),
    (
        "engineering",
        "Describe a bug you diagnosed, the evidence you collected, and how you verified the fix.",
    ),
    (
        "sql",
        "Explain how you would model users and their practice attempts in a relational database.",
    ),
    ("python", "Explain how you would handle an external service timeout in a Python application."),
    ("dsa", "Explain when you would use a queue instead of a stack, with a concrete example."),
]
