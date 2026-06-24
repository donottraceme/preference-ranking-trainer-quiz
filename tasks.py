"""
Task definitions for the Preference Ranking trainer practice app.

Each TASK contains:
  - user_request : the prompt sent to the assistant
  - category     : the predicted category (shown as a small label)
  - responses    : list of {id, label, markdown} for each candidate response

Tasks (in landing-page order):

1. coding_random_sampling_v1 — canonical PDF example
   ("Provide example python code to draw 60 random samples without
   replacement and compute their average.") with three candidate
   responses of deliberately different quality.

   - Response A : INCORRECT primary logic. Uses np.random.randint
                  which samples WITH replacement. PDF's "bad" reference.
                  Expected: Following = Partially, Truthful = Partially /
                  Not Truthful, Satisfaction ~ Slightly Unsatisfying.
   - Response B : CORRECT, idiomatic, concise. Uses
                  np.random.choice(..., replace=False).
                  Expected: Fully / Truthful / Good / Highly Satisfying.
   - Response C : CORRECT but VERBOSE. Uses random.sample, pads with
                  long intro, prose repeats, "alternative approaches".
                  Expected: Fully / Truthful / Acceptable (too long) /
                  Slightly Satisfying.

2. logic_dogs_v1 — set/inclusion-exclusion word problem about a kennel
   with three dimensions (color / tail / hair). Trainee has to pick
   between three derivations of the same target count (3 black, long
   hair, no short tail).

   - Response A : Correct final answer + simple table, but the derivation
                  is mildly circular (asserts "6 do not have long hair"
                  without proving it).
   - Response B : Cleanest — uses inclusion-exclusion on the
                  no-short-tail subset (9 black + 12 long-hair across 18
                  dogs ⇒ 3 overlap). Concise and rigorous.
   - Response C : Heavy formal set-theory walkthrough that gets stuck
                  ("x is between 3 and 9 inclusive — but we need to
                  determine x uniquely") and contradicts itself before
                  trailing off mid-derivation. Incomplete + inconsistent.

3. html_webpage_v1 — "Write HTML and CSS for a simple webpage…". Three
   responses that all produce a working page; differentiation is
   idiomatic CSS placement and presentational artifacts.

   - Response A : Clean, idiomatic — color blue applied to <h1>,
                  text-align center on <header>. Tight, well-explained.
   - Response B : Works, but applies color: blue to <header> and relies
                  on inheritance; slightly less precise. No comments.
   - Response C : Adds unrequested visual chrome (background colors,
                  box-shadows, rounded corners, max-width). All
                  user-stated requirements are met but the response
                  goes well beyond the brief.

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


# -----------------------------------------------------------------------------
# Task 2 — kennel logic puzzle (set theory / inclusion–exclusion)
# -----------------------------------------------------------------------------

TASK_2 = {
    "task_id": "logic_dogs_v1",
    "category": "MATH/LOGIC_V1.1",
    "user_request": (
        "There are twenty four dogs in a kennel. Twelve of the dogs are "
        "black, six of the dogs have short tails, and fifteen of the dogs "
        "have long hair. There is only one dog that is black with a short "
        "tail and long hair. Two of the dogs are black with short tails and "
        "do not have long hair. Two of the dogs have short tails and long "
        "hair but are not black. Why is the number of black dogs with long "
        "hair but do not have short tails only 3? Can you break it down for "
        "me?"
    ),
    "responses": [
        {
            "id": "A",
            "label": "Response A",
            "markdown": r"""\
The reason the number of black dogs with long hair (but no short tail) is
3 is that you have to subtract the dogs that fit into other categories
from the total count of black dogs.

Here is the step-by-step breakdown to show exactly where that number
comes from.

**1. Start with the total number of Black Dogs**

We know there are 12 black dogs in total. We need to figure out how many
of these 12 fit into specific groups, and whatever is left over will be
the group you are asking about.

**2. Account for the Black Dogs with Short Tails**

The problem gives us information about the black dogs that have short
tails:

- 1 dog is black, has a short tail, and has long hair.
- 2 dogs are black, have a short tail, and do not have long hair.

This means there are 3 black dogs with short tails in total
($1 + 2 = 3$).

Remaining black dogs: $12 - 3 = 9$. (These 9 dogs are black, do not have
short tails, and may or may not have long hair.)

**3. Account for the Long Hair**

We know there are 15 dogs total with long hair. Let's see how many of
those "long hair" spots are taken by dogs that are not the ones we are
looking for:

- 1 spot is taken by the black dog with a short tail and long hair
  (already counted).
- 2 spots are taken by dogs with short tails and long hair that are not
  black.

This means 3 of the "long hair" dogs have short tails.

**4. Find the Black Dogs with Long Hair (No Short Tail)**

Now we look at the remaining 9 black dogs (the ones without short tails).
We need to know how many of them have long hair.

To find this, we look at the total count of long-haired dogs (15) and
subtract the ones we know are not in our target group:

- Total Long Hair Dogs: 15
- Minus the black, short-tailed, long-haired dog: −1 → 14 left
- Minus the non-black, short-tailed, long-haired dogs: −2 → 12 left

These 12 remaining dogs have long hair and do not have short tails.

However, these 12 dogs can be either Black or Not Black. We know from
Step 2 that there are exactly 9 black dogs without short tails.

The question implies that out of those 9 black dogs without short tails,
6 of them do not have long hair. Therefore, the math works out like
this:

$$(\text{Total Black Dogs}) - (\text{Black w/ Short Tails}) - (\text{Black w/o Long Hair}) = \text{Target Group}$$

$$12 - 3 - 6 = 3$$

**Summary Table**

| Category                              | Number of Dogs |
| ------------------------------------- | -------------- |
| Total Black Dogs                      | 12             |
| Black + Short Tail + Long Hair        | 1              |
| Black + Short Tail + No Long Hair     | 2              |
| Black + Long Hair + No Short Tail     | 3              |
| Black + No Short Tail + No Long Hair  | 6              |
| Total                                 | 12             |

Because $1 + 2 + 6 = 9$, and you have 12 black dogs total, there are
only 3 spots left for black dogs that have long hair but no short tail.
""",
        },
        {
            "id": "B",
            "label": "Response B",
            "markdown": r"""\
To understand why there are exactly 3 black dogs with long hair and long
tails (i.e., not short tails), we need to use the information provided
to figure out the total number of dogs with short tails first.

This is a classic logic puzzle that can be solved by breaking down the
group of short-tailed dogs.

Here is the step-by-step breakdown:

**Step 1: Analyze the "Short Tail" Group**

The prompt tells us there are 6 dogs with short tails in total. It also
tells us exactly what the rest of their features are:

- 1 dog is black, has a short tail, and has long hair.
- 2 dogs are black, have short tails, and have short hair (not long
  hair).
- 2 dogs are not black, have short tails, and have long hair.

If we add these up ($1 + 2 + 2 = 5$), we get 5 dogs. Since there are 6
short-tailed dogs in total, the last remaining short-tailed dog
($6 - 5 = 1$) must be not black and have short hair.

**Step 2: Find the total number of Black Dogs (without short tails)**

Now let's look at the 12 black dogs. From Step 1, we know how many of
them have short tails:

- 1 is black with a short tail and long hair.
- 2 are black with short tails and short hair.

That is a total of 3 black dogs with short tails. This leaves 9 black
dogs that do not have short tails ($12 - 3 = 9$).

**Step 3: Find the total number of Long-Haired Dogs (without short tails)**

Now let's look at the 15 long-haired dogs. From Step 1, we know how many
of them have short tails:

- 1 is black with a short tail and long hair.
- 2 are not black, but have short tails and long hair.

That is a total of 3 long-haired dogs with short tails. This leaves 12
long-haired dogs that do not have short tails ($15 - 3 = 12$).

**Step 4: Put it all together**

We have 24 dogs in total. If we subtract the 6 short-tailed dogs from
the total, we are left with 18 dogs that do not have short tails.

Within those 18 dogs:

- 9 of them are black.
- 12 of them have long hair.

If we add those two groups together ($9 + 12 = 21$), we get 21 features
to distribute among 18 dogs.

Because 21 is 3 more than 18 ($21 - 18 = 3$), there must be an overlap
of exactly 3 dogs that possess both features.

**Conclusion**

Therefore, there must be exactly 3 dogs that are black AND have long
hair (but do not have short tails).
""",
        },
        {
            "id": "C",
            "label": "Response C",
            "markdown": r"""\
Let's break this down step by step using set theory and a Venn
diagram-style approach. We are dealing with three characteristics of
dogs:

- Black (B): 12 dogs
- Short tail (S): 6 dogs
- Long hair (L): 15 dogs
- Total dogs: 24

We are given several overlapping counts:

- Black AND Short tail AND Long hair ($B \cap S \cap L$) = 1 dog
- Black AND Short tail AND NOT Long hair ($B \cap S \cap \neg L$) = 2 dogs
- Short tail AND Long hair AND NOT Black ($\neg B \cap S \cap L$) = 2 dogs

We are asked to explain why the number of Black AND Long hair AND NOT
Short tail ($B \cap L \cap \neg S$) is 3.

**Step 1: Analyze the Short Tail (S) group (6 dogs total)**

The 6 dogs with short tails are divided into mutually exclusive
subgroups:

- $B \cap S \cap L = 1$
- $B \cap S \cap \neg L = 2$
- $\neg B \cap S \cap L = 2$

Add these: $1 + 2 + 2 = 5$. So 5 of the 6 short-tailed dogs are
accounted for. That leaves $\neg B \cap S \cap \neg L = 6 - 5 = 1$ dog
(not black, short tail, not long hair). All short-tailed dogs are now
accounted for.

**Step 2: Analyze the Black (B) group (12 dogs total)**

We already know:

- $B \cap S \cap L = 1$
- $B \cap S \cap \neg L = 2$

So black dogs with short tails: $1 + 2 = 3$. Therefore, black dogs
without short tails: $12 - 3 = 9$.

These 9 black dogs are split into:

- $B \cap L \cap \neg S = ?$ (this is what we want)
- $B \cap \neg L \cap \neg S = ?$

Let $x = B \cap L \cap \neg S$ → black, long hair, long tail → this is
what we are solving for. Let $y = B \cap \neg L \cap \neg S$ → black,
short hair, long tail.

Then: $x + y = 9$ (Equation A).

**Step 3: Analyze the Long Hair (L) group (15 dogs total)**

We know:

- $B \cap S \cap L = 1$
- $\neg B \cap S \cap L = 2$

So long-haired dogs with short tails: $1 + 2 = 3$. Therefore,
long-haired dogs without short tails: $15 - 3 = 12$.

These 12 are split into:

- $B \cap L \cap \neg S = x$
- $\neg B \cap L \cap \neg S = ?$

Let $z = \neg B \cap L \cap \neg S$ → not black, long hair, long tail.

Then: $x + z = 12$ (Equation B).

**Step 4: Use total number of dogs = 24**

Let's list all 8 possible combinations of the three traits and sum them:

- $B \cap S \cap L = 1$
- $B \cap S \cap \neg L = 2$
- $\neg B \cap S \cap L = 2$
- $\neg B \cap S \cap \neg L = 1$ (calculated earlier)
- $B \cap L \cap \neg S = x$
- $B \cap \neg L \cap \neg S = y$
- $\neg B \cap L \cap \neg S = z$
- $\neg B \cap \neg L \cap \neg S = w$

Sum all = 24, so $1 + 2 + 2 + 1 + x + y + z + w = 24$, i.e.
$x + y + z + w = 18$ (Equation C).

From earlier: $y = 9 - x$ and $z = 12 - x$. Substitute into Equation C:

$x + (9 - x) + (12 - x) + w = 18$
$\Rightarrow w = x - 3$.

Now, $w$ is the number of dogs that are not black, not short tail, not
long hair. This number cannot be negative, so $x \geq 3$.

All counts must be non-negative integers, which gives:

- $y = 9 - x \geq 0 \Rightarrow x \leq 9$
- $z = 12 - x \geq 0 \Rightarrow x \leq 12$
- $w = x - 3 \geq 0 \Rightarrow x \geq 3$

So $x$ is between 3 and 9 inclusive. But we need to determine $x$
uniquely.

Wait — is there any missing constraint? Let's verify with the short-hair
totals: long hair = 15, so not long hair = $24 - 15 = 9$ dogs. Dogs with
not long hair are $B \cap S \cap \neg L + \neg B \cap S \cap \neg L +
B \cap \neg L \cap \neg S + \neg B \cap \neg L \cap \neg S = 2 + 1 + y +
w = 3 + y + w$, which must equal 9, so $y + w = 6$ (Equation D).

Substitute into Equation D: $(9 - x) + (x - 3) = 6 \Rightarrow 6 = 6$.
This is always true — consistent, but doesn't give new info.

Let me list the values in terms of $x$:

| Group                     | Count        |
| ------------------------- | ------------ |
| $B \cap S \cap L$         | 1            |
| $B \cap S \cap \neg L$    | 2            |
| $\neg B \cap S \cap L$    | 2            |
| $\neg B \cap S \cap \neg L$ | 1          |
| $B \cap L \cap \neg S$    | $x$          |
| $B \cap \neg L \cap \neg S$ | $y = 9 - x$ |
| $\neg B \cap L \cap \neg S$ | $z = 1$    |
| $\neg B \cap \neg L \cap \neg S$ | $w$    |

Total long hair: $1 + 2 + x + 1 = $
""",
        },
    ],
}


# -----------------------------------------------------------------------------
# Task 3 — HTML/CSS simple webpage
# -----------------------------------------------------------------------------

TASK_3 = {
    "task_id": "html_webpage_v1",
    "category": "CODING/WEB_V1.1",
    "user_request": (
        "Write HTML and CSS for a simple webpage that has a header with the "
        "text 'Welcome to My Website' centered and colored blue, and a main "
        "section with the text 'This is my first webpage' in a paragraph "
        "tag."
    ),
    "responses": [
        {
            "id": "A",
            "label": "Response A",
            "markdown": """\
Here is the complete HTML and CSS code for the webpage. You can save
this code as an `.html` file (e.g., `index.html`) and open it in any
web browser.

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My First Webpage</title>
    <style>
        /* CSS Styles */
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f4f4f9;
        }

        header {
            text-align: center; /* Centers the text */
            margin-bottom: 30px;
        }

        h1 {
            color: blue; /* Sets text color to blue */
        }

        main {
            text-align: center;
        }

        p {
            font-size: 1.2rem;
            color: #333;
        }
    </style>
</head>
<body>

    <header>
        <h1>Welcome to My Website</h1>
    </header>

    <main>
        <p>This is my first webpage.</p>
    </main>

</body>
</html>
```

**Explanation of the code:**

- `<style>` block: This contains the CSS rules.
- `text-align: center;` is used on the header to center the title.
- `color: blue;` is applied to the `<h1>` tag to change the text color.
- `<header>`: Contains the main title text as requested.
- `<main>`: Contains the paragraph with the text "This is my first
  webpage."
- `font-family`: Added to the body to make the text look cleaner and
  more modern.
""",
        },
        {
            "id": "B",
            "label": "Response B",
            "markdown": """\
Here's a simple HTML and CSS webpage that meets your requirements:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My First Webpage</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
        }

        header {
            text-align: center;
            color: blue;
            margin-bottom: 20px;
        }

        header h1 {
            margin: 0;
        }

        main {
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <header>
        <h1>Welcome to My Website</h1>
    </header>

    <main>
        <p>This is my first webpage</p>
    </main>
</body>
</html>
```

This webpage includes:

**HTML structure:**

- A `<header>` section containing an `<h1>` tag with "Welcome to My
  Website".
- A `<main>` section containing a `<p>` tag with "This is my first
  webpage".

**CSS styling:**

- The header text is centered using `text-align: center`.
- The header text is colored blue using `color: blue`.
- Basic styling for better readability including font family and
  spacing.

The header text is centered and blue as requested, and the main content
appears in a paragraph tag below it.
""",
        },
        {
            "id": "C",
            "label": "Response C",
            "markdown": """\
Here is the complete HTML and CSS code for your webpage. You can save
this as an `.html` file (for example, `index.html`) and open it in any
web browser.

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My First Webpage</title>
    <style>
        /* CSS Styles */
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f4f4f9;
        }

        header {
            background-color: #ffffff;
            padding: 20px 0;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }

        h1 {
            text-align: center;
            color: blue;
            margin: 0;
        }

        main {
            max-width: 800px;
            margin: 40px auto;
            padding: 20px;
            background-color: #ffffff;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }

        p {
            font-size: 18px;
            color: #333333;
            line-height: 1.6;
        }
    </style>
</head>
<body>

    <!-- Header Section -->
    <header>
        <h1>Welcome to My Website</h1>
    </header>

    <!-- Main Content Section -->
    <main>
        <p>This is my first webpage.</p>
    </main>

</body>
</html>
```

**Key Features of this Code:**

- **Centered & Blue Header:** The `<h1>` tag inside the `<header>` uses
  the CSS properties `text-align: center;` and `color: blue;`.
- **Main Section:** Uses the semantic `<main>` tag with a standard
  paragraph (`<p>`) inside.
- **Clean Design:** I added a few extra CSS styles (like a background
  color, a nice font, and subtle drop shadows) to make it look modern
  and polished, rather than just plain text on a white background.
""",
        },
    ],
}


ALL_TASKS = [TASK, TASK_2, TASK_3]


def get_task(task_id: str | None = None) -> dict:
    """Return a task by id. Defaults to the first task."""
    if task_id is None:
        return ALL_TASKS[0]
    for t in ALL_TASKS:
        if t["task_id"] == task_id:
            return t
    raise KeyError(f"Unknown task_id: {task_id}")
