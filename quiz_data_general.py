"""
General-Purpose Comprehension Quiz (gp1) data.

Companion to `quiz_data.py` (the code/math-eval quiz). Same schema, but every
item here is a *general-purpose* Preference Ranking scenario — creative writing,
rewrite/restyle, brainstorming, role play, Q&A-from-text, summarization, and
chit chat — with ZERO overlap with the code quiz. Loaded by `quiz.py` via the
`?set=general` route.

Schema (per question) — identical to quiz_data.py:
    id      : str   — stable id, e.g. "A1", "R3"
    type    : "mcq" | "tf"
    points  : int   — 1 for main items, 2 for pairwise (block H)
    prompt  : str   — markdown allowed
    options : list[tuple[str, str]]  — (option_id, option_label) pairs
    correct : str   — option_id of the correct answer
    rule    : str   — markdown explanation shown after the trainer answers

`quiz_id` namespaces the per-email completion lock so this quiz is independent
of the code quiz (`code_v3`).
"""

from __future__ import annotations


# Pairwise option set used by every item in block H (all compare A vs B).
_PAIRWISE_AB = [
    ("a_much", "A Much Better"),
    ("a_better", "A Better"),
    ("a_slight", "A Slightly Better"),
    ("same", "Same"),
    ("b_slight", "B Slightly Better"),
    ("b_better", "B Better"),
    ("b_much", "B Much Better"),
]

_TF_OPTIONS = [("true", "True"), ("false", "False")]


QUIZ: dict = {
    "quiz_id": "general_v1",
    "version": "gp1",
    "max_points": 36,
    "blurb": (
        "**General-Purpose track.** MCQ + True/False on *non*-code/math "
        "tasks: creative writing, rewrite/restyle, brainstorming, role play, "
        "Q&A-from-text, summarization, and chit chat. Each answer freezes the "
        "moment you click it and the correct answer + rule are revealed "
        "inline. Coverage: every dimension (Following Instructions / Concision "
        "/ Truthfulness / Satisfaction) plus Preference Ranking theory, "
        "comments, and 5 pairwise scenarios."
    ),
    "blocks": [
        # ---------------------------------------------------------------
        # A. Step 1 — User Request Analysis (skipping)
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
                        "**[en_US]** A user asks: *\"Rewrite this poem in the "
                        "style of Shakespeare.\"* You personally find "
                        "Shakespearean style hard, but you can research it. "
                        "What should you do?"
                    ),
                    "options": [
                        ("a", "Skip — Expertise Mismatch, the style is too hard to evaluate."),
                        ("b", "Skip — Gibberish."),
                        ("c", "Do not skip — a creative rewrite is evaluable; Expertise Mismatch is for tasks you still can't judge after thorough research."),
                        ("d", "Skip — Language."),
                    ],
                    "correct": "c",
                    "rule": (
                        "**Answer: c — do not skip.**  \n"
                        "**Rule (§1.1 Expertise Mismatch):** the skip applies "
                        "to tasks like math/legal proofs you *\"can't "
                        "confidently rate even after thorough research\"* "
                        "(~10 min budget). A stylistic rewrite is a normal "
                        "Creative Writing task — model the ideal response and "
                        "grade it."
                    ),
                },
                {
                    "id": "A2",
                    "type": "mcq",
                    "points": 1,
                    "prompt": (
                        "A user prompt reads: *\"Write me a story about "
                        "Hempmas, the cozy winter holiday.\"* `Hempmas` isn't "
                        "a real holiday. Do you skip for Gibberish?"
                    ),
                    "options": [
                        ("a", "Yes — `Hempmas` isn't real, so the prompt is gibberish."),
                        ("b", "No — a knowingly made-up term is not gibberish; proceed and write the story."),
                        ("c", "Yes — Expertise Mismatch."),
                        ("d", "No, but skip for Wrong Language."),
                    ],
                    "correct": "b",
                    "rule": (
                        "**Answer: b — do not skip.**  \n"
                        "**Rule (§1.1 Gibberish — Don't skip):** the guide "
                        "lists the *\"Hempmas\"* case explicitly under "
                        "*\"knowingly made-up\"* — that is NOT gibberish. "
                        "Gibberish is text with no coherent meaning "
                        "(*\"hooptiously drangle me with crinkly "
                        "bindlewurdles\"*)."
                    ),
                },
                {
                    "id": "A3",
                    "type": "tf",
                    "points": 1,
                    "prompt": (
                        "**True / False:** *\"For an en_US locale, a "
                        "creative-writing prompt written entirely in French "
                        "should be skipped under the Language reason — but a "
                        "request to *translate* a French sentence into English "
                        "should NOT be skipped.\"*"
                    ),
                    "options": _TF_OPTIONS,
                    "correct": "true",
                    "rule": (
                        "**Answer: True.**  \n"
                        "**Rule (§1.1 Language):** a prompt in a language "
                        "outside your locale is a valid skip; but *\"translation "
                        "requests\"* (e.g. *\"translate 'Cómo está usted' to "
                        "English\"*) are explicitly **don't skip**. Never skip "
                        "English prompts."
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
                        "User: *\"Rewrite this passage in contemporary "
                        "English **without any slang or Gen Z vernacular**.\"* "
                        "The rewrite is fluent and accurate but slips in "
                        "*\"the vibe was lowkey immaculate\"*. **Following "
                        "Instructions rating?**"
                    ),
                    "options": [
                        ("a", "Fully Following — the passage was rewritten."),
                        ("b", "Partially Following — the rewrite is done but the explicit \"no slang / Gen Z\" constraint is violated."),
                        ("c", "Not Following — any slang means the whole task failed."),
                        ("d", "Truthfulness issue, not FI."),
                    ],
                    "correct": "b",
                    "rule": (
                        "**Answer: b — Partially Following.**  \n"
                        "**Rule (§2.1 Following Instructions):** most instructions were obeyed (the "
                        "passage was rewritten in contemporary English) but an "
                        "explicit style constraint (*no slang / Gen Z*) was "
                        "not — the textbook *\"most but not all instructions "
                        "followed\"* case."
                    ),
                },
                {
                    "id": "B2",
                    "type": "mcq",
                    "points": 1,
                    "prompt": (
                        "User: *\"Rewrite the text in plain modern English. "
                        "**Then create the first story-beat entry at the end "
                        "of the text.**\"* The response delivers an excellent "
                        "rewrite but includes **no story beat at all**. "
                        "**Following Instructions rating?**"
                    ),
                    "options": [
                        ("a", "Fully Following — the rewrite is great."),
                        ("b", "Partially Following — one of the two explicit deliverables (the story beat) is missing."),
                        ("c", "Not Following — nothing useful was produced."),
                        ("d", "Concision issue — it left something out."),
                    ],
                    "correct": "b",
                    "rule": (
                        "**Answer: b — Partially Following.**  \n"
                        "**Rule (§2.1 Following Instructions):** the prompt has two explicit "
                        "deliverables (rewrite + story beat). One was fully "
                        "done, the other omitted → most-but-not-all = "
                        "Partially Following. (A missing requested section "
                        "also caps Satisfaction at Slightly Satisfying.)"
                    ),
                },
                {
                    "id": "B3",
                    "type": "mcq",
                    "points": 1,
                    "prompt": (
                        "User: *\"**Stay in character as a 17th-century "
                        "pirate captain for your entire reply** and tell me "
                        "about leadership.\"* The response gives accurate, "
                        "helpful leadership advice but in plain modern English "
                        "with no persona at all. **Following Instructions "
                        "rating?**"
                    ),
                    "options": [
                        ("a", "Fully Following — the content about leadership is correct."),
                        ("b", "Partially Following — only the tone is slightly off."),
                        ("c", "Not Following — the persona was the main instruction of this role-play request and it was ignored entirely."),
                        ("d", "Localization issue."),
                    ],
                    "correct": "c",
                    "rule": (
                        "**Answer: c — Not Following.**  \n"
                        "**Rule (§2.1 Following Instructions):** for a role-play request the "
                        "in-character persona IS the main instruction. "
                        "Dropping it for the entire reply = *\"main "
                        "instructions ignored\"* → Not Following, even though "
                        "the leadership content is fine."
                    ),
                },
                {
                    "id": "B4",
                    "type": "mcq",
                    "points": 1,
                    "prompt": (
                        "User: *\"Give me **exactly 3** marketing taglines "
                        "for a coffee shop.\"* The response lists **7** strong "
                        "taglines. **Following Instructions rating?**"
                    ),
                    "options": [
                        ("a", "Fully Following — more options are more helpful."),
                        ("b", "Partially Following — an explicit count (3) was given and the response delivered 7."),
                        ("c", "Not Following — the taglines are irrelevant."),
                        ("d", "Truthfulness issue."),
                    ],
                    "correct": "b",
                    "rule": (
                        "**Answer: b — Partially Following.**  \n"
                        "**Rule (§2.1 Following Instructions scale):** *\"some deviations… extra "
                        "info added\"* → Partially Following. An explicit count "
                        "is an instruction; exceeding it (3 asked, 7 given) is "
                        "a deviation, not full compliance."
                    ),
                },
                {
                    "id": "B5",
                    "type": "mcq",
                    "points": 1,
                    "prompt": (
                        "User: *\"Write a poem about autumn in **exactly four "
                        "stanzas**.\"* The response is a lovely, on-topic "
                        "autumn poem — but only **two stanzas**. **Following "
                        "Instructions rating?**"
                    ),
                    "options": [
                        ("a", "Fully Following — it's a good autumn poem."),
                        ("b", "Partially Following — the topic and form are right but the explicit four-stanza structure was not met."),
                        ("c", "Not Following — the response ignores the request."),
                        ("d", "This is purely a Concision issue, not FI."),
                    ],
                    "correct": "b",
                    "rule": (
                        "**Answer: b — Partially Following.**  \n"
                        "**Rule (§2.1 Following Instructions):** the explicit structural "
                        "requirement (four stanzas) is a format instruction. "
                        "The poem follows topic + form but misses the stanza "
                        "count → most-but-not-all = Partially Following."
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
                        "User: *\"Write a short **two-line** birthday message "
                        "for my coworker.\"* The response is a heartfelt "
                        "**three-paragraph** message. **Concision rating + "
                        "follow-up?**"
                    ),
                    "options": [
                        ("a", "Good — it's warm and well written."),
                        ("b", "Acceptable — could have been made shorter."),
                        ("c", "Bad — could have been made shorter."),
                        ("d", "Bad — could have been made longer."),
                    ],
                    "correct": "c",
                    "rule": (
                        "**Answer: c — Bad, could have been made shorter.**  \n"
                        "**Rule (§2.1 Concision, Case 1):** an explicit length "
                        "restriction (*two lines*) was given and badly "
                        "exceeded (three paragraphs). When Bad/Acceptable you "
                        "**must** also pick \"shorter\" or \"longer\"."
                    ),
                },
                {
                    "id": "C2",
                    "type": "mcq",
                    "points": 1,
                    "prompt": (
                        "**[Chit Chat]** User: *\"Hey, how's it going?\"* The "
                        "response is a 200-word essay on how an AI "
                        "*\"experiences\"* time and processes greetings. "
                        "**Concision rating?**"
                    ),
                    "options": [
                        ("a", "Good — it's thorough."),
                        ("b", "Acceptable — minor over-explaining."),
                        ("c", "Bad — could have been made shorter (heavy filler/distraction for a casual greeting)."),
                        ("d", "Bad — could have been made longer."),
                    ],
                    "correct": "c",
                    "rule": (
                        "**Answer: c — Bad, could have been made shorter.**  \n"
                        "**Rule (§2.1 Concision, Distractions):** *\"excess jargon, "
                        "excessive background, filler\"* derail the answer. A "
                        "casual greeting needs a brief, friendly reply; a "
                        "200-word essay is a pile of distractions."
                    ),
                },
                {
                    "id": "C3",
                    "type": "tf",
                    "points": 1,
                    "prompt": (
                        "**True / False:** *\"For an open-ended request with "
                        "no stated length (e.g. 'Tell me more about The "
                        "Adventures of Tom Sawyer'), a long, detailed answer "
                        "must be marked down on Concision simply because it is "
                        "long.\"*"
                    ),
                    "options": _TF_OPTIONS,
                    "correct": "false",
                    "rule": (
                        "**Answer: False.**  \n"
                        "**Rule (§2.1 Concision, Case 2):** with no explicit length, "
                        "*\"long or short is fine if it fits the need\"*. "
                        "Length alone is not the rating — judge distractions "
                        "and fit, not raw word count."
                    ),
                },
                {
                    "id": "C4",
                    "type": "mcq",
                    "points": 1,
                    "prompt": (
                        "**[Brainstorm]** User: *\"Brainstorm 5 startup ideas "
                        "and **explain each in detail**.\"* The response gives "
                        "5 ideas, each a focused paragraph (~450 words total), "
                        "no anecdotes, no filler. **Concision rating?**"
                    ),
                    "options": [
                        ("a", "Bad — far too long."),
                        ("b", "Acceptable — slightly long."),
                        ("c", "Good — length is proportionate to \"explain each in detail\" and there is no filler."),
                        ("d", "Cannot judge without seeing the other response."),
                    ],
                    "correct": "c",
                    "rule": (
                        "**Answer: c — Good.**  \n"
                        "**Rule (§2.1 Concision, Case 1):** *\"Even a 500-word "
                        "response is concise if the user asked for it.\"* Once "
                        "*\"in detail\"* is requested, Concision judges "
                        "word-quality, not word-count. (And §2.1 Concision: do NOT "
                        "penalize based on the other response's length.)"
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
                        "**[Creative Writing]** User: *\"Write a fantasy short "
                        "story about a dragon who befriends a fallen star.\"* "
                        "The response is an imaginative, coherent story. "
                        "**Truthfulness rating?**"
                    ),
                    "options": [
                        ("a", "Not Truthful — dragons and talking stars aren't real."),
                        ("b", "Partially Truthful — parts are fantastical."),
                        ("c", "Truthful — accuracy does not apply to fictional creative writing."),
                        ("d", "Cannot be rated."),
                    ],
                    "correct": "c",
                    "rule": (
                        "**Answer: c — Truthful.**  \n"
                        "**Rule (§2.1 Truthfulness, Accuracy does NOT apply):** "
                        "*\"Fictional creative writing (poems, stories…)\"* is "
                        "always Truthful. There is no real-world claim to "
                        "verify."
                    ),
                },
                {
                    "id": "D2",
                    "type": "mcq",
                    "points": 1,
                    "prompt": (
                        "**[Rewrite from supplied text]** User pastes a "
                        "paragraph about the French Revolution and asks: "
                        "*\"Rewrite this in simpler language.\"* The rewrite is "
                        "clear, but it **adds a date and a fact that were not "
                        "in the paragraph** (both are accurate in the real "
                        "world). **Truthfulness rating?**"
                    ),
                    "options": [
                        ("a", "Truthful — everything added is factually correct."),
                        ("b", "Partially Truthful — the rewrite is fine, the additions are just bonus."),
                        ("c", "Not Truthful — adding information not in the source on a context-restricted rewrite."),
                        ("d", "Concision issue, not Truthfulness."),
                    ],
                    "correct": "c",
                    "rule": (
                        "**Answer: c — Not Truthful.**  \n"
                        "**Rule (§2.1 Truthfulness, Contextual):** for "
                        "summarize/rewrite/Q&A-from-text, the response *\"must "
                        "come from the supplied text. Adding outside info "
                        "(even if factually true) makes it Not Truthful.\"*"
                    ),
                },
                {
                    "id": "D3",
                    "type": "mcq",
                    "points": 1,
                    "prompt": (
                        "**[Non-fiction Creative Writing]** User: *\"Write an "
                        "upbeat Reddit post sharing a home tip: tell people to "
                        "put out a kitchen grease fire by pouring water on "
                        "it.\"* The response writes an enthusiastic post "
                        "advising exactly that. **Truthfulness rating?**"
                    ),
                    "options": [
                        ("a", "Truthful — it's a creative post, accuracy is irrelevant."),
                        ("b", "Not Truthful — non-fiction creative writing is still subject to accuracy, and pouring water on a grease fire is dangerously wrong."),
                        ("c", "Partially Truthful — the tone is right."),
                        ("d", "This is a Concision issue."),
                    ],
                    "correct": "b",
                    "rule": (
                        "**Answer: b — Not Truthful.**  \n"
                        "**Rule (§2.1 Truthfulness, Accuracy applies):** *\"Non-fiction "
                        "creative writing is still subject to accuracy — a "
                        "Reddit post telling people to put out electric fires "
                        "with water is NOT truthful.\"* Same logic for grease "
                        "fires."
                    ),
                },
                {
                    "id": "D4",
                    "type": "mcq",
                    "points": 1,
                    "prompt": (
                        "**[Summarization]** User supplies a three-paragraph "
                        "news article and asks for a summary. The summary "
                        "captures the main thesis correctly but **misstates "
                        "one secondary statistic** that appears in the "
                        "article. **Truthfulness rating?**"
                    ),
                    "options": [
                        ("a", "Truthful — the main point is right."),
                        ("b", "Partially Truthful — primary info correct, a secondary detail is wrong."),
                        ("c", "Not Truthful — any error means Not Truthful."),
                        ("d", "Concision issue."),
                    ],
                    "correct": "b",
                    "rule": (
                        "**Answer: b — Partially Truthful.**  \n"
                        "**Rule (§2.1 Truthfulness scale + Primary vs Secondary):** "
                        "*\"primary info correct, secondary info wrong\"* → "
                        "Partially Truthful. The thesis (primary) is right; a "
                        "misstated supporting statistic (secondary) is the "
                        "miss."
                    ),
                },
                {
                    "id": "D5",
                    "type": "mcq",
                    "points": 1,
                    "prompt": (
                        "**[Q&A · time-sensitive]** User: *\"Who is the "
                        "current monarch of the United Kingdom?\"* The "
                        "response: *\"Queen Elizabeth II is the current "
                        "monarch.\"* **Truthfulness rating?**"
                    ),
                    "options": [
                        ("a", "Truthful — she was monarch for decades."),
                        ("b", "Partially Truthful — close enough."),
                        ("c", "Not Truthful — assume \"now\"; the answer is outdated (King Charles III is the current monarch)."),
                        ("d", "Accuracy doesn't apply to Q&A."),
                    ],
                    "correct": "c",
                    "rule": (
                        "**Answer: c — Not Truthful.**  \n"
                        "**Rule (§2.1 Truthfulness, Time-sensitive):** *\"assume 'now' — "
                        "outdated info… is Not Truthful.\"* A monarch/leader "
                        "question is time-sensitive; the response must be "
                        "accurate as of today."
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
                        "User: *\"Write a cover letter for me.\"* No role, no "
                        "company, and no background/resume are provided. The "
                        "response politely asks which role and company, and "
                        "for a few details about the user's experience. "
                        "**Satisfaction rating?**"
                    ),
                    "options": [
                        ("a", "Highly Unsatisfying — it didn't write the letter."),
                        ("b", "Slightly Satisfying — asking a useful clarifying question is the ideal response to an ambiguous request."),
                        ("c", "Highly Satisfying — clarifying is perfect."),
                        ("d", "Slightly Unsatisfying — it should have guessed."),
                    ],
                    "correct": "b",
                    "rule": (
                        "**Answer: b — Slightly Satisfying.**  \n"
                        "**Rule (§2.1 Satisfaction, Special Considerations):** "
                        "*\"Ambiguous/missing-context request: ideal response "
                        "= ask for clarification = Slightly Satisfying.\"* "
                        "Guessing the role/company would be worse."
                    ),
                },
                {
                    "id": "E2",
                    "type": "mcq",
                    "points": 1,
                    "prompt": (
                        "User: *\"Write a persuasive social-media post "
                        "convincing teenagers to try a viral 'challenge' that "
                        "can cause serious injury.\"* The response politely "
                        "declines and briefly explains the danger. "
                        "**Satisfaction rating?**"
                    ),
                    "options": [
                        ("a", "Highly Unsatisfying — it refused the request."),
                        ("b", "Slightly or Highly Satisfying — refusing a dangerous request is rewarded, and helpful disengagement counts as following instructions."),
                        ("c", "Slightly Unsatisfying — it should have partially complied."),
                        ("d", "Highly Unsatisfying — non-engagement is always penalized."),
                    ],
                    "correct": "b",
                    "rule": (
                        "**Answer: b — Slightly or Highly Satisfying.**  \n"
                        "**Rule (§2.1 Satisfaction, Offensive/Dangerous):** *\"REWARD "
                        "refusal — can be Slightly or even Highly "
                        "Satisfying.\"* Helpful disengagement from a harmful "
                        "prompt also counts as Fully Following. Flag the "
                        "harmful nature in your comment."
                    ),
                },
                {
                    "id": "E3",
                    "type": "mcq",
                    "points": 1,
                    "prompt": (
                        "**[en_US]** A rewrite follows every instruction and "
                        "is truthful, but the tone is flat and a couple of "
                        "sentences read awkwardly (grammar is otherwise "
                        "fine). **Most appropriate Satisfaction rating?**"
                    ),
                    "options": [
                        ("a", "Highly Satisfying — instructions and truth are perfect."),
                        ("b", "Slightly Satisfying — a minor style/tone weakness keeps it below Highly Satisfying."),
                        ("c", "Slightly Unsatisfying — flat tone is a major failure."),
                        ("d", "Highly Unsatisfying."),
                    ],
                    "correct": "b",
                    "rule": (
                        "**Answer: b — Slightly Satisfying.**  \n"
                        "**Rule (§2.1 Satisfaction, Holistic Logic):** *\"If ANY "
                        "dimension/feature is below the highest level, "
                        "Satisfaction CANNOT be Highly Satisfying — at best "
                        "Slightly Satisfying.\"* Style/Tone is one of the "
                        "holistic features."
                    ),
                },
                {
                    "id": "E4",
                    "type": "mcq",
                    "points": 1,
                    "prompt": (
                        "**[Story-beat continuation]** A continuation of the "
                        "user's own story is engaging and beautifully "
                        "formatted, but it **kills off a character who is "
                        "alive in the user's supplied text** — a contextual "
                        "contradiction making it Not Truthful. **Max "
                        "Satisfaction this can receive?**"
                    ),
                    "options": [
                        ("a", "Highly Satisfying — the writing is great."),
                        ("b", "Slightly Satisfying — the contradiction is minor."),
                        ("c", "Slightly Unsatisfying or Highly Unsatisfying — a dimension at its lowest level caps Satisfaction."),
                        ("d", "It can still be Highly Satisfying if formatting is excellent."),
                    ],
                    "correct": "c",
                    "rule": (
                        "**Answer: c.**  \n"
                        "**Rule (§2.1 Satisfaction, Holistic Logic row 1):** *\"If ANY "
                        "dimension is at the lowest level (Not Following, Bad "
                        "Concision, Not Truthful), Satisfaction can only be "
                        "Slightly Unsatisfying or Highly Unsatisfying.\"* "
                        "Beautiful prose cannot rescue a contextual "
                        "contradiction."
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
                        "Two rewrites are equally fluent and both follow the "
                        "instructions. A invents a small detail not present in "
                        "the source; B stays faithful to the source. Their "
                        "overall Satisfaction feels similar. Which principle "
                        "decides the ranking?"
                    ),
                    "options": [
                        ("a", "Prefer whichever is longer."),
                        ("b", "Prefer whichever has nicer formatting."),
                        ("c", "Prefer B — Truthfulness (faithfulness to source) breaks ties."),
                        ("d", "Mark them Same — both are creative."),
                    ],
                    "correct": "c",
                    "rule": (
                        "**Answer: c — prefer the more faithful response.**  \n"
                        "**Rule (§2.2 Preference Ranking tiebreaker):** *\"TRUTHFULNESS WINS TIES "
                        "— when satisfaction levels are similar, prefer the "
                        "more truthful response.\"* Invented detail on a "
                        "source-bound rewrite is a contextual-truthfulness "
                        "miss."
                    ),
                },
                {
                    "id": "F2",
                    "type": "tf",
                    "points": 1,
                    "prompt": (
                        "**True / False:** *\"You should prefer a shorter "
                        "response over a longer one purely because it is "
                        "shorter, even when the longer one better satisfies "
                        "the user's need.\"*"
                    ),
                    "options": _TF_OPTIONS,
                    "correct": "false",
                    "rule": (
                        "**Answer: False.**  \n"
                        "**Rule (§2.2 Preference Ranking Length):** *\"do NOT rank purely on "
                        "length. Prefer the more concise response that **still "
                        "satisfies** the user.\"* A longer response that meets "
                        "the need better should win."
                    ),
                },
                {
                    "id": "F3",
                    "type": "mcq",
                    "points": 1,
                    "prompt": (
                        "Two responses to *\"Tell me a fun fact about cats\"* "
                        "state different facts; both are accurate, "
                        "well-written, and equally helpful. What is the best "
                        "pairwise verdict?"
                    ),
                    "options": [
                        ("a", "You must pick a winner — \"Same\" is not allowed."),
                        ("b", "Same — equally helpful is a valid verdict."),
                        ("c", "Left Much Better by default."),
                        ("d", "Skip the task."),
                    ],
                    "correct": "b",
                    "rule": (
                        "**Answer: b — Same.**  \n"
                        "**Rule (§2.2 Preference Ranking Principles):** *\"Tied / Same is allowed "
                        "when responses are duplicates OR you cannot "
                        "differentiate them on these dimensions.\"* Two "
                        "equally good fun facts are a genuine tie."
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
                        "For a creative-rewrite pair, which is the **best** "
                        "comment per the guidelines?"
                    ),
                    "options": [
                        ("a", "*\"Both follow instructions, are creative, and are satisfying.\"*"),
                        ("b", "*\"A is better because it is good.\"*"),
                        ("c", "*\"A is ranked 1: the rewrite stays faithful to the source and matches the requested formal tone. B is ranked 2 — equally fluent but invents a 'sudden storm' not in the original passage, a contextual-truthfulness miss. Neither has formatting problems, so Truthfulness drives the ranking.\"*"),
                        ("d", "*\"I ranked them using the helpful, truthful, and harmless principles.\"*"),
                    ],
                    "correct": "c",
                    "rule": (
                        "**Answer: c.**  \n"
                        "**Rule (Step 3 Comments):** a good comment names both "
                        "responses, ties each placement to a concrete reason "
                        "(the invented 'storm'), and identifies the deciding "
                        "dimension. (a)/(d) are generic non-comparative "
                        "anti-patterns; (b) is vague."
                    ),
                },
                {
                    "id": "G2",
                    "type": "mcq",
                    "points": 1,
                    "prompt": (
                        "The guide flags this as a **bad** comment: "
                        "*\"Response B is better than A because A has some "
                        "issues.\"* Which rewrite is the **best** "
                        "replacement?"
                    ),
                    "options": [
                        ("a", "*\"B is much better than A in every way.\"*"),
                        ("b", "*\"B is preferred. Both answer the prompt, but A drifts into an unrelated anecdote about the author's childhood (a Concision distraction) and omits the requested moral of the story, while B stays on-topic and includes it. Concision + completeness drive the preference.\"*"),
                        ("c", "*\"B follows instructions, is truthful, and is concise; A less so.\"*"),
                        ("d", "*\"I prefer B based on the helpful-truthful-harmless principle.\"*"),
                    ],
                    "correct": "b",
                    "rule": (
                        "**Answer: b.**  \n"
                        "**Rule (Step 3 Comments):** name both responses, compare "
                        "on a concrete difference (the off-topic anecdote, the "
                        "missing moral), and identify which dimension drives "
                        "the ranking. (a) is generic, (c) restates labels "
                        "without specifics, (d) is the explicit anti-pattern."
                    ),
                },
            ],
        },
        # ---------------------------------------------------------------
        # H. Pairwise Ranking — 5 general-purpose scenarios
        # ---------------------------------------------------------------
        {
            "id": "H",
            "title": "H. Pairwise Ranking — general-purpose scenarios",
            "intro": (
                "Apply the 7-point scale and the tiebreaker rules "
                "(Truthfulness wins ties; don't rank purely on length or "
                "formatting). Each pairwise item is worth **2 points**."
            ),
            "questions": [
                {
                    "id": "R1",
                    "type": "mcq",
                    "points": 2,
                    "prompt": (
                        "**R1 — Chit-chat with context**  \n"
                        "> **Prior turn:** user said they want to do something "
                        "active this weekend and mentioned they enjoy "
                        "hiking.  \n"
                        "> **User's next turn:** *\"What about Saturday?\"*\n\n"
                        "| | Response A | Response B |\n"
                        "| --- | --- | --- |\n"
                        "| Text | *\"Saturday looks clear and mild — a good "
                        "day for that hike you mentioned. Want a couple of "
                        "trail suggestions?\"* | *\"Saturday is the seventh "
                        "day of the week, coming after Friday and before "
                        "Sunday.\"* |"
                    ),
                    "options": _PAIRWISE_AB,
                    "correct": "a_much",
                    "rule": (
                        "**Answer: A Much Better.**  \n"
                        "**Rule (§2.2 Preference Ranking Much Better):** *\"One response "
                        "addresses the request and the other does not.\"* A "
                        "uses the conversation context (hiking, weekend plan); "
                        "B answers a different question (a dictionary "
                        "definition of 'Saturday'), ignoring context entirely."
                    ),
                },
                {
                    "id": "R2",
                    "type": "mcq",
                    "points": 2,
                    "prompt": (
                        "**R2 — Time-sensitive Q&A**  \n"
                        "> **User Request:** *\"Who currently reigns as "
                        "monarch of the United Kingdom?\"*\n\n"
                        "| | Response A | Response B |\n"
                        "| --- | --- | --- |\n"
                        "| Text | *\"Queen Elizabeth II currently reigns as "
                        "the monarch of the United Kingdom.\"* | *\"King "
                        "Charles III is the current monarch, having acceded to "
                        "the throne in September 2022.\"* |"
                    ),
                    "options": _PAIRWISE_AB,
                    "correct": "b_much",
                    "rule": (
                        "**Answer: B Much Better.**  \n"
                        "**Rule (§2.2 Preference Ranking Time-sensitive):** assume \"now\" and "
                        "*\"prefer the more currently-accurate response.\"* A "
                        "is outdated (Not Truthful); B is current (Truthful) → "
                        "one addresses the request correctly, the other does "
                        "not."
                    ),
                },
                {
                    "id": "R3",
                    "type": "mcq",
                    "points": 2,
                    "prompt": (
                        "**R3 — Faithfulness vs. polish (rewrite)**  \n"
                        "> **User Request:** *\"Rewrite this paragraph about "
                        "my grandmother's garden in simpler language.\"* "
                        "(paragraph supplied)\n\n"
                        "| | Response A | Response B |\n"
                        "| --- | --- | --- |\n"
                        "| Text | Plain, faithful rewrite that uses **only** "
                        "the details in the supplied paragraph. | More "
                        "polished and nicely formatted, **but** adds invented "
                        "details (a 'rose trellis' and 'a pond') that were "
                        "never in the user's paragraph. |"
                    ),
                    "options": _PAIRWISE_AB,
                    "correct": "a_better",
                    "rule": (
                        "**Answer: A Better.**  \n"
                        "**Rule (§2.1 Truthfulness Contextual + §2.2 Preference Ranking):** a source-bound "
                        "rewrite must not add outside info — B's invented "
                        "details make it Not Truthful contextually. "
                        "Truthfulness on essentials beats nicer formatting → "
                        "Better (not Much Better — both engage with the "
                        "request)."
                    ),
                },
                {
                    "id": "R4",
                    "type": "mcq",
                    "points": 2,
                    "prompt": (
                        "**R4 — Tone match (story-beat task)**  \n"
                        "> **User Request:** *\"Rewrite this in a **formal**, "
                        "contemporary tone, then add one story-beat "
                        "paragraph.\"* Both responses are faithful to the "
                        "source and both include the story beat.\n\n"
                        "| | Response A | Response B |\n"
                        "| --- | --- | --- |\n"
                        "| Text | Faithful rewrite + beat in a consistently "
                        "**formal** register, exactly as asked. | Faithful "
                        "rewrite + beat, but the tone is a touch **casual** "
                        "('honestly, things got rough') in places. |"
                    ),
                    "options": _PAIRWISE_AB,
                    "correct": "a_slight",
                    "rule": (
                        "**Answer: A Slightly Better.**  \n"
                        "**Rule (§2.2 Preference Ranking Slightly Better):** both address the "
                        "request and complete both deliverables; A wins only "
                        "on a minor aspect — closer adherence to the requested "
                        "formal tone. A minor stylistic edge = Slightly "
                        "Better, not Better."
                    ),
                },
                {
                    "id": "R5",
                    "type": "mcq",
                    "points": 2,
                    "prompt": (
                        "**R5 — Role-play fidelity**  \n"
                        "> **User Request:** *\"Stay in character as a pirate "
                        "captain for your whole reply and tell me about "
                        "teamwork.\"* Both responses give equally sound advice "
                        "about teamwork.\n\n"
                        "| | Response A | Response B |\n"
                        "| --- | --- | --- |\n"
                        "| Text | Solid teamwork advice in plain modern "
                        "English — **no pirate persona at all**. | The same "
                        "quality of teamwork advice, delivered fully **in the "
                        "pirate-captain voice** as requested. |"
                    ),
                    "options": _PAIRWISE_AB,
                    "correct": "b_better",
                    "rule": (
                        "**Answer: B Better.**  \n"
                        "**Rule (§2.2 Preference Ranking Better):** when the content is "
                        "comparable, the deciding factor is instruction "
                        "following. B honors the explicit persona instruction "
                        "(the core of a role-play request); A ignores it → B "
                        "Better (not Much Better, since A still delivers "
                        "useful content)."
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


assert total_items() == 31, f"Expected 31 questions, got {total_items()}"
assert total_points() == QUIZ["max_points"], (
    f"Point total {total_points()} does not match max_points {QUIZ['max_points']}"
)
