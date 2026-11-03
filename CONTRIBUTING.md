# Contributing

These are our team rules. Read them before you start working.

## Team

| Name | GitHub |
|---|---|
| Min Tun | @trippiemin39 |
| _Wenyu Damen_ | _@Player7B48_ |

**Chat:** _Discord_. This is where we talk every day.

---

## 1. Staying in contact

We are a team of 2, so we must keep each other updated.

**Check-ins (short, 5 minutes):**

| When | What we share |
|---|---|
| **Start of the day** | What will I do today? Do I need help? |
| **End of the day** | What did I finish? What is still open? |

**Blocked?** Send a message **right away**. Don't wait until the next check-in.

**Rules:**
- Answer messages within **2 hours** during the sprint.
- If you can't work for a day, tell your teammate before that day.

---

## 2. Feedback loops

We give feedback often, in small steps.

| Moment | What happens |
|---|---|
| **Every pull request** | Your teammate reviews your code before it is merged |
| **Middle of the sprint** | Short check: are we on track? Do we need to change the plan? |
| **End of the sprint** | **Review:** show what we built. **Retro:** talk about how we worked. |

**How we give feedback:**
- Be clear and kind. Talk about the code, not the person.
- Give a reason: *"Rename this variable, because the name is unclear."*
- Also say what is good.

**How we receive feedback:**
- Don't take it personally. Feedback makes the project better.
- Fix it, or explain why you don't agree.
- Write down important feedback in the issue. We use it in our reflection.

---

## 3. Sprint plan (2 days)

| Day | Morning | End of day |
|---|---|---|
| **Day 1** | Sprint planning: pick tasks, give each task an owner | Check-in + feedback on progress |
| **Day 2** | Check-in: what is left? | Sprint review + retrospective |

---

## 4. Project board

- Every task is an **issue** on the project board.
- Every issue has: an **owner**, a **priority**, a **size** and an **iteration**.
- Move your card when the status changes:

`Backlog → Ready → In progress → In review → Done`

- Only work on **1 task at a time**.

---

## 5. Branches

- `main`: the stable version. **Never work on main directly.**
- `Develop`: all finished work comes together here.
- For every task, make a new branch **from Develop**:

```
feature/<issue-number>-<short-name>
```

Example: `feature/28-date-id-connection`

Tip: open the issue and click **"Create a branch"** under *Development*.

Delete the branch after it is merged.

---

## 6. Commits

Start every commit message with the issue number:

```
#<issue-number> <what you did>
```

Examples:
- `#28 add date_id column to fact table`
- `#30 fix missing values in state prices`

Make small commits. One commit = one change.

---

## 7. Pull requests

1. Open a pull request from your branch **into Develop**.
2. Write `Closes #<issue-number>` in the description.
3. Explain in 1–3 lines what you changed.
4. Ask your teammate to review.
5. The reviewer answers within **4 hours** (it's a short sprint).
6. Fix the feedback, then merge.

**Reviewer checklist:**
- [ ] Does the code work?
- [ ] Is the code easy to read?
- [ ] Does it do what the issue asks?
- [ ] No API keys or passwords in the code?

---

## 8. Definition of Done

A task is **Done** when:

- [ ] The code works and the pipeline still runs with one command
- [ ] All "Done when" points in the issue are checked
- [ ] A teammate reviewed and approved the pull request
- [ ] The pull request is merged into Develop
- [ ] The README is updated (if needed)
- [ ] No secrets (API keys) are in the code

---

## 9. Safety

- Never put your API key in the code. Keep it in `API_CODE/FRED_API.txt`.
- This file is in `.gitignore`, so it is never uploaded.
