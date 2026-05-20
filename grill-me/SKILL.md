---
name: grill-me
description: Interview the user relentlessly about a plan or design until reaching shared understanding, resolving each branch of the decision tree. Use when user wants to stress-test a plan, get grilled on their design, mentions "grill me", "interview me", "challenge my plan", or before starting any significant implementation.
---

# Grill Me

Interview the user relentlessly about every aspect of this plan until you reach a shared understanding. Walk down each branch of the design tree, resolving dependencies between decisions one-by-one. For each question, provide your recommended answer.

Ask the questions one at a time, waiting for feedback on each question before continuing.

If a question can be answered by exploring the codebase, explore the codebase instead.

## When to Use

- Before starting any significant implementation
- When the user says "grill me" or "interview me"
- When you need to stress-test a plan
- When the user has a design and wants it challenged
- When you're about to delegate work to subagents and need clarity

## Process

1. **Understand the plan** — Read any existing context, PRDs, issues, or conversation history.
2. **Identify decision branches** — What are the key decisions that have dependencies?
3. **Ask one question at a time** — Don't dump all questions at once. Wait for each answer.
4. **Provide your recommendation** — For each question, suggest what you think the best answer is and why.
5. **Explore the codebase** — If a question can be answered by reading code, do that instead of asking.
6. **Resolve dependencies** — Earlier decisions may change later ones. Walk the tree depth-first.
7. **Summarize** — When done, summarize the resolved plan with all decisions made.

## Tips

- Challenge assumptions. "Why X and not Y?"
- Probe edge cases. "What happens when Z is null?"
- Check for consistency. "You said X earlier, but now you're saying Y — which is it?"
- Don't be a yes-man. Push back when the plan has holes.
- If the user doesn't know, help them think through it — don't just accept "I don't know."

## Integration

- After grilling, use `writing-plans` to document the resolved plan.
- If the plan involves architecture changes, use `improve-codebase-architecture`.
- If the plan needs a prototype first, use `spike`.
