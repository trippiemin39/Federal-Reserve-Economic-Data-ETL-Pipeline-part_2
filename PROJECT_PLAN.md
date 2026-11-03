# Project Plan – Part 2

## Where we start (Part 1)

In part 1 we built an ETL pipeline in Python:

- **Extract:** we get 6 economic indicators from the FRED API
  (CPI, CPI energy, electricity, natural gas, oil, recession indicator).
- **Transform:** we clean the data and turn daily prices into monthly averages.
- **Load:** we save everything in a star schema in SQLite
  (1 fact table + 3 dimension tables).

The pipeline works for the whole United States, with data from 1947 to 2026.

## What we want to find out (Part 2)

**Main question:**
How strongly are energy prices and inflation connected,
and do data centers make energy more expensive?

## The big picture

| Epic | What we do | Type of work |
|---|---|---|
| #18 Project setup | Get the repo, the team and the rules ready | Organize |
| #19 Pipeline expansion | Add energy prices per US state and data center data. Connect the date table. | Change |
| #20 Correlation analysis | Measure the link between energy prices and inflation. Compare states with many and few data centers. | Research + Analyse |
| #21 Dashboard | Show the results in a dashboard that everyone can understand | Create |
| #22 Documentation & delivery | Update the README, the diagrams and give the final presentation | Explain |

## How the parts connect

```
Part 1 pipeline  →  #19 more data  →  #20 analysis  →  #21 dashboard  →  #22 presentation
       (base)        (per state)       (answers)        (visual)          (share)
```

Each step uses the result of the step before.

## How we work

- All tasks are on our 🐻-FREDDY-PROJECT-🐻.
- We work in **sprints** of a day
- Every task gets its own **branch** from `Develop`.
- Every change goes through a **pull request** and a review by a teammate.
- See `CONTRIBUTING.md` for the team rules.
