# Jessica Architecture Vision

## Modular Skill Design
Each skill is a dedicated AI model trained for a specific domain.
Jessica's core handles planning and routing — not expertise.

### Why
- One model can't be expert at everything
- Small domain-specific models are faster, cheaper, better
- Scales to billions of users with unique skill combinations

### How it maps to code
- METHOD_REGISTRY routes goals to skill handlers
- Each skill handler calls its own model (or the LLM fallback for now)
- Swapping general LLM for a fine-tuned expert = change one function, nothing else

## Current state
- LLM fallback = general intelligence (good enough for now)
- Future: replace with fine-tuned models per skill domain

## Personal Jessica skills (your instance)
- build_confidence
- build_AI
- learn_HTN_planning

Design C — the LLM generates subtasks and labels each one as either "needs further breakdown" or "primitive action". Jessica only recurses on the ones labelled for breakdown. One or two API calls maximum, intelligent decomposition