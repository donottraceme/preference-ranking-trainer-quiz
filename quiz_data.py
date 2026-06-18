"""
Apple AFM — Code Eval Comprehension Quiz (v3) data.

Structured Python representation of every item from
`Project_data/Preference_Ranking_QA_Quiz_v3.md`. Loaded by `quiz.py` to render
the quiz UI. Keep the order identical to the markdown — quiz.py does not shuffle.

Schema (per question):
    id      : str   — stable id, e.g. "A1", "R5a"
    type    : "mcq" | "tf"
    points  : int   — 1 for main items, 2 for pairwise (block H)
    prompt  : str   — markdown allowed
    options : list[tuple[str, str]]
              — (option_id, option_label) pairs. option_id is the letter
                used in the answer key (e.g. "a", "b", "true", "false",
                "a_much", "b_much", "same", ...). option_label is what
                the trainer sees in the radio.
    correct : str   — option_id of the correct answer
    rule    : str   — markdown explanation shown after the trainer answers
"""

from __future__ import annotations


# Pairwise option set used by every item in block H. Kept as a module-level
# constant so the 7-point scale stays consistent across all R items.
_PAIRWISE_AB = [
    ("a_much", "A Much Better"),
    ("a_better", "A Better"),
    ("a_slight", "A Slightly Better"),
    ("same", "Same"),
    ("b_slight", "B Slightly Better"),
    ("b_better", "B Better"),
    ("b_much", "B Much Better"),
]

# R5a compares A vs D instead of A vs B — same scale, different letters.
_PAIRWISE_AD = [
    ("a_much", "A Much Better"),
    ("a_better", "A Better"),
    ("a_slight", "A Slightly Better"),
    ("same", "Same"),
    ("d_slight", "D Slightly Better"),
    ("d_better", "D Better"),
    ("d_much", "D Much Better"),
]

# R5b compares B vs C.
_PAIRWISE_BC = [
    ("b_much", "B Much Better"),
    ("b_better", "B Better"),
    ("b_slight", "B Slightly Better"),
    ("same", "Same"),
    ("c_slight", "C Slightly Better"),
    ("c_better", "C Better"),
    ("c_much", "C Much Better"),
]

_TF_OPTIONS = [("true", "True"), ("false", "False")]


QUIZ: dict = {
    "version": "v3",
    "max_points": 34,
    "blurb": (
        "**Format:** MCQ + True/False. Each answer freezes the moment you "
        "click it and the correct answer + rule are revealed inline. "
        "Coverage: every dimension (FI / Concision / Truthfulness / "
        "Satisfaction) gets base + code-eval questions, plus highlighted-rules "
        "items and 6 pairwise scenarios."
    ),
    "blocks": [
        # ---------------------------------------------------------------
        # A. Step 1 — User Request Analysis
        # ---------------------------------------------------------------
        {
            "id": "A",
            "title": "A. Step 1 — User Request Analysis",
            "questions": [
                {
                    "id": "A1",
                    "type": "mcq",
                    "points": 1,
                    "prompt": (
                        "Which of the following is **NOT** a valid reason to "
                        "skip a task via \"Report a Problem\"?"
                    ),
                    "options": [
                        ("a", "The UI is broken and your rating selections cannot be submitted."),
                        ("b", "The user request is in French and your locale is fr_FR but you only speak English."),
                        ("c", "The response sequence has letters A, C, D, F (no B, no E)."),
                        ("d", "The prompt is *\"And hooptiously drangle me with crinkly bindlewurdles.\"*"),
                    ],
                    "correct": "c",
                    "rule": (
                        "**Answer: c.**  \n"
                        "**Rule (§3.3):** Letter gaps in the response sequence "
                        "(A, C, D, F is fine) are explicitly listed under *\"do "
                        "not skip when\"* for Technical Issues. (a) is a valid "
                        "Technical Issues skip; (b) is valid Wrong-Language; "
                        "(d) is valid Gibberish."
                    ),
                },
                {
                    "id": "A2",
                    "type": "tf",
                    "points": 1,
                    "prompt": (
                        "**True / False:** *\"If the user request contains a "
                        "link, you can rate the response without opening the "
                        "link as long as the response addresses the question "
                        "on its own.\"*"
                    ),
                    "options": _TF_OPTIONS,
                    "correct": "false",
                    "rule": (
                        "**Answer: False.**  \n"
                        "**Rule (§3.1 + §4.5):** *\"Open every link in the user "
                        "request before judging the response. Links are part of "
                        "the request.\"* Skipping a link can mean missing "
                        "constraints, examples, or the entire data set the "
                        "response was supposed to use."
                    ),
                },
            ],
        },
        # ---------------------------------------------------------------
        # B. Following Instructions
        # ---------------------------------------------------------------
        {
            "id": "B",
            "title": "B. Following Instructions",
            "questions": [
                {
                    "id": "B1",
                    "type": "mcq",
                    "points": 1,
                    "prompt": (
                        "A user asks: *\"Write a Python function. Just the "
                        "code, no comments.\"* The response is a correct, "
                        "working function — but starts with `# Solution:` on "
                        "line 1 and ends with `# end of function` on the last "
                        "line. **Following Instructions** rating?"
                    ),
                    "options": [
                        ("a", "Fully Following — the code works."),
                        ("b", "Partially Following — the code follows the request but ignores \"no comments\"."),
                        ("c", "Not Following — the code has comments."),
                        ("d", "Truthfulness issue, not FI."),
                    ],
                    "correct": "b",
                    "rule": (
                        "**Answer: b — Partially Following.**  \n"
                        "**Rule (§4.1 guardrails):** *\"Just the code, no "
                        "comment\" → comments in the response = Partially / Not "
                        "Following.* Truthfulness is fine (the code works); the "
                        "violation is the explicit \"no comments\" instruction."
                    ),
                },
                {
                    "id": "B2",
                    "type": "mcq",
                    "points": 1,
                    "prompt": (
                        "*\"What is the capital of Oregon?\"* → response: "
                        "*\"The capital city of Oregon is Portland.\"* What is "
                        "the **Following Instructions** rating?"
                    ),
                    "options": [
                        ("a", "Not Following — the answer is wrong."),
                        ("b", "Partially Following — wrong answer counts partially."),
                        ("c", "Fully Following — the response attempts to answer the question."),
                        ("d", "Cannot be rated separately from Truthfulness."),
                    ],
                    "correct": "c",
                    "rule": (
                        "**Answer: c — Fully Following** (Truthfulness is "
                        "separately Not Truthful — Salem is the capital).  \n"
                        "**Rule (§4.1):** *\"Following Instructions is "
                        "**independent** of Truthfulness — Portland is the "
                        "capital of Oregon still attempts to answer the "
                        "question.\"* The two dimensions disagree here on "
                        "purpose."
                    ),
                },
                {
                    "id": "B3",
                    "type": "mcq",
                    "points": 1,
                    "prompt": (
                        "**[CODE]** A user asks: *\"Write the function in "
                        "**Python**, no third-party libraries.\"* The response "
                        "provides a clean, correct implementation — **in "
                        "JavaScript**. **FI rating?**"
                    ),
                    "options": [
                        ("a", "Fully Following — the function is correct."),
                        ("b", "Partially Following — wrong language but correct logic."),
                        ("c", "Not Following — the explicit language instruction was ignored."),
                        ("d", "Localization issue — the code should be in Python."),
                    ],
                    "correct": "c",
                    "rule": (
                        "**Answer: c — Not Following.**  \n"
                        "**Rule (§4.1 guardrails, v3.1+):** *\"Wrong response "
                        "language → Not Following.\"* The user's explicit "
                        "programming language requirement is treated the same "
                        "as any other ignored explicit instruction. "
                        "(Localization is hidden for en_US and is about prose, "
                        "not code.)"
                    ),
                },
                {
                    "id": "B4",
                    "type": "mcq",
                    "points": 1,
                    "prompt": (
                        "**[CODE]** A user asks: *\"Implement the function "
                        "with this exact signature: `def merge_lists(a: "
                        "list[int], b: list[int]) -> list[int]:`.\"* The "
                        "response is logically correct but defines `def "
                        "merge(arr1, arr2):` (renamed function, untyped "
                        "parameters). **FI rating?**"
                    ),
                    "options": [
                        ("a", "Fully Following — the logic is right."),
                        ("b", "Partially Following — the signature was an explicit instruction and was ignored."),
                        ("c", "Not Truthful — the function name is wrong."),
                        ("d", "Concision issue — too verbose."),
                    ],
                    "correct": "b",
                    "rule": (
                        "**Answer: b — Partially Following.**  \n"
                        "**Rule (§4.1):** A specified function signature is an "
                        "explicit instruction (format/style). Most main "
                        "instructions were obeyed (the function works), but the "
                        "signature was not — exactly the *\"most but not all "
                        "instructions obeyed\"* definition of Partially "
                        "Following."
                    ),
                },
            ],
        },
        # ---------------------------------------------------------------
        # C. Concision
        # ---------------------------------------------------------------
        {
            "id": "C",
            "title": "C. Concision",
            "questions": [
                {
                    "id": "C1",
                    "type": "mcq",
                    "points": 1,
                    "prompt": (
                        "A user asks: *\"Can you explain the process of "
                        "photosynthesis in 2 lines?\"* Response B is two "
                        "paragraphs and 120 words — well-written, no factual "
                        "errors. **Concision rating + the follow-up:**"
                    ),
                    "options": [
                        ("a", "Good (no follow-up needed)."),
                        ("b", "Acceptable — could have been made shorter."),
                        ("c", "Bad — could have been made shorter."),
                        ("d", "Bad — could have been made longer."),
                    ],
                    "correct": "c",
                    "rule": (
                        "**Answer: c — Bad, could have been made shorter.**  \n"
                        "**Rule (§4.3 Example — Simple):** *\"Length "
                        "restrictions given by the user are not followed.\"* "
                        "The user gave an explicit 2-line cap; two paragraphs "
                        "/ 120 words violates the length restriction "
                        "regardless of factual accuracy. When Bad/Acceptable, "
                        "you **must** pick \"shorter\" or \"longer\"."
                    ),
                },
                {
                    "id": "C2",
                    "type": "tf",
                    "points": 1,
                    "prompt": (
                        "**True / False:** *\"If Response A is 50 words and "
                        "Response B is 200 words, A is automatically more "
                        "concise (Good) and B is automatically Acceptable / "
                        "Bad.\"*"
                    ),
                    "options": _TF_OPTIONS,
                    "correct": "false",
                    "rule": (
                        "**Answer: False.**  \n"
                        "**Rule (§4.3 guardrails):** *\"Judge each response "
                        "**independently** — don't compare lengths.\"* A "
                        "200-word answer can be Good if the user asked for "
                        "detail; a 50-word answer can be Bad if it's all "
                        "filler (\"Great question! As an AI…\"). Length alone "
                        "is not the rating."
                    ),
                },
                {
                    "id": "C3",
                    "type": "mcq",
                    "points": 1,
                    "prompt": (
                        "**[CODE]** User: *\"Write a Python bubble sort. "
                        "**Just the code, no comments**.\"* Response opens "
                        "with *\"Sure! Here's a bubble sort implementation:\"*"
                        ", then the correct code, then *\"Hope this helps! "
                        "Let me know if you'd like a stricter version.\"* "
                        "**Concision rating?**"
                    ),
                    "options": [
                        ("a", "Good — the code itself is tight."),
                        ("b", "Acceptable — minor preamble."),
                        ("c", "Bad — could have been made shorter."),
                        ("d", "Bad — could have been made longer."),
                    ],
                    "correct": "c",
                    "rule": (
                        "**Answer: c — Bad, could have been made shorter.**  \n"
                        "**Rule (§4.3 + §4.1):** When the user said *\"just "
                        "the code\"*, *\"surrounding prose is filler\"* — the "
                        "preamble and the trailing prose are textbook "
                        "Concision distractions. (Same response is also "
                        "**Partially Following** for the same reason — "
                        "Concision and FI both flag this.)"
                    ),
                },
                {
                    "id": "C4",
                    "type": "mcq",
                    "points": 1,
                    "prompt": (
                        "**[CODE]** User: *\"How do I sort a list in "
                        "Python? **Explain in detail.**\"* Response is 400 "
                        "words covering `list.sort()` vs `sorted()`, the "
                        "`key` parameter, `reverse`, stability, and time "
                        "complexity — well-organized, no anecdotes, no "
                        "filler. **Concision rating?**"
                    ),
                    "options": [
                        ("a", "Bad — far too long."),
                        ("b", "Acceptable — slightly long."),
                        ("c", "Good — length is proportionate to \"in detail\" and there is no filler."),
                        ("d", "Cannot judge without seeing other responses."),
                    ],
                    "correct": "c",
                    "rule": (
                        "**Answer: c — Good.**  \n"
                        "**Rule (§4.3):** *\"Even a 500-word response is "
                        "concise if the user asked for it.\"* Once length is "
                        "specified (\"in detail\"), Concision only judges "
                        "word-quality, not word-count. No distractions = Good."
                    ),
                },
            ],
        },
        # ---------------------------------------------------------------
        # D. Truthfulness
        # ---------------------------------------------------------------
        {
            "id": "D",
            "title": "D. Truthfulness",
            "questions": [
                {
                    "id": "D1",
                    "type": "mcq",
                    "points": 1,
                    "prompt": (
                        "**[CODE]** User: *\"Provide example python code to "
                        "draw 60 random samples **without replacement** and "
                        "compute their average.\"* The response uses "
                        "`np.random.randint(0, population_size, "
                        "size=sample_size)` for the indices and prints the "
                        "mean. **Most accurate Truthfulness rating per the "
                        "source?**"
                    ),
                    "options": [
                        ("a", "Truthful — the mean computation is correct."),
                        ("b", "Partially Truthful — the sampling step (primary requirement) is wrong."),
                        ("c", "Not Truthful — fabricated APIs."),
                        ("d", "Accuracy doesn't apply to coding."),
                    ],
                    "correct": "b",
                    "rule": (
                        "**Answer: b — Partially Truthful** (some annotators "
                        "rate Not Truthful since the core requirement is "
                        "broken).  \n"
                        "**Rule (§4.4 Example — Coding, verbatim):** *\"This "
                        "example not following instruction is the same as "
                        "being inaccurate too — often the case with math and "
                        "coding related user requests.\"* The mean step is "
                        "correct; the sampling step (primary) is wrong."
                    ),
                },
                {
                    "id": "D2",
                    "type": "mcq",
                    "points": 1,
                    "prompt": (
                        "A user supplies a passage about Japanese pro "
                        "wrestling and asks *\"Extract the names of all "
                        "people in this text.\"* The response lists every "
                        "name from the text **plus** adds biographical "
                        "sentences (years, nicknames, achievements) that "
                        "**were not in the supplied passage**, even though "
                        "the biographical info is factually accurate in the "
                        "real world. **Truthfulness rating?**"
                    ),
                    "options": [
                        ("a", "Truthful — everything stated is true in the real world."),
                        ("b", "Partially Truthful — primary correct, secondary embellished."),
                        ("c", "Not Truthful — outside info on a context-restricted task."),
                        ("d", "Slightly Satisfying — minor over-reach."),
                    ],
                    "correct": "c",
                    "rule": (
                        "**Answer: c — Not Truthful.**  \n"
                        "**Rule (§4.4):** *\"For Q&A from a provided body of "
                        "text… if the response is based on some information "
                        "not mentioned in the given text, it is not truthful "
                        "either.\"* Adding outside info is Not Truthful even "
                        "when factually accurate. Real-world accuracy doesn't "
                        "override context-restriction."
                    ),
                },
                {
                    "id": "D3",
                    "type": "tf",
                    "points": 1,
                    "prompt": (
                        "**True / False:** *\"For a math word problem, if "
                        "the response gives the correct final number but the "
                        "reasoning chain shown to the user contains an "
                        "arithmetic mistake in the middle, the rating is "
                        "still Truthful because the answer is right.\"*"
                    ),
                    "options": _TF_OPTIONS,
                    "correct": "false",
                    "rule": (
                        "**Answer: False.**  \n"
                        "**Rule (§4.4):** *\"For math/reasoning requests, the "
                        "final answer is correct but the reasoning is "
                        "incorrect\"* → **Partially Truthful**, not Truthful. "
                        "*\"Both answer **and** reasoning must be right for "
                        "Truthful.\"* (Same logic applies to code: right "
                        "output by accident, wrong logic shown = Partially "
                        "Truthful.)"
                    ),
                },
                {
                    "id": "D4",
                    "type": "mcq",
                    "points": 1,
                    "prompt": (
                        "**[CODE]** A response computes the median of "
                        "`[1, 2, 3, 4]` and returns `3` (the upper-middle "
                        "element). The user explicitly said *\"average the "
                        "two middle values when count is even.\"* The "
                        "function is correct on odd-length lists. "
                        "**Truthfulness rating?**"
                    ),
                    "options": [
                        ("a", "Truthful — works on most inputs."),
                        ("b", "Partially Truthful — primary logic correct, fails on a documented edge case."),
                        ("c", "Not Truthful — wrong output."),
                        ("d", "Concision issue, not Truthfulness."),
                    ],
                    "correct": "b",
                    "rule": (
                        "**Answer: b — Partially Truthful.**  \n"
                        "**Rule (§4.4 scale):** *\"For coding requests, the "
                        "code might fail in edge cases but code's logic is "
                        "correct.\"* Odd-length is fine; even-length is "
                        "broken — that's an edge-case failure on a primary "
                        "requirement → Partially Truthful (not Not Truthful, "
                        "because the algorithm is in the right ballpark)."
                    ),
                },
                {
                    "id": "D5",
                    "type": "mcq",
                    "points": 1,
                    "prompt": (
                        "**[CODE]** A response includes the line `result = "
                        "numpy.argmin_with_index(arr)` to get both the "
                        "minimum value and its index in one call. NumPy has "
                        "`np.argmin()` and `np.min()` but **no** "
                        "`argmin_with_index`. The function then proceeds "
                        "assuming this call returned a `(value, index)` "
                        "tuple. **Truthfulness rating?**"
                    ),
                    "options": [
                        ("a", "Truthful — the intent is clear."),
                        ("b", "Partially Truthful — only one line is wrong."),
                        ("c", "Not Truthful — the code uses a fabricated API and will crash."),
                        ("d", "Satisfaction issue, not Truthfulness."),
                    ],
                    "correct": "c",
                    "rule": (
                        "**Answer: c — Not Truthful.**  \n"
                        "**Rule (§4.4):** *\"For coding requests, the code "
                        "has mistakes that will lead to incorrect outputs\"* "
                        "→ Not Truthful. Hallucinated APIs / methods are the "
                        "most common code Truthfulness failure — the code "
                        "doesn't run at all, so the primary requirement is "
                        "broken."
                    ),
                },
                {
                    "id": "D6",
                    "type": "mcq",
                    "points": 1,
                    "prompt": (
                        "**[CODE]** User: *\"Write a **SQL Server** query "
                        "that returns rows 21–30 of `Orders` ordered by "
                        "`OrderDate`.\"* Response: *\"Use `SELECT * FROM "
                        "Orders ORDER BY OrderDate LIMIT 10 OFFSET 20;`.\"* "
                        "That is **MySQL/PostgreSQL** syntax — SQL Server "
                        "requires `OFFSET 20 ROWS FETCH NEXT 10 ROWS ONLY`. "
                        "**Truthfulness rating?**"
                    ),
                    "options": [
                        ("a", "Truthful — the logic is correct in the abstract."),
                        ("b", "Partially Truthful — only the dialect is off."),
                        ("c", "Not Truthful — the query will not run on the dialect the user asked for, so the primary requirement is broken."),
                        ("d", "Following Instructions issue, not Truthfulness."),
                    ],
                    "correct": "c",
                    "rule": (
                        "**Answer: c — Not Truthful.** (FI is also Partially "
                        "/ Not Following — both can fail simultaneously.)  \n"
                        "**Rule (§4.4):** When the user constrains the "
                        "dialect/version/runtime, *\"answering the wrong "
                        "question\"* — even with otherwise sensible logic — "
                        "is Not Truthful. The code will literally not run on "
                        "the user's database. *\"Truthfulness can differ by "
                        "locale\"* — and by dialect/runtime — so verify "
                        "against the **user's** stated environment."
                    ),
                },
            ],
        },
        # ---------------------------------------------------------------
        # E. Satisfaction
        # ---------------------------------------------------------------
        {
            "id": "E",
            "title": "E. Satisfaction",
            "questions": [
                {
                    "id": "E1",
                    "type": "mcq",
                    "points": 1,
                    "prompt": (
                        "Per the holistic-logic table, if **Concision = "
                        "Bad** and the prompt is harmless, what Satisfaction "
                        "levels are still allowed?"
                    ),
                    "options": [
                        ("a", "Highly Satisfying or Slightly Satisfying."),
                        ("b", "Slightly Satisfying or Slightly Unsatisfying."),
                        ("c", "Slightly Unsatisfying or Highly Unsatisfying."),
                        ("d", "Any of the four levels — the dimensions are independent."),
                    ],
                    "correct": "c",
                    "rule": (
                        "**Answer: c — Slightly Unsatisfying or Highly "
                        "Unsatisfying.**  \n"
                        "**Rule (§4.5 holistic-logic table, row 1):** *\"Any "
                        "dimension at its lowest level (Not Following / Bad "
                        "/ Not Truthful) → Satisfaction can only be Slightly "
                        "Unsatisfying or Highly Unsatisfying.\"*"
                    ),
                },
                {
                    "id": "E2",
                    "type": "mcq",
                    "points": 1,
                    "prompt": (
                        "**[CODE]** User: *\"Can you write me a C++ function "
                        "to find the intersection of two lists?\"* Response: "
                        "a syntactically correct nested-loop function "
                        "(O(n·m)) that returns the right answer on every "
                        "input. **Most likely Satisfaction rating per the "
                        "source?**"
                    ),
                    "options": [
                        ("a", "Highly Satisfying — the code works."),
                        ("b", "Slightly Satisfying — correct but not optimized."),
                        ("c", "Slightly Unsatisfying — the algorithm is slow."),
                        ("d", "Highly Unsatisfying — performance issues are critical."),
                    ],
                    "correct": "b",
                    "rule": (
                        "**Answer: b — Slightly Satisfying.**  \n"
                        "**Rule (§4.5 Example — Coding, verbatim):** *\"The "
                        "C++ function is correct and returns the desired "
                        "intersection. However, the code can be further "
                        "optimized in terms of time complexity by using map "
                        "or ordered_map.\"* Highly-Satisfying-for-code "
                        "requires *\"optimized in terms of time and space "
                        "complexity\"* — so unoptimized correct code can't "
                        "be Highly Satisfying."
                    ),
                },
                {
                    "id": "E3",
                    "type": "mcq",
                    "points": 1,
                    "prompt": (
                        "**[CODE]** A 40-line recursive backtracking "
                        "function for \"solve a Sudoku\" is **logically "
                        "correct** and passes all test puzzles. Variables "
                        "are named `a`, `b`, `c`, `tmp`, `flag`. There are "
                        "zero comments and zero docstrings. **Most "
                        "appropriate Satisfaction rating per the source's "
                        "coding criteria?**"
                    ),
                    "options": [
                        ("a", "Highly Satisfying — correctness is what matters."),
                        ("b", "Slightly Satisfying — correct but fails the \"good naming + non-trivial code well-documented\" criteria for Highly Satisfying."),
                        ("c", "Slightly Unsatisfying — bad style is a major issue."),
                        ("d", "Highly Unsatisfying — uncommented code is unreadable."),
                    ],
                    "correct": "b",
                    "rule": (
                        "**Answer: b — Slightly Satisfying.**  \n"
                        "**Rule (§4.5 coding criteria for Highly "
                        "Satisfying):** *\"good variable and function "
                        "naming, well-structured… any non-trivial code "
                        "should be well-documented.\"* All five "
                        "Highly-Satisfying coding bullets must hold; this "
                        "response misses two of them, so it caps at "
                        "Slightly Satisfying."
                    ),
                },
            ],
        },
        # ---------------------------------------------------------------
        # F. Preference Ranking — theory
        # ---------------------------------------------------------------
        {
            "id": "F",
            "title": "F. Preference Ranking — theory",
            "questions": [
                {
                    "id": "F1",
                    "type": "mcq",
                    "points": 1,
                    "prompt": (
                        "Which of the following is the **#1 tiebreaker** "
                        "when two responses have similar overall "
                        "Satisfaction?"
                    ),
                    "options": [
                        ("a", "Whichever is shorter — concision wins ties."),
                        ("b", "Whichever is better-formatted — formatting wins ties."),
                        ("c", "Whichever is more truthful on essentials."),
                        ("d", "Whichever uses more idiomatic code style."),
                    ],
                    "correct": "c",
                    "rule": (
                        "**Answer: c — more truthful on essentials.**  \n"
                        "**Rule (§5.2 tiebreaker 1):** *\"Truthfulness wins "
                        "ties. When two responses have similar level of "
                        "satisfaction, prefer the more truthful "
                        "response.\"* Length, formatting, and idiom are "
                        "explicitly **not** primary tiebreakers — they only "
                        "break ties when truthfulness, completeness, and "
                        "clarification-vs-assumption are all equal."
                    ),
                },
                {
                    "id": "F2",
                    "type": "tf",
                    "points": 1,
                    "prompt": (
                        "**True / False:** *\"If the prompt is "
                        "offensive/dangerous and Response A engages with it "
                        "(producing harmful content of higher quality) "
                        "while Response B refuses politely with a reason, A "
                        "can still be ranked 'Much Better' if the engaging "
                        "content is clearly more thorough.\"*"
                    ),
                    "options": _TF_OPTIONS,
                    "correct": "false",
                    "rule": (
                        "**Answer: False.**  \n"
                        "**Rule (§4.5 offensive/dangerous decision tree + §5 "
                        "ranking):** *\"If the 'better' response engaged "
                        "with harmful content → CANNOT be 'Much Better'.\"* "
                        "The refusing response is preferred; the engaging "
                        "response can never reach the Much-Better tier on a "
                        "harmful prompt. Always flag the harmful nature in "
                        "your English-language comment."
                    ),
                },
                {
                    "id": "F3",
                    "type": "tf",
                    "points": 1,
                    "prompt": (
                        "**True / False:** *\"If two responses are "
                        "essentially duplicates of each other (or you "
                        "genuinely cannot distinguish them on any "
                        "dimension), you must still pick a side — 'Same' is "
                        "not a real option.\"*"
                    ),
                    "options": _TF_OPTIONS,
                    "correct": "false",
                    "rule": (
                        "**Answer: False.**  \n"
                        "**Rule (§5.1 + §5.3):** *\"Same: equally helpful, "
                        "or equally unhelpful, or duplicates, or you "
                        "genuinely cannot differentiate.\"* \"Same\" is a "
                        "valid ranking — use it for true ties or duplicates "
                        "rather than guessing."
                    ),
                },
            ],
        },
        # ---------------------------------------------------------------
        # G. Comments
        # ---------------------------------------------------------------
        {
            "id": "G",
            "title": "G. Comments",
            "questions": [
                {
                    "id": "G1",
                    "type": "mcq",
                    "points": 1,
                    "prompt": (
                        "Which of these is the **best** comment per the "
                        "source's guidance?"
                    ),
                    "options": [
                        ("a", "*\"All responses are concise, follow instructions, harmless and satisfying.\"*"),
                        ("b", "*\"I ranked the responses based on the helpful, truthful, and harmless principles.\"*"),
                        ("c", "*\"C is the most complete and most informative. Ranked 1. B is rank 2 — close to rank 1 but missing details on edge-case handling for empty input. A and D are too generic. E expresses biased judgement on the user's coding style and is ranked worst.\"*"),
                        ("d", "*\"It would be the best response but contains issues.\"*"),
                    ],
                    "correct": "c",
                    "rule": (
                        "**Answer: c.**  \n"
                        "**Rule (§6.2):** This pattern is the source's *Good "
                        "Example 2* — names every response, ties each "
                        "placement to a specific reason, and is comparative "
                        "throughout. The other three are quoted verbatim "
                        "from §6.2 as **bad** comments — generic / "
                        "non-comparative / vague."
                    ),
                },
                {
                    "id": "G3",
                    "type": "mcq",
                    "points": 1,
                    "prompt": (
                        "The source labels this as a **bad** comment: "
                        "*\"Response B is better than Response A because it "
                        "follows instructions more and A has some issues.\"* "
                        "Which of the following rewrites is the **best** "
                        "replacement per §6.2 guidance?"
                    ),
                    "options": [
                        ("a", "*\"B is much better than A in every way.\"*"),
                        ("b", "*\"B is preferred. Both functions compute the median correctly for non-empty input, but A throws `IndexError` on empty input while B returns `None` with a guard clause — the user explicitly asked for empty-input handling. Truthfulness on the empty-input edge case decides it; readability is comparable.\"*"),
                        ("c", "*\"B follows instructions, is truthful, and is concise. A does not follow instructions as well.\"*"),
                        ("d", "*\"I prefer B based on the helpful-truthful-harmless principle.\"*"),
                    ],
                    "correct": "b",
                    "rule": (
                        "**Answer: b.**  \n"
                        "**Rule (§6.1):** A good comment **names** both "
                        "responses, **compares** them on a **concrete** "
                        "difference (named function / error / edge case), "
                        "and **identifies which dimension drives the "
                        "ranking**. (a) is generic; (c) restates the "
                        "dimension labels without specifics; (d) is the "
                        "explicit anti-pattern from §6.2."
                    ),
                },
            ],
        },
        # ---------------------------------------------------------------
        # H. Pairwise Ranking — 5 scenarios (R5 splits into 5a + 5b)
        # ---------------------------------------------------------------
        {
            "id": "H",
            "title": "H. Pairwise Ranking — source-grounded scenarios",
            "intro": (
                "Apply the 7-point scale and the tiebreaker rules. Each "
                "pairwise item is worth **2 points**."
            ),
            "questions": [
                {
                    "id": "R1",
                    "type": "mcq",
                    "points": 2,
                    "prompt": (
                        "**R1 — Multi-turn context (Washington capital)**  \n"
                        "> **Prior turn:** *\"What is the capital of Texas?\"* "
                        "→ assistant: *\"The capital of Texas is Austin.\"*  \n"
                        "> **User's next turn:** *\"How about Washington "
                        "state?\"*\n\n"
                        "| | Response A | Response B |\n"
                        "| --- | --- | --- |\n"
                        "| Text | *\"Washington is located on the West Coast "
                        "of the United States, and is bordered by the "
                        "Canadian province of British Columbia to the north, "
                        "Oregon to the south, Idaho to the east, and the "
                        "Pacific Ocean to the west.\"* | *\"The capital of "
                        "Washington state is Olympia.\"* |"
                    ),
                    "options": _PAIRWISE_AB,
                    "correct": "b_much",
                    "rule": (
                        "**Answer: B Much Better.**  \n"
                        "**Rule (§5.4 verbatim):** *\"B is much more "
                        "useful/satisfying than A since the user is seeking "
                        "the capital city of Washington state based on the "
                        "context.\"* A doesn't address the request at all "
                        "(answers a different question); B answers it "
                        "directly → meets the **Much Better** criterion: "
                        "*\"One response addresses the request and the other "
                        "does not.\"*"
                    ),
                },
                {
                    "id": "R2",
                    "type": "mcq",
                    "points": 2,
                    "prompt": (
                        "**R2 — Time-sensitive request (FIFA World Cup)**  \n"
                        "> **User Request:** *\"Which country won the latest "
                        "FIFA World Cup?\"*\n\n"
                        "| | Response A | Response B |\n"
                        "| --- | --- | --- |\n"
                        "| Text | *\"As of my knowledge up until December "
                        "2021, France is the champion of the most recent "
                        "FIFA World Cup in 2018.\"* | *\"As of my knowledge "
                        "up until July 2023, the 2022 FIFA World Cup was won "
                        "by Argentina.\"* |"
                    ),
                    "options": _PAIRWISE_AB,
                    "correct": "b_much",
                    "rule": (
                        "**Answer: B Much Better.**  \n"
                        "**Rule (§5.4 verbatim):** *\"The information in A "
                        "is no longer accurate.\"* Per §5.2 tiebreaker 1 "
                        "(Truthfulness wins) and §5.3 *\"Time-sensitive → "
                        "prefer the response most accurate as of today.\"* "
                        "A is outdated (Not Truthful); B is current "
                        "(Truthful)."
                    ),
                },
                {
                    "id": "R3",
                    "type": "mcq",
                    "points": 2,
                    "prompt": (
                        "**R3 — Surface vs. substance (Google Sheets "
                        "filter)**  \n"
                        "> **User Request:** *\"How to filter a column in "
                        "google sheet\"*\n\n"
                        "| | Response A | Response B |\n"
                        "| --- | --- | --- |\n"
                        "| Text (excerpt) | Short, accurate, follows the "
                        "actual Google Sheets UI: *\"Click on the letter at "
                        "the top of the column you want to filter… Click on "
                        "'Data' → 'Create a filter'…\"* | Longer, "
                        "multi-method, better-formatted, **but** describes "
                        "UI fields that don't exist in Google Sheets: "
                        "*\"Method 1: Filter by Cell Value… Click 'Filter "
                        "Views' → 'Create new filter view.' Enter the "
                        "criteria in the **Search Criteria** field…\"* (no "
                        "such field exists). |"
                    ),
                    "options": _PAIRWISE_AB,
                    "correct": "a_better",
                    "rule": (
                        "**Answer: A Better.**  \n"
                        "**Rule (§5.5 verbatim):** *\"Although B provides "
                        "more options for filtering a column and has better "
                        "formatting, the steps it describes are incorrect "
                        "if we apply its instructions to Google Sheets. On "
                        "the other hand, A provides a correct and concise "
                        "response.\"* Per §5.3: *\"Recall that a longer "
                        "response is NOT necessarily better.\"* "
                        "Truthfulness on essentials beats length + "
                        "formatting → Better (not Much Better — both engage "
                        "with the request)."
                    ),
                },
                {
                    "id": "R5a",
                    "type": "mcq",
                    "points": 2,
                    "prompt": (
                        "**R5a — A vs. D (both generic; A slightly easier "
                        "to understand)**  \n"
                        "> **Source ground truth (from §6.2 Good Example "
                        "2):** for a 5-response set, the source's analyst "
                        "ranked **C > B > A > D > E**, with rationale: "
                        "*\"…A and D are ranked 3 and 4 because they are "
                        "too generic and lack of details. A is slightly "
                        "easier to understand…\"*"
                    ),
                    "options": _PAIRWISE_AD,
                    "correct": "a_slight",
                    "rule": (
                        "**Answer: A Slightly Better.**  \n"
                        "**Rule (§5.1 + §6.2):** Both are equally generic "
                        "on the primary dimension; A wins only on a minor "
                        "stylistic axis (readability) → **Slightly "
                        "Better**, per §5.1: *\"both address the request, "
                        "but one is mildly superior on a minor aspect.\"* "
                        "(Stylistic preference alone is never enough for "
                        "\"Better\".)"
                    ),
                },
                {
                    "id": "R5b",
                    "type": "mcq",
                    "points": 2,
                    "prompt": (
                        "**R5b — B vs. C (B is \"very close to rank 1\", "
                        "missing some details)**  \n"
                        "> Same source ground truth as R5a — C is Rank 1, "
                        "B is Rank 2: *\"B is ranked 2 — very close to "
                        "Rank 1 but missing some details on XXX.\"*"
                    ),
                    "options": _PAIRWISE_BC,
                    "correct": "c_slight",
                    "rule": (
                        "**Answer: C Slightly Better.**  \n"
                        "**Rule (§5.1):** *\"More truthful on "
                        "non-essentials\"* / minor completeness gap → "
                        "**Slightly Better**, not Better. The source's own "
                        "phrasing (\"very close to Rank 1, missing some "
                        "details\") is the textbook description of a "
                        "Slightly-Better gap."
                    ),
                },
            ],
        },
    ],
}


def iter_questions():
    """Yield every question dict in order. Convenience helper for quiz.py."""
    for block in QUIZ["blocks"]:
        for q in block["questions"]:
            yield block, q


def total_items() -> int:
    return sum(len(b["questions"]) for b in QUIZ["blocks"])


def total_points() -> int:
    return sum(q["points"] for _, q in iter_questions())


assert total_items() == 29, f"Expected 29 questions, got {total_items()}"
assert total_points() == QUIZ["max_points"], (
    f"Point total {total_points()} does not match max_points {QUIZ['max_points']}"
)
