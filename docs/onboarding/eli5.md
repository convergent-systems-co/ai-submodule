# Explain This Repo Like I'm 5

Imagine your team writes code every day. Before anyone's changes get added to the project, someone has to check them — making sure the code is safe, well-written, and follows the rules.

Normally, a human does that checking. But humans are slow, they get tired, and they can make mistakes.

**This repo teaches an AI assistant how to do those checks instead.**

---

## What Does It Actually Do?

When a developer wants to merge code into a project, this platform:

1. **Reads the change** — what problem is being solved?
2. **Asks a team of AI reviewers** — is it safe? Is it correct? Does it follow the rules?
3. **Collects their answers** and makes a decision: merge it, fix it, or block it.
4. **Writes down everything it decided** so there is always a record of why.

No human has to sit in the middle waiting to approve things.

---

## Who Are the "AI Reviewers"?

Think of them like specialists at a company:

| Name | Job |
|------|-----|
| **DevOps Engineer** | The receptionist — checks everything is ready before work starts |
| **Tech Lead** | The project manager — assigns tasks, watches progress, makes final calls |
| **Coder** | The developer — actually writes the code changes |
| **Tester** | The quality checker — reviews the Coder's work before it ships |

They pass notes to each other (like `ASSIGN`, `APPROVE`, `BLOCK`) until the work is done.

---

## What's in This Repo?

This repo is a **toolbox of instructions and rules**. There is no app here — just files that tell AI assistants what to do:

| Folder | What's Inside |
|--------|---------------|
| `governance/personas/` | Descriptions of each AI reviewer's personality and job |
| `governance/prompts/reviews/` | The actual questions each reviewer asks |
| `governance/policy/` | The rules: when to auto-merge, when to block, when to ask a human |
| `governance/schemas/` | The forms reviewers fill out (so a computer can read their answers) |
| `bin/` | Setup scripts to install this into another project |

---

## How Does a Project Use This?

You add this repo as a **submodule** (a shared library of files) to your project:

```bash
git submodule add git@github.com:convergent-systems-co/dark-forge.git .ai
bash .ai/bin/init.sh
```

After that, your AI assistant knows all the rules and can run the full review pipeline on your code.

---

## Why Not Just Have a Human Review?

| Problem with human review | How this helps |
|--------------------------|----------------|
| Slow — waiting on schedules | Instant — runs in CI automatically |
| Inconsistent — depends on the reviewer | Consistent — same rules every time |
| No audit trail | Every decision is logged |
| Doesn't scale | Runs on every PR across every repo |

---

## The Simple Version

> **This repo is the employee handbook and org chart for a team of AI assistants that review code so humans don't have to.**

You add it to your project, and your AI tools learn how to behave like a disciplined, auditable software delivery team.

---

## Want to Go Deeper?

- [Developer Quick Guide](developer-guide.md) — how to set it up and use it day-to-day
- [README](../../README.md) — full architecture and reference documentation
- [End-to-End Walkthrough](../tutorials/end-to-end-walkthrough.md) — a complete example from issue to merge
