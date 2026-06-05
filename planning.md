# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

<!-- What domain did you choose? Why is this knowledge valuable and hard to find through official channels? -->

---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | www.forbes.com|  Should You Switch Your Student Loans To The New Repayment Assistance Plan? | https://www.forbes.com/sites/adamminsky/2026/05/14/should-you-switch-your-student-loans-to-the-new-repayment-assistance-plan/ |
| 2 | www.forbes.com | These Student Loan Borrowers May Get Locked Out Of Key Repayment Plan Unless They Act Quickly| | https://www.forbes.com/sites/adamminsky/2026/05/06/these-student-loan-borrowers-may-get-locked-out-of-key-repayment-plan-unless-they-act-quickly/ |
| 3 | https://www.savingforcollege.com| How Will Your Student Loan Payment Change With the Repayment Assistance Plan (RAP)? | https://www.savingforcollege.com/article/student-loan-repayment-assistance-plan-rap |
| 4 | www.forbes.com | Education Department Sends Mass Warnings To Student Loan Borrowers To Change Repayment Plans, Or Else |  https://www.forbes.com/sites/adamminsky/2026/05/26/education-department-sends-mass-warnings-to-student-loan-borrowers-to-change-repayment-plans-or-else/ |
| 5 | https://www.cnbc.com | Student loan borrowers will have two new repayment options come July 1. Here's how to pick one | https://www.cnbc.com/amp/2026/05/29/student-loan-borrowers-new-repayment-plans.html |
| 6 | https://www.cbsnews.com/ | 4 things student loan borrowers should do before July 1 | https://www.cbsnews.com/news/what-student-loan-borrowers-should-do-before-july-2026/ |
| 7 | https://studentaid.gov/ | Beautiful Bill Act Updates | https://studentaid.gov/announcements-events/big-updates |
| 8 | https://www.nytimes.com | Student Loan Repayments Are Being Overhauled. What Borrowers Should Know. |  https://www.nytimes.com/2026/05/25/your-money/student-loans-repayment-save-biden.html |
| 9 | https://www.earnest.com/| Income-driven repayment plans are changing: What borrowers need to know in 2026 | https://www.earnest.com/blog/income-driven-repayment-changes?cs=0&hl=en-US&biw=1710&bih=802 |
| 10 | https://ticas.org/ | Upcoming Changes to Income-Driven Repayment Plans | https://ticas.org/affordability-2/upcoming-changes-to-income-driven-repayment-plans/?cs=0&hl=en-US&biw=1710&bih=802 |
| 11 | https://studentloanborrowerassistance.org/ | Big Bill Means Big Changes For Student Loan Borrowers: What You Need to Know | https://studentloanborrowerassistance.org/big-bill-means-big-changes-for-student-loan-borrowers-what-you-need-to-know/ |

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:**

**Overlap:**

**Reasoning:**

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:**

**Top-k:**

**Production tradeoff reflection:**

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1.

2.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:**

**Milestone 4 — Embedding and retrieval:**

**Milestone 5 — Generation and interface:**
