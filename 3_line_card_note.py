"""
1. What failure does this prevent?
2. What determinism guarantee does this enforce?
3. What proof/debugging capability does this enable?


1. Guess from the name first

Before tracing usage, ask:

what do I think this means just from the name?

why would the planner need this?

Example:

max_steps → probably a guard against unbounded plan growth

rng_trace → probably a record of randomness used during deterministic selection

This gives you a prediction.

2. Trace usage

Now do what you already did:

where is it assigned?

where is it read?

what affects it?

what does it affect?

This gives you evidence.

3. Finish with one sentence

Then compress it into:

“X exists to ___ so that ___.”








Rule 1 — Tiny daily wins

Not weeks.
Not big milestones.

Every day:

recall 1 concept

understand 1 small block of code

write 5–20 lines yourself

Consistency beats intensity.

Rule 2 — Always recall before reading

Before looking at code, try:

rewrite from memory

explain what a function does

This strengthens the brain.

Rule 3 — Build small systems

Instead of “finish Jessica”, focus on pieces:

Example progression:

deterministic planner

HTN expansion

skill registry

execution loop

learning / mutation

Each piece becomes a mini project.












Step 1 — ROLE

File name only

Step 2 — GUESS

Function names + docstrings only

No loop reading

No conditionals

Step 3 — CHECK & EXPLAIN

Read logic

Correct your mental model

Include one detail you didn’t know before

A quick self-test:

“Did I learn at least one thing I couldn’t have guessed?"""

"""
ROLE:
What job does this file do in P2 HTN planning?

GUESS:
How do I think this enforces determinism, safety, or structure?
(Wrong guesses are GOOD.)

CHECK & EXPLAIN:
Correct explanation in 1 sentence.

P2 ANCHOR (one line):
Which P2 rule does this file satisfy?
- determinism
- no cycles
- method validity
- proof trace
"""



'''before copying

Ask:

what role does this line/block play?

why is it needed?

what bad thing happens if it is missing?

after copying

Close the reference and explain:

what each variable is for

what invariant this block protects

whether this block decides, records, or enforces something'''