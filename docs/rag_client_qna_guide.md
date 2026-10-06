# RAG Optimization Platform: Client Q&A and Capacity Guide

This guide compiles answers to key client-facing questions regarding the AutoRAG scoring system, performance metrics, data ingestion benchmarks, and system capacities. It is designed to serve as a reference for explaining technical RAG concepts to non-technical stakeholders.

---

## Part 1: The RAG Scoring System

The system evaluates RAG performance across several categories to calculate a single **Unified Score**:

$$\text{Unified Score} = (0.25 \times \text{Retrieval}) + (0.35 \times \text{Quality}) + (0.25 \times \text{Faithfulness}) - \text{Latency Penalty} - \text{Cost Penalty}$$

### How Individual Metrics Are Measured

#### 1. Retrieval Score (Search Accuracy) — *Weight: 25%*
Measures whether the search engine successfully retrieves the correct source documents.
*   **Methodology:** The system compares the chunks retrieved by the RAG pipeline against the "expected" chunk IDs defined in the Golden Set.
*   **Formula:** 
    $$\text{Recall} = \frac{\text{Number of Expected Chunks Successfully Retrieved}}{\text{Total Number of Expected Chunks}}$$

#### 2. Quality Score — *Weight: 35%*
Measures the relevance and ranking of retrieved data and the structure of the answer. It is the average of two components:
*   **Context Precision (Rank-Aware):** Evaluates if the most relevant search results are ranked at the top of the search results list rather than at the bottom.
*   **Answer Relevancy:** An LLM (acting as a judge) evaluates if the generated answer directly addresses the user's question, scoring it from $0.0$ to $1.0$.

#### 3. Faithfulness (Factuality / Anti-Hallucination) — *Weight: 25%*
Measures whether the generated answer is strictly supported by facts (i.e. no hallucinations).
*   **Methodology:** An LLM judge reads the question, the ground-truth answer, and the generated response, rating the factuality on a scale of $0.0$ to $1.0$.

---

### The "100% = 85%" Paradox

A common point of confusion is when the dashboard displays **100%** on all sub-metric cards (Retrieval, Quality, Faithfulness, Adversarial Pass), but the **Unified Score** shows **85%**. 

**This is the correct, maximum possible score.**
*   The positive weights ($0.25 + 0.35 + 0.25$) add up to $0.85$ ($85\%$).
*   The remaining $15\%$ is reserved for **Performance Penalties** (up to $10\%$ for latency and $5\%$ for cost).
*   Because latency and cost are *subtracted* as penalties rather than added as scores, a flawless system with zero latency/cost penalties will hit a ceiling of **85%**. This is well above the **72% Gate Approved** deploy threshold.

---

## Part 2: Latency Penalties vs. Total Evaluation Run Time

### Why the Evaluation Took 2 Minutes, but Incurred 0 Penalty
The system distinguishes between the time it takes to run a batch test and the experience of a single user:
*   **Total Evaluation Time:** The time taken to run all test queries in a batch, send requests to the cloud, wait for LLM generations, and execute LLM judging tasks. This suite run can take 1 to 2 minutes due to sequential network queues and API limits.
*   **Query Latency:** The response time of a single question for a real user. **The Latency Penalty is based ONLY on the median of this single query response time.**

### Latency Thresholds
*   **$\le 8$ seconds:** Good (No Penalty)
*   **$8 - 15$ seconds:** OK ($0.5$ deduction)
*   **$> 15$ seconds:** Bad ($1.0$ deduction)

If your evaluation took 2 minutes total, but each test query responded in $4$ seconds on average, the median latency is $4000\text{ ms}$. This is under the $8$-second limit, resulting in a **0.0 penalty** (Perfect).

---

## Part 3: Safety Guardrails (Adversarial Pass)

The **Adversarial Pass** is an anti-hallucination check that tests the AI's ability to refuse to answer questions when the database does not contain the answer.

### The Guardrail Test
The system sends 5 hardcoded "trick" questions to the AI that are not present in your files (e.g., *"What is the revenue forecast for 2035?"*). 
*   **Pass (Score: 1):** The system detects refusal phrases in the output (e.g., *"I don't know"*, *"cannot answer"*, *"no information found"*, *"not present"*).
*   **Fail (Score: 0):** The AI tries to make up an answer or guess.

### The Hard Gate Rule
Because safety is critical, the deployment gate has an **absolute threshold of 100%** for the Adversarial Pass. If the model hallucinates an answer to even one trick question, the entire pipeline is **blocked from deployment**, even if all other metrics are perfect.

---

## Part 4: The Golden Set (The System Benchmark)

The **Golden Set** is a frozen, standardized test suite generated automatically when you first ingest documents. It contains 10 questions (5 document-based synthetic queries and 5 adversarial queries) along with expected answers and source chunk IDs.

*   **Why it is frozen:** By testing every pipeline configuration against the exact same static set of questions, we ensure a fair comparison. If the test questions changed every time, you could not tell if a higher score was due to a better model or easier questions.

---

## Part 5: Under the Hood — Custom RAGAS Emulation

Although `ragas` is listed as a project dependency, the backend code **does not import the Python `ragas` package**. 

Instead, the codebase custom-emulates RAGAS metrics in pure Python. This provides three major benefits:
1.  **Speed:** Bypasses heavy wrapper libraries, making async database and API calls in parallel.
2.  **Cost:** Reduces the volume of upstream API tokens consumed by limiting evaluations to exactly two judge calls per query.
3.  **Stability:** Prevents pipeline crashes caused by external changes or breaking updates in the RAGAS library.

---

## Part 6: Ingestion Speed & Capacity Benchmarks

### Processing Timelines by Data Size

These estimates show how processing scales from standard team servers to enterprise clusters:

| Data Volume | Est. Page Count | Standard Ingestion Time | Tiers & Infrastructure |
| :--- | :--- | :--- | :--- |
| **1 GB** | ~50,000 Pages | **1 – 1.5 Hours** | Standard Server (4 Workers) |
| **5 GB** | ~250,000 Pages | **4 – 6 Hours** | Standard Server (4 Workers) |
| **10 GB** | ~500,000 Pages | **8 – 12 Hours** | Standard Server (8 Workers) |
| **50 GB** | ~2.5 Million Pages | **12 – 18 Hours** | Scaled Cluster (16 Workers) |
| **100 GB** | ~5 Million Pages | **24 – 30 Hours** | Enterprise Cluster (32 Workers) |
| **500 GB** | ~25 Million Pages | **12 – 18 Hours (Distributed)** | Enterprise Cluster (64 Workers) |
| **1 TB** | ~50 Million Pages | **24 – 36 Hours (Distributed)**| Enterprise Cluster (64 Workers) |

---

### Processing Speeds by File Type

Different file types require different levels of processing. Native files are processed using quick python parsers, whereas images/scans require Vision AI models.

| Document Format | Speed (Per Worker) | Core Processing Step |
| :--- | :--- | :--- |
| **Plain Text (`.txt`, `.md`)** | ~50,000 pages / min | Direct text chunking (instantaneous). |
| **Word Docs (`.docx`)** | ~2,000 pages / min | Automated structure parser (`python-docx`). |
| **Spreadsheets (`.csv`, `.xlsx`)** | ~10,000 rows / min | Formats tables into markdown strings. |
| **PowerPoints (`.pptx`)** | ~500 slides / min | slide-by-slide text extraction. |
| **Searchable PDFs (`.pdf`)** | ~500 pages / min | Direct stream text extraction (`PyMuPDF`). |
| **Scanned PDFs / Tables** | ~10 – 30 pages / min | Coordinate-based cell parsing (`pdfplumber`). |
| **Images (`.png`, `.jpg`)** | ~30 – 45 images / min | **Vision AI:** Converts image to text & auto-generates description. |

---

### Scaling and Architecture Capacity

*   **Database Limit (Supabase/pgvector):** A standard PostgreSQL database with HNSW vector indexing can store and query **100+ Gigabytes of text embeddings** (~100 million paragraphs) with sub-second retrieval times.
*   **LLM API Limit:** The bottleneck is the Google Gemini API limits. By batching our embeddings, the system can write up to **1.5 to 2 Terabytes of text per day** under enterprise API tiers.
*   **Worker Scaling:** The system runs tasks on a Celery/Redis queue, meaning you can add or remove worker containers on the fly to accelerate speeds for large datasets.

---

## Part 7: Supabase Storage & Embedding Dimensions

### Supabase Free Tier Limits
If running on Supabase's Free plan, the system is constrained by the following quotas:
*   **Database Space (500 MB):** Can store **100,000 to 150,000 vector embeddings** (~25,000 to 35,000 pages of text).
*   **File Storage (1 GB):** Can store ~1,000 raw PDFs (averaging 1 MB each).
*   **Upgrade Path:** Upgrading to the **Pro Plan ($25/mo)** unlocks 8 GB of database space and 100 GB of file storage.

### Why We Use 768-Dimension Embeddings
Although Gemini supports up to 3072 dimensions, we truncate vectors to **768 dimensions** using Google’s Matryoshka Representation Learning (MRL):
*   **$4\times$ Storage & Index Savings:** Drastically reduces database RAM requirements, letting you stay on the Free Tier longer.
*   **$4\times$ Faster Searches:** Calculating distances across 768 dimensions is significantly faster than 3072.
*   **Accuracy Trade-Off:** The first 768 dimensions contain over **98%** of the semantic accuracy, making the drop in accuracy negligible for standard business applications.

---

## Part 8: GPU vs. CPU (Cloud-Based Embeddings)

A common architecture question is why the backend server does not require a GPU (Graphics Processing Unit) to generate embeddings.

### How Embeddings Are Generated Here
Your local servers/workers run on standard, low-cost **CPUs**. They do not perform the intensive math of vector generation locally.
*   **API-Driven Architecture:** The backend chunks the documents using CPU power and then sends those text blocks via HTTPS calls to Google (Gemini) or OpenAI.
*   **Offloaded Computation:** Google and OpenAI run massive clusters of GPUs/TPUs in their own secure data centers. They calculate the embeddings and send the completed vectors back to your system.
*   **Server Load:** Your servers only handle basic text splitting, database writes, and REST API orchestration—tasks that are highly efficient on cheap CPUs.

### When is a GPU Actually Required?
You would only need to invest in local or dedicated GPU infrastructure if:
1.  **Fully On-Premise Deployment (No Internet):** If data privacy/compliance rules forbid sending text to external APIs (Google/OpenAI). You would need to host open-source models (like Llama 3 or BGE-embeddings) locally on enterprise GPUs (e.g., NVIDIA A100 or L40S).
2.  **Local Image / Heavy OCR Processing:** If you run heavy offline PDF parsing and OCR engines (like LayoutLM or Tesseract OCR) locally on your own VMs at a massive scale (millions of pages/day).
3.  **Custom Model Training:** If you decide to pre-train or fine-tune your own embedding or LLM models on proprietary data.

---

## Part 9: Proprietary vs. Open-Source AI Models

Understanding the difference between proprietary and open-source models is key to choosing the right infrastructure and budgeting strategy.

### Proprietary AI Models (Closed-Source)
Proprietary models are owned, hosted, and controlled entirely by a single company.
*   **Examples:** Google Gemini, OpenAI GPT-4, Anthropic Claude.
*   **The "Secret Recipe" Analogy:** You do not get access to the actual code, weights, or math behind the model. You can only use it by sending data to their servers over the internet and paying for what you use (per query/token).
*   **Pros:** Access to the most advanced AI intelligence, automatic updates, and zero hardware maintenance costs.
*   **Cons:** You do not own the model, you pay per transaction, and you must trust the provider with data handling.

### Open-Source AI Models
Open-source models have their code, neural network architecture, and weights released publicly for anyone to download and modify.
*   **Examples:** Meta Llama 3, Mistral, BGE-Embeddings.
*   **The "Open Recipe" Analogy:** Anyone can download the model files and run them on their own servers for free.
*   **Pros:** Complete data privacy (can run 100% offline), no per-query API fees, and absolute code ownership.
*   **Cons:** You must purchase/rent expensive GPU hardware to run them, and you are responsible for maintaining the system availability.

---

## Part 10: RAG Explained in Layman's Terms (The Open-Book Analogy)

To explain RAG (Retrieval-Augmented Generation) to a non-technical client, use the **"Open-Book Exam"** analogy.

### The Problem with standard AI (Closed-Book Exam)
Imagine a brilliant student sitting for an exam. 
*   **Without RAG:** The exam is **closed-book**. The student must answer questions relying only on what they memorized during school (their training phase). 
*   **The result:** If you ask the student about a new company policy written yesterday, or a private document they've never seen, they will either guess and make up a fake fact (**hallucinate**) or say they don't know.

### The Solution: RAG (Open-Book Exam)
RAG turns the process into an **open-book exam**. When a question is asked, the system retrieves the exact pages needed from your private library and hands them to the AI to read before writing the answer.

### The 3-Step RAG Pipeline
Here is how your data travels through the system:

```mermaid
graph TD
    subgraph Phase 1: Building the Library (Ingestion)
        A[Upload Documents] --> B[Slice into Paragraphs]
        B --> C[Index with Coordinates]
        C --> D[(Vector filing Cabinet)]
    end
    subgraph Phase 2: The Exam (Query & Answer)
        E[User Asks Question] --> F[Filer pulls matching paragraphs]
        D --> F
        F --> G[AI reads paragraphs]
        G --> H[AI writes answer with citations]
    end
```

#### Step 1: Ingestion (Building the Library)
*   **Paragraph slicing (Chunking):** We take your large documents (PDFs, Word files) and slice them into small paragraphs. The AI cannot read a 500-page book in a millisecond, so we make it bite-sized.
*   **Indexing (Embedding):** We translate each paragraph into a set of "semantic coordinates." This tells the database exactly what topic the paragraph is about.
*   **Filing Cabinet (Vector Database):** We store these categorized paragraphs in a special database (Supabase/PostgreSQL) for rapid lookup.

#### Step 2: Retrieval (Finding the Facts)
*   When a user asks a question, the system translates the question into the same coordinate style.
*   It immediately searches the database and pulls out the **3 to 5 most relevant paragraphs** that contain the answer.

#### Step 3: Generation (Writing the Answer)
*   We bundle the user's question and the retrieved paragraphs together.
*   We hand them to the AI (the LLM) and say: *"Read these 5 paragraphs. Answer the question using ONLY this information, and cite which paragraph you got it from."*
*   The AI outputs a precise, truthful answer with footnotes (e.g. `[1]`, `[2]`), referencing your sources.



