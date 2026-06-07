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
| 12 | https://studentaid.gov                      | Federal Student Loan Repayment Plans                                                                  | https://studentaid.gov/manage-loans/repayment/plans
| 13 | https://aidvantage.studentaid.gov/          | Federal Student Loan Repayment Options                                                                | https://aidvantage.studentaid.gov/in-repayment/federal-options#repayment-resources
| 14 | https://studentaid.gov/.                    | One Big Beautiful Bill Act – Important Definitions                                                    | https://aidvantage.studentaid.gov/in-repayment/federal-options#repayment-resources

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

# Spec: `chunk_document()`

**File:** `ingest.py`

---

## Purpose

Split a single student loan article into smaller chunks suitable for embedding and semantic retrieval. Each chunk should carry enough context to be meaningful on its own when retrieved in response to a user query.

---

## Input / Output Contract

**Inputs:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `text` | `str` | The full text of a student loan article |
| `article_name` | `str` | The name of the article (i.e. ) |

**Output:** `list[dict]`

Each dict in the returned list contains exactly these keys:

| Key | Type | Description |
|-----|------|-------------|
| `"text"` | `str` | The chunk text |
| `"game"` | `str` | The game name (passed through from `game_name`) |
| `"chunk_id"` | `str` | A unique identifier for this chunk (e.g., `"catan_0"`, `"catan_1"`) |

Returns an empty list `[]` if the input text is empty or produces no valid chunks.

**Chunk size:**

I will experiment with this. I will first try a 300 token (word) strategy, but based on what I learned from the RulesBot Tinker, I will probably switch to using a sentence, paragraph, or section strategy. I will record my experimentation here. 

Attempt 2: 150 chunk strategy

**Overlap:**

I will start with a 50 token overlapping strategy. We learned from the Tinker lab that "Overlap reduces the effective size of each chunk by distributing boundary content across neighbors, which keeps individual embeddings more focused and semantically precise.", so I will try to use it at first. I found from the Tinker lab that I got my best results from using a section strategy, so this might not be needed.   


Attempt 2: 40 chunk overlap

**Reasoning:**
I am starting with 300-token chunks because this size is likely large enough to capture a complete idea from a typical article paragraph, while still keeping chunks small enough for precise retrieval.
I am using 50-token overlap to preserve continuity across chunk boundaries, especially when a sentence or concept spans two chunks. Because my sources are mostly online news and explainers with overlapping content, I expect a sentence/paragraph/section strategy may ultimately be better, but I want to test the 300-token baseline first.

Results:
Strategy 1: 300 chunk/word and 50 chunk overlap strategy yielded 

Returned 3 300 chunk excerpts and answered question partially correctly. 

Retrieved chunks:

1.
     1. Should You Switch Your Student Loans To The New Repayment Assistance Plan (distance=0.5522, words=300)
even if those loans are consolidated. Drawbacks Of Moving Student Loans To Repayment Assistance Plan But while the interest subsidy and directed principal payment are major benefits of RAP, there are also some serious downsides. In addition to being more expensive than SAVE, PAYE, and new IBR (which will cause all of those borrowers to experience higher monthly payments on their federal student loans when they are forced to change plans), RAP will have no cap or upper limits on high the payments can get. IBR and PAYE, on the other hand, cap monthly student loan payments at the amount equivalent to the 10-year Standard plan. That’s a critical downside of RAP, because that means that at some point, payments under RAP could become much more expensive than IBR and other federal student loan repayment plan options as a borrower’s income increases over time. RAP will have other payment quirks that are arguably downsides. Unlike all other income- driven repayment plans, RAP will have a minimum required monthly payment of at least $10 per month. That may not sound like much, but even borrowers who can demonstrate that they have no income whatsoever will still have to pay at least $10 per month. Under existing income-driven repayment plans, including IBR, borrowers earning under 100% or 150% of the federal poverty limit based on their family size can have a $0 payment for up to 12 months. In addition, RAP has a less generous definition of family size than existing income-driven plans, offering only a flat $50 monthly payment deduction per dependent child; that limitation will hit multigenerational and nontraditional families hard, as a borrower’s monthly payment may not be adjusted to reflect the additional expenses associated with supporting a larger family. And RAP’s unique tiered repayment formula, whereby the percentage
2. Student Loan Repayments Are Being Overhauled (distance=0.5537, words=300)
     8. (but taxable as income). But RAP’s mechanics are different. • RAP payments are graduated, ranging from 1 percent to 10 percent of the borrower’s adjusted gross income — the higher your income, the higher the percentage. (In contrast, I.B.R. shields a share of borrowers’ income from payments to cover basic expenses and calculates the payment on income above that amount.) • RAP’s term is up to 30 years (at which point any remaining debt is wiped away). That’s five to 10 years longer than earlier income-driven plans. • Borrowers can deduct $50 from their payment for each dependent claimed on their tax return, while I.B.R. has a broader and more generous adjustment for household members. • RAP also requires people with extremely low or no income to make a token payment of $10 a month, whereas other income-driven plans don’t require any payment. RAP has some beneficial features. If your monthly payment amount doesn’t cover the interest owed, the interest will be waived and erased. There’s also a guarantee that your loan’s principal — the amount you borrowed — will fall by up to $50 a month. Let’s say you have a monthly payment of $50 (or greater). If your payment chips away at only $20 of the principal, for example, the federal government kicks in an additional $30, experts said. These features were crafted so a borrower’s balance won’t grow over time. But there’s a significant drawback that could make this plan more expensive over time: RAP is not indexed for inflation, so a borrower whose income merely kept pace with inflation could be bumped into higher payment tiers. “For someone who has a modest income today, and whose paycheck just keeps up with inflation, they’d essentially see their monthly payment double over 20 years without really seeing a
3. Should You Switch Your Student Loans To The New Repayment Assistance Plan (distance=0.5870, words=300)
     8. a larger balance could mean a higher tax bill at discharge (or a larger balance to pay off, if the borrower’s financial circumstances change before then). RAP will have a major benefit that waives any interest that accrues in excess of a borrower’s minimum require monthly student loan payment (as long as they make their payment on time), preventing runaway balance growth. This is similar to what the SAVE plan had offered, before it was suspended and ultimately eliminated. In addition, for borrowers in this situation (whose payments are not covering all their interest), RAP will allow up to $50 of each payment made on their student loans to go directly to principal, a unique feature that no other income-driven repayment plan offers. The net effect of these benefits is that not only will a borrower’s federal student loan balance not grow any further under RAP, but it should actually decrease for all borrowers over time (even if only marginally). As for monthly payments, the benefits of RAP are a bit more muddled. RAP will almost universally have lower monthly payments than the ICR plan, and will often (but not always) have lower monthly payments than the older version of the IBR plan for borrowers who first took out their federal student loans before July 1, 2014. However, payments under RAP will typically be higher compared to SAVE, PAYE, and the newer version of IBR. Importantly, Parent PLUS loans will not be able to enroll in RAP under any circumstances, even if those loans are consolidated. Drawbacks Of Moving Student Loans To Repayment Assistance Plan But while the interest subsidy and directed principal payment are major benefits of RAP, there are also some serious downsides. In addition to being more expensive than SAVE, PAYE, and new IBR (which will cause

A: According to Source 2, RAP is not indexed for inflation, so a borrower whose income merely kept pace with inflation could be bumped into higher payment tiers. This could cause their monthly payment to double over 20 years without a corresponding increase in income.

Evaluation: missing part of answer (RAP has no payment cap (IBR and PAYE cap payments at the 10-year Standard amount), and is citing citation Source 2 instead of Source 1 and 8. The source is also in Source 1, apparently, so Claude missed that when generating test questions. My model isn't perfect. I want to try with a smaller chunking strategy, and then try out section based chunking. 

Attempt 2 Results
Chunk_size(words) = 300
Overlap = 40 


Retrieved chunks:

1. Should You Switch Your Student Loans To The New Repayment Assistance Plan (distance=0.5222, words=150)
     1. and directed principal payment are major benefits of RAP, there are also some serious downsides. In addition to being more expensive than SAVE, PAYE, and new IBR (which will cause all of those borrowers to experience higher monthly payments on their federal student loans when they are forced to change plans), RAP will have no cap or upper limits on high the payments can get. IBR and PAYE, on the other hand, cap monthly student loan payments at the amount equivalent to the 10-year Standard plan. That’s a critical downside of RAP, because that means that at some point, payments under RAP could become much more expensive than IBR and other federal student loan repayment plan options as a borrower’s income increases over time. RAP will have other payment quirks that are arguably downsides. Unlike all other income- driven repayment plans, RAP will have a minimum required monthly payment of
2. Should You Switch Your Student Loans To The New Repayment Assistance Plan (distance=0.5250, words=150)
     1. long as they make their payment on time), preventing runaway balance growth. This is similar to what the SAVE plan had offered, before it was suspended and ultimately eliminated. In addition, for borrowers in this situation (whose payments are not covering all their interest), RAP will allow up to $50 of each payment made on their student loans to go directly to principal, a unique feature that no other income-driven repayment plan offers. The net effect of these benefits is that not only will a borrower’s federal student loan balance not grow any further under RAP, but it should actually decrease for all borrowers over time (even if only marginally). As for monthly payments, the benefits of RAP are a bit more muddled. RAP will almost universally have lower monthly payments than the ICR plan, and will often (but not always) have lower monthly payments than the older version of
3. How Will Your Student Loan Payment Change With The Repayment Assistance Plan (distance=0.5309, words=150)
     3. radar. Critics counter that $10 a month still matters to families already struggling to juggle rent, food, and childcare costs. If you’re used to a $0 bill, plan for $120 a year under RAP. Build an automatic transfer on payday or mark your calendar so a missed $10 doesn’t snowball into late fees and credit-score damage. And recertify your income every year. Falling even a few months behind could push your payment above the $10 floor. Deferment & forbearance: Why RAP is stricter than current rules SAVE offered struggling borrowers multiple off-ramps, including $0 payments for low-income borrowers and multi-year deferment and forbearance options. Under RAP, payments remain low by capping interest and charging just $10. Yet, it removes the long deferment windows that protect a borrower’s credit during prolonged hardship (though it does still allow administrative forbearance). For anyone with unstable income, those tighter limits make RAP significantly less
According to Source 1, RAP could become more expensive over time because it has no cap or upper limits on how high the payments can get, unlike IBR and PAYE which cap monthly student loan payments at the amount equivalent to the 10-year Standard plan.

Evaluation: Now the resultws missing part of answer (RAP is not indexed for inflation), and is now citing source 1 (the source my ansewr key has listed as correct). 

Claude is suggesting that I improve the prompting, increase N_RESULTS to give the model more candidate evidence to combine, increase overlap, experiment with sentence/paragraph/section chunking, and use a stronger enbeddingn model but first I will commit here so that you can evaluate project before I make more changes.  



---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:**
I am using all-MiniLM-L6-v2 via sentence-transformers as my embedding model. 

Advantages of all-MiniLM-L6-v2 via sentence-transformers
Fast and lightweight

Small model size means much lower latency for embedding generation.
Good for local development, quick experiments, and lower compute costs.
Strong semantic retrieval quality

Designed for sentence-level and short-document embeddings.
Works well for web articles, FAQs, and question-answer retrieval tasks.
Easy integration

sentence-transformers provides a simple API: encode text directly into vectors.
No manual tokenization or embedding pipeline required.
Stable offline usage

Downloads once and runs locally, which is useful when you want a self-contained retrieval pipeline.
Avoids API dependency and per-call costs.
Good general-purpose performance

Balances speed and accuracy well for many domains.
Especially strong for English text and short-to-medium chunks like your article segments.

This is also part of the recommended stack, so I feel good about my decision. 


**Top-k:**

Top-k = N_RESULTS = 3

**Production tradeoff reflection:**

Production tradeoffs for all-MiniLM-L6-v2
Advantages

Fast inference and low latency
Small model footprint, so it runs well on CPU and is easy to deploy
Low cost for embedding generation
Good baseline for general English text and retrieval from article-like sources
Works well offline with sentence-transformers and avoids API dependency
Drawbacks

Lower semantic accuracy than larger models
Less robust on domain-specific or highly nuanced student loan language
Not ideal if you need the best possible ranking quality for hard queries
Embeddings may be less stable for longer or complex chunks
Production tradeoffs

Use it when: speed, cost, and simplicity matter more than the last bit of retrieval accuracy
Avoid it when: you need high-precision retrieval, especially for rare domain terms or legal/financial nuance
If cost is not a constraint, a stronger model like all-mpnet-base-v2 or a premium API embedding will likely give better relevance
If you need multilingual support or more robust comparison for longer chunks, this model is a weaker choice

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

**Source key:**
1. Forbes / Minsky — *Should You Switch Your Loans to RAP?*
2. Forbes / Minsky — *Borrowers May Get Locked Out of PAYE*
3. Saving for College — *How Will Your Payment Change With RAP?*
4. Forbes / Minsky — *Education Dept. Sends Mass Warnings*
5. CNBC — *Two New Repayment Options Come July 1*
6. CBS News — *4 Things Borrowers Should Do Before July 1*
7. StudentAid.gov — *One Big Beautiful Bill Act Updates*
8. NYT — *Student Loan Repayments Are Being Overhauled*
9. Earnest — *Income-Driven Repayment Plans Are Changing*
10. TICAS — *Upcoming Changes to IDR Plans*
11. NCLC / SLBA — *Big Bill Means Big Changes*
12. StudentAid.gov — *Federal Student Loan Repayment Plans*
13. Aidvantage — *Federal Student Loan Repayment Options*
14. StudentAid.gov - *One Big Beautiful Bill Act Definitions*

| # | Question                                                                                                    | Expected answer                                                           |Source
|---|----------|--------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------|
| 1 | Why could RAP become more expensive over time despite its low starting percentages?                         | RAP has no payment cap (IBR and PAYE cap payments at the 10-year Standard amount), and it is not indexed for inflation — so a borrower whose pay merely keeps up with inflation can be bumped into higher tiers, with payments effectively rising over time.                                                                                                     | *(Sources 1, 8)*| |
| 2 | What must a Parent PLUS borrower do to keep access to an income-driven plan, and which plan can they get?   |  They must consolidate before July 1, 2026 and enroll in ICR (making at least one payment) before the 2028 phase-out; they then become eligible for IBR — not RAP.                                                                                                                                                                                            | *(Sources 8, 11, 12)*| |
| 3 | How do "old IBR" and "new IBR" differ?                                                                      | Old IBR (loans before July 1, 2014): 15% of discretionary income, forgiveness after 25 years. New IBR (loans July 1, 2014 onward): 10% of discretionary income, forgiveness after 20 years                                                                                                                                                                      | *(Sources 8, 11, 5)*
| 4 | What is the apparent contradiction in the Education Department's PAYE rules?                                | The finalized regulations restrict PAYE re-enrollment, yet the Department's own online guidance said there would be "no restriction" on enrolling in IBR, ICR, or PAYE for borrowers with pre–July 2026 loans — and the OBBBA statute itself doesn't contain those enrollment restrictions.                                                                       | *(Source 2)*| |
| 5 | What risk does consolidating loans pose to forgiveness progress?                                             | Consolidating erases existing income-driven forgiveness credit (a consequence of the court decision vacating SAVE), and consolidating after July 1, 2026 limits the borrower to only RAP and the Tiered Standard Plan — losing access to IBR.                                                                                                                   | *(Source 8)*| |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1. Noisy or inconsistent documents

     -Many news articles repeat the same high-level facts in different ways, and some may include opinion or speculation.
     -If the retrieval system embeds and returns these noisy passages, the assistant can answer with inconsistent or outdated information.

2. Chunks split key information across boundaries

     -Fixed-size chunking can cut sentences or ideas in half.
     -That means a relevant answer may require combining two chunks, but retrieval may only return one, causing incomplete or misleading responses.

3. Off-topic retrieval

     -My articles have many overlapping terms like “RAP,” “SAVE,” and “loan forgiveness.”
     -A query may retrieve a chunk that mentions the keyword but is actually about a different program or borrower type, leading to a wrong answer.

3. Missing source attribution

     -If chunks don’t preserve clear document metadata, the model can’t say “this came from Forbes vs. StudentAid.gov.”
     -That makes it harder to verify answers and raises the risk of producing responses that sound confident but are not traceable to the original source.
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
I will use Claude to help me ingest the pdf documents using pdfplumber. 
I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()

**Milestone 4 — Embedding and retrieval:**

**Milestone 5 — Generation and interface:**
