# OpenJarvis file index (generated 2026-11-05)

Every file under the local OpenJarvis checkout (excluding .git, node_modules, target): 2202 files. Columns: path | bytes | lines | first docstring / title / export.

```
.gitignore | 2594 | 0 | 
.pre-commit-config.yaml | 159 | 8 | 
CHANGELOG.md | 25769 | 457 | Changelog
CODE_OF_CONDUCT.md | 5622 | 86 | Contributor Covenant Code of Conduct
CONTRIBUTING.md | 7234 | 202 | Contributing to OpenJarvis
LICENSE | 10963 | 0 | 
Makefile | 505 | 0 | 
README.md | 10217 | 185 | Install skills from public sources
REVIEW.md | 2632 | 44 | OpenJarvis PR Review Instructions
mkdocs.yml | 6698 | 208 | 
pyproject.toml | 12499 | 320 | 
render.yaml | 2304 | 48 | 
uv.lock | 1692938 | 10480 | 
.github/CODEOWNERS | 819 | 0 | 
.github/dependabot.yml | 1582 | 71 | 
.github/pull_request_template.md | 511 | 17 | 
.github/ISSUE_TEMPLATE/bug_report.yml | 2221 | 96 | 
.github/ISSUE_TEMPLATE/config.yml | 186 | 6 | 
.github/ISSUE_TEMPLATE/feature_request.yml | 1292 | 48 | 
.github/ISSUE_TEMPLATE/new_eval.yml | 1587 | 64 | 
.github/ISSUE_TEMPLATE/pearl_model_validation.yml | 3120 | 99 | 
.github/clone-stats/badge.json | 123 | 8 | 
.github/clone-stats/clone-data.json | 5585 | 229 | 
.github/workflows/autotag.yml | 3641 | 93 | 
.github/workflows/bash-tests.yml | 635 | 30 | 
.github/workflows/ci.yml | 6499 | 193 | 
.github/workflows/claude-issues.yml | 3956 | 87 | 
.github/workflows/claude-review.yml | 2296 | 59 | 
.github/workflows/desktop.yml | 31623 | 689 | 
.github/workflows/docs.yml | 2417 | 84 | 
.github/workflows/frontend.yml | 1255 | 49 | 
.github/workflows/installer-integration.yml | 3446 | 119 | 
.github/workflows/pypi-publish.yml | 5640 | 156 | 
.github/workflows/security-sast.yml | 3657 | 101 | 
.github/workflows/take-assign.yml | 965 | 30 | 
.github/workflows/track-clones.yml | 2712 | 87 | 
assets/OpenJarvis_Circular_Logo.png | 393298 | 0 | 
assets/OpenJarvis_Horizontal_Logo.png | 799977 | 0 | 
assets/openjarvis-slack-icon.jpg | 102125 | 0 | 
assets/openjarvis_demo_reel.webp | 4731810 | 0 | 
configs/openjarvis/config.toml | 6072 | 125 | 
configs/openjarvis/examples/chat-simple.toml | 675 | 25 | 
configs/openjarvis/examples/code-assistant.toml | 691 | 22 | 
configs/openjarvis/examples/deep-research.toml | 826 | 28 | 
configs/openjarvis/examples/full-system-access.toml | 1153 | 40 | 
configs/openjarvis/examples/morning-digest-linux.toml | 1327 | 52 | 
configs/openjarvis/examples/morning-digest-mac.toml | 2096 | 57 | 
configs/openjarvis/examples/morning-digest-minimal.toml | 744 | 32 | 
configs/openjarvis/examples/scheduled-monitor.toml | 1085 | 36 | 
configs/openjarvis/examples/spec-search-quickstart.toml | 3130 | 77 | 
configs/openjarvis/prompts/personas/jarvis.md | 950 | 17 | 
configs/openjarvis/prompts/personas/neutral.md | 353 | 12 | 
deploy/docker/.env.example | 338 | 0 | 
deploy/docker/Dockerfile | 3895 | 0 | 
deploy/docker/Dockerfile.gpu | 3415 | 0 | 
deploy/docker/Dockerfile.gpu.rocm | 3640 | 0 | 
deploy/docker/Dockerfile.sandbox | 3244 | 0 | 
deploy/docker/docker-compose.gpu.nvidia.yml | 992 | 34 | 
deploy/docker/docker-compose.gpu.rocm.yml | 363 | 16 | 
deploy/docker/docker-compose.yml | 1253 | 38 | 
deploy/launchd/com.openjarvis.plist | 1294 | 0 | 
deploy/posthog/posthog-hetzner-prep.sh | 4989 | 143 | 
deploy/systemd/openjarvis.service | 1398 | 0 | 
deploy/windows/README.md | 4346 | 127 | OpenJarvis on native Windows
deploy/windows/install.ps1 | 27563 | 627 | 
deploy/windows/jarvis-service.ps1 | 8136 | 209 | 
desktop/src-tauri/binaries/ollama-aarch64-apple-darwin | 77038640 | 0 | 
desktop/src-tauri/src/overlay.html | 18050 | 451 | 
docs/desktop-auto-update.md | 4901 | 118 | Desktop auto-update
docs/downloads.md | 7084 | 256 | Downloads
docs/gen_install_script.py | 1111 | 31 | Publish the canonical install scripts into the docs site.
docs/gen_ref_pages.py | 987 | 32 | Generate the code reference pages.
docs/index.md | 9564 | 247 | Personal AI, On Personal Devices
docs/leaderboard.md | 2159 | 60 | Savings Leaderboard
docs/telemetry.md | 8972 | 186 | Telemetry
docs/architecture/agents.md | 23463 | 568 | Agentic Logic Primitive
docs/architecture/channels.md | 7870 | 193 | Channels Architecture
docs/architecture/design-principles.md | 10743 | 301 | Design Principles
docs/architecture/engine.md | 18617 | 433 | Inference Engine Primitive
docs/architecture/intelligence.md | 12231 | 259 | Intelligence Primitive
docs/architecture/learning.md | 24342 | 616 | Learning & Traces
docs/architecture/memory.md | 12517 | 356 | Memory Primitive
docs/architecture/overview.md | 15704 | 243 | Architecture Overview
docs/architecture/query-flow.md | 11517 | 332 | Query Flow
docs/architecture/security.md | 8559 | 212 | Security Architecture
docs/architecture/skills.md | 9621 | 223 | Skills Architecture
docs/assets/OpenJarvis_Architecture.png | 240689 | 0 | 
docs/assets/analytics-opt-in/desktop.jpg | 31150 | 0 | 
docs/assets/showcase/README.md | 2484 | 46 | Showcase screenshots
docs/assets/showcase/coding-assistant.png | 6383 | 0 | 
docs/assets/showcase/cost-savings.png | 6383 | 0 | 
docs/assets/showcase/discord-companion.png | 6383 | 0 | 
docs/assets/showcase/morning-brief.png | 6383 | 0 | 
docs/assets/showcase/persistent-memory.png | 6383 | 0 | 
docs/deployment/api-server.md | 17494 | 552 | API Server
docs/deployment/docker.md | 9812 | 351 | Docker Deployment
docs/deployment/index.md | 828 | 35 | Deployment
docs/deployment/launchd.md | 9180 | 267 | launchd Service (macOS)
docs/deployment/render.md | 2350 | 46 | Deploy on Render
docs/deployment/systemd.md | 9620 | 258 | systemd Service (Linux)
docs/design/2026-05-05-apple-silicon-pearl-mining-design.md | 53169 | 712 | Spec B — Apple Silicon enablement for Pearl mining
docs/design/2026-05-05-apple-silicon-pearl-mining-plan-v1.md | 66979 | 1812 | Apple Silicon Pearl mining v1 — implementation plan
docs/design/2026-05-05-pearl-coordination-discussion-draft.md | 7111 | 92 | Pearl coordination thread — draft
docs/design/2026-05-05-vllm-pearl-mining-integration-design.md | 34413 | 561 | Spec A — vLLM-Pearl mining integration (v1)
docs/design/2026-05-05-vllm-pearl-mining-integration-plan.md | 124581 | 3559 | vLLM-Pearl mining integration — implementation plan
docs/development/contributing.md | 14481 | 416 | Contributing Guide
docs/development/mining-nvidia-validation.md | 7972 | 290 | NVIDIA Pearl Mining Validation Runbook
docs/development/mining.md | 2927 | 85 | Adding a Mining Provider
docs/development/pearl-model-enablement.md | 5927 | 149 | Pearl Model Enablement
docs/development/release-checklist.md | 2272 | 53 | Release Checklist
docs/development/roadmap.md | 12261 | 142 | Roadmap
docs/getting-started/configuration.md | 43096 | 1223 | Configuration
docs/getting-started/install.md | 6362 | 151 | Installation
docs/getting-started/installation.md | 14474 | 443 | Installation
docs/getting-started/linux.md | 659 | 31 | Linux Install
docs/getting-started/macos.md | 935 | 27 | macOS Install
docs/getting-started/quickstart.md | 19561 | 617 | Quick Start
docs/getting-started/snippets.md | 3323 | 136 | Code Snippets
docs/getting-started/windows-native.md | 5311 | 139 | Native Windows (advanced)
docs/getting-started/wsl2.md | 1170 | 35 | WSL2 Install
docs/includes/abbreviations.md | 446 | 14 | 
docs/javascripts/docsearch-init.js | 916 | 37 | 
docs/javascripts/leaderboard-config.js | 707 | 13 | 
docs/javascripts/leaderboard.js | 9157 | 222 | 
docs/learning/ace.md | 5134 | 136 | ACE optimizer (Agentic Context Engineering)
docs/overrides/main.html | 1238 | 34 | 
docs/showcase/CONTRIBUTING.md | 4842 | 105 | Contributing a Showcase Entry
docs/showcase/coding-assistant.md | 2446 | 37 | 🛠️ Offline Code Reviewer — code review on an airplane
docs/showcase/cost-savings.md | 2413 | 39 | 💸 Track Your Savings — the leaderboard that makes local-first feel real
docs/showcase/discord-companion.md | 2472 | 35 | 💬 Discord Companion — a personal assistant that lives in my Discord
docs/showcase/index.md | 3309 | 73 | Showcase
docs/showcase/morning-brief.md | 2685 | 40 | ☕ Morning Brief — Jarvis reads everything overnight so I don't have to
docs/showcase/persistent-memory.md | 2563 | 35 | 🧠 Memory That Doesn't Reset — Jarvis actually knows me
docs/stylesheets/extra.css | 18269 | 587 | 
docs/testing/agent-qa-runbook.md | 5915 | 76 | Agent QA Runbook
docs/tutorials/code-companion.md | 9864 | 219 | Code Companion
docs/tutorials/deep-research.md | 7650 | 198 | Deep Research Assistant
docs/tutorials/index.md | 2917 | 71 | Tutorials
docs/tutorials/messaging-hub.md | 8289 | 216 | Messaging Hub
docs/tutorials/scheduled-ops.md | 8438 | 216 | Scheduled Personal Ops
docs/tutorials/skills-workflow.md | 8863 | 243 | Skills Workflow Tutorial
docs/user-guide/agents.md | 44922 | 811 | Agents
docs/user-guide/benchmarks.md | 11884 | 338 | Benchmarks
docs/user-guide/channels-and-connectors.md | 22218 | 561 | Channels & Connectors
docs/user-guide/channels.md | 23191 | 647 | Channels
docs/user-guide/chat-simple.md | 4442 | 155 | Simple Chat
docs/user-guide/cli-interactive-picker.md | 2567 | 73 | Interactive CLI model and runtime picker (TUI)
docs/user-guide/cli.md | 19683 | 522 | CLI Reference
docs/user-guide/code-assistant.md | 5436 | 138 | Code Assistant
docs/user-guide/data-boundary-scan.md | 6989 | 188 | Data-boundary scan
docs/user-guide/deep-research.md | 6379 | 166 | Deep Research
docs/user-guide/evaluations.md | 39484 | 811 | Evaluations
docs/user-guide/llm-guided-spec-search.md | 9206 | 215 | LLM-Guided Spec Search
docs/user-guide/mcp-external-servers.md | 8142 | 192 | External MCP Server Integration
docs/user-guide/memory.md | 13653 | 369 | Memory
docs/user-guide/mining-apple-silicon.md | 6366 | 163 | Mining Pearl on Apple Silicon (and other CPU hosts)
docs/user-guide/mining.md | 4927 | 142 | Pearl Mining
docs/user-guide/morning-digest.md | 7665 | 219 | Morning Digest
docs/user-guide/pearl.md | 1703 | 59 | Pearl CLI Integration
docs/user-guide/python-sdk.md | 11029 | 386 | Python SDK
docs/user-guide/scheduled-monitor.md | 7045 | 202 | Scheduled Monitor
docs/user-guide/scheduler.md | 8927 | 241 | Task Scheduler
docs/user-guide/security.md | 20498 | 539 | Security
docs/user-guide/skills.md | 14918 | 426 | Skills
docs/user-guide/system-access.md | 7670 | 213 | System Access
docs/user-guide/telemetry.md | 19851 | 424 | Telemetry & Traces
docs/user-guide/tools.md | 27480 | 669 | Tools
examples/browser_assistant/README.md | 1219 | 32 | Browser Assistant
examples/browser_assistant/browser_assistant.py | 3349 | 114 | Browser Assistant — web browsing agent with orchestrator loop.
examples/code_companion/README.md | 4311 | 149 | Code Companion
examples/code_companion/debugger.py | 3696 | 124 | Debug Assistant — investigate errors and propose fixes with a ReAct agent.
examples/code_companion/reviewer.py | 3392 | 113 | Code Review Assistant — review diffs between branches with a ReAct agent.
examples/code_companion/test_gen.py | 4271 | 138 | Test Generator — generate comprehensive tests for a Python module with a ReAct agent.
examples/cross_device_travel/Cargo.lock | 2794 | 108 | 
examples/cross_device_travel/Cargo.toml | 313 | 14 | 
examples/cross_device_travel/README.md | 12200 | 214 | Cross-device travel planning handoff
examples/cross_device_travel/src/laptop.rs | 9687 | 238 | Laptop research and heavy-model replacement points. Everything here is a fixture;
examples/cross_device_travel/src/lib.rs | 203 | 8 | Illustrative cross-device execution; all demo data and device actions are synthetic.
examples/cross_device_travel/src/main.rs | 1316 | 42 | 
examples/cross_device_travel/src/protocol.rs | 4456 | 161 | Demo protocol v1. These JSON types are intentionally independent of A2A.
examples/cross_device_travel/src/runtime.rs | 9259 | 233 | Sequential laptop scheduler. Discovery, transport and placement policy are
examples/cross_device_travel/src/travel.rs | 19178 | 489 | Fixed travel example: replace decomposition, discovery, and handlers independently.
examples/cross_device_travel/tests/demo_trace.rs | 687 | 17 | Keep the handoff trace executable: reviewers can trust it matches the CLI.
examples/cross_device_travel/tests/review_regressions.rs | 3740 | 98 | 
examples/cross_device_travel/tests/runtime.rs | 11878 | 343 | 
examples/cross_device_travel/traces/happy.json | 28507 | 911 | 
examples/daily_digest/README.md | 1152 | 31 | Daily Digest
examples/daily_digest/daily_digest.py | 3567 | 121 | Daily Digest — morning briefing operator that searches and summarizes news.
examples/deep_research/README.md | 4244 | 112 | Deep Research Assistant
examples/deep_research/research.py | 3443 | 119 | Deep Research Assistant — multi-source research with memory-augmented orchestrator.
examples/deep_research/research.toml | 713 | 24 | 
examples/doc_qa/README.md | 1453 | 37 | Document QA
examples/doc_qa/doc_qa.py | 3386 | 121 | Document QA — index documents and answer questions with citations.
examples/messaging_hub/README.md | 4379 | 145 | Messaging Hub
examples/messaging_hub/messaging.toml | 609 | 26 | 
examples/messaging_hub/smart_inbox.py | 8855 | 268 | Smart Inbox — message triage and auto-reply with an orchestrator agent.
examples/multi_model_router/README.md | 2052 | 53 | Multi-Model Router
examples/multi_model_router/multi_model_router.py | 4640 | 152 | Multi-Model Router — route queries to the cheapest capable model.
examples/openjarvis/spec_search_quickstart.py | 11767 | 307 | LLM-Guided Spec Search — runnable quickstart.
examples/scheduled_ops/README.md | 4670 | 130 | Scheduled Personal Ops
examples/scheduled_ops/code_review.py | 3189 | 106 | Weekly code review — summarizes recent commits in a repository.
examples/scheduled_ops/daily_digest.py | 2774 | 94 | Daily news digest — searches for and summarizes top stories on chosen topics.
examples/scheduled_ops/gym_scheduler.py | 4185 | 138 | Gym schedule checker — looks up gym hours and class availability.
examples/scheduled_ops/schedules.toml | 440 | 20 | 
examples/security_scanner/README.md | 1330 | 34 | Security Scanner
examples/security_scanner/security_scanner.py | 3877 | 118 | Security Scanner — scan a local project for secrets and vulnerabilities.
examples/twitter_bot/slack_preview.py | 9819 | 212 | Overnight Slack preview — generates proactive tweets on a loop.
examples/twitter_bot/test_grounding.py | 4372 | 127 | Verify that dense retrieval grounds the bot's reply in real doc facts.
examples/twitter_bot/test_real_world.py | 9320 | 277 | Stress-test the twitter bot on diverse mentions with the dense-retrieval pipeline.
examples/twitter_bot/twitter_bot.py | 40158 | 1061 | OpenJarvis Twitter Bot — @OpenJarvisAI reactive mention handler.
frontend/.npmrc | 47 | 0 | 
frontend/components.json | 540 | 26 | 
frontend/index.html | 526 | 17 | 
frontend/package-lock.json | 383623 | 10333 | 
frontend/package.json | 1908 | 70 | 
frontend/tsconfig.json | 670 | 26 | 
frontend/tsconfig.tsbuildinfo | 1913 | 0 | 
frontend/vite.config.ts | 2848 | 83 | 
frontend/public/apple-touch-icon.png | 65468 | 0 | 
frontend/public/favicon.ico | 11343 | 0 | 
frontend/public/pwa-192x192.png | 73299 | 0 | 
frontend/public/pwa-512x512.png | 422450 | 0 | 
frontend/src/App.tsx | 8085 | 204 | exports App
frontend/src/index.css | 21801 | 756 | 
frontend/src/main.tsx | 1606 | 47 | 
frontend/src/vite-env.d.ts | 252 | 12 | 
frontend/src/components/ApprovalBell.tsx | 10973 | 265 | exports ApprovalBell
frontend/src/components/CommandPalette.tsx | 26478 | 587 | exports CommandPalette
frontend/src/components/ErrorBoundary.tsx | 2026 | 61 | exports ErrorBoundary
frontend/src/components/InferenceSourceSetup.test.tsx | 4793 | 134 | 
frontend/src/components/InferenceSourceSetup.tsx | 13419 | 386 | exports inferenceSetupReducer
frontend/src/components/Layout.tsx | 2643 | 75 | exports Layout
frontend/src/components/OptInModal.test.tsx | 1863 | 52 | 
frontend/src/components/OptInModal.tsx | 11063 | 267 | exports OptInModal
frontend/src/components/SetupScreen.tsx | 9257 | 269 | exports SetupScreen
frontend/src/components/SystemPulse.tsx | 2055 | 61 | exports SystemPulse
frontend/src/components/Chat/AudioPlayer.tsx | 3617 | 120 | exports AudioPlayer
frontend/src/components/Chat/ChatArea.tsx | 12099 | 262 | exports ChatArea
frontend/src/components/Chat/InputArea.tsx | 24703 | 658 | exports InputArea
frontend/src/components/Chat/MessageBubble.tsx | 6475 | 192 | exports MessageBubble
frontend/src/components/Chat/MicButton.tsx | 2950 | 81 | exports MicButton
frontend/src/components/Chat/ResearchTimeline.tsx | 7300 | 237 | exports ResearchTimeline
frontend/src/components/Chat/SpeakMessageButton.test.tsx | 1304 | 39 | 
frontend/src/components/Chat/SpeakMessageButton.tsx | 1816 | 52 | exports SpeakMessageButton
frontend/src/components/Chat/StreamingDots.tsx | 912 | 30 | exports StreamingDots
frontend/src/components/Chat/SystemPanel.tsx | 11463 | 316 | exports SystemPanel
frontend/src/components/Chat/ToolCallCard.tsx | 5796 | 173 | exports ToolCallCard
frontend/src/components/Chat/XRayFooter.tsx | 5362 | 133 | exports XRayFooter
frontend/src/components/Dashboard/CostComparison.tsx | 4137 | 102 | exports CostComparison
frontend/src/components/Dashboard/EnergyDashboard.tsx | 6125 | 202 | exports EnergyDashboard
frontend/src/components/Dashboard/TraceDebugger.tsx | 7414 | 205 | exports TraceDebugger
frontend/src/components/Desktop/AdminPanel.tsx | 12893 | 455 | exports AdminPanel
frontend/src/components/Desktop/AgentsPanel.tsx | 47163 | 1217 | exports AgentsPanel
frontend/src/components/Desktop/EnergyDashboard.tsx | 11404 | 407 | exports EnergyDashboard
frontend/src/components/Desktop/LearningCurve.tsx | 12783 | 437 | exports LearningCurve
frontend/src/components/Desktop/MemoryBrowser.tsx | 10299 | 370 | exports MemoryBrowser
frontend/src/components/Desktop/SavingsDashboard.tsx | 22283 | 675 | exports SavingsDashboard
frontend/src/components/Desktop/SettingsPanel.tsx | 5452 | 206 | exports SettingsPanel
frontend/src/components/Desktop/TraceDebugger.tsx | 15976 | 608 | exports TraceDebugger
frontend/src/components/Desktop/UpdateChecker.tsx | 6724 | 232 | exports isAutoUpdateDisabled
frontend/src/components/Desktop/hooks/useTauriApi.ts | 2665 | 88 | exports isTauri
frontend/src/components/Desktop/lib/api.ts | 6333 | 186 | exports ManagedAgentConfig
frontend/src/components/Sidebar/ConversationList.tsx | 4055 | 110 | exports ConversationList
frontend/src/components/Sidebar/Sidebar.tsx | 9706 | 236 | exports Sidebar
frontend/src/components/setup/IngestDashboard.tsx | 6239 | 180 | exports IngestDashboard
frontend/src/components/setup/ReadyScreen.tsx | 4673 | 143 | exports ReadyScreen
frontend/src/components/setup/SetupWizard.tsx | 4288 | 120 | exports SetupWizard
frontend/src/components/setup/SourceConnectFlow.tsx | 21569 | 641 | exports SourceConnectFlow
frontend/src/components/setup/SourcePicker.tsx | 5673 | 179 | exports SourcePicker
frontend/src/components/ui/button.tsx | 3235 | 59 | 
frontend/src/components/ui/dialog.tsx | 4174 | 158 | 
frontend/src/components/ui/input.tsx | 1060 | 21 | 
frontend/src/components/ui/select.tsx | 6840 | 200 | 
frontend/src/components/ui/sonner.tsx | 1128 | 44 | 
frontend/src/components/ui/tooltip.tsx | 2896 | 65 | 
frontend/src/hooks/useSpeech.ts | 2773 | 93 | exports useSpeech
frontend/src/hooks/useTts.ts | 1140 | 39 | exports useTts
frontend/src/lib/agent-schedule.test.ts | 2747 | 99 | 
frontend/src/lib/agent-schedule.ts | 2484 | 85 | exports AgentScheduleSource
frontend/src/lib/analytics-invitation.test.ts | 3571 | 88 | 
frontend/src/lib/analytics-invitation.ts | 1104 | 34 | exports offerAnalyticsChoice
frontend/src/lib/analytics.test.ts | 6542 | 155 | 
frontend/src/lib/analytics.ts | 8045 | 243 | exports AnalyticsIdentity
frontend/src/lib/api.auth.test.ts | 4722 | 139 | 
frontend/src/lib/api.memory.test.ts | 2620 | 66 | 
frontend/src/lib/api.ts | 41290 | 1229 | exports isTauri
frontend/src/lib/chat-telemetry.test.ts | 2016 | 69 | 
frontend/src/lib/chat-telemetry.ts | 1256 | 42 | exports engineFromCompletionChunk
frontend/src/lib/connectors-api.auth.test.ts | 6205 | 185 | 
frontend/src/lib/connectors-api.ts | 5718 | 163 | exports startServerOAuth
frontend/src/lib/deep-link.ts | 2192 | 62 | exports DeepLinkTarget
frontend/src/lib/markdown-math.test.tsx | 1051 | 30 | 
frontend/src/lib/message-text.test.ts | 1199 | 32 | 
frontend/src/lib/message-text.ts | 1525 | 35 | exports stripThinkTags
frontend/src/lib/model-capabilities.test.ts | 571 | 20 | 
frontend/src/lib/model-capabilities.ts | 531 | 23 | exports isEmbedOnlyModel
frontend/src/lib/polyfills.test.ts | 1429 | 36 | 
frontend/src/lib/polyfills.ts | 1212 | 23 | exports ensureRandomUUID
frontend/src/lib/profanity.ts | 1054 | 25 | exports isProfane
frontend/src/lib/rehype-citations.ts | 6206 | 204 | exports rehypeCitations
frontend/src/lib/sse.ts | 3100 | 110 | exports ChatRequest
frontend/src/lib/store.models.test.ts | 1808 | 65 | 
frontend/src/lib/store.stream-ownership.test.ts | 2594 | 83 | 
frontend/src/lib/store.tool-call-repair.test.ts | 3477 | 123 | 
frontend/src/lib/store.ts | 21531 | 605 | exports CachedConnector
frontend/src/lib/supabase.ts | 638 | 12 | exports SUPABASE_URL
frontend/src/lib/tool-call.test.ts | 667 | 23 | 
frontend/src/lib/tool-call.ts | 349 | 12 | exports serializeToolCallArguments
frontend/src/lib/tts.test.ts | 8214 | 255 | 
frontend/src/lib/tts.ts | 5275 | 171 | exports shouldAutoplayFinishedReply
frontend/src/lib/useAgentEvents.test.ts | 2494 | 86 | 
frontend/src/lib/useAgentEvents.ts | 3186 | 115 | exports AgentEvent
frontend/src/lib/utils.ts | 172 | 7 | exports cn
frontend/src/pages/AgentsPage.tsx | 169203 | 4008 | exports AgentsPage
frontend/src/pages/ChatPage.tsx | 469 | 17 | exports ChatPage
frontend/src/pages/DashboardPage.tsx | 1343 | 36 | exports DashboardPage
frontend/src/pages/DataSourcesPage.lifecycle.test.tsx | 1327 | 46 | 
frontend/src/pages/DataSourcesPage.tsx | 96707 | 2400 | exports SyncStatusDisplay
frontend/src/pages/GetStartedPage.tsx | 18328 | 486 | exports GetStartedPage
frontend/src/pages/LogsPage.tsx | 3996 | 95 | exports LogsPage
frontend/src/pages/SettingsPage.cloud-providers.test.tsx | 769 | 18 | 
frontend/src/pages/SettingsPage.memory.test.tsx | 1651 | 46 | 
frontend/src/pages/SettingsPage.tsx | 43474 | 989 | exports MemoryStatusRow
frontend/src/styles/shadcn.css | 18100 | 662 | 
frontend/src/types/connectors.ts | 22439 | 542 | exports SetupStep
frontend/src/types/index.ts | 3967 | 202 | exports SSEEvent
frontend/src-tauri/Cargo.lock | 162948 | 6482 | 
frontend/src-tauri/Cargo.toml | 1766 | 47 | 
frontend/src-tauri/Entitlements.plist | 683 | 0 | 
frontend/src-tauri/Info.plist | 555 | 0 | 
frontend/src-tauri/build.rs | 43 | 4 | 
frontend/src-tauri/tauri.conf.json | 2316 | 73 | 
frontend/src-tauri/binaries/.gitignore | 91 | 0 | 
frontend/src-tauri/capabilities/default.json | 792 | 30 | 
frontend/src-tauri/icons/128x128.png | 34374 | 0 | 
frontend/src-tauri/icons/128x128@2x.png | 109770 | 0 | 
frontend/src-tauri/icons/256x256.png | 109770 | 0 | 
frontend/src-tauri/icons/32x32.png | 3148 | 0 | 
frontend/src-tauri/icons/icon.icns | 2550868 | 0 | 
frontend/src-tauri/icons/icon.ico | 165539 | 0 | 
frontend/src-tauri/icons/icon.png | 1125714 | 0 | 
frontend/src-tauri/scripts/download-ollama.sh | 5781 | 177 | 
frontend/src-tauri/scripts/verify-arm64-pe.mjs | 820 | 16 | 
frontend/src-tauri/src/lib.rs | 170938 | 4465 | Small, fast model used when startup needs a default Ollama tag.
frontend/src-tauri/src/main.rs | 179 | 7 | 
frontend/src-tauri/src/overlay.html | 18050 | 451 | 
rust/Cargo.lock | 84888 | 3347 | 
rust/Cargo.toml | 1567 | 53 | 
rust/rust-toolchain.toml | 170 | 6 | 
rust/crates/openjarvis-a2a/Cargo.toml | 236 | 11 | 
rust/crates/openjarvis-a2a/src/lib.rs | 10571 | 344 | OpenJarvis A2A — Agent-to-Agent protocol types and in-memory task store.
rust/crates/openjarvis-agents/Cargo.toml | 612 | 21 | 
rust/crates/openjarvis-agents/src/helpers.rs | 2357 | 81 | Agent helpers — legacy utilities (use `utils` module instead).
rust/crates/openjarvis-agents/src/lib.rs | 689 | 24 | Agents primitive — pluggable agent logic for queries, tool calls, memory.
rust/crates/openjarvis-agents/src/loop_guard.rs | 4567 | 142 | Loop guard — detect and prevent agent loops.
rust/crates/openjarvis-agents/src/monitor_operative.rs | 18087 | 474 | MonitorOperativeAgent -- long-horizon monitoring agent with configurable strategies.
rust/crates/openjarvis-agents/src/native_openhands.rs | 12361 | 340 | NativeOpenHandsAgent -- CodeAct-style agent that uses code actions.
rust/crates/openjarvis-agents/src/native_react.rs | 7258 | 212 | NativeReActAgent — Thought-Action-Observation loop with regex parsing.
rust/crates/openjarvis-agents/src/orchestrator.rs | 3117 | 101 | OrchestratorAgent — multi-turn tool loop with function calling.
rust/crates/openjarvis-agents/src/simple.rs | 2457 | 80 | SimpleAgent — single-turn generation without tools.
rust/crates/openjarvis-agents/src/traits.rs | 626 | 21 | OjAgent trait — interface for all agent implementations.
rust/crates/openjarvis-agents/src/utils.rs | 961 | 33 | Agent utilities — shared helper functions for all agent implementations.
rust/crates/openjarvis-core/Cargo.toml | 450 | 20 | 
rust/crates/openjarvis-core/src/config.rs | 31666 | 1054 | Configuration loading and TOML deserialization.
rust/crates/openjarvis-core/src/error.rs | 6202 | 268 | Error types for OpenJarvis.
rust/crates/openjarvis-core/src/events.rs | 9105 | 325 | Pub/sub event bus for cross-cutting concerns.
rust/crates/openjarvis-core/src/hardware.rs | 10264 | 346 | Hardware detection and engine recommendation.
rust/crates/openjarvis-core/src/lib.rs | 631 | 20 | OpenJarvis Core — foundation types, registry, config, and event bus.
rust/crates/openjarvis-core/src/model_catalog.rs | 11489 | 307 | Built-in model catalog with well-known ModelSpec entries.
rust/crates/openjarvis-core/src/registry.rs | 7934 | 231 | Decorator-based registry for runtime discovery of pluggable components.
rust/crates/openjarvis-core/src/types.rs | 21923 | 739 | Canonical data types shared across all OpenJarvis primitives.
rust/crates/openjarvis-engine/Cargo.toml | 626 | 23 | 
rust/crates/openjarvis-engine/src/discovery.rs | 4282 | 131 | Engine discovery — probe health endpoints to find running engines.
rust/crates/openjarvis-engine/src/engine_enum.rs | 7626 | 208 | Engine enum — static dispatch over all engine backends.
rust/crates/openjarvis-engine/src/lib.rs | 677 | 24 | Inference Engine primitive — LLM runtime management.
rust/crates/openjarvis-engine/src/llamacpp.rs | 11090 | 338 | llama.cpp inference engine backend.
rust/crates/openjarvis-engine/src/ollama.rs | 8924 | 275 | Ollama inference engine backend.
rust/crates/openjarvis-engine/src/openai_compat.rs | 12092 | 381 | OpenAI-compatible inference engine for vLLM, SGLang, LM Studio, etc.
rust/crates/openjarvis-engine/src/rig_adapter.rs | 9011 | 277 | Rig-core model adapter — bridges `InferenceEngine` into rig's `CompletionModel`.
rust/crates/openjarvis-engine/src/sglang.rs | 10467 | 326 | SGLang inference engine backend.
rust/crates/openjarvis-engine/src/traits.rs | 3680 | 116 | InferenceEngine trait and shared utilities.
rust/crates/openjarvis-engine/src/vllm.rs | 11861 | 367 | vLLM inference engine backend.
rust/crates/openjarvis-learning/Cargo.toml | 524 | 19 | 
rust/crates/openjarvis-learning/src/agent_advisor.rs | 6266 | 192 | Agent advisor — analyzes trace patterns and suggests improvements.
rust/crates/openjarvis-learning/src/agent_evolver.rs | 9286 | 284 | AgentConfigEvolver — analyze traces to produce agent configuration recommendations.
rust/crates/openjarvis-learning/src/bandit.rs | 5274 | 189 | BanditRouterPolicy — Thompson Sampling / UCB1 for model selection.
rust/crates/openjarvis-learning/src/grpo.rs | 3698 | 130 | GRPORouterPolicy — softmax sampling with group relative advantage.
rust/crates/openjarvis-learning/src/heuristic.rs | 2096 | 81 | HeuristicRouter — rule-based model selection.
rust/crates/openjarvis-learning/src/heuristic_reward.rs | 2745 | 94 | Heuristic reward function — weighted score from latency, cost, efficiency.
rust/crates/openjarvis-learning/src/icl_updater.rs | 7631 | 234 | ICL (in-context learning) example updater with versioning and rollback.
rust/crates/openjarvis-learning/src/learning_orchestrator.rs | 6620 | 200 | LearningOrchestrator — coordinate the trace→learn→eval cycle.
rust/crates/openjarvis-learning/src/lib.rs | 1592 | 41 | Learning — router policies, bandits, GRPO, trace-driven learning.
rust/crates/openjarvis-learning/src/orchestrator_types.rs | 12286 | 384 | Episode dataclasses for orchestrator training.
rust/crates/openjarvis-learning/src/reward.rs | 11967 | 336 | Multi-objective reward function for orchestrator training.
rust/crates/openjarvis-learning/src/router_enum.rs | 1139 | 36 | RouterPolicyEnum — static dispatch over router policy implementations.
rust/crates/openjarvis-learning/src/sft_policy.rs | 6224 | 180 | SFT router — learns query_class → model mappings from trace data.
rust/crates/openjarvis-learning/src/skill_discovery.rs | 6524 | 199 | Skill discovery — mine recurring tool sequences from traces.
rust/crates/openjarvis-learning/src/trace_policy.rs | 10157 | 325 | Trace-driven router policy — learns from interaction history.
rust/crates/openjarvis-learning/src/training_data.rs | 12385 | 346 | TrainingDataMiner — extract supervised training pairs from trace data.
rust/crates/openjarvis-learning/src/traits.rs | 496 | 19 | Learning trait definitions.
rust/crates/openjarvis-learning/src/optimize/engine.rs | 16490 | 485 | OptimizationEngine -- orchestrates the optimize loop.
rust/crates/openjarvis-learning/src/optimize/llm_optimizer.rs | 29943 | 861 | LLM-based optimizer for OpenJarvis configuration tuning.
rust/crates/openjarvis-learning/src/optimize/mod.rs | 798 | 21 | Optimization framework for OpenJarvis configuration tuning.
rust/crates/openjarvis-learning/src/optimize/search_space.rs | 13064 | 355 | Search space builder and default search space for configuration optimization.
rust/crates/openjarvis-learning/src/optimize/store.rs | 25034 | 672 | SQLite-backed storage for optimization runs and trials.
rust/crates/openjarvis-learning/src/optimize/types.rs | 22658 | 639 | Core data types for the optimization framework.
rust/crates/openjarvis-mcp/Cargo.toml | 356 | 14 | 
rust/crates/openjarvis-mcp/src/lib.rs | 194 | 8 | MCP (Model Context Protocol) — JSON-RPC server/client for tool exposure.
rust/crates/openjarvis-mcp/src/protocol.rs | 2909 | 111 | MCP JSON-RPC 2.0 protocol types.
rust/crates/openjarvis-mcp/src/server.rs | 4989 | 154 | MCP server — handles JSON-RPC tool discovery and invocation.
rust/crates/openjarvis-python/Cargo.toml | 1246 | 33 | 
rust/crates/openjarvis-python/pyproject.toml | 265 | 13 | 
rust/crates/openjarvis-python/uv.lock | 144 | 9 | 
rust/crates/openjarvis-python/src/a2a.rs | 3097 | 112 | PyO3 bindings for A2A (Agent-to-Agent) protocol types and task store.
rust/crates/openjarvis-python/src/agents.rs | 12724 | 379 | PyO3 bindings for agent types.
rust/crates/openjarvis-python/src/core.rs | 4867 | 213 | PyO3 bindings for core types.
rust/crates/openjarvis-python/src/engine.rs | 6618 | 190 | PyO3 bindings for engine types.
rust/crates/openjarvis-python/src/learning.rs | 18809 | 574 | PyO3 bindings for learning/router policy types and optimization.
rust/crates/openjarvis-python/src/lib.rs | 6890 | 196 | PyO3 bridge — exposes ~50 Rust classes to Python via `openjarvis_rust`.
rust/crates/openjarvis-python/src/mcp.rs | 625 | 26 | PyO3 bindings for the MCP server.
rust/crates/openjarvis-python/src/recipes.rs | 1541 | 68 | PyO3 bindings for composable recipes.
rust/crates/openjarvis-python/src/scheduler.rs | 2019 | 62 | PyO3 bindings for task scheduler.
rust/crates/openjarvis-python/src/security.rs | 7320 | 259 | PyO3 bindings for security types.
rust/crates/openjarvis-python/src/sessions.rs | 1991 | 67 | PyO3 bindings for session management.
rust/crates/openjarvis-python/src/skills.rs | 3740 | 129 | PyO3 bindings for skill manifests and verification.
rust/crates/openjarvis-python/src/storage.rs | 13837 | 383 | PyO3 bindings for storage/memory backends.
rust/crates/openjarvis-python/src/telemetry.rs | 12500 | 383 | PyO3 bindings for telemetry types.
rust/crates/openjarvis-python/src/templates.rs | 1242 | 58 | PyO3 bindings for agent templates.
rust/crates/openjarvis-python/src/tools.rs | 6996 | 238 | PyO3 bindings for tool types.
rust/crates/openjarvis-python/src/traces.rs | 2844 | 93 | PyO3 bindings for trace types.
rust/crates/openjarvis-python/src/workflow.rs | 3795 | 128 | PyO3 bindings for workflow engine.
rust/crates/openjarvis-recipes/Cargo.toml | 240 | 11 | 
rust/crates/openjarvis-recipes/src/lib.rs | 5746 | 187 | OpenJarvis Recipes — composable TOML configs that wire all five primitives.
rust/crates/openjarvis-scheduler/Cargo.toml | 306 | 13 | 
rust/crates/openjarvis-scheduler/src/lib.rs | 14094 | 432 | OpenJarvis Scheduler — task scheduling with cron, interval, and one-shot
rust/crates/openjarvis-security/Cargo.toml | 697 | 26 | 
rust/crates/openjarvis-security/src/audit.rs | 10563 | 324 | Audit logger — persist security events to SQLite with Merkle hash chain.
rust/crates/openjarvis-security/src/capabilities.rs | 7187 | 239 | RBAC capability system — fine-grained permission model for tool dispatch.
rust/crates/openjarvis-security/src/file_policy.rs | 9042 | 281 | File sensitivity policy — block access to secrets, credentials, and keys.
rust/crates/openjarvis-security/src/guardrails.rs | 8831 | 268 | GuardrailsEngine — security-aware inference engine wrapper.
rust/crates/openjarvis-security/src/injection.rs | 7847 | 233 | Prompt injection scanner — detect malicious patterns in text.
rust/crates/openjarvis-security/src/lib.rs | 734 | 24 | Security guardrails — scanners, RBAC, taint tracking, audit, SSRF protection.
rust/crates/openjarvis-security/src/rate_limiter.rs | 3821 | 148 | Rate limiter — token bucket algorithm for per-agent/per-tool throttling.
rust/crates/openjarvis-security/src/scanner.rs | 9497 | 316 | Concrete security scanners — secrets and PII detection.
rust/crates/openjarvis-security/src/ssrf.rs | 11411 | 320 | SSRF protection — block requests to private IPs and cloud metadata endpoints.
rust/crates/openjarvis-security/src/taint.rs | 5941 | 196 | Taint tracking — information flow control.
rust/crates/openjarvis-security/src/types.rs | 3416 | 128 | Security data types — threat levels, scan findings, security events.
rust/crates/openjarvis-sessions/Cargo.toml | 274 | 12 | 
rust/crates/openjarvis-sessions/src/lib.rs | 25469 | 732 | OpenJarvis Sessions — cross-channel persistent session management.
rust/crates/openjarvis-skills/Cargo.toml | 277 | 12 | 
rust/crates/openjarvis-skills/src/lib.rs | 5252 | 165 | OpenJarvis Skills — skill manifests, execution results, and signature verification.
rust/crates/openjarvis-telemetry/Cargo.toml | 577 | 22 | 
rust/crates/openjarvis-telemetry/src/aggregator.rs | 643 | 24 | TelemetryAggregator — read-only SQL aggregation queries.
rust/crates/openjarvis-telemetry/src/energy.rs | 2651 | 101 | Energy monitoring — EnergyMonitor trait and vendor implementations.
rust/crates/openjarvis-telemetry/src/flops.rs | 6875 | 229 | FLOPs estimation and Model FLOPs Utilization (MFU) computation.
rust/crates/openjarvis-telemetry/src/instrumented.rs | 3312 | 118 | InstrumentedEngine — wraps any InferenceEngine with telemetry recording.
rust/crates/openjarvis-telemetry/src/itl.rs | 5155 | 157 | Inter-token latency (ITL) statistics — percentiles, mean, min, max.
rust/crates/openjarvis-telemetry/src/lib.rs | 336 | 15 | Telemetry — InstrumentedEngine, TelemetryStore, energy monitoring.
rust/crates/openjarvis-telemetry/src/phase.rs | 6697 | 202 | Phase-level metrics: energy, power, and per-token efficiency for prefill/decode phases.
rust/crates/openjarvis-telemetry/src/session.rs | 12315 | 392 | Ring-buffer backed telemetry session for high-frequency power/energy sampling.
rust/crates/openjarvis-telemetry/src/store.rs | 5156 | 153 | TelemetryStore — SQLite persistence for telemetry records.
rust/crates/openjarvis-templates/Cargo.toml | 242 | 11 | 
rust/crates/openjarvis-templates/src/lib.rs | 2429 | 80 | OpenJarvis Templates — pre-configured agent templates loaded from TOML.
rust/crates/openjarvis-tools/Cargo.toml | 807 | 29 | 
rust/crates/openjarvis-tools/src/executor.rs | 4948 | 148 | ToolExecutor — central dispatch with RBAC, taint, timeout.
rust/crates/openjarvis-tools/src/lib.rs | 245 | 11 | Tools primitive — BaseTool trait, ToolExecutor, built-in tools, storage backends.
rust/crates/openjarvis-tools/src/rig_tools.rs | 13525 | 417 | Rig-core tool adapters — typed Args structs implementing rig's `Tool` trait.
rust/crates/openjarvis-tools/src/traits.rs | 758 | 25 | BaseTool trait — interface for all tool implementations.
rust/crates/openjarvis-tools/src/builtin/calculator.rs | 2528 | 91 | Calculator tool — evaluate mathematical expressions.
rust/crates/openjarvis-tools/src/builtin/file_tools.rs | 4549 | 148 | File read/write tools.
rust/crates/openjarvis-tools/src/builtin/git_tools.rs | 3346 | 93 | Git tools — status, diff, log.
rust/crates/openjarvis-tools/src/builtin/http_tools.rs | 3457 | 100 | HTTP request tool.
rust/crates/openjarvis-tools/src/builtin/mod.rs | 1939 | 60 | Built-in tool implementations.
rust/crates/openjarvis-tools/src/builtin/shell.rs | 2541 | 80 | Shell execution tool.
rust/crates/openjarvis-tools/src/builtin/think.rs | 1305 | 47 | Think tool — allows the agent to express reasoning steps.
rust/crates/openjarvis-tools/src/storage/backend_enum.rs | 2627 | 84 | MemoryBackendEnum — static dispatch over storage backends.
rust/crates/openjarvis-tools/src/storage/bm25.rs | 5577 | 197 | BM25 memory backend — pure Rust BM25 scoring.
rust/crates/openjarvis-tools/src/storage/colbert.rs | 14234 | 416 | ColBERT-style memory backend — token-level embeddings with MaxSim scoring.
rust/crates/openjarvis-tools/src/storage/faiss.rs | 13095 | 394 | FAISS-style vector similarity memory backend — pure Rust brute-force cosine similarity.
rust/crates/openjarvis-tools/src/storage/hybrid.rs | 8094 | 244 | Hybrid memory backend — Reciprocal Rank Fusion (RRF) over multiple backends.
rust/crates/openjarvis-tools/src/storage/knowledge_graph.rs | 8461 | 264 | Knowledge graph memory — SQLite entity-relation store.
rust/crates/openjarvis-tools/src/storage/mod.rs | 534 | 21 | Memory/storage backends — SQLite FTS5, BM25, FAISS, ColBERT, KnowledgeGraph, Hybrid.
rust/crates/openjarvis-tools/src/storage/sqlite.rs | 21092 | 545 | SQLite + FTS5 memory backend.
rust/crates/openjarvis-tools/src/storage/traits.rs | 686 | 23 | MemoryBackend trait for all storage backends.
rust/crates/openjarvis-tools/src/storage/utils.rs | 1452 | 58 | Storage utilities — text chunking and document ingestion.
rust/crates/openjarvis-traces/Cargo.toml | 414 | 18 | 
rust/crates/openjarvis-traces/src/analyzer.rs | 4835 | 154 | TraceAnalyzer — compute statistics from stored traces.
rust/crates/openjarvis-traces/src/collector.rs | 2998 | 103 | TraceCollector — subscribes to EventBus and assembles traces.
rust/crates/openjarvis-traces/src/lib.rs | 220 | 10 | Traces — full interaction-level recording and analysis.
rust/crates/openjarvis-traces/src/store.rs | 8553 | 247 | TraceStore — SQLite persistence for traces.
rust/crates/openjarvis-workflow/Cargo.toml | 241 | 11 | 
rust/crates/openjarvis-workflow/src/lib.rs | 15795 | 499 | OpenJarvis Workflow — DAG-based workflow graph, builder, and execution planner.
scripts/bump-desktop-version.sh | 1859 | 57 | 
scripts/index_docs.py | 6316 | 185 | Index OpenJarvis docs (README.md + docs/**/*.md) into a DenseMemory backend.
scripts/launch-claude.sh | 1494 | 40 | 
scripts/oauth_all.py | 12379 | 359 | Run OAuth flows for Google, Strava, and Spotify in sequence.
scripts/quickstart.sh | 13320 | 329 | 
scripts/setup-energy-monitor.sh | 2215 | 72 | 
scripts/smoke_framework_comparison.sh | 3372 | 96 | 
scripts/install/bg-orchestrator.sh | 1407 | 50 | 
scripts/install/build-extension.sh | 2181 | 61 | 
scripts/install/install-rust.sh | 710 | 24 | 
scripts/install/install.sh | 29668 | 848 | 
scripts/install/jarvis-uninstall.sh | 4063 | 134 | 
scripts/install/jarvis-wrapper.sh | 466 | 15 | 
scripts/install/pull-model.sh | 1544 | 58 | 
scripts/mining/pearl_model_converter.py | 402 | 17 | Compatibility wrapper for Pearl model conversion tooling.
scripts/pearl/README.md | 504 | 12 | Pearl Tooling
scripts/pearl/model_converter.py | 11610 | 362 | Create experimental Pearl-compatible compressed-tensors checkpoints.
src/openjarvis/__init__.py | 1152 | 36 | OpenJarvis — modular AI assistant backend with composable intelligence primitives.
src/openjarvis/_rust_bridge.py | 6339 | 195 | Single point of contact between Python and the Rust ``openjarvis_rust`` module.
src/openjarvis/sdk.py | 23474 | 678 | High-level Python SDK for OpenJarvis.
src/openjarvis/a2a/__init__.py | 434 | 17 | Agent-to-Agent protocol — Google A2A spec implementation.
src/openjarvis/a2a/client.py | 3596 | 116 | A2A client — discover and call external A2A agents.
src/openjarvis/a2a/protocol.py | 3255 | 117 | A2A protocol types — Google A2A spec (JSON-RPC 2.0).
src/openjarvis/a2a/server.py | 6038 | 169 | A2A server — exposes agents via /.well-known/agent.json and /a2a/tasks.
src/openjarvis/a2a/tool.py | 2666 | 82 | A2AAgentTool — wraps an external A2A agent as an invocable tool.
src/openjarvis/agents/__init__.py | 2487 | 105 | Agents primitive — multi-turn reasoning and tool use.
src/openjarvis/agents/_stubs.py | 19633 | 511 | ABC for agent implementations.
src/openjarvis/agents/channel_agent.py | 5421 | 155 | ChannelAgent — bridge between messaging channels and AI agents.
src/openjarvis/agents/claude_code.py | 9764 | 276 | ClaudeCodeAgent -- wraps the Claude Agent SDK via Node.js subprocess bridge.
src/openjarvis/agents/deep_research.py | 15015 | 383 | DeepResearchAgent -- multi-hop retrieval agent with cited reports.
src/openjarvis/agents/digest_store.py | 5528 | 156 | DigestStore — SQLite-backed storage for pre-computed digest artifacts.
src/openjarvis/agents/errors.py | 3539 | 117 | Error classification for managed agent execution.
src/openjarvis/agents/executor.py | 39805 | 992 | AgentExecutor — runs a single agent tick.
src/openjarvis/agents/loop_guard.py | 9667 | 244 | Agent loop guard — detect and prevent degenerate tool-calling loops.
src/openjarvis/agents/manager.py | 34481 | 873 | Persistent agent lifecycle manager.
src/openjarvis/agents/monitor_operative.py | 31320 | 759 | MonitorOperativeAgent -- long-horizon agent with configurable strategies.
src/openjarvis/agents/morning_digest.py | 9968 | 244 | Morning Digest Agent — synthesizes a daily briefing from multiple sources.
src/openjarvis/agents/native_openhands.py | 17988 | 440 | NativeOpenHandsAgent -- code-execution-centric agent.
src/openjarvis/agents/native_react.py | 13926 | 368 | NativeReActAgent -- Thought-Action-Observation loop agent.
src/openjarvis/agents/opencode.py | 25957 | 611 | OpenCodeAgent -- wraps the `opencode` coding agent via its headless HTTP server.
src/openjarvis/agents/openhands.py | 3144 | 97 | OpenHandsAgent -- wraps the real openhands-sdk for AI-driven development.
src/openjarvis/agents/operative.py | 12401 | 329 | OperativeAgent — persistent, scheduled agent for autonomous operation.
src/openjarvis/agents/orchestrator.py | 20828 | 545 | OrchestratorAgent — multi-turn agent with tool-calling loop.
src/openjarvis/agents/proactive_agent.py | 27290 | 694 | Proactive Agent — runs on a cron (default 5am local) to autonomously handle
src/openjarvis/agents/prompt_loader.py | 2756 | 85 | Load system prompt and few-shot overrides from $OPENJARVIS_HOME.
src/openjarvis/agents/research_loop.py | 38126 | 886 | Agentic research loop over the hybrid-search tool.
src/openjarvis/agents/rlm.py | 19888 | 521 | RLM (Recursive Language Model) Agent — recursive decomposition via persistent REPL.
src/openjarvis/agents/rlm_repl.py | 8476 | 248 | Sandboxed REPL environment for the RLM agent.
src/openjarvis/agents/scheduler.py | 11445 | 326 | AgentScheduler — cron/interval tick scheduling for managed agents.
src/openjarvis/agents/simple.py | 1049 | 37 | SimpleAgent — single-turn query-to-response agent (no tool calling).
src/openjarvis/agents/tool_resolver.py | 16940 | 509 | Canonical managed-agent tool resolution.
src/openjarvis/agents/claude_code_runner/index.mjs | 3752 | 132 | 
src/openjarvis/agents/claude_code_runner/package.json | 172 | 9 | 
src/openjarvis/agents/hybrid/README.md | 5245 | 102 | Hybrid local+cloud paradigm agents
src/openjarvis/agents/hybrid/__init__.py | 1832 | 45 | Hybrid local+cloud paradigms — ported from `hybrid-local-cloud-compute`.
src/openjarvis/agents/hybrid/_base.py | 58270 | 1479 | LocalCloudAgent — shared base for hybrid local+cloud paradigm agents.
src/openjarvis/agents/hybrid/_energy.py | 6563 | 176 | GPU energy collector for hybrid cell runs.
src/openjarvis/agents/hybrid/_openai_retry.py | 14227 | 361 | Process-wide retry + concurrency hardening for cloud OpenAI calls.
src/openjarvis/agents/hybrid/_prices.py | 3098 | 74 | Cloud-model pricing + per-family quirks for hybrid paradigm agents.
src/openjarvis/agents/hybrid/_prompts.py | 2697 | 69 | Bench-specific answer-format instructions for hybrid paradigm agents.
src/openjarvis/agents/hybrid/advisors.py | 19111 | 468 | AdvisorsAgent — inference-only port of advisor-models (Asawa et al., 2026).
src/openjarvis/agents/hybrid/archon.py | 27117 | 707 | ArchonAgent — port of ScalingIntelligence/Archon.
src/openjarvis/agents/hybrid/baseline_cloud.py | 7861 | 193 | BaselineCloudAgent — cloud-only reference for the hybrid ablation.
src/openjarvis/agents/hybrid/baseline_local.py | 6297 | 160 | BaselineLocalAgent — local-only reference for the hybrid ablation.
src/openjarvis/agents/hybrid/conductor.py | 46269 | 1116 | ConductorAgent — static-DAG planner (Sakana AI, arXiv 2512.04388).
src/openjarvis/agents/hybrid/mini_swe_agent.py | 58541 | 1599 | MiniSWEAgent — vendored, ~330-line port of mini-SWE-agent v2.
src/openjarvis/agents/hybrid/minions.py | 32381 | 803 | MinionsAgent — port of HazyResearch Minions protocol.
src/openjarvis/agents/hybrid/runner.py | 34221 | 933 | CLI runner for hybrid paradigm experiments.
src/openjarvis/agents/hybrid/skillorchestra.py | 16945 | 435 | SkillOrchestraAgent — inference-time router (Wang et al., 2026).
src/openjarvis/agents/hybrid/toolorchestra.py | 83368 | 1980 | ToolOrchestraAgent — port of NVlabs ToolOrchestra (arXiv:2511.21689).
src/openjarvis/agents/hybrid/registry/advisors.toml | 1560 | 42 | 
src/openjarvis/agents/hybrid/registry/archon.toml | 3862 | 95 | 
src/openjarvis/agents/hybrid/registry/baseline_local.toml | 3551 | 83 | 
src/openjarvis/agents/hybrid/registry/conductor.toml | 5914 | 106 | 
src/openjarvis/agents/hybrid/registry/mini_swe_agent.toml | 1592 | 34 | 
src/openjarvis/agents/hybrid/registry/minions.toml | 3840 | 97 | 
src/openjarvis/agents/hybrid/registry/skillorchestra.toml | 2912 | 60 | 
src/openjarvis/agents/hybrid/registry/swe_agent_loop.toml | 3669 | 71 | 
src/openjarvis/agents/hybrid/registry/toolorchestra.toml | 13216 | 230 | 
src/openjarvis/agents/hybrid/scripts/new_experiment.sh | 4109 | 109 | 
src/openjarvis/agents/hybrid/skillorchestra/README.md | 2582 | 49 | skillorchestra — faithful port of SkillOrchestra (arXiv:2602.19672)
src/openjarvis/agents/hybrid/skillorchestra/__init__.py | 1046 | 23 | SkillOrchestra — faithful port of the eval-orchestrator (arXiv:2602.19672).
src/openjarvis/agents/hybrid/skillorchestra/agent.py | 7614 | 187 | SkillOrchestraAgent — the OpenJarvis harness entry point.
src/openjarvis/agents/hybrid/skillorchestra/handbook_seed.json | 14955 | 500 | 
src/openjarvis/agents/hybrid/skillorchestra/orchestrator.py | 15661 | 434 | The SkillOrchestra eval-orchestrator loop.
src/openjarvis/agents/hybrid/skillorchestra/pool.py | 5767 | 177 | Model-alias pool for the SkillOrchestra eval orchestrator.
src/openjarvis/agents/hybrid/skillorchestra/stage_router.py | 19671 | 531 | Adapter for orchestration eval script.
src/openjarvis/agents/hybrid/skillorchestra/tools.py | 16231 | 470 | The three SkillOrchestra tools: search, enhance_reasoning (code), answer.
src/openjarvis/agents/hybrid/skillorchestra/types.py | 15563 | 435 | Core data types for SkillOrchestra.
src/openjarvis/agents/hybrid/skillorchestra/prompts/__init__.py | 1496 | 50 | Prompt templates for SkillOrchestra.
src/openjarvis/agents/hybrid/skillorchestra/prompts/eval_orchestrator.py | 9604 | 234 | Eval orchestrator prompts for skill-based agent orchestration.
src/openjarvis/agents/hybrid/skillorchestra/prompts/learning.py | 15345 | 449 | LLM prompt templates for Skill Handbook learning.
src/openjarvis/agents/hybrid/skillorchestra/prompts/model_routing.py | 8459 | 135 | Prompt templates for model routing (skill-based and baseline).
src/openjarvis/agents/templates/__init__.py | 0 | 0 | 
src/openjarvis/agents/templates/code_reviewer.toml | 2474 | 49 | 
src/openjarvis/agents/templates/inbox_triager.toml | 2383 | 45 | 
src/openjarvis/agents/templates/personal_deep_research.toml | 476 | 13 | 
src/openjarvis/agents/templates/research_monitor.toml | 2693 | 46 | 
src/openjarvis/analytics/__init__.py | 1049 | 34 | External anonymous usage analytics.
src/openjarvis/analytics/aggregator.py | 6635 | 187 | Per-session aggregator — turns many internal events into one analytics event.
src/openjarvis/analytics/bridge.py | 9099 | 223 | Bridge between the internal event bus and the analytics client.
src/openjarvis/analytics/client.py | 4884 | 147 | PostHog client wrapper.
src/openjarvis/analytics/events.py | 11481 | 408 | Canonical registry of external analytics events.
src/openjarvis/analytics/identity.py | 1576 | 50 | Anonymous identity for external analytics.
src/openjarvis/analytics/redaction.py | 4058 | 107 | PII redaction for analytics property values.
src/openjarvis/bench/__init__.py | 840 | 30 | Benchmarking framework for OpenJarvis inference engines.
src/openjarvis/bench/_stats.py | 1159 | 36 | Shared statistics helpers for benchmark per-sample metrics.
src/openjarvis/bench/_stubs.py | 4990 | 157 | ABC for benchmark implementations and the BenchmarkSuite runner.
src/openjarvis/bench/energy.py | 7003 | 185 | Energy benchmark — per-sample energy, power, and efficiency measurement.
src/openjarvis/bench/latency.py | 2802 | 93 | Latency benchmark — measures per-call inference latency.
src/openjarvis/bench/throughput.py | 3282 | 101 | Throughput benchmark — measures tokens per second with per-sample stats.
src/openjarvis/channels/__init__.py | 1208 | 59 | Channel abstraction for multi-platform messaging.
src/openjarvis/channels/_stubs.py | 3215 | 99 | ABC for channel implementations and shared types.
src/openjarvis/channels/bluebubbles.py | 4280 | 135 | BlueBubblesChannel — BlueBubbles (iMessage bridge) adapter.
src/openjarvis/channels/discord_channel.py | 12885 | 341 | DiscordChannel — native Discord Bot API adapter.
src/openjarvis/channels/email_channel.py | 8659 | 244 | EmailChannel — SMTP/IMAP email adapter (stdlib only, zero extra deps).
src/openjarvis/channels/feishu.py | 5390 | 166 | FeishuChannel — Feishu (Lark) adapter.
src/openjarvis/channels/gmail.py | 11057 | 306 | GmailChannel — native Gmail API adapter using OAuth2.
src/openjarvis/channels/google_chat.py | 3931 | 128 | GoogleChatChannel — Google Chat webhook adapter.
src/openjarvis/channels/imessage_daemon.py | 6344 | 206 | iMessage daemon — polls chat.db and routes to DeepResearchAgent.
src/openjarvis/channels/irc_channel.py | 4853 | 146 | IRCChannel — IRC adapter using stdlib socket.
src/openjarvis/channels/line_channel.py | 4968 | 157 | LineChannel — LINE Messaging API adapter via line-bot-sdk.
src/openjarvis/channels/mastodon_channel.py | 5183 | 158 | MastodonChannel — Mastodon adapter via Mastodon.py.
src/openjarvis/channels/matrix_channel.py | 4521 | 142 | MatrixChannel — Matrix homeserver adapter.
src/openjarvis/channels/mattermost.py | 4380 | 139 | MattermostChannel — Mattermost REST API adapter.
src/openjarvis/channels/messenger_channel.py | 4154 | 137 | MessengerChannel — Facebook Messenger adapter via pymessenger.
src/openjarvis/channels/nostr_channel.py | 5381 | 165 | NostrChannel — Nostr protocol adapter via pynostr.
src/openjarvis/channels/reddit_channel.py | 5743 | 172 | RedditChannel — Reddit adapter via praw.
src/openjarvis/channels/rocketchat_channel.py | 5670 | 170 | RocketChatChannel — Rocket.Chat adapter via rocketchat_API.
src/openjarvis/channels/sendblue.py | 7375 | 229 | SendBlue channel — iMessage/SMS API adapter.
src/openjarvis/channels/signal_channel.py | 4185 | 134 | SignalChannel — Signal adapter via signal-cli REST API.
src/openjarvis/channels/slack.py | 8159 | 227 | SlackChannel — native Slack Web API adapter.
src/openjarvis/channels/slack_daemon.py | 6556 | 226 | Slack Socket Mode daemon — listens for DMs and responds with DeepResearch.
src/openjarvis/channels/teams.py | 4827 | 146 | TeamsChannel — Microsoft Teams Bot Framework adapter.
src/openjarvis/channels/telegram.py | 18793 | 457 | TelegramChannel — native Telegram Bot API adapter.
src/openjarvis/channels/twilio_sms.py | 4135 | 141 | Twilio SMS channel for sending and receiving text messages.
src/openjarvis/channels/twitch_channel.py | 5383 | 165 | TwitchChannel — Twitch chat adapter via twitchio.
src/openjarvis/channels/twitter_channel.py | 12069 | 344 | TwitterChannel — Twitter/X API v2 adapter using OAuth 1.0a.
src/openjarvis/channels/viber_channel.py | 4605 | 147 | ViberChannel — Viber adapter via viberbot.
src/openjarvis/channels/webchat.py | 3555 | 115 | WebChatChannel — in-memory message queue for webchat/testing.
src/openjarvis/channels/webhook.py | 4386 | 144 | WebhookChannel — generic outbound webhook adapter (zero extra deps).
src/openjarvis/channels/whatsapp.py | 4526 | 144 | WhatsAppChannel — WhatsApp Cloud API adapter.
src/openjarvis/channels/whatsapp_baileys.py | 12275 | 342 | WhatsAppBaileysChannel -- bidirectional WhatsApp messaging via Baileys protocol.
src/openjarvis/channels/xmpp_channel.py | 4761 | 154 | XMPPChannel — XMPP/Jabber adapter via slixmpp.
src/openjarvis/channels/zulip_channel.py | 5585 | 170 | ZulipChannel — Zulip adapter via zulip Python bindings.
src/openjarvis/channels/whatsapp_baileys_bridge/package-lock.json | 49465 | 1352 | 
src/openjarvis/channels/whatsapp_baileys_bridge/package.json | 427 | 18 | 
src/openjarvis/channels/whatsapp_baileys_bridge/tsconfig.json | 271 | 14 | 
src/openjarvis/channels/whatsapp_baileys_bridge/src/bridge.ts | 4574 | 157 | 
src/openjarvis/cli/__init__.py | 8412 | 222 | Command-line interface for OpenJarvis (Click-based).
src/openjarvis/cli/__main__.py | 115 | 7 | Entry point for CLI execution.
src/openjarvis/cli/_analytics_consent.py | 2569 | 61 | Dedicated terminal consent for optional external usage analytics.
src/openjarvis/cli/_banner.py | 1571 | 40 | Startup banner — OpenJarvis wordmark + tagline.
src/openjarvis/cli/_bg_state.py | 3222 | 89 | Read background-work state from ``~/.openjarvis/.state/``.
src/openjarvis/cli/_bootstrap.py | 7857 | 250 | Cloud-key auto-detection and initial-config writing.
src/openjarvis/cli/_chat_banner.py | 1008 | 30 | Chat startup banner — renders BgStatus as a one-line status string.
src/openjarvis/cli/_chat_notifications.py | 1895 | 49 | Between-turn completion notifications for background work.
src/openjarvis/cli/_first_run.py | 1660 | 49 | Bare-`jarvis` first-run guard.
src/openjarvis/cli/_install_detect.py | 3197 | 89 | Detect how OpenJarvis was installed so we can show the right upgrade
src/openjarvis/cli/_model_switch.py | 4116 | 139 | Resolve chat CLI model: per-command presets, ``-m smart``, ``default_model``.
src/openjarvis/cli/_runtime_panel.py | 5394 | 168 | Interactive runtime panel: GPU offload and context window (Ollama).
src/openjarvis/cli/_screen.py | 2623 | 80 | Screen capture for vision input (``jarvis ask --screen``).
src/openjarvis/cli/_tool_names.py | 1119 | 41 | Helpers for resolving CLI tool selections.
src/openjarvis/cli/_version_check.py | 7235 | 224 | Check for newer OpenJarvis releases on PyPI.
src/openjarvis/cli/_voice_chat.py | 8796 | 215 | Voice input/output helpers for the interactive chat session.
src/openjarvis/cli/add_cmd.py | 4173 | 139 | ``jarvis add`` — quick MCP server setup.
src/openjarvis/cli/agent_cmd.py | 32481 | 885 | ``jarvis agents`` — persistent agent lifecycle management.
src/openjarvis/cli/ask.py | 46607 | 1249 | ``jarvis ask`` — send a query to the assistant.
src/openjarvis/cli/auth_cmd.py | 1891 | 72 | CLI commands for API key management.
src/openjarvis/cli/bench_cmd.py | 15652 | 490 | ``jarvis bench`` — run inference benchmarks.
src/openjarvis/cli/channel_cmd.py | 8228 | 267 | ``jarvis channel`` -- channel management commands.
src/openjarvis/cli/channels_cmd.py | 4840 | 164 | ``jarvis channels`` — manage messaging channels for the agent.
src/openjarvis/cli/chat_cmd.py | 19898 | 521 | ``jarvis chat`` — interactive multi-turn chat REPL.
src/openjarvis/cli/compose_cmd.py | 16794 | 484 | ``jarvis compose`` — unified composition CLI for discrete agents and operators.
src/openjarvis/cli/config_cmd.py | 14674 | 406 | ``jarvis config`` — configuration inspection commands.
src/openjarvis/cli/connect_cmd.py | 8081 | 228 | ``jarvis connect`` -- manage data source connections.
src/openjarvis/cli/daemon_cmd.py | 20861 | 564 | ``jarvis start|stop|restart|status`` — daemon management commands.
src/openjarvis/cli/dashboard.py | 5973 | 168 | TUI dashboard — terminal-based system monitoring via textual.
src/openjarvis/cli/deep_research_setup_cmd.py | 15626 | 459 | ``jarvis deep-research-setup`` — auto-detect local sources, ingest, and chat.
src/openjarvis/cli/digest_cmd.py | 10363 | 293 | ``jarvis digest`` — display and play the morning digest.
src/openjarvis/cli/doctor_cmd.py | 15679 | 465 | ``jarvis doctor`` — run diagnostic checks on the OpenJarvis installation.
src/openjarvis/cli/eval_cmd.py | 20338 | 621 | ``jarvis eval`` — evaluation framework CLI commands.
src/openjarvis/cli/feedback_cmd.py | 6027 | 199 | ``jarvis feedback`` — trace feedback management CLI.
src/openjarvis/cli/gateway_cmd.py | 2971 | 108 | ``jarvis gateway start|stop|status|logs`` — multi-channel gateway management.
src/openjarvis/cli/gui_cmd.py | 23433 | 612 | ``jarvis gui`` — start and open the local graphical interface.
src/openjarvis/cli/hints.py | 2137 | 53 | Rich-formatted error hints for common CLI failure modes.
src/openjarvis/cli/host_cmd.py | 12779 | 418 | ``jarvis host`` — download and serve a model locally with auto backend setup.
src/openjarvis/cli/init_cmd.py | 20213 | 585 | ``jarvis init`` — detect hardware, generate config, write to disk.
src/openjarvis/cli/log_config.py | 2543 | 88 | Global logging configuration for the OpenJarvis CLI.
src/openjarvis/cli/memory_cmd.py | 9824 | 336 | ``jarvis memory`` — memory management subcommands.
src/openjarvis/cli/mine_cmd.py | 34393 | 994 | ``jarvis mine`` command group.
src/openjarvis/cli/model.py | 26699 | 721 | ``jarvis model`` — model management subcommands.
src/openjarvis/cli/operators_cmd.py | 10030 | 287 | ``jarvis operators`` — operator lifecycle management commands.
src/openjarvis/cli/optimize_cmd.py | 16616 | 514 | ``jarvis optimize`` — LLM-driven configuration optimization CLI.
src/openjarvis/cli/pearl_cmd.py | 5128 | 150 | ``jarvis pearl`` — thin wrappers around Pearl's native CLIs.
src/openjarvis/cli/quickstart_cmd.py | 5802 | 161 | ``jarvis quickstart`` — guided 5-step setup for new users.
src/openjarvis/cli/registry_cmd.py | 4915 | 147 | ``jarvis registry`` — registry inspection commands.
src/openjarvis/cli/scan_cmd.py | 23569 | 671 | ``jarvis scan`` — audit your environment for privacy and security risks.
src/openjarvis/cli/scheduler_cmd.py | 10388 | 337 | ``jarvis scheduler`` -- task scheduling commands.
src/openjarvis/cli/self_update_cmd.py | 5716 | 167 | `jarvis self-update` — upgrade OpenJarvis to the latest release.
src/openjarvis/cli/serve.py | 31736 | 802 | ``jarvis serve`` — OpenAI-compatible API server.
src/openjarvis/cli/skill_cmd.py | 24284 | 734 | CLI commands for skill management.
src/openjarvis/cli/telemetry_cmd.py | 8894 | 233 | ``jarvis telemetry`` — query and manage telemetry data.
src/openjarvis/cli/tool_cmd.py | 4147 | 108 | ``jarvis tool`` — tool management commands.
src/openjarvis/cli/tunnel_cmd.py | 2117 | 72 | CLI commands for Cloudflare Tunnel management.
src/openjarvis/cli/vault_cmd.py | 3969 | 141 | ``jarvis vault`` — encrypted credential store.
src/openjarvis/cli/workflow_cmd.py | 2431 | 71 | ``jarvis workflow`` — workflow management commands.
src/openjarvis/connectors/__init__.py | 2989 | 145 | Data source connectors for Deep Research.
src/openjarvis/connectors/_stubs.py | 3856 | 116 | Base types for data source connectors.
src/openjarvis/connectors/apple_calendar.py | 14013 | 442 | Apple Calendar connector — reads directly from the macOS Calendar SQLite database.
src/openjarvis/connectors/apple_contacts.py | 16543 | 483 | Apple Contacts connector — reads directly from the macOS Contacts SQLite database.
src/openjarvis/connectors/apple_health.py | 15908 | 420 | Apple Health connector -- reads HealthKit SQLite DB or iPhone Health export XML.
src/openjarvis/connectors/apple_music.py | 8300 | 252 | Apple Music connector -- reads tracks from the local Music.app via AppleScript.
src/openjarvis/connectors/apple_notes.py | 10918 | 314 | Apple Notes connector — reads directly from the macOS Notes SQLite database.
src/openjarvis/connectors/attachment_store.py | 6212 | 181 | AttachmentStore — content-addressed blob storage for Deep Research attachments.
src/openjarvis/connectors/chunker.py | 15216 | 399 | Type-aware semantic chunker for Deep Research ingestion.
src/openjarvis/connectors/dropbox.py | 13026 | 376 | Dropbox connector — bulk file sync via the Dropbox API v2.
src/openjarvis/connectors/embedding_store.py | 5955 | 180 | EmbeddingStore --- disk-persistent ColBERT token-level embeddings.
src/openjarvis/connectors/embeddings.py | 6654 | 187 | Dense embedding clients for the IngestionPipeline.
src/openjarvis/connectors/gcalendar.py | 20820 | 564 | Google Calendar connector — event sync via the Calendar REST API v3.
src/openjarvis/connectors/gcontacts.py | 13070 | 361 | Google Contacts connector — bulk contact sync via the People REST API v1.
src/openjarvis/connectors/gdrive.py | 14124 | 384 | Google Drive connector — bulk file sync via the Drive REST API v3.
src/openjarvis/connectors/github_notifications.py | 4416 | 127 | GitHub Notifications connector — unread notifications via GitHub REST API.
src/openjarvis/connectors/gmail.py | 25173 | 688 | Gmail connector — bulk email sync via the Gmail REST API.
src/openjarvis/connectors/gmail_imap.py | 20403 | 524 | Gmail IMAP connector — reads email via IMAP with app password.
src/openjarvis/connectors/google_auth.py | 4895 | 131 | Shared Google OAuth helpers: access token read + one-shot 401 refresh.
src/openjarvis/connectors/google_tasks.py | 4798 | 134 | Google Tasks connector — tasks due today, overdue, and recently completed.
src/openjarvis/connectors/granola.py | 16642 | 461 | Granola connector — syncs meeting notes via the Granola public API.
src/openjarvis/connectors/hackernews.py | 2800 | 92 | Hacker News connector — top stories from the HN Firebase API.
src/openjarvis/connectors/hybrid_search.py | 27307 | 779 | Hybrid retrieval over the KnowledgeStore: metadata filter + BM25 + vector cosine.
src/openjarvis/connectors/imap.py | 9834 | 283 | Generic IMAP email connector for any provider.
src/openjarvis/connectors/imessage.py | 10587 | 287 | iMessage connector — reads directly from the macOS Messages SQLite database.
src/openjarvis/connectors/news_rss.py | 13930 | 380 | News/RSS connector — aggregate headlines from RSS and Atom feeds.
src/openjarvis/connectors/notion.py | 15412 | 440 | Notion connector — syncs pages via the Notion REST API.
src/openjarvis/connectors/oauth.py | 24949 | 740 | Shared OAuth 2.0 helpers for all connectors.
src/openjarvis/connectors/obsidian.py | 8175 | 236 | Obsidian / Markdown vault connector.
src/openjarvis/connectors/oura.py | 3706 | 104 | Oura Ring connector — sleep, readiness, and activity via REST API v2.
src/openjarvis/connectors/outlook.py | 1865 | 59 | Outlook / Microsoft 365 connector — reads email via IMAP with app password.
src/openjarvis/connectors/pipeline.py | 13521 | 319 | IngestionPipeline — deduplicate, chunk, and store Documents.
src/openjarvis/connectors/retriever.py | 10242 | 302 | TwoStageRetriever — BM25 recall from KnowledgeStore + optional reranking.
src/openjarvis/connectors/scheduler.py | 5329 | 150 | SyncScheduler — background thread for periodic incremental connector syncs.
src/openjarvis/connectors/slack_connector.py | 27661 | 704 | Slack connector — bulk channel message sync via the Slack Web API.
src/openjarvis/connectors/spotify.py | 6006 | 164 | Spotify connector — recently played tracks via Spotify Web API.
src/openjarvis/connectors/store.py | 22656 | 586 | KnowledgeStore — source-aware SQLite/FTS5 memory backend for Deep Research.
src/openjarvis/connectors/strava.py | 6370 | 182 | Strava connector — recent activities via REST API v3.
src/openjarvis/connectors/sync_engine.py | 10743 | 289 | SyncEngine — checkpoint/resume orchestration for connector syncs.
src/openjarvis/connectors/weather.py | 9013 | 249 | Weather connector — current conditions and forecast via OpenWeatherMap API.
src/openjarvis/connectors/whatsapp.py | 11064 | 300 | WhatsApp chat export connector.
src/openjarvis/core/__init__.py | 937 | 48 | Core module — registries, types, configuration, and event bus.
src/openjarvis/core/config.py | 83326 | 2524 | Configuration loading, hardware detection, and engine recommendation.
src/openjarvis/core/credentials.py | 8044 | 232 | Credential persistence for tools and channels.
src/openjarvis/core/events.py | 7481 | 213 | Thread-safe pub/sub event bus for inter-primitive telemetry.
src/openjarvis/core/paths.py | 4907 | 123 | Central, env-aware resolution of OpenJarvis' home directory.
src/openjarvis/core/registry.py | 5769 | 190 | Decorator-based registry for runtime discovery of pluggable components.
src/openjarvis/core/types.py | 10550 | 318 | Canonical data types shared across all OpenJarvis primitives.
src/openjarvis/core/utils.py | 7054 | 194 | Small cross-platform utilities used by the CLI, OAuth flow, and evals.
src/openjarvis/daemon/__init__.py | 36 | 2 | 
src/openjarvis/daemon/gateway.py | 1078 | 40 | classes: GatewayDaemon
src/openjarvis/daemon/service.py | 1396 | 58 | 
src/openjarvis/daemon/session_expiry.py | 1233 | 34 | classes: SessionExpiryHook
src/openjarvis/engine/__init__.py | 1677 | 51 | Inference Engine primitive — LLM runtime management.
src/openjarvis/engine/_apple_fm_support.py | 5540 | 152 | Pure helpers for the Apple Foundation Models engine and shim.
src/openjarvis/engine/_async_loop.py | 2031 | 61 | Run an asyncio event loop on a background thread.
src/openjarvis/engine/_base.py | 4804 | 131 | Shared engine utilities and re-exports.
src/openjarvis/engine/_discovery.py | 9661 | 266 | Engine discovery — probe running engines and aggregate available models.
src/openjarvis/engine/_http_async.py | 5262 | 129 | Shared async-HTTP plumbing for engines that stream over httpx.
src/openjarvis/engine/_openai_compat.py | 14737 | 342 | Shared base for OpenAI-compatible ``/v1/`` engines.
src/openjarvis/engine/_stubs.py | 4669 | 141 | ABC for inference engine backends.
src/openjarvis/engine/apple_fm.py | 22898 | 581 | In-process Apple Foundation Models (AFM 3) engine.
src/openjarvis/engine/apple_fm_shim.py | 9093 | 269 | Apple Foundation Models shim.
src/openjarvis/engine/cloud.py | 82924 | 2117 | Cloud inference engine.
src/openjarvis/engine/gemma_cpp.py | 6426 | 180 | gemma.cpp inference engine backend via pygemma pybind11 bindings.
src/openjarvis/engine/litellm.py | 5009 | 151 | LiteLLM inference engine — unified access to 100+ LLM providers.
src/openjarvis/engine/multi.py | 4871 | 140 | Multi-engine wrapper — routes requests to the right backend by model name.
src/openjarvis/engine/nexa_shim.py | 4495 | 165 | Nexa SDK shim.
src/openjarvis/engine/nim.py | 10510 | 284 | NVIDIA NIM inference engine — self-hosted inference microservices.
src/openjarvis/engine/ollama.py | 23448 | 555 | Ollama inference engine backend.
src/openjarvis/engine/openai_compat_engines.py | 2385 | 62 | Data-driven registration of OpenAI-compatible inference engines.
src/openjarvis/evals/__init__.py | 40 | 2 | OpenJarvis Evaluation Framework.
src/openjarvis/evals/__main__.py | 139 | 7 | Allow running as ``python -m openjarvis.evals``.
src/openjarvis/evals/cli.py | 65543 | 1801 | CLI for the OpenJarvis evaluation framework.
src/openjarvis/evals/skill_benchmark.py | 19539 | 509 | SkillBenchmarkRunner — orchestrate the 4-condition × N-seed × M-task
src/openjarvis/evals/backends/__init__.py | 42 | 2 | Inference backends for evaluation.
src/openjarvis/evals/backends/_commit_util.py | 1032 | 35 | Shared helper for resolving the openjarvis repo's HEAD commit.
src/openjarvis/evals/backends/_endpoint_util.py | 1743 | 53 | Shared helper for targeting an explicit OpenAI-compatible endpoint.
src/openjarvis/evals/backends/jarvis_agent.py | 9091 | 224 | Jarvis Agent backend — agent-level inference with tool calling.
src/openjarvis/evals/backends/jarvis_direct.py | 5487 | 148 | Jarvis Direct backend — engine-level inference for local and cloud models.
src/openjarvis/evals/backends/tb_agent.py | 957 | 33 | Custom terminal-bench agent that wraps NaiveAgent with LiteLLM construction.
src/openjarvis/evals/backends/terminalbench_native.py | 10715 | 278 | Native TerminalBench V2.1 backend.
src/openjarvis/evals/backends/external/__init__.py | 272 | 7 | External-framework subprocess backends (Hermes Agent, OpenClaw).
src/openjarvis/evals/backends/external/_subprocess_runner.py | 10013 | 325 | Shared one-shot subprocess invocation with energy/timing capture.
src/openjarvis/evals/backends/external/hermes_agent.py | 4246 | 135 | HermesBackend - runs real Hermes Agent as a subprocess per task.
src/openjarvis/evals/backends/external/openclaw.py | 3730 | 123 | OpenClawBackend - runs real OpenClaw as a Node subprocess per task.
src/openjarvis/evals/backends/external/_runners/__init__.py | 232 | 7 | Subprocess bridge scripts for foreign-framework evaluation backends.
src/openjarvis/evals/backends/external/_runners/hermes_runner.py | 7822 | 201 | Subprocess bridge: runs one task through real Hermes Agent and emits JSON.
src/openjarvis/evals/backends/external/_runners/openclaw_runner.mjs | 4882 | 143 | 
src/openjarvis/evals/comparison/__init__.py | 190 | 6 | Framework-comparison toolkit.
src/openjarvis/evals/comparison/make_configs.py | 6407 | 208 | CLI for generating framework-comparison eval configs from `_template.toml`.
src/openjarvis/evals/comparison/table_gen.py | 14089 | 425 | LaTeX table generator for the framework-comparison harness.
src/openjarvis/evals/comparison/third_party.py | 6157 | 171 | Path resolution and commit-pin verification for foreign frameworks.
src/openjarvis/evals/configs/deepplanning-monitor-operative.toml | 1003 | 43 | 
src/openjarvis/evals/configs/full-suite.toml | 1073 | 64 | 
src/openjarvis/evals/configs/gaia-gemini-31-pro.toml | 596 | 30 | 
src/openjarvis/evals/configs/gaia-gemma4-26b.toml | 652 | 32 | 
src/openjarvis/evals/configs/gaia-gpt54.toml | 581 | 30 | 
src/openjarvis/evals/configs/gaia-nemotron-nano.toml | 718 | 31 | 
src/openjarvis/evals/configs/gaia-nemotron-super.toml | 686 | 31 | 
src/openjarvis/evals/configs/gaia-nemotron3-super.toml | 656 | 32 | 
src/openjarvis/evals/configs/gaia-qwen-122b.toml | 622 | 31 | 
src/openjarvis/evals/configs/gaia-qwen-27b.toml | 646 | 31 | 
src/openjarvis/evals/configs/gaia-qwen-2b.toml | 616 | 31 | 
src/openjarvis/evals/configs/gaia-qwen-35b.toml | 614 | 31 | 
src/openjarvis/evals/configs/gaia-qwen-9b.toml | 618 | 32 | 
src/openjarvis/evals/configs/gaia-qwen122b.toml | 611 | 31 | 
src/openjarvis/evals/configs/gaia-qwen35b.toml | 603 | 31 | 
src/openjarvis/evals/configs/gaia-rerun-claude-opus.toml | 618 | 30 | 
src/openjarvis/evals/configs/gaia-rerun-claude-sonnet.toml | 628 | 30 | 
src/openjarvis/evals/configs/gaia-rerun-glm47flash.toml | 647 | 31 | 
src/openjarvis/evals/configs/gaia-rerun-gpt5mini.toml | 630 | 30 | 
src/openjarvis/evals/configs/gaia-rerun-minimax-m25.toml | 652 | 31 | 
src/openjarvis/evals/configs/gaia-rerun-qwen122b.toml | 696 | 33 | 
src/openjarvis/evals/configs/gaia-rerun-qwen35b.toml | 650 | 31 | 
src/openjarvis/evals/configs/gaia-rerun-qwen397b.toml | 658 | 31 | 
src/openjarvis/evals/configs/gaia-trinity-large.toml | 939 | 35 | 
src/openjarvis/evals/configs/glm-4.7-flash-openhands-remaining.toml | 1338 | 61 | 
src/openjarvis/evals/configs/glm-4.7-flash-openhands.toml | 1849 | 70 | 
src/openjarvis/evals/configs/glm-4.7-fp8-openhands-gaia.toml | 1152 | 44 | 
src/openjarvis/evals/configs/glm5-fp8-monitor-operative.toml | 1976 | 75 | 
src/openjarvis/evals/configs/kimi-k2.5-monitor-operative.toml | 2066 | 75 | 
src/openjarvis/evals/configs/livecodebench-claude-opus.toml | 659 | 31 | 
src/openjarvis/evals/configs/livecodebench-gemma4-26b.toml | 646 | 31 | 
src/openjarvis/evals/configs/livecodebench-gemma4-e4b.toml | 636 | 31 | 
src/openjarvis/evals/configs/livecodebench-kimi-k25.toml | 1115 | 40 | 
src/openjarvis/evals/configs/livecodebench-minimax-m25.toml | 1015 | 37 | 
src/openjarvis/evals/configs/livecodebench-nemotron-nano.toml | 702 | 31 | 
src/openjarvis/evals/configs/livecodebench-nemotron-super.toml | 623 | 29 | 
src/openjarvis/evals/configs/livecodebench-qwen-122b.toml | 559 | 29 | 
src/openjarvis/evals/configs/livecodebench-qwen-27b.toml | 629 | 31 | 
src/openjarvis/evals/configs/livecodebench-qwen-2b.toml | 614 | 31 | 
src/openjarvis/evals/configs/livecodebench-qwen-35b.toml | 551 | 29 | 
src/openjarvis/evals/configs/livecodebench-qwen-9b.toml | 614 | 31 | 
src/openjarvis/evals/configs/liveresearch-claude-opus.toml | 633 | 30 | 
src/openjarvis/evals/configs/liveresearch-gemini-31-pro.toml | 654 | 30 | 
src/openjarvis/evals/configs/liveresearch-gemma4-26b.toml | 698 | 32 | 
src/openjarvis/evals/configs/liveresearch-gemma4-31b.toml | 651 | 31 | 
src/openjarvis/evals/configs/liveresearch-gpt54.toml | 626 | 30 | 
src/openjarvis/evals/configs/liveresearch-granite-3.3-8b-lora.toml | 669 | 31 | 
src/openjarvis/evals/configs/liveresearch-granite-3.3-8b.toml | 701 | 31 | 
src/openjarvis/evals/configs/liveresearch-granite-4.0-h-small.toml | 699 | 31 | 
src/openjarvis/evals/configs/liveresearch-granite-4.0-micro.toml | 689 | 31 | 
src/openjarvis/evals/configs/liveresearch-nemotron-nano.toml | 768 | 31 | 
src/openjarvis/evals/configs/liveresearch-nemotron-super.toml | 727 | 31 | 
src/openjarvis/evals/configs/liveresearch-qwen-122b.toml | 663 | 31 | 
src/openjarvis/evals/configs/liveresearch-qwen-27b-lora-r32.toml | 697 | 31 | 
src/openjarvis/evals/configs/liveresearch-qwen-27b.toml | 696 | 31 | 
src/openjarvis/evals/configs/liveresearch-qwen-2b-lora-r16.toml | 705 | 32 | 
src/openjarvis/evals/configs/liveresearch-qwen-2b-lora-r32.toml | 705 | 32 | 
src/openjarvis/evals/configs/liveresearch-qwen-2b-mixed.toml | 690 | 32 | 
src/openjarvis/evals/configs/liveresearch-qwen-2b-trackb.toml | 695 | 32 | 
src/openjarvis/evals/configs/liveresearch-qwen-2b.toml | 664 | 32 | 
src/openjarvis/evals/configs/liveresearch-qwen-35b.toml | 655 | 31 | 
src/openjarvis/evals/configs/liveresearch-qwen-9b-lora-r32.toml | 705 | 32 | 
src/openjarvis/evals/configs/liveresearch-qwen-9b-mixed.toml | 690 | 32 | 
src/openjarvis/evals/configs/liveresearch-qwen-9b-trackb.toml | 695 | 32 | 
src/openjarvis/evals/configs/liveresearch-qwen-9b.toml | 664 | 32 | 
src/openjarvis/evals/configs/liveresearch-trinity-large.toml | 1002 | 35 | 
src/openjarvis/evals/configs/liveresearchbench-qwen-27b.toml | 660 | 32 | 
src/openjarvis/evals/configs/liveresearchbench-qwen-2b.toml | 643 | 32 | 
src/openjarvis/evals/configs/liveresearchbench-qwen-9b.toml | 643 | 32 | 
src/openjarvis/evals/configs/long-horizon-claude-opus.toml | 1122 | 52 | 
src/openjarvis/evals/configs/long-horizon-claude-sonnet.toml | 1132 | 52 | 
src/openjarvis/evals/configs/long-horizon-glm47flash.toml | 1301 | 59 | 
src/openjarvis/evals/configs/long-horizon-gpt5mini.toml | 1101 | 52 | 
src/openjarvis/evals/configs/long-horizon-kimik25.toml | 1382 | 61 | 
src/openjarvis/evals/configs/long-horizon-minimax-m25.toml | 1293 | 59 | 
src/openjarvis/evals/configs/long-horizon-qwen122b.toml | 1305 | 59 | 
src/openjarvis/evals/configs/long-horizon-qwen35b.toml | 1295 | 59 | 
src/openjarvis/evals/configs/long-horizon-qwen397b.toml | 1301 | 59 | 
src/openjarvis/evals/configs/minimal.toml | 134 | 8 | 
src/openjarvis/evals/configs/paperarena-monitor-operative.toml | 984 | 43 | 
src/openjarvis/evals/configs/pinchbench-claude-opus.toml | 803 | 36 | 
src/openjarvis/evals/configs/pinchbench-gemini-31-pro.toml | 828 | 36 | 
src/openjarvis/evals/configs/pinchbench-gemma4-26b.toml | 837 | 36 | 
src/openjarvis/evals/configs/pinchbench-gemma4-e4b.toml | 827 | 36 | 
src/openjarvis/evals/configs/pinchbench-gpt54.toml | 748 | 35 | 
src/openjarvis/evals/configs/pinchbench-kimi-k25.toml | 1305 | 45 | 
src/openjarvis/evals/configs/pinchbench-minimax-m25.toml | 1205 | 42 | 
src/openjarvis/evals/configs/pinchbench-nemotron-nano.toml | 893 | 36 | 
src/openjarvis/evals/configs/pinchbench-nemotron-super.toml | 831 | 35 | 
src/openjarvis/evals/configs/pinchbench-nemotron3-super.toml | 838 | 36 | 
src/openjarvis/evals/configs/pinchbench-qwen-122b.toml | 767 | 35 | 
src/openjarvis/evals/configs/pinchbench-qwen-27b.toml | 820 | 36 | 
src/openjarvis/evals/configs/pinchbench-qwen-2b.toml | 805 | 36 | 
src/openjarvis/evals/configs/pinchbench-qwen-35b.toml | 759 | 35 | 
src/openjarvis/evals/configs/pinchbench-qwen-9b.toml | 805 | 36 | 
src/openjarvis/evals/configs/pinchbench-qwen122b.toml | 815 | 36 | 
src/openjarvis/evals/configs/pinchbench-qwen35b.toml | 807 | 36 | 
src/openjarvis/evals/configs/pinchbench-qwen397b.toml | 815 | 36 | 
src/openjarvis/evals/configs/pinchbench.toml | 554 | 27 | 
src/openjarvis/evals/configs/qwen3.5-122b-kg-agentic.toml | 1038 | 43 | 
src/openjarvis/evals/configs/qwen3.5-122b-kg-hightoken.toml | 941 | 39 | 
src/openjarvis/evals/configs/qwen3.5-122b-reasoning-suite.toml | 1147 | 52 | 
src/openjarvis/evals/configs/qwen3.5-35b-kg.toml | 819 | 39 | 
src/openjarvis/evals/configs/qwen3.5-35b-monitor-operative.toml | 1742 | 58 | 
src/openjarvis/evals/configs/qwen3.5-397b-monitor-operative.toml | 1386 | 43 | 
src/openjarvis/evals/configs/single-run.toml | 566 | 32 | 
src/openjarvis/evals/configs/smoke_amd.toml | 3232 | 107 | 
src/openjarvis/evals/configs/smoke_apple.toml | 2213 | 80 | 
src/openjarvis/evals/configs/smoke_nvidia.toml | 3300 | 113 | 
src/openjarvis/evals/configs/taubench-claude-opus.toml | 585 | 30 | 
src/openjarvis/evals/configs/taubench-gemini-31-pro.toml | 651 | 31 | 
src/openjarvis/evals/configs/taubench-gemma4-26b.toml | 660 | 32 | 
src/openjarvis/evals/configs/taubench-gemma4-e4b.toml | 650 | 32 | 
src/openjarvis/evals/configs/taubench-gpt54.toml | 571 | 30 | 
src/openjarvis/evals/configs/taubench-kimi-k25.toml | 1128 | 41 | 
src/openjarvis/evals/configs/taubench-minimax-m25.toml | 1028 | 38 | 
src/openjarvis/evals/configs/taubench-nemotron-nano.toml | 716 | 32 | 
src/openjarvis/evals/configs/taubench-nemotron-super.toml | 624 | 30 | 
src/openjarvis/evals/configs/taubench-nemotron3-super.toml | 593 | 30 | 
src/openjarvis/evals/configs/taubench-qwen-122b.toml | 560 | 30 | 
src/openjarvis/evals/configs/taubench-qwen-27b.toml | 643 | 32 | 
src/openjarvis/evals/configs/taubench-qwen-2b.toml | 628 | 32 | 
src/openjarvis/evals/configs/taubench-qwen-35b.toml | 552 | 30 | 
src/openjarvis/evals/configs/taubench-qwen-9b.toml | 628 | 32 | 
src/openjarvis/evals/configs/taubench-qwen122b.toml | 557 | 29 | 
src/openjarvis/evals/configs/taubench-qwen35b.toml | 549 | 29 | 
src/openjarvis/evals/configs/taubench-qwen397b.toml | 621 | 31 | 
src/openjarvis/evals/configs/taubench-telecom-claude.toml | 519 | 28 | 
src/openjarvis/evals/configs/taubench-telecom-gemma4-26b.toml | 604 | 30 | 
src/openjarvis/evals/configs/taubench-telecom-gpt54.toml | 504 | 28 | 
src/openjarvis/evals/configs/taubench-telecom-nemotron-nano.toml | 657 | 29 | 
src/openjarvis/evals/configs/taubench-telecom-nemotron-super.toml | 633 | 30 | 
src/openjarvis/evals/configs/taubench-telecom-nemotron.toml | 550 | 29 | 
src/openjarvis/evals/configs/taubench-telecom-qwen-122b.toml | 569 | 30 | 
src/openjarvis/evals/configs/taubench-telecom-qwen-27b.toml | 584 | 29 | 
src/openjarvis/evals/configs/taubench-telecom-qwen-35b.toml | 561 | 30 | 
src/openjarvis/evals/configs/taubench-telecom-qwen27b.toml | 586 | 30 | 
src/openjarvis/evals/configs/taubench-telecom-qwen2b.toml | 569 | 30 | 
src/openjarvis/evals/configs/taubench-telecom-qwen9b.toml | 569 | 30 | 
src/openjarvis/evals/configs/taubench-telecom-trinity-large.toml | 654 | 29 | 
src/openjarvis/evals/configs/terminalbench-native-qwen122b.toml | 636 | 31 | 
src/openjarvis/evals/configs/terminalbench-qwen122b.toml | 663 | 31 | 
src/openjarvis/evals/configs/toolcall15-claude-opus.toml | 563 | 29 | 
src/openjarvis/evals/configs/toolcall15-gemma4-26b.toml | 625 | 30 | 
src/openjarvis/evals/configs/toolcall15-gemma4-e4b.toml | 614 | 30 | 
src/openjarvis/evals/configs/toolcall15-kimi-k25.toml | 1090 | 39 | 
src/openjarvis/evals/configs/toolcall15-minimax-m25.toml | 990 | 36 | 
src/openjarvis/evals/configs/toolcall15-nemotron-nano.toml | 680 | 30 | 
src/openjarvis/evals/configs/toolcall15-nemotron-super.toml | 608 | 29 | 
src/openjarvis/evals/configs/toolcall15-qwen-122b.toml | 544 | 29 | 
src/openjarvis/evals/configs/toolcall15-qwen-27b.toml | 608 | 30 | 
src/openjarvis/evals/configs/toolcall15-qwen-2b.toml | 592 | 30 | 
src/openjarvis/evals/configs/toolcall15-qwen-35b.toml | 536 | 29 | 
src/openjarvis/evals/configs/toolcall15-qwen-9b.toml | 592 | 30 | 
src/openjarvis/evals/configs/use_case_cloud_comparison.toml | 1662 | 79 | 
src/openjarvis/evals/configs/use_case_cloud_openhands.toml | 1960 | 94 | 
src/openjarvis/evals/configs/use_case_cloud_orchestrator.toml | 1898 | 94 | 
src/openjarvis/evals/configs/use_case_direct.toml | 927 | 48 | 
src/openjarvis/evals/configs/use_case_ibm_granite.toml | 1086 | 57 | 
src/openjarvis/evals/configs/use_case_openhands.toml | 1177 | 58 | 
src/openjarvis/evals/configs/use_case_opensource_openhands.toml | 2241 | 102 | 
src/openjarvis/evals/configs/use_case_opensource_orchestrator.toml | 2179 | 102 | 
src/openjarvis/evals/configs/use_case_orchestrator.toml | 1151 | 58 | 
src/openjarvis/evals/configs/use_case_react.toml | 1150 | 58 | 
src/openjarvis/evals/configs/use_case_suite.toml | 915 | 49 | 
src/openjarvis/evals/configs/use_case_v2_cloud.toml | 1052 | 65 | 
src/openjarvis/evals/configs/use_case_v2_granite.toml | 894 | 53 | 
src/openjarvis/evals/configs/use_case_v2_local.toml | 983 | 61 | 
src/openjarvis/evals/configs/use_case_v2_suite.toml | 1253 | 58 | 
src/openjarvis/evals/configs/framework_comparison/_template.toml | 1374 | 50 | 
src/openjarvis/evals/configs/framework_comparison/_third_party.toml | 1073 | 28 | 
src/openjarvis/evals/core/__init__.py | 39 | 2 | Core evaluation types and ABCs.
src/openjarvis/evals/core/agentic_runner.py | 37140 | 905 | AgenticRunner — multi-turn agent execution with energy telemetry correlation.
src/openjarvis/evals/core/backend.py | 1576 | 56 | Abstract base class for inference backends.
src/openjarvis/evals/core/config.py | 13353 | 368 | TOML config loader and matrix expansion for eval suites.
src/openjarvis/evals/core/dataset.py | 1797 | 63 | Abstract base class for dataset providers.
src/openjarvis/evals/core/display.py | 15779 | 454 | Rich display helpers for the evaluation framework and bench CLI.
src/openjarvis/evals/core/environment.py | 2175 | 68 | Environment provider ABC for benchmarks requiring external environments.
src/openjarvis/evals/core/event_recorder.py | 3000 | 99 | Event recording system for agent execution telemetry.
src/openjarvis/evals/core/export.py | 18135 | 506 | Export functions for agentic run traces and profiling records.
src/openjarvis/evals/core/pricing.py | 609 | 18 | Cost computation for agentic eval runs — wraps engine/cloud.py pricing.
src/openjarvis/evals/core/runner.py | 62334 | 1424 | EvalRunner — parallel execution of evaluation samples.
src/openjarvis/evals/core/scorer.py | 1500 | 56 | Abstract base classes for scoring.
src/openjarvis/evals/core/splits.py | 1210 | 41 | Deterministic train/test split helper used by dataset providers.
src/openjarvis/evals/core/trace.py | 15013 | 356 | Trace data model for agentic eval runs.
src/openjarvis/evals/core/tracker.py | 992 | 35 | ResultTracker ABC for external experiment tracking.
src/openjarvis/evals/core/types.py | 11526 | 329 | Core data types for the evaluation framework.
src/openjarvis/evals/datasets/__init__.py | 52 | 2 | Dataset providers for evaluation benchmarks.
src/openjarvis/evals/datasets/adp.py | 7490 | 208 | Agent Data Collection (neulab) — external agent-trajectory corpus.
src/openjarvis/evals/datasets/ama_bench.py | 10082 | 273 | AMA-Bench dataset loader.
src/openjarvis/evals/datasets/browser_assistant.py | 16968 | 446 | browser_assistant dataset — 30 web research tasks.
src/openjarvis/evals/datasets/coding_assistant.py | 67037 | 1633 | coding_assistant dataset — 30 buggy code projects for agent-based debugging.
src/openjarvis/evals/datasets/coding_task.py | 29948 | 285 | Coding task benchmark dataset.
src/openjarvis/evals/datasets/daily_digest.py | 37752 | 689 | daily_digest dataset — 30 realistic workday briefing tasks.
src/openjarvis/evals/datasets/deepplanning.py | 8759 | 237 | DeepPlanning: long-horizon planning with constraints.
src/openjarvis/evals/datasets/doc_qa.py | 70590 | 1107 | doc_qa dataset — 30 document-grounded QA tasks.
src/openjarvis/evals/datasets/email_triage.py | 16214 | 335 | Email triage benchmark dataset.
src/openjarvis/evals/datasets/frames.py | 4457 | 142 | FRAMES benchmark dataset (google/frames-benchmark).
src/openjarvis/evals/datasets/gaia.py | 5893 | 180 | GAIA benchmark dataset (gaia-benchmark/GAIA).
src/openjarvis/evals/datasets/generalthoughts.py | 4151 | 119 | GeneralThought-430K (filtered) — external reasoning corpus.
src/openjarvis/evals/datasets/gpqa.py | 4256 | 147 | GPQA dataset provider (Idavidrein/gpqa).
src/openjarvis/evals/datasets/hle.py | 4056 | 136 | HLE dataset provider (cais/hle).
src/openjarvis/evals/datasets/ipw_mixed.py | 6668 | 196 | IPW mixed dataset provider.
src/openjarvis/evals/datasets/knowledge_base.py | 23367 | 228 | Knowledge base benchmark dataset.
src/openjarvis/evals/datasets/lifelong_agent.py | 20273 | 518 | LifelongAgentBench dataset loader.
src/openjarvis/evals/datasets/livecodebench.py | 10160 | 287 | LiveCodeBench dataset provider — competitive programming code generation.
src/openjarvis/evals/datasets/liveresearch.py | 7135 | 199 | DeepResearchBench dataset provider — deep research benchmark.
src/openjarvis/evals/datasets/liveresearchbench.py | 7039 | 191 | LiveResearchBench dataset provider — Salesforce's checklist-based benchmark.
src/openjarvis/evals/datasets/loghub.py | 8748 | 260 | LogHub log anomaly detection dataset.
src/openjarvis/evals/datasets/math500.py | 3072 | 111 | MATH-500 dataset provider (HuggingFaceH4/MATH-500).
src/openjarvis/evals/datasets/mmlu_pro.py | 3318 | 116 | MMLU-Pro dataset provider (TIGER-Lab/MMLU-Pro).
src/openjarvis/evals/datasets/morning_brief.py | 14447 | 218 | Morning brief benchmark dataset.
src/openjarvis/evals/datasets/natural_reasoning.py | 3316 | 116 | Natural Reasoning dataset provider (facebook/natural_reasoning).
src/openjarvis/evals/datasets/paperarena.py | 5862 | 171 | PaperArena: scientific literature reasoning benchmark.
src/openjarvis/evals/datasets/pinchbench.py | 8190 | 221 | PinchBench dataset provider — real-world agent task benchmark.
src/openjarvis/evals/datasets/research_mining.py | 14363 | 267 | Research mining benchmark dataset.
src/openjarvis/evals/datasets/security_scanner.py | 41904 | 1075 | security_scanner dataset — 30 vulnerable code projects for security auditing.
src/openjarvis/evals/datasets/simpleqa.py | 3851 | 130 | SimpleQA dataset provider (basicv8vc/SimpleQA).
src/openjarvis/evals/datasets/supergpqa.py | 3743 | 129 | SuperGPQA dataset provider (m-a-p/SuperGPQA).
src/openjarvis/evals/datasets/swebench.py | 5607 | 175 | SWE-bench dataset (princeton-nlp/SWE-bench_Verified).
src/openjarvis/evals/datasets/swefficiency.py | 5343 | 174 | SWEfficiency dataset (swefficiency/swefficiency).
src/openjarvis/evals/datasets/taubench.py | 10375 | 276 | TauBench V2 dataset provider — multi-turn customer service benchmark.
src/openjarvis/evals/datasets/terminalbench.py | 3546 | 124 | TerminalBench dataset (terminal-bench/terminal-bench).
src/openjarvis/evals/datasets/terminalbench_native.py | 6185 | 188 | TerminalBench Native dataset — loads from the terminal-bench pip package (v2 API).
src/openjarvis/evals/datasets/terminalbench_v2_1.py | 9014 | 243 | TerminalBench V2.1 dataset provider.
src/openjarvis/evals/datasets/toolcall15.py | 24953 | 724 | ToolCall-15 dataset provider — lightweight tool calling benchmark.
src/openjarvis/evals/datasets/toolorchestra.py | 6135 | 172 | ToolScale (nvidia) — external tool-use corpus.
src/openjarvis/evals/datasets/webchorearena.py | 9350 | 268 | WebChoreArena: Realistic tedious web browsing tasks.
src/openjarvis/evals/datasets/wildchat.py | 3447 | 112 | WildChat dataset provider (allenai/WildChat-1M).
src/openjarvis/evals/datasets/workarena.py | 8325 | 258 | WorkArena++ enterprise workflow benchmark on ServiceNow.
src/openjarvis/evals/environments/__init__.py | 163 | 6 | Task environments for interactive multi-turn evaluation.
src/openjarvis/evals/environments/base.py | 5272 | 155 | Abstract base for multi-turn task environments.
src/openjarvis/evals/environments/lifelong_agent_env.py | 44508 | 1186 | Multi-turn task environments for LifelongAgentBench.
src/openjarvis/evals/execution/__init__.py | 58 | 2 | Execution environments for agentic eval workloads.
src/openjarvis/evals/execution/pinchbench_env.py | 6110 | 162 | PinchBench task environment — per-task workspace setup and grading.
src/openjarvis/evals/execution/taubench_env.py | 14536 | 410 | TauBench task environment — native OpenJarvis agent in tau2 simulation.
src/openjarvis/evals/execution/terminalbench_env.py | 12409 | 301 | TerminalBench task environment — per-task Docker lifecycle + test execution.
src/openjarvis/evals/execution/terminalbench_v2_1_env.py | 4293 | 124 | TerminalBench V2.1 task environment.
src/openjarvis/evals/execution/webchorearena_env.py | 29320 | 778 | WebChoreArena task environment — Playwright-based browser interaction.
src/openjarvis/evals/execution/workarena_env.py | 17132 | 497 | WorkArena task environment — per-task BrowserGym lifecycle + validation.
src/openjarvis/evals/scorers/__init__.py | 58 | 2 | Scoring implementations for evaluation benchmarks.
src/openjarvis/evals/scorers/_checklist.py | 5360 | 173 | Shared binary checklist scorer and text normalization utilities.
src/openjarvis/evals/scorers/ama_bench_judge.py | 5242 | 160 | LLM-judge scorer for AMA-Bench agent memory assessment.
src/openjarvis/evals/scorers/browser_assistant.py | 8305 | 237 | browser_assistant scorer — exact match, semantic checklist, and source check.
src/openjarvis/evals/scorers/coding_assistant.py | 5679 | 173 | coding_assistant scorer — test-based evaluation of bug fixes.
src/openjarvis/evals/scorers/coding_task.py | 4400 | 143 | Coding task scorer — test pass rate + structural validation.
src/openjarvis/evals/scorers/daily_digest.py | 5808 | 170 | daily_digest scorer — phrase match, ordering, and checklist evaluation.
src/openjarvis/evals/scorers/deepplanning_scorer.py | 2583 | 90 | LLM-judge scorer for DeepPlanning constraint satisfaction.
src/openjarvis/evals/scorers/doc_qa.py | 6203 | 187 | doc_qa scorer — fact match, citation check, and checklist evaluation.
src/openjarvis/evals/scorers/email_triage.py | 4532 | 137 | Email triage scorer — classification accuracy + draft quality.
src/openjarvis/evals/scorers/frames_judge.py | 3639 | 106 | FRAMES scorer — LLM-as-judge for multi-hop factual retrieval.
src/openjarvis/evals/scorers/gaia_exact.py | 5765 | 168 | GAIA scorer — normalized exact match with LLM fallback.
src/openjarvis/evals/scorers/gpqa_mcq.py | 3237 | 107 | GPQA MCQ scorer — LLM-based letter extraction + exact match.
src/openjarvis/evals/scorers/hle_judge.py | 3390 | 103 | HLE scorer -- LLM-as-judge for Humanity's Last Exam.
src/openjarvis/evals/scorers/ipw_mixed.py | 3939 | 112 | IPW mixed scorer -- LLM-as-judge for mixed-source evaluation datasets.
src/openjarvis/evals/scorers/knowledge_base.py | 3965 | 119 | Knowledge base scorer — answer correctness via normalized match + LLM fallback.
src/openjarvis/evals/scorers/lifelong_agent_scorer.py | 32069 | 932 | Scorer for LifelongAgentBench.
src/openjarvis/evals/scorers/livecodebench.py | 8231 | 257 | LiveCodeBench scorer — sandboxed code execution with test cases.
src/openjarvis/evals/scorers/liveresearch.py | 14984 | 433 | DeepResearchBench scorer — LLM-as-judge for deep research quality.
src/openjarvis/evals/scorers/liveresearchbench.py | 7369 | 229 | LiveResearchBench scorer — checklist-based LLM-as-judge scoring.
src/openjarvis/evals/scorers/loghub_scorer.py | 3077 | 84 | Scorer for LogHub log anomaly detection benchmark.
src/openjarvis/evals/scorers/mmlu_pro_mcq.py | 3248 | 107 | MMLU-Pro MCQ scorer — LLM-based letter extraction + exact match.
src/openjarvis/evals/scorers/morning_brief.py | 4225 | 129 | Morning brief scorer — LLM judge for briefing quality.
src/openjarvis/evals/scorers/paperarena_judge.py | 5288 | 163 | Scorer for PaperArena: MC exact match + LLM judge for CA/OA.
src/openjarvis/evals/scorers/pinchbench.py | 19708 | 579 | PinchBench grading helpers and scorer.
src/openjarvis/evals/scorers/reasoning_judge.py | 5334 | 167 | Reasoning judge scorer -- LLM-as-judge for math and reasoning tasks.
src/openjarvis/evals/scorers/research_mining.py | 3401 | 110 | Research mining scorer — LLM judge for research synthesis quality.
src/openjarvis/evals/scorers/security_scanner.py | 9517 | 264 | security_scanner scorer — vulnerability detection evaluation.
src/openjarvis/evals/scorers/simpleqa_judge.py | 4733 | 143 | SimpleQA scorer -- normalized exact match with LLM fallback.
src/openjarvis/evals/scorers/supergpqa_mcq.py | 3262 | 107 | SuperGPQA MCQ scorer — LLM-based letter extraction + exact match.
src/openjarvis/evals/scorers/swebench_harness.py | 22078 | 575 | SWE-bench harness scorer — runs the official `swebench` test harness.
src/openjarvis/evals/scorers/swebench_structural.py | 2189 | 72 | SWE-bench scorer — structural patch validation.
src/openjarvis/evals/scorers/swefficiency_structural.py | 2258 | 73 | SWEfficiency scorer — structural patch validation.
src/openjarvis/evals/scorers/taubench.py | 1531 | 49 | TauBench scorer — wraps tau2-bench's evaluation results.
src/openjarvis/evals/scorers/terminalbench_judge.py | 3882 | 110 | TerminalBench scorer — LLM-as-judge for terminal task evaluation.
src/openjarvis/evals/scorers/terminalbench_native_structural.py | 2347 | 70 | TerminalBench Native scorer — test-result-based evaluation.
src/openjarvis/evals/scorers/terminalbench_v2_1.py | 9055 | 259 | TerminalBench V2.1 scorer.
src/openjarvis/evals/scorers/toolcall15.py | 21498 | 607 | ToolCall-15 scorer — deterministic tool-calling evaluation.
src/openjarvis/evals/scorers/webchorearena_scorer.py | 3361 | 95 | Scorer for WebChoreArena web chore tasks.
src/openjarvis/evals/scorers/wildchat_judge.py | 5596 | 174 | WildChat scorer — dual-comparison LLM-as-judge.
src/openjarvis/evals/scorers/workarena_scorer.py | 2949 | 89 | Scorer for WorkArena++ enterprise workflow tasks.
src/openjarvis/evals/tests/__init__.py | 43 | 2 | Tests for the evaluation framework.
src/openjarvis/evals/tests/conftest.py | 4089 | 155 | Shared test fixtures for the evaluation framework.
src/openjarvis/evals/tests/test_backends.py | 11873 | 288 | Tests for backend construction with mocks.
src/openjarvis/evals/tests/test_cli_endpoint.py | 7549 | 191 | --base-url/--api-key forwarding through the eval CLI plumbing.
src/openjarvis/evals/tests/test_cli_flags.py | 549 | 20 | Tests for eval CLI display flags.
src/openjarvis/evals/tests/test_config.py | 23895 | 720 | Tests for eval suite config loading and matrix expansion.
src/openjarvis/evals/tests/test_display.py | 4808 | 153 | Tests for eval display functions.
src/openjarvis/evals/tests/test_frames.py | 3763 | 112 | Tests for FRAMES scorer (judge prompt formatting and verdict parsing).
src/openjarvis/evals/tests/test_gaia.py | 4562 | 139 | Tests for GAIA scorer logic (normalization and exact match).
src/openjarvis/evals/tests/test_runner.py | 15222 | 466 | Tests for the EvalRunner.
src/openjarvis/evals/tests/test_supergpqa.py | 3650 | 106 | Tests for SuperGPQA scorer logic.
src/openjarvis/evals/tests/test_types.py | 13785 | 445 | Tests for core data types.
src/openjarvis/evals/tests/test_wildchat.py | 4557 | 118 | Tests for WildChat scorer (verdict parsing and dual comparison).
src/openjarvis/evals/trackers/__init__.py | 708 | 24 | External experiment trackers for the eval framework.
src/openjarvis/evals/trackers/sheets_tracker.py | 5290 | 165 | Google Sheets experiment tracker for the eval framework.
src/openjarvis/evals/trackers/wandb_tracker.py | 5794 | 158 | W&B experiment tracker for the eval framework.
src/openjarvis/intelligence/__init__.py | 420 | 18 | Intelligence primitive — the model definition and catalog.
src/openjarvis/intelligence/model_catalog.py | 42187 | 1234 | Built-in model catalog with well-known ModelSpec entries.
src/openjarvis/learning/__init__.py | 2684 | 91 | Learning primitive -- router policies, reward functions, learning.
src/openjarvis/learning/_stubs.py | 2096 | 79 | Learning primitive ABCs -- router policies, reward functions, learning policies.
src/openjarvis/learning/learning_orchestrator.py | 10085 | 257 | LearningOrchestrator — coordinate the full trace->learn->eval loop.
src/openjarvis/learning/agents/__init__.py | 115 | 4 | Agent learning — config optimization via DSPy, GEPA, and evolution.
src/openjarvis/learning/agents/ace_optimizer.py | 8957 | 244 | ACE agent optimizer — context evolution via the ACE Generator /
src/openjarvis/learning/agents/agent_evolver.py | 13100 | 366 | AgentConfigEvolver — analyze traces to evolve agent TOML configs.
src/openjarvis/learning/agents/dspy_optimizer.py | 7768 | 212 | DSPy agent optimizer -- programmatic pipeline optimization.
src/openjarvis/learning/agents/gepa_optimizer.py | 11887 | 327 | GEPA agent optimizer -- Pareto-efficient evolutionary optimization.
src/openjarvis/learning/agents/skill_discovery.py | 7699 | 205 | Skill discovery -- mine recurring tool sequences from traces.
src/openjarvis/learning/agents/skill_optimizer.py | 11902 | 315 | SkillOptimizer — per-skill DSPy/GEPA optimization wrapper (Plan 2A).
src/openjarvis/learning/intelligence/__init__.py | 428 | 14 | Intelligence learning — model fine-tuning via SFT and GRPO.
src/openjarvis/learning/intelligence/grpo_trainer.py | 12850 | 374 | General-purpose GRPO trainer -- Group Relative Policy Optimization.
src/openjarvis/learning/intelligence/sft_trainer.py | 5192 | 148 | General-purpose SFT trainer -- fine-tune any local LM on trace-derived pairs.
src/openjarvis/learning/intelligence/orchestrator/__init__.py | 2617 | 88 | Orchestrator training infrastructure — SFT and GRPO pipelines.
src/openjarvis/learning/intelligence/orchestrator/environment.py | 4119 | 130 | RL environment for orchestrator training.
src/openjarvis/learning/intelligence/orchestrator/grpo_trainer.py | 16991 | 492 | GRPO (Group Relative Policy Optimization) trainer for orchestrator.
src/openjarvis/learning/intelligence/orchestrator/policy_model.py | 9275 | 281 | Policy model wrapper for orchestrator training.
src/openjarvis/learning/intelligence/orchestrator/prompt_registry.py | 12608 | 346 | Prompt registry for orchestrator structured mode.
src/openjarvis/learning/intelligence/orchestrator/reward.py | 7868 | 218 | Multi-objective reward function for orchestrator training.
src/openjarvis/learning/intelligence/orchestrator/sft_trainer.py | 13808 | 416 | SFT (Supervised Fine-Tuning) trainer for orchestrator.
src/openjarvis/learning/intelligence/orchestrator/types.py | 9694 | 335 | Episode dataclasses for orchestrator training.
src/openjarvis/learning/optimize/__init__.py | 1539 | 62 | Optimization framework for OpenJarvis configuration tuning.
src/openjarvis/learning/optimize/config.py | 3487 | 103 | TOML config loader for optimization runs.
src/openjarvis/learning/optimize/llm_optimizer.py | 26662 | 662 | LLM-based optimizer for OpenJarvis configuration tuning.
src/openjarvis/learning/optimize/optimizer.py | 16487 | 438 | OptimizationEngine -- orchestrates the optimize loop.
src/openjarvis/learning/optimize/search_space.py | 6557 | 201 | Search space builder and default search space for configuration optimization.
src/openjarvis/learning/optimize/store.py | 19190 | 509 | SQLite-backed storage for optimization runs and trials.
src/openjarvis/learning/optimize/trial_runner.py | 14992 | 404 | TrialRunner -- evaluates a proposed config against a benchmark.
src/openjarvis/learning/optimize/types.py | 8569 | 254 | Core data types for the optimization framework.
src/openjarvis/learning/optimize/configs/qwen3-235b-dry-run.toml | 2349 | 91 | 
src/openjarvis/learning/optimize/configs/qwen3.5-joint-agentic.toml | 2461 | 92 | 
src/openjarvis/learning/optimize/feedback/__init__.py | 270 | 7 | Feedback subsystem: LLM-as-judge scoring and signal aggregation.
src/openjarvis/learning/optimize/feedback/collector.py | 4021 | 121 | FeedbackCollector -- aggregates feedback from multiple sources.
src/openjarvis/learning/optimize/feedback/judge.py | 3830 | 120 | TraceJudge -- LLM-as-judge scoring for agent traces.
src/openjarvis/learning/optimize/personal/__init__.py | 586 | 18 | Personal benchmark system -- synthesize benchmarks from interaction traces.
src/openjarvis/learning/optimize/personal/dataset.py | 1734 | 55 | DatasetProvider adapter for personal benchmarks.
src/openjarvis/learning/optimize/personal/scorer.py | 1839 | 51 | LLM-judge scorer for personal benchmarks.
src/openjarvis/learning/optimize/personal/synthesizer.py | 3951 | 120 | Synthesize personal benchmarks from interaction traces.
src/openjarvis/learning/routing/__init__.py | 114 | 4 | Routing policies — model selection based on query characteristics.
src/openjarvis/learning/routing/_utils.py | 847 | 35 | Shared query classification utilities for routing policies.
src/openjarvis/learning/routing/complexity.py | 9613 | 282 | Query complexity analyzer — scores queries and suggests token budgets.
src/openjarvis/learning/routing/heuristic_policy.py | 489 | 16 | Wire the existing HeuristicRouter into the RouterPolicyRegistry.
src/openjarvis/learning/routing/heuristic_reward.py | 1827 | 57 | Heuristic reward function — weighted score from latency, cost, efficiency.
src/openjarvis/learning/routing/learned_router.py | 8473 | 237 | Learned router policy — trace-driven query_class -> model mapping.
src/openjarvis/learning/routing/router.py | 7272 | 202 | Heuristic model router — selects the best model based on query characteristics.
src/openjarvis/learning/spec_search/__init__.py | 67 | 2 | LLM-guided spec search: frontier-driven learning subsystem.
src/openjarvis/learning/spec_search/composite_reward.py | 3131 | 98 | Composite reward for Intelligence-edit training (paper §3.3, Eq. 1).
src/openjarvis/learning/spec_search/external_adapter.py | 2475 | 71 | Adapt external agent-dataset records into TraceStore rows.
src/openjarvis/learning/spec_search/models.py | 12181 | 373 | Pydantic models and enums for the spec-search subsystem.
src/openjarvis/learning/spec_search/multi_session.py | 4639 | 130 | Multi-session loop for LLM-guided spec search (paper Algorithm 1).
src/openjarvis/learning/spec_search/orchestrator.py | 18165 | 464 | SpecSearchOrchestrator: top-level driver for a learning session.
src/openjarvis/learning/spec_search/pending_queue.py | 2629 | 76 | Pending review queue for edits awaiting user approval.
src/openjarvis/learning/spec_search/student_runner.py | 4173 | 136 | Real student runner for spec-search experiments.
src/openjarvis/learning/spec_search/triggers.py | 1795 | 67 | Trigger types for the spec-search subsystem.
src/openjarvis/learning/spec_search/checkpoint/__init__.py | 56 | 2 | Git-backed checkpoint store for config rollback.
src/openjarvis/learning/spec_search/checkpoint/store.py | 8909 | 256 | Git-backed checkpoint store for spec-search config rollback.
src/openjarvis/learning/spec_search/diagnose/__init__.py | 56 | 2 | Diagnose phase: teacher-driven failure analysis.
src/openjarvis/learning/spec_search/diagnose/runner.py | 11583 | 319 | DiagnosisRunner: orchestrates phase 1 of the spec-search loop.
src/openjarvis/learning/spec_search/diagnose/teacher_agent.py | 9794 | 270 | TeacherAgent: frontier model as a tool-calling meta-engineer.
src/openjarvis/learning/spec_search/diagnose/tools.py | 21296 | 545 | Diagnostic tools exposed to the teacher in the diagnose phase.
src/openjarvis/learning/spec_search/diagnose/types.py | 3177 | 130 | Data types for the diagnose phase.
src/openjarvis/learning/spec_search/execute/__init__.py | 64 | 2 | Execute phase: apply edits to the harness configuration.
src/openjarvis/learning/spec_search/execute/base.py | 2615 | 96 | EditApplier ABC, registry, and context types for the execute phase.
src/openjarvis/learning/spec_search/execute/loop.py | 6062 | 195 | Per-edit execution loop for the spec-search execute phase.
src/openjarvis/learning/spec_search/execute/appliers/__init__.py | 212 | 7 | Concrete EditApplier implementations.
src/openjarvis/learning/spec_search/execute/appliers/agent.py | 8497 | 227 | Agent-pillar appliers: prompts, class, params, few-shot.
src/openjarvis/learning/spec_search/execute/appliers/intelligence.py | 4653 | 118 | Intelligence-pillar appliers: model routing and parameters.
src/openjarvis/learning/spec_search/execute/appliers/lora_stub.py | 1175 | 39 | LoRA fine-tuning stub — deferred to v2.
src/openjarvis/learning/spec_search/execute/appliers/tools.py | 6133 | 160 | Tools-pillar appliers: add/remove tools, edit descriptions.
src/openjarvis/learning/spec_search/gate/__init__.py | 60 | 2 | Gate phase: benchmark-based accept/reject for edits.
src/openjarvis/learning/spec_search/gate/benchmark_gate.py | 4079 | 132 | BenchmarkGate: accept or reject edits based on benchmark performance.
src/openjarvis/learning/spec_search/gate/cold_start.py | 3067 | 110 | Cold start detection and bootstrap for the spec-search subsystem.
src/openjarvis/learning/spec_search/gate/regression.py | 1778 | 61 | Per-cluster regression detection for the benchmark gate.
src/openjarvis/learning/spec_search/plan/__init__.py | 66 | 2 | Plan phase: converts diagnosis into a frozen LearningPlan.
src/openjarvis/learning/spec_search/plan/planner.py | 9913 | 283 | LearningPlanner: converts a diagnosis into a frozen LearningPlan.
src/openjarvis/learning/spec_search/plan/prompt_diff.py | 5546 | 171 | Prompt diff utilities for the plan phase.
src/openjarvis/learning/spec_search/plan/risk_tier.py | 2356 | 64 | Deterministic risk tier assignment for edits.
src/openjarvis/learning/spec_search/storage/__init__.py | 56 | 2 | Storage primitives: paths, SQLite session store.
src/openjarvis/learning/spec_search/storage/paths.py | 3891 | 99 | Filesystem path resolution for the spec-search subsystem.
src/openjarvis/learning/spec_search/storage/session_store.py | 10905 | 305 | SQLite-backed storage for spec-search LearningSession records.
src/openjarvis/learning/training/__init__.py | 372 | 16 | Training data extraction and fine-tuning pipelines for trace-driven learning.
src/openjarvis/learning/training/data.py | 8263 | 222 | TrainingDataMiner — extract supervised training pairs from the TraceStore.
src/openjarvis/learning/training/lora.py | 14275 | 436 | LoRATrainer — fine-tune local models via LoRA/QLoRA from trace-derived SFT pairs.
src/openjarvis/mcp/__init__.py | 653 | 27 | MCP (Model Context Protocol) layer for OpenJarvis.
src/openjarvis/mcp/client.py | 5629 | 155 | MCP Client — connects to MCP servers and discovers/calls tools.
src/openjarvis/mcp/loader.py | 6152 | 151 | Shared helper for loading MCP server tools from a TOML config blob.
src/openjarvis/mcp/protocol.py | 3808 | 146 | MCP JSON-RPC 2.0 protocol message types.
src/openjarvis/mcp/server.py | 11435 | 326 | MCP Server — wraps OpenJarvis tools as MCP-discoverable tools.
src/openjarvis/mcp/transport.py | 14942 | 407 | MCP transport implementations.
src/openjarvis/memory/__init__.py | 964 | 36 | Native persistent long-term memory for OpenJarvis.
src/openjarvis/memory/extractor.py | 5950 | 156 | LLM-backed extraction of durable facts from a conversation turn.
src/openjarvis/memory/service.py | 12591 | 333 | Persistent memory service: async fact extraction integrated into core.
src/openjarvis/memory/store.py | 17102 | 457 | Persistent stores for automatically extracted long-term memory facts.
src/openjarvis/mining/__init__.py | 1673 | 61 | Pearl mining subsystem.
src/openjarvis/mining/_collector.py | 2669 | 79 | Background poller for mining telemetry.
src/openjarvis/mining/_constants.py | 2057 | 56 | Constants for the Pearl mining subsystem.
src/openjarvis/mining/_discovery.py | 6249 | 177 | Capability detection for mining providers.
src/openjarvis/mining/_docker.py | 17702 | 462 | Pearl Docker container orchestration.
src/openjarvis/mining/_install.py | 2299 | 63 | Detection and install hints for the upstream Pearl Python packages.
src/openjarvis/mining/_metrics.py | 3853 | 97 | Pearl/vLLM Prometheus → MiningStats adapter.
src/openjarvis/mining/_miner_loop_main.py | 8457 | 232 | CPU mining-loop subprocess entry point.
src/openjarvis/mining/_models.py | 2803 | 93 | Pearl mining model support registry.
src/openjarvis/mining/_mps_miner_loop_main.py | 11702 | 312 | Experimental Apple-MPS Pearl miner-loop subprocess.
src/openjarvis/mining/_pearl_subprocess.py | 7731 | 207 | Subprocess launcher for Pearl providers.
src/openjarvis/mining/_stubs.py | 5385 | 178 | ABCs and dataclasses for the mining subsystem.
src/openjarvis/mining/apple_mps_pearl.py | 3980 | 104 | Experimental Apple-GPU Pearl mining provider via PyTorch MPS.
src/openjarvis/mining/cpu_pearl.py | 8372 | 215 | CPU-based Pearl mining provider (decoupled from inference).
src/openjarvis/mining/vllm_pearl.py | 5576 | 153 | The v1 vllm-pearl mining provider.
src/openjarvis/mining/pools/__init__.py | 350 | 10 | RESERVED for v2 pool support.
src/openjarvis/operators/__init__.py | 304 | 8 | Operators — persistent, scheduled autonomous agents.
src/openjarvis/operators/loader.py | 2576 | 72 | Operator loader — load operator manifests from TOML files.
src/openjarvis/operators/manager.py | 11973 | 318 | Operator manager — lifecycle management for autonomous operators.
src/openjarvis/operators/types.py | 978 | 37 | Operator type definitions.
src/openjarvis/operators/data/knowledge_curator.toml | 1668 | 46 | 
src/openjarvis/operators/data/news_digest.toml | 1504 | 48 | 
src/openjarvis/operators/data/researcher.toml | 1453 | 44 | 
src/openjarvis/operators/data/system_monitor.toml | 1370 | 43 | 
src/openjarvis/prompt/__init__.py | 36 | 2 | 
src/openjarvis/prompt/builder.py | 11573 | 291 | classes: PromptSection, SystemPromptBuilder
src/openjarvis/recipes/__init__.py | 438 | 22 | Recipe system — composable primitive configurations.
src/openjarvis/recipes/composer.py | 4875 | 144 | Composer bridges — convert a Recipe into EvalSuiteConfig or OperatorManifest.
src/openjarvis/recipes/loader.py | 12182 | 336 | Recipe loader — load and resolve TOML recipe files.
src/openjarvis/recipes/data/coding_assistant.toml | 641 | 26 | 
src/openjarvis/recipes/data/coding_benchmark.toml | 1103 | 37 | 
src/openjarvis/recipes/data/gaia_orchestrator.toml | 1053 | 36 | 
src/openjarvis/recipes/data/general_assistant.toml | 534 | 25 | 
src/openjarvis/recipes/data/monitor_assistant.toml | 602 | 26 | 
src/openjarvis/recipes/data/research_assistant.toml | 619 | 25 | 
src/openjarvis/recipes/data/swebench_openhands.toml | 1236 | 42 | 
src/openjarvis/recipes/data/terminalbench_react.toml | 1046 | 36 | 
src/openjarvis/recipes/data/operators/correspondent.toml | 412 | 15 | 
src/openjarvis/recipes/data/operators/correspondent_prompt.md | 2676 | 53 | 
src/openjarvis/recipes/data/operators/inbox_triage.toml | 1791 | 58 | 
src/openjarvis/recipes/data/operators/news_briefing.toml | 1819 | 58 | 
src/openjarvis/recipes/data/operators/openjarvis_twitter_bot.toml | 541 | 23 | 
src/openjarvis/recipes/data/operators/openjarvis_twitter_bot_prompt.md | 3975 | 76 | 
src/openjarvis/recipes/data/operators/repo_watcher.toml | 1917 | 65 | 
src/openjarvis/recipes/data/operators/researcher.toml | 505 | 15 | 
src/openjarvis/recipes/data/operators/researcher_prompt.md | 2442 | 46 | 
src/openjarvis/recipes/data/operators/sentinel.toml | 470 | 15 | 
src/openjarvis/recipes/data/operators/sentinel_prompt.md | 3641 | 75 | 
src/openjarvis/recipes/data/operators/twitter_sentinel.toml | 1793 | 51 | 
src/openjarvis/sandbox/__init__.py | 417 | 19 | Container sandbox for isolated agent execution.
src/openjarvis/sandbox/mount_security.py | 5322 | 196 | Mount validation and security for container sandboxes.
src/openjarvis/sandbox/runner.py | 11105 | 362 | Container runner and sandboxed agent wrapper.
src/openjarvis/sandbox/wasm_runner.py | 4931 | 160 | WASM sandbox — lightweight isolation via Wasmtime.
src/openjarvis/scheduler/__init__.py | 284 | 7 | Task scheduler module — cron/interval/once scheduling with SQLite persistence.
src/openjarvis/scheduler/scheduler.py | 12021 | 342 | Task scheduler — cron/interval/once execution with background polling.
src/openjarvis/scheduler/store.py | 5908 | 168 | SQLite-backed persistence for scheduled tasks and run logs.
src/openjarvis/scheduler/tools.py | 12044 | 351 | MCP tools for scheduler operations — schedule, list, pause, resume, cancel.
src/openjarvis/security/__init__.py | 7028 | 198 | Security guardrails — scanners, engine wrapper, audit, SSRF.
src/openjarvis/security/_stubs.py | 667 | 29 | ABC for security scanners.
src/openjarvis/security/audit.py | 11816 | 329 | Audit logger — persist security events to SQLite with Merkle hash chain.
src/openjarvis/security/boundary.py | 4614 | 140 | BoundaryGuard — scans content at device exit points.
src/openjarvis/security/capabilities.py | 14318 | 346 | RBAC capability system — fine-grained permission model for tool dispatch.
src/openjarvis/security/credential_stripper.py | 1108 | 32 | classes: CredentialStripper
src/openjarvis/security/data_boundary_audit.py | 73791 | 1882 | Application data-boundary diagnostics for OpenJarvis.
src/openjarvis/security/file_policy.py | 2875 | 99 | File sensitivity policy — block access to secrets, credentials, and keys.
src/openjarvis/security/file_utils.py | 2573 | 88 | Secure file and directory creation helpers.
src/openjarvis/security/guardrails.py | 10951 | 331 | GuardrailsEngine — security-aware inference engine wrapper.
src/openjarvis/security/injection_scanner.py | 6497 | 197 | Prompt injection scanner — detect malicious patterns in text.
src/openjarvis/security/rate_limiter.py | 3561 | 108 | Rate limiter -- token bucket algorithm for per-agent/per-tool throttling.
src/openjarvis/security/runtime.py | 7029 | 207 | Shared helpers for securing agent and direct tool execution paths.
src/openjarvis/security/scanner.py | 4929 | 149 | Concrete security scanners — secrets and PII detection.
src/openjarvis/security/severity_policy.py | 659 | 23 | classes: SeverityPolicy
src/openjarvis/security/signing.py | 4148 | 133 | Ed25519 signing — supply chain integrity for agent and skill manifests.
src/openjarvis/security/ssrf.py | 7240 | 188 | SSRF protection — block requests to private IPs and cloud metadata endpoints.
src/openjarvis/security/subprocess_sandbox.py | 3720 | 128 | Subprocess sandbox — secure process execution with environment isolation.
src/openjarvis/security/taint.py | 4517 | 144 | Taint tracking — information flow control.
src/openjarvis/security/types.py | 2693 | 106 | Security data types — threat levels, scan findings, and security events.
src/openjarvis/server/__init__.py | 90 | 4 | OpenAI-compatible API server for OpenJarvis.
src/openjarvis/server/agent_manager_routes.py | 103093 | 2594 | FastAPI routes for the Agent Manager.
src/openjarvis/server/analytics_routes.py | 5652 | 152 | Small router exposing the anonymous analytics identity to the frontend.
src/openjarvis/server/api_routes.py | 47530 | 1365 | Extended API routes for agents, workflows, memory, traces, etc.
src/openjarvis/server/app.py | 23556 | 568 | FastAPI application factory for the OpenJarvis API server.
src/openjarvis/server/approval_routes.py | 2355 | 80 | REST endpoints for the proactive-agent approval queue.
src/openjarvis/server/auth_middleware.py | 8310 | 206 | API key authentication middleware for the OpenJarvis server.
src/openjarvis/server/channel_bridge.py | 14046 | 380 | ChannelBridge — unified orchestrator for multi-channel messaging.
src/openjarvis/server/cloud_router.py | 15473 | 439 | Direct cloud API router — bypasses the engine system entirely.
src/openjarvis/server/comparison.py | 15682 | 452 | Comparison page -- static cost comparison of local vs cloud inference.
src/openjarvis/server/connectors_router.py | 43992 | 1021 | FastAPI router for /v1/connectors — connector management endpoints.
src/openjarvis/server/cost_calculator.py | 3940 | 138 | Cost calculator -- estimate monthly cloud API costs for common use cases.
src/openjarvis/server/daemon.py | 1413 | 42 | Register daemon state only after Uvicorn has opened its listening socket.
src/openjarvis/server/dashboard.py | 15688 | 436 | Dashboard route — serves the savings dashboard HTML page.
src/openjarvis/server/digest_routes.py | 4279 | 131 | FastAPI routes for the morning digest.
src/openjarvis/server/middleware.py | 3089 | 76 | Security middleware -- HTTP security headers and request guards.
src/openjarvis/server/model_capabilities.py | 969 | 35 | Model capability helpers shared by server model-selection routes.
src/openjarvis/server/models.py | 3654 | 135 | Pydantic request/response models for the OpenAI-compatible API.
src/openjarvis/server/research_router.py | 23366 | 601 | HTTP route: ``POST /api/research`` — agentic research over the knowledge store.
src/openjarvis/server/routes.py | 55780 | 1474 | Route handlers for the OpenAI-compatible API server.
src/openjarvis/server/savings.py | 7839 | 211 | Savings calculation — compare local inference cost against cloud providers.
src/openjarvis/server/session_store.py | 7427 | 212 | SQLite-backed session store for channel conversations.
src/openjarvis/server/stream_bridge.py | 12835 | 331 | Bridge sync agent.run() + EventBus events to an async SSE generator.
src/openjarvis/server/upload_router.py | 6835 | 219 | Upload / Paste router for ingesting documents into the knowledge store.
src/openjarvis/server/webhook_routes.py | 17827 | 468 | Webhook endpoints for receiving messages from external platforms.
src/openjarvis/server/ws_bridge.py | 5029 | 123 | WebSocket bridge: EventBus → connected WebSocket clients.
src/openjarvis/sessions/__init__.py | 183 | 6 | Cross-channel session management.
src/openjarvis/sessions/compression.py | 3779 | 103 | classes: BaseCompressor, SessionConsolidation
src/openjarvis/sessions/session.py | 12565 | 364 | Session management — cross-channel persistent sessions.
src/openjarvis/skills/__init__.py | 1356 | 47 | Skill system — reusable multi-tool compositions.
src/openjarvis/skills/dependency.py | 6563 | 195 | Dependency graph: cycle detection, topological sort, capability union.
src/openjarvis/skills/executor.py | 7818 | 220 | SkillExecutor — runs skill steps sequentially through ToolExecutor.
src/openjarvis/skills/importer.py | 10884 | 274 | SkillImporter — install ResolvedSkill instances into ~/.openjarvis/skills/.
src/openjarvis/skills/index.py | 3222 | 100 | Skill index — load and search a remote/local skill catalog.
src/openjarvis/skills/loader.py | 11518 | 323 | Skill loader — load and verify skill manifests from TOML files.
src/openjarvis/skills/manager.py | 18663 | 477 | SkillManager — coordinates skill discovery, catalog, tool wrapping, and execution.
src/openjarvis/skills/overlay.py | 4983 | 152 | SkillOverlay — sidecar storage for optimization output (Plan 2A).
src/openjarvis/skills/parser.py | 9042 | 232 | SkillParser — strict spec validation + tolerant field mapping.
src/openjarvis/skills/security.py | 1862 | 66 | Skill security — capability validation and trust tiers.
src/openjarvis/skills/tool_adapter.py | 7141 | 197 | SkillTool — wraps a skill as a tool that agents can invoke.
src/openjarvis/skills/tool_translator.py | 4217 | 115 | ToolTranslator — translate external tool names to OpenJarvis equivalents.
src/openjarvis/skills/types.py | 2032 | 63 | Skill type definitions.
src/openjarvis/skills/data/backup-files.toml | 643 | 21 | 
src/openjarvis/skills/data/calendar-prep.toml | 813 | 21 | 
src/openjarvis/skills/data/code-lint.toml | 775 | 21 | 
src/openjarvis/skills/data/code-test-gen.toml | 973 | 26 | 
src/openjarvis/skills/data/compare-docs.toml | 910 | 26 | 
src/openjarvis/skills/data/daily-digest.toml | 788 | 21 | 
src/openjarvis/skills/data/data-analyze.toml | 1035 | 26 | 
src/openjarvis/skills/data/dependency-audit.toml | 913 | 26 | 
src/openjarvis/skills/data/email-draft.toml | 874 | 21 | 
src/openjarvis/skills/data/file-deduplicator.toml | 734 | 21 | 
src/openjarvis/skills/data/file-organizer.toml | 992 | 26 | 
src/openjarvis/skills/data/knowledge-extract.toml | 672 | 21 | 
src/openjarvis/skills/data/meeting-notes.toml | 826 | 21 | 
src/openjarvis/skills/data/pdf-summarize.toml | 708 | 21 | 
src/openjarvis/skills/data/search-and-index.toml | 840 | 26 | 
src/openjarvis/skills/data/security-scan.toml | 806 | 21 | 
src/openjarvis/skills/data/todo-from-notes.toml | 770 | 21 | 
src/openjarvis/skills/data/topic-research.toml | 832 | 26 | 
src/openjarvis/skills/data/translate-doc.toml | 1030 | 26 | 
src/openjarvis/skills/data/web-summarize.toml | 634 | 21 | 
src/openjarvis/skills/sources/__init__.py | 551 | 17 | Skill source resolvers — Hermes, OpenClaw, generic GitHub.
src/openjarvis/skills/sources/base.py | 3081 | 94 | Source resolver ABC + ResolvedSkill dataclass.
src/openjarvis/skills/sources/github.py | 3574 | 112 | GitHubResolver — generic resolver for any GitHub repo containing skills.
src/openjarvis/skills/sources/hermes.py | 3854 | 121 | HermesResolver — resolves skills from NousResearch/hermes-agent.
src/openjarvis/skills/sources/openclaw.py | 3883 | 121 | OpenClawResolver — resolves skills from the OpenClaw skill index.
src/openjarvis/speech/__init__.py | 605 | 18 | Speech subsystem — speech-to-text and text-to-speech backends.
src/openjarvis/speech/_discovery.py | 2484 | 87 | Auto-discover available speech-to-text backends.
src/openjarvis/speech/_stubs.py | 1381 | 56 | Abstract base classes and data types for the speech subsystem.
src/openjarvis/speech/_tts_discovery.py | 2939 | 87 | Auto-discover available text-to-speech backends.
src/openjarvis/speech/cartesia_tts.py | 3357 | 116 | Cartesia text-to-speech backend.
src/openjarvis/speech/deepgram.py | 3112 | 98 | Deepgram speech-to-text backend (cloud).
src/openjarvis/speech/elevenlabs_tts.py | 6192 | 195 | ElevenLabs text-to-speech backend.
src/openjarvis/speech/faster_whisper.py | 5931 | 176 | Faster-Whisper speech-to-text backend (local, CTranslate2-based).
src/openjarvis/speech/kokoro_tts.py | 13124 | 341 | Kokoro TTS backend — fully open-source, runs locally.
src/openjarvis/speech/openai_tts.py | 2208 | 83 | OpenAI TTS backend — cloud-based voice synthesis via OpenAI API.
src/openjarvis/speech/openai_whisper.py | 2132 | 65 | OpenAI Whisper API speech-to-text backend (cloud).
src/openjarvis/speech/tts.py | 1324 | 54 | Abstract base classes and data types for text-to-speech backends.
src/openjarvis/speech/voice_io.py | 3843 | 127 | Microphone recording with silence detection and audio playback helpers.
src/openjarvis/system/__init__.py | 623 | 24 | Top-level system composition: JarvisSystem, SystemBuilder, and helpers.
src/openjarvis/system/_channel_kwargs.py | 5567 | 204 | Per-channel config→kwargs mappers for ChannelRegistry.create().
src/openjarvis/system/builder.py | 29214 | 754 | Config-driven fluent builder that wires up a JarvisSystem.
src/openjarvis/system/bundles.py | 2049 | 61 | Bundle dataclasses that group cohesive subsystems of JarvisSystem.
src/openjarvis/system/core.py | 12800 | 336 | JarvisSystem — the fully wired system dataclass.
src/openjarvis/system/orchestrator.py | 13794 | 367 | Executes user queries through the engine or through an agent.
src/openjarvis/system/protocols.py | 1546 | 42 | Structural protocols for substituting fakes in place of JarvisSystem.
src/openjarvis/telemetry/__init__.py | 2599 | 112 | Telemetry — SQLite-backed inference recording and instrumented wrappers.
src/openjarvis/telemetry/aggregator.py | 19923 | 490 | Read-only telemetry aggregation — query stored inference records.
src/openjarvis/telemetry/batch.py | 4260 | 127 | Batch-level energy accounting — group requests and compute per-token energy.
src/openjarvis/telemetry/efficiency.py | 4456 | 130 | MFU/MBU efficiency calculator for GPU inference telemetry.
src/openjarvis/telemetry/energy_amd.py | 4665 | 138 | AMD energy monitor — hardware counters via amdsmi (ROCm 6.1+).
src/openjarvis/telemetry/energy_apple.py | 14592 | 410 | Apple Silicon energy monitor — per-rail IOReport counters via zeus-apple-silicon.
src/openjarvis/telemetry/energy_monitor.py | 8657 | 243 | EnergyMonitor ABC — multi-vendor energy measurement with hardware counters.
src/openjarvis/telemetry/energy_nvidia.py | 9958 | 268 | NVIDIA energy monitor — hardware counters (Volta+) with polling fallback.
src/openjarvis/telemetry/energy_rapl.py | 6592 | 198 | CPU RAPL energy monitor — reads Intel/AMD RAPL counters from sysfs.
src/openjarvis/telemetry/flops.py | 3758 | 113 | FLOPs estimation and Model FLOPs Utilization (MFU) computation.
src/openjarvis/telemetry/gpu_monitor.py | 13033 | 358 | GPU monitoring via pynvml — background poller for GPU metrics.
src/openjarvis/telemetry/instrumented_engine.py | 25546 | 655 | Transparent telemetry wrapper for inference engines.
src/openjarvis/telemetry/itl.py | 1311 | 48 | Inter-token latency percentile computation.
src/openjarvis/telemetry/phase_metrics.py | 1347 | 45 | Phase metrics computation -- prefill/decode energy separation.
src/openjarvis/telemetry/session.py | 5941 | 161 | Background-sampling telemetry session.
src/openjarvis/telemetry/steady_state.py | 4178 | 130 | Steady-state detection for energy measurement at thermal equilibrium.
src/openjarvis/telemetry/store.py | 17942 | 438 | SQLite-backed telemetry storage.
src/openjarvis/telemetry/vllm_metrics.py | 5963 | 183 | vLLM Prometheus metrics scraper — fetches and parses /metrics endpoint.
src/openjarvis/telemetry/wrapper.py | 1696 | 58 | Instrumented wrappers for inference engines — timing and telemetry publishing.
src/openjarvis/templates/__init__.py | 257 | 10 | Agent template system — pre-configured agent manifests.
src/openjarvis/templates/agent_templates.py | 3439 | 109 | Agent template loader — load pre-configured agent manifests from TOML files.
src/openjarvis/templates/data/architect.toml | 677 | 11 | 
src/openjarvis/templates/data/assistant.toml | 679 | 11 | 
src/openjarvis/templates/data/code-reviewer.toml | 639 | 11 | 
src/openjarvis/templates/data/data-analyst.toml | 694 | 11 | 
src/openjarvis/templates/data/debugger.toml | 670 | 11 | 
src/openjarvis/templates/data/deep-researcher.toml | 719 | 11 | 
src/openjarvis/templates/data/fact-checker.toml | 655 | 11 | 
src/openjarvis/templates/data/inbox-triager.toml | 620 | 11 | 
src/openjarvis/templates/data/meeting-prep.toml | 660 | 11 | 
src/openjarvis/templates/data/monitor.toml | 1007 | 26 | 
src/openjarvis/templates/data/note-taker.toml | 611 | 11 | 
src/openjarvis/templates/data/security-auditor.toml | 740 | 11 | 
src/openjarvis/templates/data/summarizer.toml | 657 | 11 | 
src/openjarvis/templates/data/translator.toml | 680 | 11 | 
src/openjarvis/templates/data/tutor.toml | 655 | 11 | 
src/openjarvis/templates/data/writer.toml | 659 | 11 | 
src/openjarvis/tools/__init__.py | 3843 | 187 | Tools primitive — tool system with ABC interface and built-in tools.
src/openjarvis/tools/_paths.py | 1568 | 39 | Default directory allow-list for the filesystem tools.
src/openjarvis/tools/_stubs.py | 26307 | 658 | ABC for tool implementations and the ToolExecutor dispatch engine.
src/openjarvis/tools/agent_tools.py | 10248 | 325 | Inter-agent lifecycle tools — spawn, send, list, and kill agents.
src/openjarvis/tools/apple_calendar.py | 3595 | 100 | Executable tools for the local Apple Calendar connector.
src/openjarvis/tools/apply_patch.py | 11449 | 341 | Apply-patch tool — apply unified diff patches to files.
src/openjarvis/tools/approval_store.py | 14169 | 407 | ApprovalStore — SQLite-backed store for proactive agent action approvals.
src/openjarvis/tools/audio_tool.py | 5996 | 181 | Audio transcription tool — transcribe audio via OpenAI Whisper.
src/openjarvis/tools/browser.py | 25783 | 697 | Browser automation tools — Playwright-based web interaction.
src/openjarvis/tools/browser_axtree.py | 4299 | 138 | Browser accessibility tree extraction tool.
src/openjarvis/tools/calculator.py | 5659 | 174 | Calculator tool — safe math evaluation via ``ast`` module.
src/openjarvis/tools/channel_tools.py | 6112 | 190 | Channel MCP tools — expose channel operations as BaseTool instances.
src/openjarvis/tools/code_interpreter.py | 8817 | 232 | Code interpreter tool — Python execution with AST validation + hardening.
src/openjarvis/tools/code_interpreter_docker.py | 4874 | 143 | Docker-sandboxed code interpreter tool.
src/openjarvis/tools/db_query.py | 11910 | 358 | Database query tool — execute SQL queries against SQLite and PostgreSQL.
src/openjarvis/tools/description_loader.py | 2473 | 80 | Load tool description overrides from $OPENJARVIS_HOME/tools/descriptions.toml.
src/openjarvis/tools/digest_collect.py | 21316 | 584 | Digest collection tool — fetches recent data from configured connectors.
src/openjarvis/tools/docker_shell_exec.py | 5775 | 173 | Container-scoped shell executor.
src/openjarvis/tools/file_read.py | 5034 | 145 | File read tool — read file contents with path validation.
src/openjarvis/tools/file_write.py | 7500 | 214 | File write tool — write content to files with path validation.
src/openjarvis/tools/fx_macro.py | 16115 | 399 | Native FX and macroeconomic data tool backed by the FXMacroData REST API.
src/openjarvis/tools/git_tool.py | 12833 | 400 | Git tools — version control operations via subprocess.
src/openjarvis/tools/http_request.py | 9272 | 255 | HTTP request tool — make HTTP requests with SSRF protection.
src/openjarvis/tools/image_tool.py | 5026 | 152 | Image generation tool — generate images via OpenAI DALL-E.
src/openjarvis/tools/knowledge_search.py | 7477 | 207 | KnowledgeSearchTool — filtered BM25 retrieval with source attribution.
src/openjarvis/tools/knowledge_sql.py | 5095 | 146 | KnowledgeSQLTool — read-only SQL queries against the KnowledgeStore.
src/openjarvis/tools/knowledge_tools.py | 10035 | 295 | MCP tools for knowledge graph operations.
src/openjarvis/tools/llm_tool.py | 3014 | 96 | LLM tool — delegate a sub-query to an inference engine.
src/openjarvis/tools/mcp_adapter.py | 2382 | 76 | MCP tool adapter — wraps external MCP server tools as native BaseTool instances.
src/openjarvis/tools/memory_manage.py | 5052 | 143 | Manage persistent agent memory (MEMORY.md).
src/openjarvis/tools/pdf_tool.py | 5834 | 177 | PDF text extraction tool — extract text from PDF files via pdfplumber.
src/openjarvis/tools/proactive_tools.py | 22880 | 623 | Proactive agent tools — check/record permissions, queue and execute actions.
src/openjarvis/tools/repl.py | 10625 | 337 | Persistent Python REPL tool — maintains state across calls within a session.
src/openjarvis/tools/retrieval.py | 2939 | 93 | Retrieval tool — search memory backends for relevant context.
src/openjarvis/tools/scan_chunks.py | 6890 | 192 | ScanChunksTool — semantic grep via LM-powered chunk scanning.
src/openjarvis/tools/shell_exec.py | 8137 | 242 | Shell execution tool — run shell commands with security constraints.
src/openjarvis/tools/skill_manage.py | 5533 | 156 | SkillManageTool — create, list, load, or delete agent-authored skills.
src/openjarvis/tools/storage_tools.py | 10733 | 316 | Storage MCP tools — expose MemoryBackend operations as BaseTool instances.
src/openjarvis/tools/text_to_speech.py | 5810 | 148 | Text-to-speech tool — synthesize text to audio via configurable TTS backend.
src/openjarvis/tools/think.py | 1749 | 59 | Think tool — zero-cost reasoning scratchpad.
src/openjarvis/tools/user_profile_manage.py | 5005 | 141 | Manage persistent user profile (USER.md).
src/openjarvis/tools/weather.py | 12729 | 317 | Native, parameterized weather tool backed by OpenWeatherMap.
src/openjarvis/tools/web_search.py | 33964 | 824 | Web search tool — You.com or Tavily, with a DuckDuckGo fallback.
src/openjarvis/tools/storage/__init__.py | 1244 | 50 | Storage primitive — persistent searchable storage.
src/openjarvis/tools/storage/_stubs.py | 2911 | 94 | ABC for memory / retrieval backends.
src/openjarvis/tools/storage/bm25.py | 2999 | 99 | BM25 memory backend — classic term-frequency retrieval.
src/openjarvis/tools/storage/chunking.py | 6114 | 179 | Document chunking with configurable size and overlap.
src/openjarvis/tools/storage/colbert_backend.py | 7654 | 252 | ColBERTv2 late interaction memory backend.
src/openjarvis/tools/storage/context.py | 8705 | 246 | Context injection — retrieve relevant memory and inject into prompts.
src/openjarvis/tools/storage/dense.py | 28267 | 770 | In-memory dense retrieval backend.
src/openjarvis/tools/storage/embeddings.py | 6011 | 174 | Embeddings abstraction for dense retrieval backends.
src/openjarvis/tools/storage/faiss_backend.py | 4918 | 162 | FAISS dense retrieval memory backend.
src/openjarvis/tools/storage/hybrid.py | 5259 | 185 | Hybrid memory backend — Reciprocal Rank Fusion of two retrievers.
src/openjarvis/tools/storage/ingest.py | 6110 | 247 | Document ingestion — file reading, type detection, directory walking.
src/openjarvis/tools/storage/knowledge_graph.py | 11278 | 317 | Knowledge graph storage backend — entity-relation store with pattern queries.
src/openjarvis/tools/storage/sqlite.py | 5247 | 166 | SQLite/FTS5 memory backend — zero-dependency default.
src/openjarvis/tools/templates/__init__.py | 201 | 6 | MCP tool templates — reusable tool definitions from TOML.
src/openjarvis/tools/templates/loader.py | 13424 | 368 | Template loader — dynamically construct BaseTool from TOML definitions.
src/openjarvis/tools/templates/builtin/base64_encode.toml | 256 | 12 | 
src/openjarvis/tools/templates/builtin/date_info.toml | 204 | 9 | 
src/openjarvis/tools/templates/builtin/hash_compute.toml | 263 | 12 | 
src/openjarvis/tools/templates/builtin/json_transform.toml | 278 | 12 | 
src/openjarvis/tools/templates/builtin/regex_extract.toml | 356 | 15 | 
src/openjarvis/tools/templates/builtin/text_length.toml | 262 | 12 | 
src/openjarvis/tools/templates/builtin/text_lower.toml | 252 | 12 | 
src/openjarvis/tools/templates/builtin/text_reverse.toml | 252 | 12 | 
src/openjarvis/tools/templates/builtin/text_upper.toml | 252 | 12 | 
src/openjarvis/tools/templates/builtin/unit_convert.toml | 440 | 18 | 
src/openjarvis/traces/__init__.py | 653 | 16 | Trace system — full interaction-level recording and analysis.
src/openjarvis/traces/analyzer.py | 11910 | 329 | TraceAnalyzer — read-only query layer over stored traces.
src/openjarvis/traces/collector.py | 10352 | 284 | TraceCollector — wraps any BaseAgent to record interaction traces.
src/openjarvis/traces/store.py | 12122 | 349 | SQLite-backed trace storage.
src/openjarvis/workflow/__init__.py | 610 | 24 | Workflow engine — DAG-based multi-agent pipelines.
src/openjarvis/workflow/builder.py | 4061 | 151 | WorkflowBuilder — fluent API for constructing workflows.
src/openjarvis/workflow/engine.py | 12175 | 347 | WorkflowEngine — executes a WorkflowGraph against a JarvisSystem.
src/openjarvis/workflow/graph.py | 4626 | 128 | WorkflowGraph — DAG with validation and topological sort.
src/openjarvis/workflow/loader.py | 2245 | 85 | Workflow loader — load workflows from TOML files.
src/openjarvis/workflow/types.py | 1536 | 67 | Workflow type definitions.
tests/__init__.py | 0 | 0 | 
tests/conftest.py | 12117 | 382 | Shared fixtures — clear all registries and the event bus between tests.
tests/test_conftest_lifecycle.py | 2084 | 68 | Regression tests for the session-wide test-home lifecycle.
tests/test_digest_integration.py | 2571 | 80 | End-to-end integration test for the morning digest pipeline.
tests/test_query_orchestrator.py | 6122 | 183 | Isolated QueryOrchestrator tests using a minimal fake system.
tests/test_vision.py | 3308 | 95 | Tests for vision input support: ``Message.images`` -> Ollama payload.
tests/a2a/test_a2a.py | 6854 | 224 | Tests for A2A protocol (Phase 16.1).
tests/a2a/test_a2a_auth.py | 1606 | 52 | A2A server authentication tests (issue #217).
tests/agents/__init__.py | 0 | 0 | 
tests/agents/conftest.py | 1538 | 50 | Shared fixtures for agent tests.
tests/agents/fake_engine.py | 2158 | 78 | Scripted inference engine for deterministic agent testing.
tests/agents/scenario_harness.py | 1076 | 39 | Shared harness dataclasses for agent lifecycle scenario tests.
tests/agents/test_agent_lifecycle_scenarios.py | 18705 | 539 | Agent lifecycle scenario tests.
tests/agents/test_agent_routing_matrix.py | 7097 | 186 | Cross-product tests: agent x engine x model.
tests/agents/test_base_agent.py | 16989 | 457 | Tests for BaseAgent helpers and ToolUsingAgent.
tests/agents/test_budget.py | 2829 | 81 | 
tests/agents/test_channel_agent.py | 11203 | 319 | Tests for ChannelAgent and classify_query.
tests/agents/test_channel_agent_integration.py | 9805 | 285 | Integration tests for ChannelAgent with DeepResearchAgent and KnowledgeStore.
tests/agents/test_claude_code.py | 19797 | 621 | Tests for ClaudeCodeAgent.
tests/agents/test_config_defaults.py | 6927 | 172 | Tests for agent constructor config-based default resolution.
tests/agents/test_continuation.py | 3455 | 103 | Tests for continuation handling (Phase 14.2).
tests/agents/test_deep_research.py | 6096 | 179 | Tests for DeepResearchAgent -- multi-hop retrieval with citations.
tests/agents/test_deep_research_integration.py | 7773 | 222 | End-to-end integration tests for the Deep Research pipeline.
tests/agents/test_deep_research_prompt.py | 3177 | 87 | Tests for DeepResearch system prompt — date injection and adaptive behavior.
tests/agents/test_digest_store.py | 2473 | 78 | Tests for DigestStore and DigestArtifact.
tests/agents/test_direct_operation_security.py | 3551 | 107 | Security gates for agents that execute outside ToolUsingAgent.
tests/agents/test_errors.py | 3197 | 86 | Tests for agent error classification.
tests/agents/test_executor.py | 8523 | 241 | Tests for AgentExecutor single-tick execution.
tests/agents/test_executor_ephemeral.py | 3967 | 119 | classes: _FlushProbe, _RecordingLimiter
tests/agents/test_executor_error_detail.py | 1522 | 39 | Tests for structured error_detail in executor traces.
tests/agents/test_executor_tool_persistence.py | 4334 | 128 | Regression tests for managed-agent tool-call persistence.
tests/agents/test_executor_tools.py | 24578 | 710 | Tests for tool wiring in AgentExecutor.
tests/agents/test_fake_engine.py | 1333 | 51 | Tests for FakeEngine.
tests/agents/test_hybrid_provider_search_security.py | 8085 | 250 | Provider-search security regressions across hybrid agents.
tests/agents/test_learning_integration.py | 3516 | 106 | Integration tests for LearningOrchestrator agent_id scoping.
tests/agents/test_loop_guard.py | 5267 | 135 | Tests for agent loop guard (Phase 14.3).
tests/agents/test_loop_guard_warn.py | 2267 | 69 | 
tests/agents/test_manager.py | 21512 | 535 | Tests for AgentManager persistent agent lifecycle.
tests/agents/test_manager_recover.py | 1298 | 38 | Tests for AgentManager.recover_agent() always resetting status.
tests/agents/test_monitor_operative.py | 2931 | 79 | Tests for MonitorOperativeAgent.
tests/agents/test_morning_digest.py | 2637 | 84 | Tests for MorningDigestAgent.
tests/agents/test_native_openhands.py | 24892 | 645 | Tests for NativeOpenHandsAgent (formerly OpenHandsAgent).
tests/agents/test_native_react.py | 28761 | 732 | Tests for NativeReActAgent (formerly ReActAgent).
tests/agents/test_opencode_agent.py | 17744 | 501 | Tests for OpenCodeAgent (wraps the `opencode` coding agent).
tests/agents/test_opencode_v2_protocol.py | 15991 | 435 | OpenCode protocol regressions using real HTTPX requests, without a model.
tests/agents/test_openhands.py | 1935 | 58 | Tests for OpenHandsAgent (real openhands-sdk wrapper).
tests/agents/test_orchestrator.py | 33529 | 927 | Tests for the OrchestratorAgent.
tests/agents/test_persona_persistent.py | 3948 | 97 | Persona files reach persistent agents, not just one-shot `jarvis ask` (#376).
tests/agents/test_proactive_agent.py | 4536 | 132 | Regression tests for proactive scheduling and notification setup.
tests/agents/test_research_loop.py | 23198 | 619 | Tests for the research_loop agent — focused on loop invariants.
tests/agents/test_rlm.py | 22293 | 605 | Tests for the RLM agent.
tests/agents/test_rlm_repl.py | 8145 | 252 | Tests for the RLM REPL environment.
tests/agents/test_scenario_harness_smoke.py | 727 | 23 | Smoke test for the scenario harness fixture.
tests/agents/test_scheduler.py | 7770 | 222 | Tests for AgentScheduler tick scheduling.
tests/agents/test_simple.py | 5416 | 141 | Tests for the SimpleAgent.
tests/agents/test_skillorchestra_security.py | 11021 | 320 | Security regressions for SkillOrchestra direct QA operations.
tests/agents/test_stall.py | 4521 | 144 | Tests for activity-based stall detection.
tests/agents/test_suggest_action.py | 872 | 30 | Tests for suggest_action helper.
tests/agents/test_system_prompt_builder_integration.py | 882 | 29 | 
tests/agents/test_template_prompts.py | 1591 | 41 | Tests for system_prompt_template expansion in agent creation.
tests/agents/test_tool_resolver.py | 10116 | 313 | Focused tests for canonical managed-agent tool resolution (#688).
tests/agents/test_toolorchestra_security.py | 5793 | 187 | Security regressions for ToolOrchestra worker/action dispatch.
tests/agents/test_trace_recording.py | 3260 | 102 | Tests for trace recording in AgentExecutor.
tests/analytics/__init__.py | 0 | 0 | 
tests/analytics/test_opt_in.py | 1926 | 54 | Default-off analytics must not create an identity or initialise sending.
tests/analytics/test_preferences.py | 7816 | 202 | An explicit UI choice must persist and immediately gate both senders.
tests/analytics/test_redaction.py | 10476 | 340 | Tests for openjarvis.analytics.redaction.
tests/bench/__init__.py | 0 | 0 | 
tests/bench/test_bench_stats.py | 2383 | 70 | Tests for benchmark stats output and Rich table rendering.
tests/bench/test_energy.py | 4072 | 121 | Tests for the energy benchmark.
tests/bench/test_engine_info.py | 2571 | 89 | Tests for ``engine_info`` — run metadata from self-describing engines.
tests/bench/test_latency.py | 2634 | 87 | Tests for the latency benchmark.
tests/bench/test_stubs.py | 4191 | 130 | Tests for benchmark stubs — BenchmarkResult, BaseBenchmark, BenchmarkSuite.
tests/bench/test_throughput.py | 2695 | 79 | Tests for the throughput benchmark.
tests/channels/__init__.py | 0 | 0 | 
tests/channels/channel_test_helpers.py | 2069 | 66 | Shared parametrized tests for channel implementations.
tests/channels/conftest.py | 2308 | 70 | Shared fixtures for channel integration tests.
tests/channels/test_agent_channel_e2e.py | 2217 | 74 | Agent-channel E2E tests — using WebChatChannel (in-memory, no external deps).
tests/channels/test_bluebubbles.py | 4522 | 132 | Tests for the BlueBubblesChannel adapter.
tests/channels/test_channel_config.py | 6498 | 219 | Tests for channel configuration — nested sub-configs and TOML loading.
tests/channels/test_channel_contract.py | 2638 | 84 | Parametrized contract tests — verify every channel implements BaseChannel correctly.
tests/channels/test_channel_registry.py | 3965 | 131 | Tests for channel registration in the ChannelRegistry.
tests/channels/test_channels_phase21.py | 11372 | 334 | Tests for Phase 21 messaging channels.
tests/channels/test_config.py | 2715 | 79 | Tests for channel configuration.
tests/channels/test_discord_channel.py | 16281 | 438 | Tests for the DiscordChannel adapter.
tests/channels/test_email_channel.py | 6448 | 189 | Tests for the EmailChannel adapter.
tests/channels/test_feishu.py | 4288 | 130 | Tests for the FeishuChannel adapter.
tests/channels/test_google_chat.py | 4507 | 140 | Tests for the GoogleChatChannel adapter.
tests/channels/test_imessage_daemon.py | 3519 | 109 | Tests for iMessage AppleScript daemon.
tests/channels/test_irc_channel.py | 4119 | 132 | Tests for the IRCChannel adapter.
tests/channels/test_matrix_channel.py | 4659 | 144 | Tests for the MatrixChannel adapter.
tests/channels/test_mattermost.py | 4927 | 142 | Tests for the MattermostChannel adapter.
tests/channels/test_sendblue.py | 8628 | 267 | Tests for SendBlue iMessage/SMS channel.
tests/channels/test_signal_channel.py | 4258 | 132 | Tests for the SignalChannel adapter.
tests/channels/test_slack.py | 4907 | 142 | Tests for the SlackChannel adapter.
tests/channels/test_slack_messaging.py | 2911 | 90 | Tests for Slack messaging channel — Socket Mode binding and message handling.
tests/channels/test_stubs.py | 3991 | 121 | Tests for the channel abstraction stubs.
tests/channels/test_teams.py | 3986 | 122 | Tests for the TeamsChannel adapter.
tests/channels/test_telegram.py | 28407 | 767 | Tests for the TelegramChannel adapter.
tests/channels/test_tier1_gmail.py | 6583 | 196 | Tests for the GmailChannel adapter.
tests/channels/test_twilio_sms.py | 3979 | 127 | Tests for Twilio SMS channel.
tests/channels/test_twitter_bot_e2e.py | 33921 | 880 | End-to-end tests for the Twitter bot mention handler.
tests/channels/test_twitter_channel.py | 6904 | 218 | Tests for the TwitterChannel adapter.
tests/channels/test_webchat.py | 2182 | 71 | Tests for the WebChatChannel adapter.
tests/channels/test_webhook.py | 6154 | 185 | Tests for the WebhookChannel adapter.
tests/channels/test_whatsapp.py | 4317 | 133 | Tests for the WhatsAppChannel adapter.
tests/channels/test_whatsapp_baileys.py | 11103 | 334 | Tests for the WhatsAppBaileysChannel adapter.
tests/cli/__init__.py | 0 | 0 | 
tests/cli/test_add_cmd.py | 2356 | 62 | Tests for the ``jarvis add`` CLI command.
tests/cli/test_agent_cmd.py | 4464 | 120 | Tests for the ``jarvis agents`` CLI commands.
tests/cli/test_ask_agent.py | 19624 | 541 | Tests for ``jarvis ask --agent`` CLI integration.
tests/cli/test_ask_context.py | 2798 | 85 | Tests for context injection integration in ``jarvis ask``.
tests/cli/test_ask_e2e.py | 3679 | 104 | End-to-end tests for ``jarvis ask``.
tests/cli/test_ask_research_model.py | 1374 | 36 | Tests for the ``jarvis ask --research`` planner-model resolution.
tests/cli/test_ask_router.py | 12909 | 351 | Tests for model resolution fallback chain in jarvis ask.
tests/cli/test_ask_vision.py | 4829 | 129 | CLI-level regression tests for ``jarvis ask`` vision input.
tests/cli/test_bench_cmd.py | 2863 | 85 | Tests for the ``jarvis bench`` CLI commands.
tests/cli/test_bench_skills_command.py | 3978 | 116 | Tests for jarvis bench skills CLI command (Plan 2B).
tests/cli/test_channel_cmd.py | 3567 | 105 | Tests for the ``jarvis channel`` CLI commands.
tests/cli/test_chat_cmd.py | 28374 | 750 | Tests for ``jarvis chat`` interactive REPL command.
tests/cli/test_cli.py | 9373 | 229 | Tests for the CLI skeleton.
tests/cli/test_cli_picker_integration.py | 14765 | 403 | Integration tests for CLI model picker and runtime panel paths.
tests/cli/test_cli_picker_security.py | 6267 | 163 | Security tests for CLI model picker and runtime panel layers.
tests/cli/test_config_cmd.py | 9254 | 228 | Tests for the ``jarvis config`` CLI commands.
tests/cli/test_config_set.py | 8672 | 209 | Tests for ``jarvis config set`` command.
tests/cli/test_connect.py | 3554 | 111 | Tests for ``jarvis connect`` CLI command.
tests/cli/test_daemon_cmd.py | 17284 | 411 | Tests for ``jarvis start|stop|restart|status`` daemon management commands.
tests/cli/test_daemon_identity.py | 10340 | 270 | Daemon registrations survive clock changes without accepting recycled PIDs.
tests/cli/test_daemon_state.py | 9731 | 269 | Daemon address bookkeeping.
tests/cli/test_dashboard.py | 913 | 32 | Tests for TUI dashboard (Phase 16.5).
tests/cli/test_deep_research_setup.py | 6415 | 184 | Tests for the deep-research-setup CLI command.
tests/cli/test_digest_cmd.py | 1631 | 55 | Tests for `jarvis digest` CLI command.
tests/cli/test_doctor_cmd.py | 11319 | 293 | Tests for ``jarvis doctor`` CLI command.
tests/cli/test_doctor_labels.py | 2651 | 67 | Tests for ``jarvis doctor`` optional dependency labels.
tests/cli/test_eval_cmd.py | 1522 | 40 | Tests for the ``jarvis eval`` CLI commands.
tests/cli/test_eval_cmd_external_flags.py | 910 | 27 | Verify jarvis eval run exposes --base-url / --api-key for hermes/openclaw.
tests/cli/test_first_run_picker.py | 1722 | 53 | Tests for bare ``jarvis`` routing with model picker.
tests/cli/test_gui_cmd.py | 4428 | 123 | Launch behavior for the source-checkout graphical command.
tests/cli/test_gui_lifecycle.py | 17276 | 475 | Frontend cleanup must target owned processes and release invocation hooks.
tests/cli/test_hints.py | 1999 | 60 | Tests for CLI error hint functions.
tests/cli/test_init_config.py | 3687 | 89 | Tests for ``jarvis init --config`` option (regression for #768).
tests/cli/test_init_digest.py | 2332 | 69 | Tests for ``jarvis init --digest`` config writing.
tests/cli/test_init_guidance.py | 10066 | 241 | Tests for ``jarvis init`` next-steps guidance.
tests/cli/test_init_host.py | 4726 | 118 | Tests for ``jarvis init --host`` option.
tests/cli/test_install_detect.py | 2877 | 85 | Tests for install-method detection.
tests/cli/test_log_config.py | 1290 | 38 | Tests for CLI log configuration.
tests/cli/test_memory_cmd.py | 8999 | 265 | Tests for ``jarvis memory`` CLI commands.
tests/cli/test_mine_cmd.py | 18666 | 565 | Tests for the ``jarvis mine`` CLI.
tests/cli/test_model_cmd.py | 2619 | 71 | Tests for ``jarvis model`` subcommands.
tests/cli/test_model_convert.py | 24014 | 685 | Tests for ``jarvis model convert`` command.
tests/cli/test_model_pull.py | 5662 | 154 | Tests for ``jarvis model pull`` multi-engine support.
tests/cli/test_model_switch.py | 3049 | 107 | Tests for CLI model preset / smart resolution.
tests/cli/test_optimize_skills_command.py | 2939 | 83 | Tests for jarvis optimize skills CLI command (Plan 2A).
tests/cli/test_pearl_cmd.py | 3698 | 130 | Tests for the ``jarvis pearl`` CLI wrappers.
tests/cli/test_preset_bind.py | 1011 | 29 | Preset installation must preserve safe local server defaults (#770).
tests/cli/test_quickstart.py | 8541 | 223 | Tests for ``jarvis quickstart`` command.
tests/cli/test_registry_cmd.py | 7018 | 155 | Tests for the ``jarvis registry`` CLI commands.
tests/cli/test_runtime_panel.py | 1670 | 57 | Tests for CLI runtime panel (context / GPU offload).
tests/cli/test_scan.py | 16969 | 464 | Tests for ``jarvis scan`` privacy scanner CLI command.
tests/cli/test_scan_data_boundaries.py | 12075 | 397 | 
tests/cli/test_self_update.py | 7689 | 221 | Smoke tests for `jarvis self-update`.
tests/cli/test_serve_channel_wiring.py | 14303 | 391 | Tests for JarvisSystem.wire_channel() — channel → agent routing.
tests/cli/test_serve_model_resolution.py | 1960 | 65 | Tests for API server model selection.
tests/cli/test_serve_persona.py | 5260 | 130 | Regression: ``jarvis serve`` must wire the ``SystemPromptBuilder`` into the
tests/cli/test_serve_single_build.py | 11143 | 308 | Regression tests for #263 — ``jarvis serve`` must build the system once.
tests/cli/test_serve_tools.py | 2097 | 73 | Regression tests for tool selection during ``jarvis serve`` startup.
tests/cli/test_skill_cmd.py | 12873 | 356 | Tests for the ``jarvis skill`` CLI commands.
tests/cli/test_skill_run_security.py | 7835 | 228 | End-to-end skill CLI execution and security regressions.
tests/cli/test_standalone_security.py | 5931 | 168 | Standalone channel/research launchers inherit configured security.
tests/cli/test_telemetry_cmd.py | 5459 | 155 | Tests for the ``jarvis telemetry`` CLI commands.
tests/cli/test_tool_cmd.py | 11025 | 239 | Tests for the ``jarvis tool`` CLI commands.
tests/cli/test_vault_cmd.py | 2457 | 73 | Tests for the ``jarvis vault`` CLI commands.
tests/cli/test_version_check.py | 10076 | 265 | Tests for the post-command "new version available" hint.
tests/cli/test_workflow_cmd.py | 956 | 29 | Tests for the ``jarvis workflow`` CLI commands.
tests/connectors/__init__.py | 0 | 0 | 
tests/connectors/test_apple_calendar.py | 5881 | 170 | Integration tests for the read-only Apple Calendar connector and tools.
tests/connectors/test_apple_contacts.py | 23295 | 627 | Tests for AppleContactsConnector — local macOS Contacts database connector.
tests/connectors/test_apple_health.py | 5904 | 162 | Tests for AppleHealthConnector -- local HealthKit DB / export XML.
tests/connectors/test_apple_music.py | 6402 | 178 | Tests for AppleMusicConnector -- local Music.app via AppleScript.
tests/connectors/test_apple_notes.py | 9863 | 272 | Tests for AppleNotesConnector — local macOS Notes database connector.
tests/connectors/test_attachment_store.py | 3710 | 103 | Tests for AttachmentStore — content-addressed blob storage.
tests/connectors/test_chunker.py | 10683 | 265 | Tests for SemanticChunker — type-aware text splitting.
tests/connectors/test_connector_health.py | 5777 | 176 | Health check tests for all data source connectors.
tests/connectors/test_connectors_router_oauth.py | 15595 | 373 | Regression tests for the connectors-router OAuth flow (issue #512).
tests/connectors/test_dropbox.py | 5860 | 170 | Tests for DropboxConnector — OAuth-authenticated Dropbox sync connector.
tests/connectors/test_embedding_store.py | 5695 | 165 | Tests for EmbeddingStore — disk-persistent ColBERT token-level embeddings.
tests/connectors/test_embeddings.py | 1359 | 36 | Tests for openjarvis.connectors.embeddings.default_embedder.
tests/connectors/test_gcalendar.py | 7233 | 194 | Tests for GCalendarConnector — OAuth-authenticated Google Calendar sync connector.
tests/connectors/test_gcontacts.py | 6566 | 177 | Tests for GContactsConnector — OAuth-authenticated Google Contacts sync connector.
tests/connectors/test_gdrive.py | 6882 | 183 | Tests for GDriveConnector — OAuth-authenticated Google Drive sync connector.
tests/connectors/test_github_notifications.py | 3344 | 106 | Tests for GitHubNotificationsConnector — GitHub REST API.
tests/connectors/test_gmail.py | 28589 | 777 | Tests for GmailConnector — OAuth-authenticated Gmail sync connector.
tests/connectors/test_gmail_rate_limits.py | 2270 | 76 | Gmail uses HTTP 403 as well as 429 for transient quota limits.
tests/connectors/test_google_tasks.py | 3052 | 91 | Tests for GoogleTasksConnector — Google Tasks API v1.
tests/connectors/test_granola.py | 17869 | 465 | Tests for GranolaConnector — Granola meeting notes sync connector.
tests/connectors/test_hackernews.py | 3445 | 125 | Tests for HackerNewsConnector — HN Firebase API.
tests/connectors/test_hybrid_search.py | 5775 | 182 | Tests for source-aware HybridSearch behavior.
tests/connectors/test_imap.py | 18633 | 544 | Tests for the generic IMAP connector and its network boundary.
tests/connectors/test_imessage.py | 7634 | 203 | Tests for IMessageConnector — local macOS Messages database connector.
tests/connectors/test_incremental_sync.py | 6415 | 187 | Tests for incremental sync via the `since` parameter in SyncEngine.
tests/connectors/test_integration.py | 2834 | 76 | Integration test: Obsidian vault → SyncEngine → KnowledgeStore → knowledge_search.
tests/connectors/test_live_smoke.py | 3405 | 89 | Live smoke test — full pipeline with real markdown files.
tests/connectors/test_new_connectors_live.py | 1922 | 58 | Live smoke tests for new connectors — require real API credentials.
tests/connectors/test_news_rss.py | 10821 | 359 | Tests for NewsRSSConnector — RSS/Atom feed aggregator.
tests/connectors/test_notion.py | 8939 | 252 | Tests for NotionConnector — Notion API sync connector.
tests/connectors/test_oauth_flow.py | 6638 | 184 | Tests for OAuth token exchange and Google connector integration.
tests/connectors/test_obsidian.py | 6929 | 187 | Tests for ObsidianConnector — filesystem Markdown vault connector.
tests/connectors/test_oura.py | 2548 | 96 | Tests for OuraConnector — Oura Ring REST API v2.
tests/connectors/test_outlook.py | 3494 | 94 | Tests for OutlookConnector — thin subclass of GmailIMAPConnector.
tests/connectors/test_pipeline.py | 19768 | 565 | Tests for IngestionPipeline — dedup, chunking, and indexed storage.
tests/connectors/test_pipeline_attachments.py | 5460 | 164 | Tests for attachment processing in IngestionPipeline.
tests/connectors/test_retriever.py | 11120 | 324 | Tests for TwoStageRetriever — BM25 recall + optional semantic reranking.
tests/connectors/test_scheduler.py | 5019 | 141 | Tests for SyncScheduler — periodic incremental sync background thread.
tests/connectors/test_slack_connector.py | 24043 | 620 | Tests for SlackConnector — OAuth-authenticated Slack channel message sync.
tests/connectors/test_spotify.py | 2859 | 94 | Tests for SpotifyConnector — Spotify Web API.
tests/connectors/test_store.py | 19214 | 570 | Tests for KnowledgeStore — source-aware SQLite/FTS5 memory backend.
tests/connectors/test_strava.py | 2683 | 97 | Tests for StravaConnector — Strava REST API v3.
tests/connectors/test_stubs.py | 2747 | 103 | Tests for connector base types and registry.
tests/connectors/test_sync_engine.py | 13430 | 407 | Tests for SyncEngine — checkpoint/resume connector orchestration.
tests/connectors/test_weather.py | 2783 | 97 | Tests for WeatherConnector — OpenWeatherMap API.
tests/connectors/test_whatsapp.py | 7365 | 195 | Tests for the WhatsApp chat export connector.
tests/core/__init__.py | 0 | 0 | 
tests/core/test_config.py | 23691 | 619 | Tests for configuration, hardware detection, and engine recommendation.
tests/core/test_config_key_validation.py | 2586 | 73 | Tests for config key validation.
tests/core/test_config_paths.py | 8346 | 198 | Tests for the env-aware OpenJarvis home-directory resolver (issue #462).
tests/core/test_config_phase3.py | 2542 | 79 | Tests for Phase 3 config additions (AgentConfig expansion, ServerConfig).
tests/core/test_config_phase4.py | 2970 | 78 | Tests for LearningConfig and its integration into JarvisConfig.
tests/core/test_config_phase5.py | 1969 | 55 | Phase 5 foundation tests — BenchmarkRegistry and config.
tests/core/test_config_skills_sources.py | 2461 | 79 | Tests for skills.sources config section.
tests/core/test_config_weather.py | 907 | 34 | Configuration coverage for the native weather tool.
tests/core/test_credentials.py | 9566 | 242 | Tests for credential persistence module.
tests/core/test_deep_research_config.py | 1565 | 59 | Tests for Deep Research planner configuration.
tests/core/test_events.py | 5169 | 158 | Tests for the pub/sub event bus.
tests/core/test_intent_routing.py | 2710 | 67 | Tests for intent-based agent routing in JarvisSystem.
tests/core/test_preset_configs.py | 1485 | 46 | Smoke test: every shipped preset config must load cleanly.
tests/core/test_recommend_model.py | 6348 | 166 | Tests for ``recommend_model()`` hardware-aware model recommendation.
tests/core/test_registry.py | 3921 | 113 | Tests for the decorator-based registry system.
tests/core/test_resolve_json_or_file.py | 3999 | 106 | Tests for resolve_json_or_file in openjarvis.core.config.
tests/core/test_rust_bridge.py | 9526 | 274 | Tests for the Rust bridge module.
tests/core/test_skills_learning_config.py | 1658 | 44 | Tests for SkillsLearningConfig and its wiring into LearningConfig.
tests/core/test_types.py | 3317 | 110 | Tests for core data types.
tests/core/test_utils.py | 6900 | 188 | Tests for cross-platform process helpers in ``openjarvis.core.utils``.
tests/daemon/__init__.py | 0 | 0 | 
tests/daemon/test_gateway.py | 604 | 19 | 
tests/daemon/test_session_expiry.py | 1038 | 30 | 
tests/deploy/__init__.py | 0 | 0 | 
tests/deploy/test_deploy_auth.py | 2329 | 70 | Deployment configs must not ship an unauthenticated public server (#221).
tests/deploy/test_render_blueprint.py | 5015 | 158 | Render Blueprint stays aligned with settings the server consumes.
tests/deployment/test_desktop_network_policy.py | 2436 | 65 | Regression guards for the desktop app's outbound network policy.
tests/deployment/test_docker.py | 11562 | 295 | Tests for Docker and deployment files.
tests/deployment/test_docs_leaderboard.py | 1925 | 46 | Static guards for the docs-site savings-leaderboard Supabase wiring.
tests/deployment/test_packaging.py | 7814 | 201 | Guards for the openjarvis-rust packaging split (#584 / #615).
tests/deployment/test_release_artifact_validation.py | 3577 | 111 | Release archives must fit the upload budget before publication.
tests/deployment/test_windows_arm64_desktop.py | 5079 | 139 | Exercise ARM64 sidecar staging and reject incorrectly labelled executables.
tests/engine/__init__.py | 0 | 0 | 
tests/engine/conftest.py | 659 | 25 | Engine test fixtures — ensure cloud API key isolation across tests.
tests/engine/test_anthropic_sampling.py | 3583 | 113 | Anthropic's fixed-sampling models reject the legacy temperature field.
tests/engine/test_anthropic_sdk_compat.py | 3828 | 113 | Exercise the real Anthropic SDK against an in-memory HTTP transport.
tests/engine/test_apple_fm_engine.py | 22518 | 611 | Tests for the in-process Apple Foundation Models engine.
tests/engine/test_apple_fm_shim.py | 12625 | 328 | Tests for the Apple FM shim.
tests/engine/test_base.py | 1850 | 61 | 
tests/engine/test_cache_breakpoint.py | 1363 | 38 | 
tests/engine/test_cloud.py | 35949 | 916 | Tests for the Cloud engine backend.
tests/engine/test_cloud_atlascloud.py | 20909 | 528 | Tests for Atlas Cloud cloud-provider support.
tests/engine/test_cloud_extended.py | 25310 | 652 | Extended cloud engine tests -- Gemini support and updated models.
tests/engine/test_cloud_minimax.py | 14501 | 352 | Tests for MiniMax cloud provider support.
tests/engine/test_cloud_stream_full.py | 27824 | 809 | Tests for CloudEngine.stream_full, _stream_full_openai, _stream_full_anthropic,
tests/engine/test_discovery.py | 14807 | 419 | Tests for engine discovery.
tests/engine/test_engine_model_matrix.py | 9966 | 273 | Cross-product parametrized tests: engine x scenario.
tests/engine/test_engine_wrappers.py | 4782 | 146 | Tests for InstrumentedEngine, GuardrailsEngine, and MultiEngine stream_full
tests/engine/test_gemma_cpp.py | 15870 | 424 | Tests for the gemma.cpp engine backend.
tests/engine/test_lemonade.py | 4328 | 122 | Tests for the Lemonade engine backend.
tests/engine/test_litellm.py | 7928 | 216 | Tests for the LiteLLM engine backend.
tests/engine/test_llamacpp_models.py | 7298 | 209 | Tests for llama.cpp engine with compatible models.
tests/engine/test_lmstudio.py | 3576 | 98 | Tests for the LM Studio engine backend.
tests/engine/test_mlx.py | 2522 | 71 | Tests for the MLX engine (OpenAI-compatible).
tests/engine/test_nim.py | 4563 | 136 | Tests for the NVIDIA NIM inference engine.
tests/engine/test_ollama.py | 20689 | 509 | Tests for the Ollama engine backend.
tests/engine/test_ollama_models.py | 9009 | 251 | Tests for Ollama engine with extended local model set.
tests/engine/test_ollama_runtime_options.py | 759 | 27 | Tests for Ollama runtime option wiring (num_ctx / num_gpu).
tests/engine/test_openai_compat.py | 17277 | 420 | Tests for the OpenAI-compatible engine base (covers vLLM + llama.cpp).
tests/engine/test_openai_compat_api_key.py | 4787 | 110 | API-key (Authorization header) support in the OpenAI-compat engine base.
tests/engine/test_openai_compat_tools.py | 10568 | 294 | Tests for tool_calls extraction in _OpenAICompatibleEngine and OllamaEngine.
tests/engine/test_optional_imports.py | 795 | 23 | Diagnostics for optional inference-engine imports.
tests/engine/test_stream_full.py | 8136 | 235 | Tests for StreamChunk dataclass and stream_full() engine method.
tests/engine/test_structured_output.py | 15106 | 378 | Tests for structured output / JSON mode across engines.
tests/engine/test_vllm_models.py | 8308 | 226 | Tests for vLLM engine with extended local model set.
tests/evals/__init__.py | 0 | 0 | 
tests/evals/test_agentic_runner.py | 9964 | 282 | Tests for AgenticRunner with mock agent and dataset.
tests/evals/test_ama_bench.py | 8469 | 232 | Tests for AMA-Bench dataset provider and scorer.
tests/evals/test_benchmark_datasets.py | 15765 | 452 | Tests for all 15 benchmark dataset and scorer registrations.
tests/evals/test_dataset_splits_integration.py | 4136 | 96 | Integration test: each provider's split kwarg produces disjoint train/test slices.
tests/evals/test_deepplanning.py | 3225 | 93 | Tests for DeepPlanning benchmark.
tests/evals/test_display.py | 6760 | 214 | Tests for the Rich display helpers in openjarvis.evals.core.display.
tests/evals/test_energy_rails_in_results.py | 3070 | 85 | Eval output must record which hardware did the work, and how it was measured.
tests/evals/test_environment_provider.py | 1087 | 42 | Tests for EnvironmentProvider ABC.
tests/evals/test_episode_mode.py | 1679 | 55 | Tests for EvalRunner episode mode.
tests/evals/test_eval_telemetry_wiring.py | 20119 | 592 | Tests for telemetry wiring in the eval pipeline.
tests/evals/test_eval_trace.py | 4977 | 152 | Tests for QueryTrace and TurnTrace data model.
tests/evals/test_event_recorder.py | 2691 | 90 | Tests for EventRecorder thread safety and functionality.
tests/evals/test_export.py | 18891 | 509 | Tests for eval export utilities.
tests/evals/test_jarvis_agent_backend_fields.py | 2066 | 48 | Verify JarvisAgentBackend.generate_full returns the spec §6.2 extended fields.
tests/evals/test_jarvis_agent_backend_skills.py | 2717 | 71 | Tests for JarvisAgentBackend skills_enabled / overlay_dir kwargs (Plan 2B).
tests/evals/test_jarvis_direct_backend_fields.py | 1652 | 44 | Verify JarvisDirectBackend.generate_full returns the spec §6.2 extended fields.
tests/evals/test_lifelong_agent.py | 38440 | 1098 | Tests for LifelongAgentBench benchmark.
tests/evals/test_loghub.py | 5775 | 168 | Tests for LogHub dataset provider.
tests/evals/test_paperarena.py | 4124 | 121 | Tests for PaperArena benchmark.
tests/evals/test_pinchbench_dataset.py | 2938 | 131 | Tests for PinchBench dataset provider.
tests/evals/test_pinchbench_grading.py | 5480 | 162 | Tests for PinchBench grading functions.
tests/evals/test_pinchbench_integration.py | 3687 | 124 | Integration tests for PinchBench eval pipeline.
tests/evals/test_pinchbench_transcript.py | 3539 | 94 | Tests for TurnTrace tool_calls field and PinchBench transcript translation.
tests/evals/test_pricing.py | 1273 | 39 | Tests for eval pricing module.
tests/evals/test_skill_benchmark.py | 12874 | 383 | Tests for SkillBenchmarkRunner (Plan 2B).
tests/evals/test_terminalbench_env.py | 9707 | 248 | Tests for TerminalBenchTaskEnv (mocked terminal_bench dependency).
tests/evals/test_terminalbench_native_backend.py | 11901 | 303 | Tests for the TerminalBench native backend (mocked terminal_bench).
tests/evals/test_trackers.py | 12236 | 345 | Tests for eval result trackers (W&B + Google Sheets).
tests/evals/test_use_case_benchmarks.py | 17808 | 484 | Tests for the 5 use-case benchmark datasets and scorers.
tests/evals/comparison/__init__.py | 46 | 2 | Tests for openjarvis.evals.comparison.
tests/evals/comparison/test_cli_backend_dispatch.py | 2732 | 86 | Verify cli._build_backend correctly dispatches hermes/openclaw.
tests/evals/comparison/test_export_to_table_gen_roundtrip.py | 9465 | 263 | Round-trip test: EvalRunner output -> table_gen reads it correctly.
tests/evals/comparison/test_hermes_backend.py | 6925 | 192 | Tests for openjarvis.evals.backends.external.hermes_agent.HermesBackend.
tests/evals/comparison/test_live_external.py | 3599 | 112 | Integration tests that spawn real Hermes/OpenClaw subprocesses.
tests/evals/comparison/test_make_configs.py | 3398 | 98 | Tests for openjarvis.evals.comparison.make_configs.
tests/evals/comparison/test_openclaw_backend.py | 6335 | 178 | Tests for openjarvis.evals.backends.external.openclaw.OpenClawBackend.
tests/evals/comparison/test_openclaw_runner_contract.py | 2464 | 82 | Contract tests for the OpenClaw subprocess runner.
tests/evals/comparison/test_runner_error_path_framework.py | 10178 | 306 | Verify error-path EvalResult propagates framework_name from backend.
tests/evals/comparison/test_subprocess_runner.py | 5769 | 168 | Tests for openjarvis.evals.backends.external._subprocess_runner.
tests/evals/comparison/test_table_gen.py | 9914 | 292 | Tests for openjarvis.evals.comparison.table_gen.
tests/evals/comparison/test_third_party.py | 5118 | 140 | Tests for openjarvis.evals.comparison.third_party.
tests/evals/core/__init__.py | 0 | 0 | 
tests/evals/core/test_config_split_parsing.py | 1927 | 71 | Regression: the `split` key under [[benchmarks]] is parsed and plumbed.
tests/evals/core/test_config_timeouts.py | 2143 | 73 | Tests for terminal-bench harness timeout plumbing through TOML configs.
tests/evals/core/test_splits.py | 2424 | 73 | 
tests/evals/datasets/__init__.py | 0 | 0 | 
tests/evals/datasets/test_browser_assistant.py | 1689 | 62 | Tests for the browser_assistant dataset.
tests/evals/datasets/test_coding_assistant.py | 1169 | 39 | Tests for the coding_assistant dataset.
tests/evals/datasets/test_daily_digest.py | 1126 | 39 | Tests for the daily_digest dataset.
tests/evals/datasets/test_doc_qa.py | 1576 | 57 | Tests for the doc_qa dataset.
tests/evals/datasets/test_external_agent_datasets.py | 2930 | 74 | Smoke test: each external-corpus provider loads and iterates records.
tests/evals/datasets/test_security_scanner.py | 1481 | 49 | Tests for the security_scanner dataset.
tests/evals/datasets/test_taubench.py | 3125 | 99 | Tests for the TauBench optional dependency boundary.
tests/evals/scorers/__init__.py | 0 | 0 | 
tests/evals/scorers/test_browser_assistant.py | 3227 | 106 | Tests for the browser_assistant scorer.
tests/evals/scorers/test_checklist.py | 2722 | 90 | Tests for the shared binary checklist scorer.
tests/evals/scorers/test_coding_assistant.py | 2245 | 70 | Tests for the coding_assistant scorer.
tests/evals/scorers/test_daily_digest.py | 2858 | 89 | Tests for the daily_digest scorer.
tests/evals/scorers/test_doc_qa.py | 3463 | 113 | Tests for the doc_qa scorer.
tests/evals/scorers/test_liveresearch_continuous.py | 9638 | 291 | Tests for continuous-score reporting and judge-response reparsing.
tests/evals/scorers/test_security_scanner.py | 3841 | 124 | Tests for the security_scanner scorer.
tests/fixtures/docs/channels.md | 808 | 20 | Channel Integrations
tests/fixtures/docs/engines.md | 614 | 20 | Inference Engines
tests/fixtures/docs/hardware.md | 691 | 21 | Hardware Requirements
tests/fixtures/docs/memory.md | 652 | 16 | Memory and Retrieval
tests/hardware/__init__.py | 0 | 0 | 
tests/hardware/test_amd.py | 6940 | 205 | AMD-specific hardware tests.
tests/hardware/test_apple.py | 4746 | 137 | Apple Silicon hardware tests.
tests/hardware/test_hardware_profiles.py | 5941 | 161 | Tests for hardware detection, GPU vendor identification,
tests/hardware/test_nvidia.py | 6071 | 180 | NVIDIA-specific hardware tests.
tests/install/__init__.py | 0 | 0 | 
tests/install/conftest.py | 1485 | 35 | Test fixtures for installer / cold-start refresh tests.
tests/install/test_analytics_consent.py | 4333 | 123 | Terminal answers, unattended init, and persisted runtime analytics choices.
tests/install/test_bg_state.py | 3963 | 108 | Tests for openjarvis.cli._bg_state.
tests/install/test_bootstrap_cli.py | 2502 | 83 | Tests for the jarvis _bootstrap hidden CLI command.
tests/install/test_bootstrap_config.py | 5329 | 127 | Tests for openjarvis.cli._bootstrap.write_initial_config.
tests/install/test_bootstrap_keys.py | 3221 | 102 | Tests for openjarvis.cli._bootstrap.detect_cloud_keys.
tests/install/test_chat_banner.py | 1597 | 43 | Tests for the chat startup banner.
tests/install/test_chat_notifications.py | 1815 | 51 | Tests for between-turn completion notifications.
tests/install/test_doctor_bg.py | 1431 | 37 | Tests for the doctor 'Background tasks' section.
tests/install/test_first_run.py | 3332 | 99 | Tests for openjarvis.cli._first_run.check_and_route.
tests/install/test_fixture_smoke.py | 654 | 19 | Smoke test that the tmp_openjarvis_home fixture works.
tests/install/test_init_cloud_detect.py | 2354 | 71 | Tests for init's cloud auto-detect and from-bare-jarvis flag.
tests/install/test_quickstart_prerequisites.py | 8815 | 245 | Exercise quickstart preflight with local command stubs, without installing.
tests/install/test_uninstall.py | 6038 | 190 | Safety contract for the POSIX uninstaller.
tests/install/test_version_history.py | 9121 | 246 | Exercise installer clone flags and update repair against real local Git repos.
tests/install/test_windows_prerequisites.py | 7566 | 208 | Run Windows prerequisite helpers in PowerShell without installing anything.
tests/install/bash/run_installer_pty.py | 2032 | 75 | Run the real curl-pipe installer under a terminal with scripted answers.
tests/install/bash/test_bg_orchestrator.bats | 1856 | 0 | 
tests/install/bash/test_build_extension.bats | 1690 | 0 | 
tests/install/bash/test_install.bats | 14246 | 0 | 
tests/install/bash/test_install_rust.bats | 1095 | 0 | 
tests/install/bash/test_pull_model.bats | 1677 | 0 | 
tests/install/bash/stubs/cargo | 107 | 0 | 
tests/install/bash/stubs/curl | 235 | 0 | 
tests/install/bash/stubs/git | 2116 | 0 | 
tests/install/bash/stubs/ollama | 189 | 0 | 
tests/install/bash/stubs/ollama-mock | 673 | 0 | 
tests/install/bash/stubs/rustup | 137 | 0 | 
tests/install/bash/stubs/uv | 151 | 0 | 
tests/install/cases/README.md | 673 | 18 | Failure-mode regression catalog
tests/install/cases/missing-git.md | 638 | 24 | Failure: git missing from PATH
tests/install/cases/run-as-root.md | 526 | 24 | Failure: install.sh run as root
tests/integration/test_agent_manager_e2e.py | 3076 | 88 | End-to-end test: create agent from template, add task, verify state.
tests/integration/test_atlascloud_cloud.py | 3740 | 104 | Integration test for the Atlas Cloud cloud provider.
tests/integration/test_integration.py | 21125 | 622 | End-to-end integration tests for Phase 3 and Phase 4 components.
tests/integration/test_integration_extended.py | 19230 | 558 | Extended integration tests for new components (Phase 6+).
tests/integration/test_minimax_cloud.py | 2455 | 65 | Integration test for MiniMax cloud provider.
tests/intelligence/__init__.py | 0 | 0 | 
tests/intelligence/test_model_catalog.py | 2281 | 64 | Tests for the built-in model catalog.
tests/intelligence/test_model_catalog_extended.py | 12797 | 349 | Tests for the extended model catalog -- all new ModelSpec entries.
tests/intelligence/test_router.py | 1319 | 47 | Tests for the intelligence router via canonical learning.routing.router imports.
tests/intelligence/test_routing_models.py | 1019 | 33 | Tests for the router with model catalog via canonical imports.
tests/learning/__init__.py | 0 | 0 | 
tests/learning/test_agent_evolver.py | 8201 | 241 | Tests for AgentConfigEvolver — trace-driven agent config evolution.
tests/learning/test_device_selection.py | 2524 | 84 | Tests for PyTorch device selection (cuda > mps > cpu).
tests/learning/test_feedback_collector.py | 8261 | 240 | Tests for openjarvis.optimize.feedback.collector module.
tests/learning/test_heuristic_policy.py | 855 | 24 | Tests for heuristic policy registration.
tests/learning/test_heuristic_reward.py | 4567 | 152 | Tests for HeuristicRewardFunction.
tests/learning/test_learning_api.py | 2384 | 82 | Tests for the Learning Dashboard API endpoints.
tests/learning/test_learning_orchestrator.py | 6220 | 195 | Tests for LearningOrchestrator -- coordinate trace->learn->eval loop.
tests/learning/test_learning_taxonomy.py | 1011 | 36 | Tests for the learning policy ABC taxonomy.
tests/learning/test_llm_optimizer.py | 36700 | 986 | Tests for openjarvis.optimize.llm_optimizer module.
tests/learning/test_multi_bench_runner.py | 10911 | 319 | Tests for MultiBenchTrialRunner and related multi-benchmark features.
tests/learning/test_optimize_cmd.py | 6265 | 173 | Smoke tests for ``jarvis optimize`` and ``jarvis feedback`` CLI commands,
tests/learning/test_optimize_store.py | 16457 | 469 | Tests for openjarvis.optimize.store module.
tests/learning/test_optimize_types.py | 19867 | 577 | Tests for openjarvis.optimize.types module.
tests/learning/test_optimizer_engine.py | 26125 | 792 | Tests for openjarvis.optimize.optimizer module.
tests/learning/test_orchestrator_skill_optimization.py | 4900 | 145 | Tests for LearningOrchestrator opt-in skill optimization (Plan 2A).
tests/learning/test_pareto.py | 7930 | 225 | Tests for compute_pareto_frontier.
tests/learning/test_personal_synthesizer.py | 13918 | 393 | Tests for the personal benchmark system.
tests/learning/test_router.py | 6545 | 196 | Tests for the heuristic model router (canonical location).
tests/learning/test_router_stubs.py | 2362 | 75 | Tests for RouterPolicy and QueryAnalyzer ABCs (canonical location).
tests/learning/test_routing_models.py | 7660 | 238 | Tests for router behavior with the extended model catalog.
tests/learning/test_search_space.py | 15075 | 449 | Tests for openjarvis.optimize.search_space module.
tests/learning/test_skill_discovery.py | 7914 | 212 | Tests for SkillDiscovery — mining recurring tool sequences from traces.
tests/learning/test_skill_optimizer.py | 7055 | 183 | Tests for SkillOptimizer (Plan 2A) — buckets traces by skill, runs DSPy/GEPA.
tests/learning/test_stubs.py | 1022 | 35 | Tests for learning ABC stubs.
tests/learning/test_system_learning.py | 2103 | 51 | Tests for LearningOrchestrator integration with SystemBuilder.
tests/learning/test_trace_judge.py | 7151 | 211 | Tests for openjarvis.optimize.feedback.judge module.
tests/learning/test_trial_runner.py | 15660 | 433 | Tests for openjarvis.optimize.trial_runner module.
tests/learning/agents/__init__.py | 0 | 0 | 
tests/learning/agents/test_ace_optimizer.py | 8744 | 220 | Tests for the ACE agent optimizer (mocked — no ace dep required).
tests/learning/agents/test_dspy_optimizer.py | 5549 | 147 | Tests for the DSPy agent optimizer (mocked -- no dspy dependency required).
tests/learning/agents/test_gepa_optimizer.py | 3332 | 98 | Tests for the GEPA agent optimizer (mocked -- no gepa dependency required).
tests/learning/intelligence/__init__.py | 0 | 0 | 
tests/learning/intelligence/test_grpo_trainer.py | 3319 | 89 | Tests for the general-purpose GRPO trainer.
tests/learning/intelligence/test_sft_trainer.py | 2448 | 67 | Tests for the general-purpose SFT trainer.
tests/learning/routing/__init__.py | 0 | 0 | 
tests/learning/routing/test_complexity.py | 8874 | 234 | Tests for query complexity analyzer.
tests/learning/routing/test_learned_router.py | 5541 | 170 | Tests for LearnedRouterPolicy (merged trace-driven + SFT routing).
tests/learning/routing/test_utils.py | 982 | 28 | Tests for classify_query utility.
tests/learning/spec_search/__init__.py | 44 | 2 | Tests for the spec-search subsystem.
tests/learning/spec_search/test_applier_base.py | 3735 | 106 | Tests for openjarvis.learning.spec_search.execute.base module.
tests/learning/spec_search/test_applier_lora_stub.py | 1709 | 54 | Tests for LoRA stub applier.
tests/learning/spec_search/test_appliers_agent.py | 7138 | 211 | Tests for agent-pillar appliers.
tests/learning/spec_search/test_appliers_intelligence.py | 4008 | 123 | Tests for intelligence-pillar appliers.
tests/learning/spec_search/test_appliers_tools.py | 5030 | 146 | Tests for tools-pillar appliers.
tests/learning/spec_search/test_benchmark_gate.py | 5098 | 148 | Tests for openjarvis.learning.spec_search.gate.benchmark_gate module.
tests/learning/spec_search/test_checkpoint_store.py | 7510 | 219 | Tests for openjarvis.learning.spec_search.checkpoint.store module.
tests/learning/spec_search/test_cold_start.py | 3481 | 102 | Tests for openjarvis.learning.spec_search.gate.cold_start module.
tests/learning/spec_search/test_composite_reward.py | 3125 | 80 | Tests for the paper Eq. 1 composite reward.
tests/learning/spec_search/test_diagnose_tools.py | 12106 | 331 | Tests for openjarvis.learning.spec_search.diagnose.tools module.
tests/learning/spec_search/test_diagnose_types.py | 5344 | 174 | Tests for openjarvis.learning.spec_search.diagnose.types module.
tests/learning/spec_search/test_diagnosis_runner.py | 8155 | 236 | Tests for openjarvis.learning.spec_search.diagnose.runner module.
tests/learning/spec_search/test_execution_loop.py | 5028 | 151 | Tests for the per-edit execution loop.
tests/learning/spec_search/test_external_adapter.py | 4062 | 139 | Tests for openjarvis.learning.spec_search.external_adapter.
tests/learning/spec_search/test_live_integration.py | 6071 | 178 | Live integration tests for the spec-search subsystem.
tests/learning/spec_search/test_models.py | 20953 | 587 | Tests for openjarvis.learning.spec_search.models module.
tests/learning/spec_search/test_multi_session.py | 4965 | 147 | Tests for SpecSearchLoop (paper Algorithm 1).
tests/learning/spec_search/test_orchestrator.py | 7240 | 209 | Tests for SpecSearchOrchestrator — full session with mocks.
tests/learning/spec_search/test_paths.py | 3753 | 108 | Tests for openjarvis.learning.spec_search.storage.paths module.
tests/learning/spec_search/test_pending_queue.py | 2722 | 74 | Tests for openjarvis.learning.spec_search.pending_queue module.
tests/learning/spec_search/test_planner.py | 9461 | 273 | Tests for openjarvis.learning.spec_search.plan.planner module.
tests/learning/spec_search/test_prompt_diff.py | 7006 | 213 | Tests for openjarvis.learning.spec_search.plan.prompt_diff module.
tests/learning/spec_search/test_regression.py | 3625 | 90 | Tests for openjarvis.learning.spec_search.gate.regression module.
tests/learning/spec_search/test_risk_tier.py | 5005 | 121 | Tests for openjarvis.learning.spec_search.plan.risk_tier module.
tests/learning/spec_search/test_rollback.py | 2909 | 88 | Integration test: apply session then rollback via CheckpointStore.
tests/learning/spec_search/test_session_store.py | 9672 | 286 | Tests for openjarvis.learning.spec_search.storage.session_store module.
tests/learning/spec_search/test_teacher_agent.py | 7982 | 253 | Tests for openjarvis.learning.spec_search.diagnose.teacher_agent module.
tests/learning/spec_search/test_triggers.py | 1707 | 53 | Tests for openjarvis.learning.spec_search.triggers module.
tests/learning/training/__init__.py | 0 | 0 | 
tests/learning/training/test_data.py | 8096 | 239 | Tests for TrainingDataMiner — SFT, routing, and agent config extraction.
tests/learning/training/test_lora.py | 7201 | 202 | Tests for LoRATrainer — LoRA/QLoRA fine-tuning from trace-derived SFT pairs.
tests/mcp/__init__.py | 0 | 0 | 
tests/mcp/test_client.py | 7517 | 207 | Tests for the MCP client.
tests/mcp/test_client_extended.py | 7252 | 177 | Extended tests for MCPClient — initialize params, notify, context manager.
tests/mcp/test_discovery.py | 13743 | 398 | Tests for _discover_external_mcp in SystemBuilder.
tests/mcp/test_loader.py | 11013 | 283 | Regression tests for openjarvis.mcp.loader.load_mcp_tools_from_config.
tests/mcp/test_mcp_tools_matrix.py | 3298 | 83 | Matrix tests — verify every built-in tool is discoverable and callable via MCP.
tests/mcp/test_protocol.py | 5612 | 168 | Tests for MCP protocol message types.
tests/mcp/test_resolve_mcp_servers.py | 2216 | 56 | Tests for resolve_mcp_servers in openjarvis.core.config.
tests/mcp/test_server.py | 10540 | 307 | Tests for the MCP server.
tests/mcp/test_server_upgrade.py | 5093 | 133 | Tests for MCP server upgrade to protocol version 2025-11-25.
tests/mcp/test_streamable_http_transport.py | 8558 | 205 | Tests for the StreamableHTTPTransport class.
tests/mcp/test_transport.py | 25105 | 664 | Tests for MCP transport implementations.
tests/memory/__init__.py | 0 | 0 | 
tests/memory/test_bm25.py | 4690 | 157 | Tests for the BM25 memory backend.
tests/memory/test_chunking.py | 9501 | 256 | Tests for the document chunking pipeline.
tests/memory/test_colbert.py | 4780 | 165 | Tests for the ColBERTv2 late interaction memory backend.
tests/memory/test_context.py | 16840 | 501 | Tests for context injection.
tests/memory/test_embeddings.py | 2153 | 74 | Tests for the embeddings abstraction layer.
tests/memory/test_fact_extractor.py | 3580 | 106 | Tests for the LLM-backed fact extractor (openjarvis.memory.extractor).
tests/memory/test_fact_store.py | 16230 | 505 | Tests for the persistent fact store (openjarvis.memory.store).
tests/memory/test_faiss.py | 6458 | 199 | Tests for the FAISS dense retrieval memory backend.
tests/memory/test_hybrid.py | 7318 | 225 | Tests for the Hybrid RRF memory backend.
tests/memory/test_ingest.py | 5365 | 178 | Tests for document ingestion and file type detection.
tests/memory/test_memory_service.py | 13894 | 403 | Tests for the background memory service (openjarvis.memory.service).
tests/memory/test_retrieval_quality.py | 7776 | 196 | Retrieval quality tests with a fixed corpus across backends.
tests/memory/test_sqlite.py | 5982 | 179 | Tests for the SQLite/FTS5 memory backend.
tests/memory/test_storage_suite.py | 7594 | 190 | Parametrized storage tests across all memory backends.
tests/mining/__init__.py | 0 | 0 | 
tests/mining/conftest.py | 2762 | 101 | Mining-specific test fixtures.
tests/mining/test_apple_mps_pearl.py | 7209 | 208 | Tests for openjarvis.mining.apple_mps_pearl.
tests/mining/test_cli.py | 6140 | 191 | CLI smoke tests via Click CliRunner.
tests/mining/test_collector.py | 2399 | 74 | Tests for MiningTelemetryCollector, shipped in v1 but unwired.
tests/mining/test_cpu_pearl.py | 10425 | 290 | Tests for openjarvis.mining.cpu_pearl.CpuPearlProvider.
tests/mining/test_discovery.py | 8217 | 246 | Tests for mining/_discovery.py — capability detection matrix.
tests/mining/test_docker.py | 14399 | 373 | Tests for mining/_docker.py — Docker SDK orchestration via mocks.
tests/mining/test_install.py | 2360 | 65 | Tests for openjarvis.mining._install.
tests/mining/test_metrics.py | 1921 | 55 | Tests for mining/_metrics.py — Prometheus → MiningStats adapter.
tests/mining/test_miner_loop.py | 2566 | 84 | Tests for openjarvis.mining._miner_loop_main.
tests/mining/test_pearl_subprocess.py | 5193 | 137 | Tests for openjarvis.mining._pearl_subprocess.
tests/mining/test_stubs.py | 2544 | 85 | Tests for mining/_stubs.py — ABC contract, dataclass invariants, sidecar IO.
tests/mining/test_vllm_pearl.py | 6246 | 168 | End-to-end tests for VllmPearlProvider with mocked Docker + filesystem.
tests/mining/fixtures/README.md | 896 | 18 | Mining test fixtures
tests/mining/fixtures/config_minimal.toml | 390 | 13 | 
tests/mining/fixtures/config_pool_v2.toml | 363 | 11 | 
tests/mining/fixtures/gateway_metrics_sample.txt | 974 | 19 | 
tests/operators/__init__.py | 0 | 0 | 
tests/operators/test_operator_recipes.py | 3241 | 99 | Tests for the 3 operator recipes: researcher, correspondent, sentinel.
tests/operators/test_operators.py | 30323 | 936 | Tests for the Operators subsystem.
tests/pearl/test_model_converter.py | 4295 | 123 | Tests for the experimental Pearl model converter script.
tests/prompt/__init__.py | 0 | 0 | 
tests/prompt/test_builder.py | 8224 | 224 | 
tests/prompt/test_persona_scope.py | 2134 | 54 | Tests for #380 per-invocation persona scope (_resolve_persona).
tests/prompt/test_system_prompt_builder_few_shot.py | 1294 | 38 | Tests for SystemPromptBuilder skill few-shot injection (Plan 2A).
tests/recipes/__init__.py | 0 | 0 | 
tests/recipes/test_compose.py | 15502 | 472 | Tests for the unified compose system — enhanced Recipe, bridges, and discovery.
tests/recipes/test_loader.py | 5476 | 160 | Tests for recipe system — loader, discovery, and resolution.
tests/sandbox/__init__.py | 0 | 0 | 
tests/sandbox/test_mount_security.py | 5584 | 171 | Tests for mount_security module.
tests/sandbox/test_runner.py | 9892 | 316 | Tests for ContainerRunner and SandboxedAgent.
tests/sandbox/test_wasm_runner.py | 1913 | 59 | Tests for WASM sandbox (Phase 16.4).
tests/scheduler/__init__.py | 0 | 0 | 
tests/scheduler/test_digest_schedule.py | 8002 | 222 | Tests for digest schedule integration — CLI and API endpoints.
tests/scheduler/test_scheduler.py | 12404 | 359 | Tests for TaskScheduler — scheduling logic, lifecycle, and execution.
tests/scheduler/test_store.py | 5552 | 165 | Tests for SchedulerStore — SQLite CRUD for scheduled tasks and run logs.
tests/scheduler/test_tools.py | 4562 | 139 | Tests for scheduler MCP tools.
tests/sdk/__init__.py | 0 | 0 | 
tests/sdk/test_builder_mcp_cleanup.py | 2261 | 59 | Regression test for #753: a failed MCP handshake in
tests/sdk/test_sdk.py | 15324 | 434 | Tests for the Python SDK — Jarvis class and MemoryHandle.
tests/sdk/test_system.py | 20472 | 599 | Tests for the composition layer.
tests/security/__init__.py | 0 | 0 | 
tests/security/test_audit.py | 6840 | 219 | Tests for AuditLogger.
tests/security/test_boundary_guard.py | 9078 | 267 | Tests for BoundaryGuard — scanning at device exit points.
tests/security/test_builder_skill_identity.py | 3858 | 115 | Ensure nested skill execution preserves the caller security identity.
tests/security/test_capabilities.py | 10571 | 282 | Tests for RBAC capabilities system (Phase 14.4).
tests/security/test_credential_stripper.py | 1666 | 53 | 
tests/security/test_data_boundary_audit.py | 58320 | 1572 | classes: TestWebSearchDestination
tests/security/test_file_permissions.py | 2658 | 75 | Tests for secure file creation helpers (Section 4).
tests/security/test_file_policy.py | 8357 | 235 | Tests for file sensitivity policy.
tests/security/test_file_utils.py | 1274 | 43 | Security invariants for atomic private-file persistence.
tests/security/test_guardrails.py | 20276 | 511 | Tests for GuardrailsEngine.
tests/security/test_injection_scanner.py | 5846 | 146 | Tests for prompt injection scanner.
tests/security/test_log_sanitization.py | 3744 | 111 | Tests for log sanitization (Section 5).
tests/security/test_merkle_audit.py | 5311 | 164 | Tests for Merkle audit trail (Phase 14.6).
tests/security/test_network_defaults.py | 6312 | 185 | Tests for secure network defaults (Section 1 of security hardening).
tests/security/test_rate_limiter.py | 4910 | 141 | Tests for rate limiter -- token bucket algorithm.
tests/security/test_scanner.py | 8110 | 193 | Tests for SecretScanner and PIIScanner.
tests/security/test_security_profiles.py | 1955 | 55 | Tests for security profile expansion (Section 7).
tests/security/test_security_wiring.py | 5604 | 180 | Verify security wiring reaches agents and ToolExecutor.
tests/security/test_setup_security.py | 5376 | 160 | Tests for setup_security() helper.
tests/security/test_severity_policy.py | 1057 | 34 | 
tests/security/test_signing.py | 2799 | 88 | Tests for Ed25519 signing (Phase 14.6).
tests/security/test_ssrf.py | 11261 | 272 | Tests for SSRF protection module.
tests/security/test_ssrf_disguised.py | 1402 | 40 | SSRF: disguised-IPv4 forms are normalized and unresolvable hosts fail closed.
tests/security/test_subprocess_sandbox.py | 4068 | 124 | Tests for subprocess sandbox — secure process execution.
tests/security/test_taint.py | 4782 | 143 | Tests for taint tracking system (Phase 14.5).
tests/security/test_taint_propagation.py | 4247 | 109 | Taint information-flow control: sink policy + session propagation.
tests/security/test_tool_confirmation.py | 4978 | 140 | Tests for tool confirmation enforcement in ToolExecutor.
tests/security/test_webhook_validation.py | 1250 | 39 | Tests for webhook fail-closed validation (Section 3).
tests/server/__init__.py | 0 | 0 | 
tests/server/conftest.py | 3348 | 85 | Shared fixtures for server route tests.
tests/server/test_agent_manager_routes.py | 34101 | 886 | Tests for Agent Manager API routes.
tests/server/test_agent_model_override.py | 4021 | 119 | Regression test for #759: concurrent per-request model overrides on a
tests/server/test_api_routes.py | 14393 | 389 | Tests for extended API routes.
tests/server/test_approval_routes.py | 14322 | 358 | Tests for the proactive-agent approval queue API routes.
tests/server/test_auth_middleware.py | 4768 | 144 | Tests for API key authentication middleware.
tests/server/test_channel_bridge.py | 6194 | 189 | Tests for the ChannelBridge orchestrator.
tests/server/test_channel_bridge_deep_research.py | 1678 | 56 | Test ChannelBridge routes to DeepResearchAgent.
tests/server/test_channel_routes.py | 4724 | 150 | Tests for /v1/channels endpoints.
tests/server/test_cloud_router.py | 2380 | 75 | Regression tests for cloud provider detection and model ID normalization.
tests/server/test_connector_test_isolation.py | 4843 | 125 | Regression coverage for background connector writes during test teardown.
tests/server/test_connectors_router.py | 28677 | 780 | Tests for the /v1/connectors API router.
tests/server/test_cors_auth_interaction.py | 5546 | 175 | Regression tests for #758: CORS preflight broken when an API key is set.
tests/server/test_daemon_lifecycle.py | 2799 | 82 | Exercise daemon state against real Uvicorn bind and shutdown behavior.
tests/server/test_deep_research_tools_wiring.py | 12065 | 351 | Test that _build_deep_research_tools works correctly.
tests/server/test_digest_routes.py | 4726 | 149 | Tests for /api/digest endpoints.
tests/server/test_managed_agent_resolved_tools.py | 14195 | 432 | SSE regression coverage for canonical managed-agent tool resolution.
tests/server/test_managed_agent_streaming.py | 8857 | 243 | Managed-agent streaming parity tests (#382, #386, #395).
tests/server/test_mcp_tools_cache.py | 16536 | 484 | Tests for _get_mcp_tools() caching in agent_manager_routes.
tests/server/test_middleware.py | 4937 | 141 | Tests for security middleware -- HTTP security headers.
tests/server/test_model_management.py | 11253 | 316 | Tests for model pull / delete API endpoints and streaming resilience.
tests/server/test_models_pydantic.py | 3029 | 105 | Tests for server Pydantic models.
tests/server/test_nonblocking_routes.py | 2368 | 84 | Regressions for blocking work exposed through async server routes.
tests/server/test_pwa_serving.py | 3972 | 107 | Tests for PWA static file serving in the SPA catch-all endpoint.
tests/server/test_recommended_model.py | 3424 | 92 | Tests for /v1/recommended-model endpoint.
tests/server/test_research_planner.py | 8548 | 286 | Tests for web Deep Research planner engine selection.
tests/server/test_routes.py | 67282 | 1796 | Tests for the API server routes.
tests/server/test_savings.py | 3770 | 80 | Regression tests for compute_savings — leaderboard correctness.
tests/server/test_security_factory_wiring.py | 9203 | 280 | Adversarial security wiring tests for the programmatic app factory.
tests/server/test_sendblue_webhook.py | 8692 | 261 | Integration tests for the SendBlue webhook endpoint.
tests/server/test_session_store.py | 7740 | 200 | Tests for channel session store.
tests/server/test_speech_routes.py | 12120 | 387 | Tests for speech API endpoints.
tests/server/test_stream_bridge.py | 3298 | 93 | Regression tests for streaming completed agent responses.
tests/server/test_tools_endpoint.py | 6110 | 173 | Tests for GET /v1/tools endpoint.
tests/server/test_webhook_routes.py | 8540 | 264 | Tests for webhook routes.
tests/server/test_websocket.py | 9588 | 256 | Tests for the WebSocket streaming endpoint.
tests/server/test_websocket_auth.py | 8776 | 222 | WebSocket authentication tests (issue #217).
tests/server/test_ws_bridge.py | 9247 | 254 | Tests for WebSocket event bridge.
tests/sessions/test_compression.py | 2934 | 89 | 
tests/sessions/test_session.py | 4799 | 130 | Tests for session management (Phase 15.4).
tests/sessions/test_wire_channel_history.py | 3464 | 116 | Tests for wire_channel session history
tests/skills/__init__.py | 0 | 0 | 
tests/skills/test_bundled_skills.py | 2925 | 98 | Tests for bundled skill TOML files.
tests/skills/test_cli_install.py | 3101 | 84 | End-to-end CLI tests for skill install + sync against fake sources.
tests/skills/test_dependency.py | 9297 | 270 | Tests for dependency graph and cycle detection (Task 3).
tests/skills/test_importer.py | 12218 | 322 | Tests for SkillImporter — installs ResolvedSkill instances on disk.
tests/skills/test_index.py | 3420 | 106 | Tests for skill index — sync and search.
tests/skills/test_integration_live.py | 6879 | 176 | Live integration tests for the skills system.
tests/skills/test_loader_discover.py | 2863 | 76 | Tests for discover_skills() failure diagnostics (#780).
tests/skills/test_loader_markdown.py | 7875 | 216 | Tests for SKILL.md and directory-based skill loading.
tests/skills/test_manager.py | 24638 | 650 | Tests for SkillManager — discovery, catalog, tools, and resolve.
tests/skills/test_manager_discover_from_traces.py | 3995 | 112 | Tests for SkillManager.discover_from_traces (Plan 2A).
tests/skills/test_native_react_few_shot.py | 5963 | 168 | Tests for native_react skill_few_shot_examples wiring (Plan 2B I3 fix).
tests/skills/test_overlay.py | 3475 | 100 | Tests for the skills overlay loader/writer (Plan 2A).
tests/skills/test_parser.py | 7435 | 214 | Tests for the SkillParser strict + tolerant passes.
tests/skills/test_security.py | 2038 | 60 | Tests for skill security — capability validation and trust tiers.
tests/skills/test_skill_tool_metadata_tagging.py | 3696 | 106 | Tests for SkillTool metadata tagging (Plan 2A trace tagging).
tests/skills/test_skill_trace_tagging_integration.py | 8118 | 213 | End-to-end integration test for skill trace tagging (Plan 2A C1 fix).
tests/skills/test_skills.py | 11681 | 346 | Tests for skill system (Phase 15.2).
tests/skills/test_source_refresh_fallback.py | 4617 | 126 | Cached skill installation survives failed upstream refreshes.
tests/skills/test_sources.py | 10464 | 330 | Tests for SourceResolver ABC and resolver implementations.
tests/skills/test_tool_adapter_v2.py | 7794 | 203 | Tests for SkillTool v2 — parameter extraction and markdown support.
tests/skills/test_tool_translator.py | 3217 | 82 | Tests for ToolTranslator — translate external tool names to OpenJarvis.
tests/speech/__init__.py | 0 | 0 | 
tests/speech/test_config.py | 757 | 27 | Tests for speech configuration.
tests/speech/test_deepgram.py | 2156 | 62 | Tests for Deepgram speech backend.
tests/speech/test_discovery.py | 3317 | 105 | Tests for speech backend auto-discovery.
tests/speech/test_elevenlabs_credentials.py | 5318 | 141 | Keep ElevenLabs credentials out of provider errors and downstream logs.
tests/speech/test_elevenlabs_error_propagation.py | 5302 | 137 | Exercise credential-safe errors beyond the ElevenLabs backend boundary.
tests/speech/test_faster_whisper.py | 6146 | 186 | Tests for Faster-Whisper speech backend.
tests/speech/test_openai_whisper.py | 1989 | 58 | Tests for OpenAI Whisper API speech backend.
tests/speech/test_stubs.py | 841 | 33 | Tests for speech ABC and data types.
tests/speech/test_tts_backends.py | 28438 | 859 | Tests for TTS backend infrastructure.
tests/speech/test_voice_io.py | 1629 | 62 | Timing behavior for microphone silence detection.
tests/speech/test_voice_selection.py | 4917 | 149 | Voice-ID selection for chat TTS.
tests/telemetry/__init__.py | 0 | 0 | 
tests/telemetry/energy_test_helpers.py | 1971 | 56 | Shared assertion helpers for energy monitor tests.
tests/telemetry/test_aggregator.py | 10944 | 324 | Tests for TelemetryAggregator.
tests/telemetry/test_batch.py | 10025 | 284 | Tests for batch-level energy accounting.
tests/telemetry/test_derived_metrics.py | 6820 | 197 | Tier 1: derived metrics — energy_per_output_token, throughput_per_watt.
tests/telemetry/test_efficiency.py | 7390 | 192 | Tests for MFU/MBU efficiency calculator.
tests/telemetry/test_energy_amd.py | 6764 | 189 | Tests for AmdEnergyMonitor -- mock amdsmi (no real GPU required).
tests/telemetry/test_energy_apple.py | 14350 | 393 | Tests for AppleEnergyMonitor.
tests/telemetry/test_energy_monitor.py | 8425 | 245 | Tests for EnergyMonitor ABC, EnergySample, EnergyVendor, and factory.
tests/telemetry/test_energy_nvidia.py | 13463 | 362 | Tests for NvidiaEnergyMonitor -- mock pynvml (no real GPU required).
tests/telemetry/test_energy_rapl.py | 8679 | 256 | Tests for RaplEnergyMonitor -- mock sysfs (no real RAPL required).
tests/telemetry/test_energy_wiring.py | 35101 | 1041 | Tests for energy telemetry wiring — verify CLI, SDK, bench, and
tests/telemetry/test_flops_new.py | 3121 | 94 | Tests for FLOPs estimation and MFU computation.
tests/telemetry/test_gpu_monitor.py | 14187 | 382 | Tests for GPU monitor -- mock pynvml (no real GPU required).
tests/telemetry/test_instrumented_engine.py | 15120 | 412 | Tests for InstrumentedEngine telemetry wrapper.
tests/telemetry/test_itl_metrics.py | 11403 | 357 | Tests for Tier 3 — per-token timestamps, ITL percentiles, streaming telemetry.
tests/telemetry/test_itl_new.py | 2459 | 69 | Tests for inter-token latency percentile computation.
tests/telemetry/test_phase_energy.py | 7935 | 233 | Tests for Tier 2.1 — phase energy split: decode_latency, prefill/decode energy.
tests/telemetry/test_phase_metrics_new.py | 1882 | 52 | Tests for phase metrics computation.
tests/telemetry/test_session.py | 3282 | 96 | Tests for TelemetrySession and ring buffer.
tests/telemetry/test_steady_state.py | 5865 | 162 | Tests for SteadyStateConfig, SteadyStateDetector, and SteadyStateResult.
tests/telemetry/test_store.py | 10757 | 296 | Tests for the telemetry SQLite store.
tests/telemetry/test_store_tokens_per_joule.py | 2136 | 66 | Tests for tokens_per_joule storage and aggregation.
tests/telemetry/test_vllm_metrics.py | 7281 | 203 | Tests for VLLMMetricsScraper — Prometheus text format parsing.
tests/telemetry/test_wrapper.py | 3649 | 113 | Tests for the instrumented inference wrappers.
tests/templates/__init__.py | 0 | 0 | 
tests/templates/test_agent_templates.py | 2204 | 67 | Tests for the agent template loader.
tests/test_orchestrator_learning/__init__.py | 55 | 2 | Tests for orchestrator learning infrastructure.
tests/test_orchestrator_learning/test_environment.py | 8032 | 238 | Tests for orchestrator RL environment.
tests/test_orchestrator_learning/test_grpo_trainer.py | 3783 | 104 | Tests for orchestrator GRPO trainer.
tests/test_orchestrator_learning/test_orchestrator_structured.py | 15718 | 492 | Tests for OrchestratorAgent structured mode.
tests/test_orchestrator_learning/test_policy_model.py | 4226 | 121 | Tests for orchestrator policy model.
tests/test_orchestrator_learning/test_prompt_registry.py | 2383 | 70 | Tests for orchestrator prompt registry.
tests/test_orchestrator_learning/test_reward.py | 5226 | 144 | Tests for orchestrator multi-objective reward.
tests/test_orchestrator_learning/test_sft_trainer.py | 6180 | 185 | Tests for orchestrator SFT trainer.
tests/test_orchestrator_learning/test_types.py | 7280 | 243 | Tests for orchestrator learning types.
tests/tools/__init__.py | 0 | 0 | 
tests/tools/test_agent_tools.py | 8373 | 253 | Tests for inter-agent lifecycle tools.
tests/tools/test_allowed_dirs_config.py | 9389 | 232 | `[security] allowed_dirs` is the default directory allow-list for file tools.
tests/tools/test_apply_patch.py | 8176 | 224 | Tests for the apply_patch tool.
tests/tools/test_audio_tool.py | 7528 | 198 | Tests for the audio_transcribe tool.
tests/tools/test_browser.py | 40433 | 1102 | Tests for browser automation tools.
tests/tools/test_browser_axtree.py | 4716 | 122 | Tests for browser_axtree tool.
tests/tools/test_calculator.py | 3316 | 113 | Tests for the calculator tool.
tests/tools/test_channel_tools.py | 7264 | 224 | Tests for channel MCP tools — ChannelSendTool, ChannelListTool, ChannelStatusTool.
tests/tools/test_code_interpreter.py | 5967 | 158 | Tests for the code interpreter tool.
tests/tools/test_code_interpreter_ast.py | 2424 | 69 | code_interpreter: AST validation blocks the old substring bypasses.
tests/tools/test_code_interpreter_docker.py | 5318 | 151 | Tests for the Docker-sandboxed code interpreter tool.
tests/tools/test_db_query.py | 10733 | 284 | Tests for the db_query tool.
tests/tools/test_digest_collect.py | 2003 | 61 | Tests for the digest_collect tool.
tests/tools/test_file_read.py | 4305 | 118 | Tests for the file_read tool.
tests/tools/test_file_write.py | 6205 | 166 | Tests for the file_write tool.
tests/tools/test_fx_macro.py | 13359 | 374 | Tests for the native FXMacroData macro and FX data tool.
tests/tools/test_git_tool.py | 22265 | 588 | Tests for the git tools (status, diff, commit, log).
tests/tools/test_http_request.py | 12552 | 312 | Tests for the HTTP request tool with SSRF protection.
tests/tools/test_image_tool.py | 5617 | 151 | Tests for the image_generate tool.
tests/tools/test_knowledge_graph.py | 5313 | 136 | Tests for knowledge graph storage backend (Phase 15.3).
tests/tools/test_knowledge_search.py | 8508 | 215 | Tests for the knowledge_search tool.
tests/tools/test_knowledge_sql.py | 4349 | 124 | Tests for KnowledgeSQLTool.
tests/tools/test_llm_tool.py | 2376 | 68 | Tests for the LLM tool.
tests/tools/test_mcp_adapter.py | 5498 | 159 | Tests for the MCP tool adapter — round-trip through MCPServer + MCPClient.
tests/tools/test_memory_manage.py | 1563 | 51 | 
tests/tools/test_pdf_tool.py | 7280 | 198 | Tests for the pdf_extract tool.
tests/tools/test_proactive_tools.py | 4372 | 130 | Regression tests for proactive pending-action execution.
tests/tools/test_repl.py | 9107 | 269 | Tests for the persistent REPL tool.
tests/tools/test_retrieval.py | 3367 | 111 | Tests for the retrieval tool.
tests/tools/test_scan_chunks.py | 2553 | 73 | Tests for ScanChunksTool.
tests/tools/test_shell_exec.py | 14640 | 380 | Tests for the shell_exec tool.
tests/tools/test_skill_manage.py | 2444 | 89 | 
tests/tools/test_storage_stubs.py | 2843 | 87 | Tests for tools/storage — canonical location for memory backends.
tests/tools/test_storage_tools.py | 8462 | 251 | Tests for storage MCP tools — MemoryStoreTool, MemoryRetrieveTool, etc.
tests/tools/test_stubs.py | 12792 | 360 | Tests for tools/_stubs.py — ToolSpec, BaseTool, ToolExecutor.
tests/tools/test_template_loader_security.py | 4387 | 127 | Security regression tests for the tool-template loader (issue #216).
tests/tools/test_templates.py | 5163 | 162 | Tests for MCP templates (Phase 16.3).
tests/tools/test_text_to_speech.py | 5278 | 159 | Tests for the text_to_speech tool.
tests/tools/test_think.py | 1163 | 38 | Tests for the think tool.
tests/tools/test_tool_descriptions.py | 6226 | 182 | Tests for the shared build_tool_descriptions() builder.
tests/tools/test_tool_registration.py | 5894 | 208 | Verify that importing openjarvis.tools registers all built-in tools.
tests/tools/test_tool_timeout.py | 6615 | 196 | Tests for tool execution timeout (Phase 14.1).
tests/tools/test_user_profile_manage.py | 1195 | 40 | 
tests/tools/test_weather.py | 20302 | 548 | Tests for the native parameterized OpenWeatherMap tool.
tests/tools/test_web_search.py | 71810 | 1791 | Tests for the web search tool.
tests/tools/storage/__init__.py | 0 | 0 | 
tests/tools/storage/test_dense.py | 26254 | 682 | Tests for the DenseMemory backend.
tests/traces/__init__.py | 0 | 0 | 
tests/traces/test_analyzer.py | 6570 | 196 | Tests for the TraceAnalyzer.
tests/traces/test_analyzer_energy.py | 3969 | 123 | Tests for energy aggregation in TraceAnalyzer.
tests/traces/test_collector.py | 14459 | 419 | Tests for the TraceCollector.
tests/traces/test_store.py | 8034 | 230 | Tests for the trace SQLite store.
tests/traces/test_store_fts.py | 3844 | 138 | Tests for FTS5 cross-session search on TraceStore.
tests/traces/test_types.py | 3327 | 105 | Tests for Trace and TraceStep types.
tests/workflow/test_condition_safe_eval.py | 625 | 18 | Workflow condition evaluation uses the allowlist AST interpreter, not eval().
tests/workflow/test_workflow.py | 6026 | 153 | Tests for workflow engine (Phase 15.1).
```
