"""The contents of notebooks/00_START_HERE.ipynb."""
CELLS = [
("md", """# Start here

Hello, and welcome. I'll be your teacher. **You don't need any experience:** topic 1 assumes nothing, and each topic builds on the last.

By the end, you'll understand how data systems work from the disk up, and you'll have practised the questions real data engineering interviews ask.

### A straight answer about "top 2%"

**No course can make you top 2% by itself, and be wary of any that claims to.** The very best engineers got there through this kind of knowledge plus years of running real systems. Here's what's true:

| This course gives you | You still need |
|---|---|
| 21 topics, from zero to senior-level design | **Building real pipelines** and fixing them when they break at 3 am |
| 420 tested questions, with hints and visual answers | **Speed under pressure,** which only practice gives |
| Lessons on why things work, not just which tools to use | **Hands-on time with real clusters** and real scale |
| Scenario and design questions | **Mock interviews,** and learning from people at work |

Do the work below and you'll understand data engineering more deeply than many working engineers, because you'll know why things work. That's the part of "top 2%" that a course can really give you.
"""),
("md", """## The roadmap

Go in order. Allow more time for anything new to you.

| Phase | Topics | You'll be able to | Rough time at 1–2 hours a day |
|---|---|---|---|
| **1. Foundations** | How Data Flows, Python, SQL Foundations, Advanced SQL | query anything, write small pipelines | 5–6 weeks |
| **2. How data systems work** | Databases, Modelling, Storage, Toolbox | design tables, read plans, use Git and Docker | 4–5 weeks |
| **3. Building pipelines** | Pipeline Patterns, Distributed Systems, Spark ×2, Airflow | build reliable batch pipelines | 6–8 weeks |
| **4. Real time and modern stack** | Kafka, Streaming, Quality, Lakehouse, Warehouses & dbt | choose the right architecture | 5–6 weeks |
| **5. Senior skills** | Cloud & Security, System Design, Data for AI | design and defend whole systems | 3–4 weeks |

That's roughly 6 months. These are guides, so move on when you can tick a notebook's checklist **without looking**, not when the calendar says so.

**Find every notebook in the [full list](README.md).** Already working in data? Skim the checklists and start where you can't tick the boxes.
"""),
("md", """## How to study, so it sticks

1. **Try before you look.** Struggling for 15 to 25 minutes, even if you fail, makes the answer stick far better than reading it straight away.
2. **Work the numbers on paper.** Lessons use small numbers so you can check them by hand.
3. **Open one hint at a time.**
4. **Type code, never paste it.** Then change something, and predict what happens.
5. **Come back later.** Redo a question after 3 days and again after 2 weeks, from a blank cell. It's the most effective habit here.
6. **Say answers out loud,** especially the scenario questions.
7. **Build something.** See [the labs and project ideas](../labs/README.md). Reading won't teach you what a failed backfill feels like.

**A good session (about 90 minutes):** 15 minutes redoing old questions, 30 on a lesson, 45 on new questions.
"""),
("md", """## The questions great data engineers ask

Everything in this course comes back to these. Memorise them, and ask them of every pipeline you touch.

| Question | Topic |
|---|---|
| What decision does this data support, and how fresh must it be? | How Data Flows |
| What does one row mean? | Data Modelling |
| What happens if it runs twice? | Pipeline Patterns |
| What happens if it fails halfway? | Pipeline Patterns |
| What if data arrives late, or out of order? | Pipeline Patterns, Streaming |
| What if the source changes its schema? | Storage, Data Quality |
| Which key decides how the data spreads, and is it skewed? | Distributed Systems, Spark |
| How will I know it's wrong before my users do? | Data Quality |
| What will this cost, and who can see the data? | Warehouses, Cloud & Security |
"""),
("md", """## Which technique is this question asking for?

| If you hear… | Think of… |
|---|---|
| "latest record per customer" | `ROW_NUMBER() ... = 1` |
| "top 3 per category" | `DENSE_RANK` in a CTE |
| "consecutive days" | value − `ROW_NUMBER` |
| "user sessions" | `LAG`, then a running `SUM` |
| "track address history" | SCD type 2 |
| "job stuck at 99%" | data skew |
| "too many small files" | compaction, repartition before writing |
| "safe to rerun" | overwrite a partition, or upsert |
| "only load what changed" | watermark or CDC |
| "see deletes from a database" | CDC |
| "late events" | event time and watermarks |
| "no duplicates" | idempotent sink on a unique key |
| "consumer falling behind" | lag; add consumers up to the partition count |
| "numbers doubled" | a join on a non-unique key, or a rerun with append |

### Test yourself

Answer before opening each one.

<details><summary><b>1. A daily job was rerun and revenue doubled. What's wrong, and how do you fix it?</b></summary>

It appends rather than being idempotent. Replace that day's partition now, then change the job to overwrite the partition or upsert on a key.
</details>

<details><summary><b>2. A Spark job has 199 fast tasks and 1 slow one. What's your first thought?</b></summary>

Skew. Compare input size per task in the Spark UI. Check for NULL or hot keys, then filter, broadcast, use AQE, or salt.
</details>

<details><summary><b>3. A manager asks for "real-time" sales data. What do you ask first?</b></summary>

How fast does someone act on it? Often every 15 minutes is enough, and far cheaper and simpler to run.
</details>

<details><summary><b>4. Your LEFT JOIN behaves like an INNER JOIN. Why?</b></summary>

A WHERE condition on the right table removes the NULL rows. Move it into the ON clause.
</details>

<details><summary><b>5. An Airflow run for 5 January processed 6 January's data. Why?</b></summary>

The code probably used the current date rather than the logical date. A daily run for 5 January starts on 6 January, after its interval ends.
</details>

<details><summary><b>6. A deleted customer still shows up in your warehouse copy. Why?</b></summary>

A watermark-based incremental load can't see deletes. Use CDC or soft deletes, or a periodic full comparison.
</details>
"""),
("md", """## Interview preparation

**A typical data engineering loop:**

| Round | Tested on | Topics |
|---|---|---|
| SQL | window functions, joins, modelling | 3, 4, 6 |
| Python / coding | data structures, parsing, simple algorithms | 2, plus some general DSA practice |
| Big data | Spark, Kafka, how you'd debug | 10–15 |
| System design | designing a whole pipeline aloud | 9, 17, 20 |
| Behavioural | incidents, ownership, teamwork | your own stories |

**Prepare stories using STAR** (Situation, Task, Action, Result). Have true ones ready for: an incident you handled, a pipeline you improved with numbers, a time data was wrong, a disagreement, and a mistake you made. Spend most of the time on what *you* did.

**What this course doesn't cover in depth:** general DSA for coding rounds (see the [DSA handbook](https://abpandey-dev.github.io/learn-python-from-scratch-to-advanced/handbook/)), and specific products such as Snowflake or Databricks, whose current documentation you should read for any role that needs them.

**Now open [topic 1](topics/01_big-picture.ipynb).** One question at a time. You've got this.
"""),
]
