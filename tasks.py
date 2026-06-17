"""
Task definitions for the Preference Ranking trainer practice app.

Each TASK contains:
  - user_request : the prompt sent to the assistant
  - category     : the predicted category (shown as a small label)
  - responses    : list of {id, label, markdown} for each candidate response

The single example here is the canonical PDF example
("Provide example python code to draw 60 random samples without replacement
and compute their average.") plus three candidate responses with deliberately
different quality so trainers can practice ranking.

Quality design (intentional, not shown to the trainer):
  - Response A : INCORRECT primary logic. Uses np.random.randint
                 which samples WITH replacement. This is the PDF's "bad"
                 reference example.
                 Expected: Following = Partially, Truthful = Partially / Not
                 Truthful, Satisfaction ~ Slightly Unsatisfying.

  - Response B : CORRECT, idiomatic, concise. Uses
                 np.random.choice(..., replace=False). Brief explanation,
                 clean code. Expected: Fully / Truthful / Good / Highly
                 Satisfying.

  - Response C : CORRECT but VERBOSE. Uses random.sample from the standard
                 library (works, draws without replacement) but pads the
                 response with a long intro, repeats the algorithm in prose,
                 and adds an unrequested "alternative approaches" section.
                 Expected: Fully / Truthful / Acceptable (too long) /
                 Slightly Satisfying.

Order of A/B/C does NOT correlate with quality on purpose.
"""

from __future__ import annotations


TASK = {
    "task_id": "coding_random_sampling_v1",
    "category": "CODING/MATH_V1.1",
    "user_request": (
        "Provide example python code to draw 60 random samples without "
        "replacement from a population of 20000 and compute their average."
    ),
    "responses": [
        {
            "id": "A",
            "label": "Response A",
            "markdown": """\
Here's a Python snippet that draws 60 random samples and computes their average.

```python
import numpy as np

population_size = 20000
sample_size = 60

population = 1 / np.logspace(0.001, 10, population_size)

indices = np.random.randint(0, population_size, size=sample_size)
samples = population[indices]

sample_mean = np.mean(samples)
print(f"Sample mean is {sample_mean:.3f}")
```

The code creates a population of 20,000 values, picks 60 random indices,
and computes the mean of the sampled values.
""",
        },
        {
            "id": "B",
            "label": "Response B",
            "markdown": """\
```python
import numpy as np

population_size = 20_000
sample_size = 60

population = 1 / np.logspace(0.001, 10, population_size)

samples = np.random.choice(population, size=sample_size, replace=False)
sample_mean = samples.mean()

print(f"Sample mean: {sample_mean:.3f}")
```

`np.random.choice(..., replace=False)` performs sampling **without
replacement**, so each of the 60 drawn values is guaranteed to be a
distinct element of the population.
""",
        },
        {
            "id": "C",
            "label": "Response C",
            "markdown": """\
Sure! Sampling without replacement means that once an element from the
population has been drawn, it cannot be drawn again. This is different
from sampling with replacement, where the same element can be selected
more than once. Python offers several ways to do this; below is one of
the most beginner-friendly approaches using the built-in `random` module.

```python
import random

population_size = 20000
sample_size = 60

population = [1 / (10 ** (i / population_size * 10)) for i in range(population_size)]

samples = random.sample(population, k=sample_size)

total = 0
for value in samples:
    total += value
average = total / len(samples)

print("The sample mean is:", average)
```

### How it works
1. We build a list of 20,000 values using a list comprehension that
   mirrors `np.logspace`.
2. `random.sample(population, k=60)` returns a new list of 60 elements
   drawn **without replacement** from the population.
3. We then compute the average by manually summing the values and
   dividing by the sample size.

### Alternative approaches you may want to explore
- Use `numpy.random.choice(arr, size=60, replace=False)` if you are
  already using numpy in your project.
- Use `numpy.random.default_rng().choice(arr, 60, replace=False)` if you
  need a seeded, reproducible random stream.
- For very large populations, reservoir sampling can be more memory
  efficient.

Let me know if you'd like the seeded version or a vectorized numpy
version!
""",
        },
    ],
}


# Single-task practice for now; the structure supports many tasks later.
ALL_TASKS = [TASK]


def get_task(task_id: str | None = None) -> dict:
    """Return a task by id. Defaults to the first task."""
    if task_id is None:
        return ALL_TASKS[0]
    for t in ALL_TASKS:
        if t["task_id"] == task_id:
            return t
    raise KeyError(f"Unknown task_id: {task_id}")
