# Multi-Agent RAG + MCP Platform — Project Plan

Goal: a small, fully working, cloud-deployed system that proves — end to end, defensibly — GenAI, multi-agent orchestration, RAG, MCP, cloud (EC2/S3), and Docker. Every line below maps to something you can explain in an interview. Nothing here is scoped for "impressive on paper, unexplainable in person."

---

## 0. Before you write a single line of code

**Decide the demo domain first.** RAG needs a document set. Pick something real and small — e.g. "chat with N of my own technical docs / a public dataset of research papers / your own resume + project READMEs." Don't overthink this; it's a placeholder for the pipeline, not the point of the project.

**Accounts to create (all free tier):**
| Need | Provider | Why |
|---|---|---|
| LLM API | Anthropic or OpenAI API key | Powers the agents. Budget a few dollars — free tiers don't cover LLM calls, only infra. |
| Vector DB | Qdrant Cloud (free 1GB cluster) | You already use Qdrant at work — no new tool to learn, and you can talk about it fluently. |
| Relational DB | Neon (serverless Postgres, free tier) | Simplest free managed Postgres, no setup overhead. (Alternative: AWS RDS free tier — see note below.) |
| Object storage | AWS S3 (free tier, 5GB/12mo) | Stores ingested docs + generated reports. |
| Compute | AWS EC2 (t2.micro/t3.micro, free tier) | Hosts the Dockerized app. |
| Code hosting | GitHub | Repo + README is part of the deliverable — this is what gets linked on your resume. |

**Note on DB choice:** Neon vs RDS is a real trade-off worth knowing for the interview. Neon = zero ops, spin up in 2 minutes, good enough to demonstrate the pattern. RDS = "actually inside AWS, same VPC as EC2, more realistic prod setup" but more setup friction (VPC, security groups). Pick Neon to move fast; if asked in an interview "why not RDS," your answer is literally the trade-off above — that's a good answer to have ready, not a weakness.

**Local tools to install:** Python 3.11+, Docker + Docker Compose, `uv` or `pip`, AWS CLI (configured with your credentials), Git.

**Embedding model:** use a local model (`sentence-transformers/all-MiniLM-L6-v2`) — free, no API cost, and it's a legitimate choice you can defend ("didn't want RAG quality gated on API spend for a demo project"). Don't route embeddings through a paid API just because the original plan did.

---

## 1. Agents (3 agents, all core — no stretch goals on a flagship project)

### Orchestrator Agent
**Job:** receives the user's question, decides which MCP tool(s) to call, sequences calls if more than one is needed, assembles the final answer.
**Owns no tools itself** — it's the MCP *client*. This is the piece that actually demonstrates "multi-agent orchestration," so the routing logic needs to be real decision-making (e.g. "does this need document search, structured data, or both?"), not a hardcoded if-statement pretending to be intelligence.

### Retrieval Agent (RAG) — real sub-agent, not a tool wrapper
**Job:** owns the document knowledge base, with its own LLM-driven reasoning loop (LangGraph subgraph): rewrite the query → retrieve from Qdrant → grade relevance → if not good enough, rewrite again with feedback and retry; if good enough, return grounded context to the Orchestrator. This loop is what makes the "2+ agent" claim on your resume actually true — without it, this is just a function, not an agent.
**Tools it exposes via MCP:** `search_documents`, `summarize_document`

### Action/Data Agent
**Job:** owns structured data queries and report generation. No email/Slack/external API calls — self-contained. Deliberately a plain deterministic tool, not a reasoning agent — that contrast (one real sub-agent, one tool-executor) is an accurate and defensible architecture, not a weakness to hide.
**Tools it exposes via MCP:** `query_structured_data`, `generate_report`

---

## 2. MCP Server — tools

Build this with the real MCP SDK, not a hand-rolled `tools.json` mimicking it. A genuine MCP server is the strongest, most current signal in this whole project — don't fake it.

| Tool | Owner agent | Input | Backing store | What it proves |
|---|---|---|---|---|
| `search_documents(query, top_k)` | Retrieval | query text, k — called possibly more than once per turn, inside the retrieval agent's own retry loop | Qdrant | vector search, RAG retrieval |
| `summarize_document(doc_id \| text)` | Retrieval | doc reference | Qdrant + Postgres metadata | context handling, LLM prompting |
| `query_structured_data(question)` | Action | natural-language question mapped to a **fixed set of parameterized queries** (not free-form SQL generation — avoid injection risk and unbounded scope) | Postgres (Neon) | safe structured data access |
| `generate_report(topic)` | Action | topic/query | Reads from both stores, writes file to S3, logs row to Postgres | tool orchestration + cloud storage |

Keep it at 3-4 tools. More tools ≠ more impressive; it's more surface area you have to explain in equal depth.

---

## 3. Data layer

- **Qdrant Cloud** — one collection, e.g. `documents`. Stores chunk embeddings + metadata (source, chunk index).
- **Postgres (Neon)** — lightweight schema:
  - `documents` (id, filename, upload_date, processed)
  - `query_logs` (id, agent, tool, input, output_summary, timestamp) — this table alone gives you a "audit/observability" talking point for free
  - `reports` (id, topic, s3_path, created_at)
- **S3** — one bucket, two prefixes: `uploads/` (source docs) and `reports/` (generated output).

That's it. No Redis, no MongoDB. If someone asks "why not add caching," your answer is "wasn't the bottleneck for this scale — I optimized for a clean story over a checklist of infra," which is a genuinely good answer.

---

## 4. Project structure

Flattened, no `src/` wrapper — a recruiter or interviewer opening the repo should understand the layout from the file tree alone, no digging.

```
ai-agent-mcp-platform/
├── README.md                  # architecture summary + demo link/gif — this sells the project
├── docker-compose.yml         # local dev: app + local qdrant (prod uses Qdrant Cloud)
├── Dockerfile
├── .env.example
├── requirements.txt
├── config.py                  # env-driven config (local vs cloud endpoints)
├── app.py                     # Streamlit chat UI + file uploader
├── .github/
│   └── workflows/
│       └── ci.yml              # lint + tests on every push
├── agents/
│   ├── orchestrator.py        # LangGraph StateGraph: call_model / call_tool nodes
│   ├── mcp_client.py          # langchain-mcp-adapters wiring to the MCP server
│   ├── retrieval_agent.py     # subgraph: rewrite → retrieve → grade → retry
│   └── action_agent.py
├── mcp_server/
│   ├── server.py
│   └── tools/
│       ├── search_documents.py
│       ├── summarize_document.py
│       ├── query_structured_data.py
│       └── generate_report.py
├── rag/
│   ├── ingest.py               # chunk + embed + upsert to Qdrant
│   ├── embeddings.py
│   └── retriever.py
├── db/
│   ├── postgres.py
│   └── qdrant_client.py
├── storage/
│   └── s3_client.py
├── data/
│   └── sample_docs/            # your chosen demo dataset
├── scripts/
│   └── seed_db.py              # one-command setup for reviewers/interviewers
├── tests/
│   └── test_tools.py           # real tests — this project runs them on every push, not padding
└── deploy/
    └── ec2_setup.md            # exact steps you ran — doubles as documentation
```

Note: without `src/`, keep the repo root clean — nothing but these folders and top-level config files. The moment you start dropping loose scratch scripts or notebooks at the root, you lose the exact readability benefit you flattened it for.

---

## 4.5 Agent orchestration library

**Decision: LangGraph, with MCP tools wired in via `langchain-mcp-adapters`.**

- The MCP server is still a real MCP server, built with the official `mcp` Python SDK — that doesn't change. `langchain-mcp-adapters` is the *client* side: it connects to your running MCP server and exposes its tools as LangChain-compatible `Tool` objects, which you then bind to a LangGraph agent.
- Orchestrator = a LangGraph `StateGraph` with a `call_model` node (LLM decides next step) and a `call_tool` node (executes whichever MCP tool was requested), with a conditional edge that loops between them until the model returns a final answer with no more tool calls. This is functionally the same agentic loop as before — LangGraph just gives you an explicit, inspectable graph instead of a hand-rolled `while` loop.
- Know the story you're telling: this setup demonstrates ecosystem/production-tooling fluency (LangGraph + MCP is what a lot of teams actually ship with right now) rather than raw-protocol understanding. Both are valid; just be ready to explain the graph's nodes and edges in detail if asked, the same way you'd have needed to explain the raw loop.
- RAG plumbing (chunking, retriever): use `langchain-text-splitters` for chunking — no reason to hand-roll this now that LangChain is already a dependency.

---

## 4.7 Chat UI + document upload

**Streamlit app** — one page, two pieces:
- A file uploader (`st.file_uploader`, PDF/txt) that, on upload, runs the ingestion pipeline directly (parse → chunk → embed → upsert to Qdrant, save the raw file to S3 `uploads/`, log a row in Postgres). This is a direct UI action, not something routed through the agent — the user is managing the knowledge base, not asking the agent a question.
- A chat box (`st.chat_message` / `st.chat_input`) that sends the user's question into the LangGraph orchestrator and streams back the answer.

Keep upload and chat as two clearly separate actions in the UI — don't make the agent "decide" whether an uploaded file should be ingested. That ambiguity adds failure modes for no benefit.

This becomes your demo GIF: upload a PDF, ask a question about it, get a grounded answer with the structured-data tool kicking in on a follow-up. That's the 30-second video that goes on your resume/LinkedIn.

---

## 4.9 Testing & CI

Basic, not elaborate — a flagship project needs to look cared-for, not over-engineered.

- **Tests:** a handful of real tests per tool (`search_documents` returns expected shape, `query_structured_data` rejects an out-of-scope question, `generate_report` writes to the right S3 prefix), plus one test that exercises the Retrieval agent's retry loop with a deliberately bad first query. Don't chase coverage percentage — chase "does this catch a real regression."
- **CI:** one GitHub Actions workflow (`.github/workflows/ci.yml`) that runs `ruff` (lint) and `pytest` on every push. That's it — no deploy step, no environments, no secrets management. This is the one piece of "pipeline" infrastructure worth having: it's near-zero cost to set up, and a green checkmark on your repo is a real, quick signal of engineering discipline to anyone browsing it.
- This is deliberately not the CI/CD pipeline the original AI-generated plan wanted (build → push to registry → deploy to k8s). That's still out of scope — see Section 5.

---

## 5. Cloud deployment (the whole cloud story — no more, no less)

1. Docker Compose locally for dev — proves containerization, fast iteration.
2. Single EC2 instance (t2.micro/t3.micro, free tier) — `docker compose up` in production mode, pointed at Qdrant Cloud + Neon + S3 via env vars.
3. S3 for file storage, IAM role/user scoped to just that bucket (mention least-privilege — free interview point).
4. Security group open only on the port you actually serve (e.g. 8000), SSH restricted to your IP.

Since this stays live as your flagship, not spun up once and torn down: track your AWS free-tier clock. EC2 and S3 free tiers run 12 months from account creation, not per-resource — set a calendar reminder before it lapses so you're not surprised by a bill. Neon and Qdrant Cloud's free tiers don't expire on a timer the same way, so they're not a concern here.

Skip Kubernetes, Terraform, and a full CD pipeline — this doesn't change just because the project is more important. Bolting them onto a solo project you deploy once is cargo-culting regardless of how much the project matters to you: you still won't have exercised the parts that matter (rollout, scaling, failure recovery), and now there's more pressure riding on infra you can't fully defend under questioning. If IaC/K8s matters for your resume, that's a second, separate project done properly — not a checkbox added here under pressure to make this one look bigger.

---

## 6. What's explicitly out of scope (and why)

- Email/Slack/webhook integrations — third-party auth complexity for zero demonstration value on your target skills.
- Free-form SQL generation from natural language — real injection risk, hard to demo safely, not worth it for a portfolio piece.
- Multi-database sprawl (Mongo + Redis + Postgres + Vector) — one relational + one vector store covers every claim you're making.
- Kubernetes/Terraform/CI-CD — see above.

---

## 7. Definition of done

- [ ] Repo is public, README has an embedded architecture diagram, a demo GIF/video, and a short "skills demonstrated" section mapping each part of the system to a claim on your resume
- [ ] CI is green — lint + tests pass on the latest commit
- [ ] `docker compose up` works from a clean clone with `.env.example` filled in
- [ ] Live EC2 URL works, with an AWS free-tier expiry date noted somewhere for yourself
- [ ] Retrieval agent's retry loop is demonstrable — you can show a query that fails relevance grading once and self-corrects
- [ ] You can explain, unscripted, what happens end-to-end for one real query — including why each infra choice was made and what you deliberately left out
- [ ] Resume bullet is one sentence, specific, and true

Next step once you're happy with this: day-by-day build order, or the MCP tool schemas/repo scaffolding to start coding.