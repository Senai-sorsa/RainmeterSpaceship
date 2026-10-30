# Gemini Deep Research prompt: JARVIS GOD Mode

Paste everything below the line into Gemini Deep Research.

---

## Role and goal

You are a senior AI-systems architect and security researcher. Produce a long, deeply researched, source-cited report that will be used to design and build **"JARVIS GOD Mode"**: a fully local, private, maximum-capability AI assistant mode inside my existing desktop app. Be broad first (survey the whole landscape), then go deep on every area below. Prefer primary sources (official model cards on Hugging Face, GitHub repos and their issues/PRs, papers on arXiv, official vendor docs) over blog listicles. Many 2026 "best LLM" ranking sites are low quality and name models that do not exist, so **verify every model name against its Hugging Face repo and owner**, and say when you could not.

Today's date is 2026-10-30. Favour information from 2026; flag anything older that may be outdated.

## My hardware (measured)

- Laptop, Windows 11 Home (build 26300)
- CPU: AMD Ryzen AI 9 465, 10 cores / 20 threads (also has an NPU; tell me if anything useful can run on it)
- RAM: 32 GB
- GPU: NVIDIA GeForce RTX 5070 Laptop, 8 GB VRAM (plus integrated Radeon 880M, which my current setup hides from the LLM runtime)
- Storage: one 1 TB Samsung NVMe SSD (C:), ~420 GB free
- G: is the **Google Drive for Desktop virtual drive** (cloud-backed, not a second disk). Models, memory, index and logs must NOT live on or sync to it.

## My existing system (context)

- **CSpace**: a standalone Windows desktop app (replaced my older Rainmeter skins). Backend in C# on .NET 10 (`ShipCore.Core` logic library with xUnit tests, `ShipCore.App` host using WebView2); UI in TypeScript built with Vite, tested with Vitest. It has a Control Center with an **Advanced** section, a HUD, a tray icon, notices, a help center, a power-saver policy, a schema-validated config store, an action gate (deterministic code that authorizes OS actions), and a kill switch plus a global kill chord.
- **JARVIS**: my voice assistant, written in Python (`jarvislib` package). Wake word "Hey Jarvis", Vosk for wake/stop, Whisper for speech-to-text, **Ollama** as the LLM runtime (small models like Qwen3 4B / Llama 3.1 8B for everyday use), and a ChromaDB vector index for memory/knowledge. A core rule already in place: **model output never authorizes an OS action by itself; deterministic code does.**

## What GOD Mode is

- Opened only from Control Center → Advanced. It opens its own separate chat window with a distinct, cooler design (not the normal JARVIS chat).
- The user picks a model first. Candidate lineup (verify and improve):
  - Fast: Qwen3.6-35B-A3B (or Qwen3-30B-A3B)
  - Big: gpt-oss-120b
  - Huge: Qwen3-235B-A22B or DeepSeek-V4-Flash (284B total / 13B active)
  - Chat-only unfiltered: an abliterated model (e.g. huihui-ai Qwen3.6-35B-A3B abliterated), or a low-refusal finetune such as Hermes 4 / Dolphin 3.0
- Answers may take 30 minutes to hours; that is acceptable. The system must stay inside safe RAM/CPU/GPU/thermal margins on a laptop the whole time.
- It can READ every file on the computer (with exclusions) using the best possible search and retrieval.
- It comes with many PC tools: malware scanning, bug finding, system health, crash analysis, performance, network.

### Permission modes (planned)

1. **Read-only** (default): search, read, run read-only scans, write reports.
2. **CSpace settings**: may only change CSpace settings through the app's own validated config store (schema-checked keys and values, user approval, undo). It may never touch CSpace's code, binaries, scripts, JARVIS code, or GOD Mode's own config/permissions.
3. **Limited file edit**: writes only to a staging folder or user-chosen folders, as proposed changes the user approves. No deletes.
4. *(later)* **System actions**: one approval per action, picked from a fixed list (quarantine, kill process, disable startup item...).
- The abliterated model is chat only in every mode: no tools, no files, no network.

## Hard constraints (the design must respect all of these)

1. **Local only.** No cloud inference. The GOD Mode process gets no network access. The only exceptions are opt-in and narrow (e.g. a VirusTotal *hash* lookup; Defender's own definition updates).
2. **Safety is enforced by the OS and deterministic code, never by prompts.** For example: run the model and its tools as a separate process under a restricted Windows account / low-integrity token / AppContainer with read-only access; a small, separately tested **tool broker** is the only component that may run privileged commands, and it runs only fixed, allowlisted command templates with validated arguments and checked exit codes.
3. **It must never modify its own code or the app's code.** If it attempts a forbidden action, the attempt is blocked, the session stops immediately, and a small model explains the incident **from the deterministic audit log, not from the misbehaving model's own account**.
4. **Treat every file it reads as untrusted** (prompt injection). File content must never be able to grant permissions.
5. **Secrets excluded by default** from reading and indexing: browser password stores and cookies, `.ssh`, `.env`, token caches, credential managers, crypto wallets. Unlocked only one at a time by the user.
6. **The index must skip G: (Google Drive streaming)** or only index files that are already stored locally, so it never triggers a 1 TB cloud download.
7. Everything (models, memory, chat history, index, audit logs) is stored on C: and kept out of cloud sync.
8. **Laptop-safe long jobs**: checkpoint and resume after sleep or a crash, thermal and battery awareness, pause while gaming, instant kill via the existing kill chord.
9. Must fit the existing architecture. No framework rewrite; prefer proven, maintained open-source components; keep new dependencies justified.
10. Every claim in an answer must cite its source file (path + line/page) so it can be checked.

## Research questions (cover all; go deep on each)

### A. Models
1. The current (late 2026) best open-weight models for this hardware, in tiers: fits fully in 8 GB VRAM + 32 GB RAM; partly streamed from SSD; mostly streamed from SSD. For each: exact Hugging Face repo, total/active parameters, licence, context length, GGUF availability and size per quantization, quality on reasoning/coding/long-context benchmarks (independent where possible), known refusal and censorship behaviour (including Chinese-political-topic filtering in Qwen/DeepSeek, and safety strictness in gpt-oss).
2. Is my candidate lineup still the right one? What would you change, and why?
3. Expected real-world tokens/sec and prompt-processing speed on this exact class of hardware (RTX 5070 Laptop 8 GB, 32 GB DDR5, PCIe 4/5 NVMe). Find real user benchmarks, not just theory.
4. Model routing: using a fast model to plan/search/summarise and a big model only for final reasoning, and a second model as verifier. Evidence it works, and how much time it saves.

### B. Abliterated and low-refusal models (deep dive)
1. How abliteration works (refusal-direction removal, orthogonalization), the original research, and newer variants (multi-direction, projected, "norm-preserving", DPO/ORPO-based un-refusal, etc.).
2. Measured quality cost of abliteration versus the base model (benchmarks, perplexity, reasoning), and which methods/creators damage quality least.
3. The most reputable creators and quantizers (e.g. huihui-ai, mlabonne, failspy, bartowski, unsloth, mradermacher). Which repos are trustworthy, and how to verify them (owner, revision, hashes, file formats).
4. Abliterated versus low-refusal finetunes (Hermes 4, Dolphin 3.0, others): which are better for honest, uncensored, high-quality conversation on 32 GB RAM + 8 GB VRAM. Best current picks with repo links.
5. Risks specific to abliterated models (easier to prompt-inject, more confident hallucination, loss of calibration) and the right isolation for a chat-only deployment.
6. Download safety: GGUF/safetensors versus pickle formats, known malicious-model incidents on Hugging Face, and a verification checklist.

### C. Running models bigger than RAM (the "split the work" part)
1. The best current methods: llama.cpp with MoE expert offload (`--n-cpu-moe` / tensor overrides), mmap streaming from NVMe, ik_llama.cpp, KTransformers, AirLLM-style layer streaming, PowerInfer-style hot/cold neuron splits, speculative decoding with a small draft model, KV-cache quantization, flash attention. Which actually work on Windows + an NVIDIA laptop GPU in 2026, with what speed.
2. Ollama versus llama.cpp server versus others for this use case: which gives the control needed (expert offload, mmap, KV quantization, multiple models).
3. Whether DeepSeek V4 (and other new architectures) are supported in llama.cpp/Ollama yet.
4. How to enforce RAM/VRAM/CPU/thermal ceilings: Windows Job Objects, process priority, CPU affinity, memory limits, NVIDIA power limits, reading laptop temperatures. Safe defaults for a laptop running for hours.
5. Long-job orchestration: checkpointing an agent's work so a multi-hour task survives sleep or a crash; progress reporting.
6. SSD wear and heat from hours of heavy reads.

### D. Reading and searching every file ("pristine retrieval")
1. Best local indexing pipeline: fast file enumeration (NTFS MFT / USN change journal, Everything SDK), incremental updates, and file types (code, PDF, Office, email archives, images via OCR, audio via Whisper).
2. Best local embedding and reranker models in 2026 that fit this hardware; hybrid search (BM25 + vectors + rerank); code-aware search (symbols, tree-sitter); whether to keep ChromaDB or move to something else (LanceDB, Qdrant, SQLite-vec, Tantivy). Justify any change.
3. Agentic deep-research loops over local files: plan → search → read → check for contradictions → draft → self-critique → cite. Best open-source frameworks and patterns, plus map-reduce summarisation for very large corpora.
4. Citations and grounding: forcing path+line citations, verifying them automatically, and measuring hallucination.
5. Privacy: the exclusion list, detecting secrets inside files (gitleaks/trufflehog-style), and keeping the index itself protected at rest.

### E. Security architecture (be rigorous)
1. Best way on Windows 11 **Home** to run a process that can read most files but write nothing outside a sandbox folder and has no network: a restricted user account, low-integrity tokens, AppContainer, Windows Sandbox (is it available on Home?), WSL2, Job Objects, Windows Firewall per-program rules. Compare strength and practicality.
2. Tool-broker design: allowlisted command templates, argument validation, privilege separation, audit logging, and tests.
3. Prompt-injection defences for an agent that reads untrusted files: what actually works (capability separation, dual-LLM / CaMeL-style patterns, quarantined readers) versus what doesn't.
4. Tamper protection: stopping the agent from changing its own code, config, permissions or logs, even indirectly (scheduled tasks, startup entries, symlinks/junctions, alternate data streams, file associations).
5. Incident handling: detect, block, kill, preserve evidence, explain with a small model, notify the user.
6. Threat-model the whole system (STRIDE or similar) and list the top risks with mitigations.

### F. PC tools (read-only first, actions later)
For each, give the exact tool, the safe read-only invocation, whether it needs admin, its output format, and how an LLM should interpret it:
- Malware / security: Microsoft Defender (scan without automatic remediation, threat history), Sysinternals (Autoruns, Sigcheck, Process Explorer/Process Monitor exports), YARA rules, open ports and listening processes, firewall rules, scheduled tasks, services, browser extensions, gitleaks/trufflehog on my repos, VirusTotal hash-only lookups.
- Code bugs: Semgrep, ruff, mypy/pyright, .NET analyzers, the TypeScript compiler, ESLint, dependency vulnerability scanners (pip-audit, `dotnet list package --vulnerable`, npm audit). How to run tests in a disposable copy with no network.
- System health: `sfc /verifyonly`, `DISM /CheckHealth` / `/ScanHealth`, `chkdsk /scan`, SMART/NVMe health, driver inventory, Windows Update history.
- Crashes: Event Log queries, Reliability Monitor, minidump analysis (WinDbg / `cdb !analyze`).
- Performance and battery: startup impact, top resource users, `powercfg /batteryreport` and `/energy`, disk-space analysis, duplicate finders.
- Network: adapter/Wi-Fi info, DNS/latency checks, speed test.
- **Anything else genuinely useful** I haven't thought of.

### G. Features and add-ons that would make it a true "GOD Mode"
Research and propose many, ranked by value ÷ effort, each with how it fits the constraints. Ideas to evaluate (and go beyond):
- A job queue: ask, walk away, get a CSpace notice when it's done
- A live "thinking" view: plan tree, files being read, tokens/sec, ETA, RAM/VRAM/temperature
- A second-model verifier and a confidence score per claim
- Persistent long-term memory of past investigations (with user control to view/delete)
- Scheduled health reports (weekly security + system check)
- Vision: screenshots, images, diagrams, scanned PDFs (local VLMs)
- Voice in/out reusing JARVIS (Whisper + TTS) for GOD Mode summaries
- A code-understanding mode: a knowledge graph of my repos, "explain this system", bug hunting
- A sandboxed calculator / Python for data analysis (no file writes outside scratch, no network)
- Personal timeline: "what did I work on in March?" from file activity
- Export answers as reports (Markdown/PDF)
- Model management UI: download with hash verification, benchmark on this machine, disk usage
- An audit-log viewer and a "replay" of what the agent did
- Anything from current open-source projects (e.g. Open WebUI, AnythingLLM, LM Studio, Jan, Khoj, Perplexica, OpenHands, smolagents, LangGraph, MCP servers) worth borrowing as an idea or component

### H. UI and UX
Design ideas for a distinct, "cooler" GOD Mode chat window inside a WebView2 + TypeScript app: visual language, how to show multi-hour progress, mode/permission indicators that can't be confused, incident screens, and accessibility. Include examples from real products.

## Output format

1. **Executive summary** (one page): the recommended lineup, architecture, and top 10 features.
2. **Detailed sections A–H**, each ending with a clear recommendation and its trade-offs.
3. **Comparison tables**: models (size/speed/quality/licence/refusals), sandboxing options, retrieval stacks, tools.
4. **A proposed architecture**: components, processes, privilege boundaries, data flow; described in text plus a diagram in Mermaid.
5. **A phased build plan** (small, independently testable slices), with acceptance tests for each slice and safety tests (e.g. "agent tries to write to its own folder → blocked, session killed, incident explained").
6. **Risks and open questions**, including what you could NOT verify.
7. **Full source list** with links. Mark each claim as *verified from a primary source*, *from a secondary source*, or *my estimate*.

Be thorough and long. Do not stop at surface-level summaries; when sources disagree, say so and explain which you trust and why.
