---
id: 001
title: Phase V Constitution Amendment
stage: constitution
date: 2026-02-07
surface: agent
model: claude-opus-4-6
feature: none
branch: main
user: Shumaila
command: /sp.constitution
labels: ["constitution", "phase-v", "event-driven", "dapr", "cloud-deployment"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .specify/memory/constitution.md
  - CLAUDE.md
tests:
  - none
---

## Prompt

You are an expert in creating long-term guiding constitutions for multi-phase, agentic development projects.

Create a complete sp.constitution.md file specifically for **Phase V: Advanced Cloud Deployment** of the Todo AI Chatbot project.

Use the exact same structure, tone, depth and style as the Phase III constitution I previously gave you (the one with sections 1–10, warm assistant personality, absolute non-negotiables, prioritization ladder, etc.).

Phase V key facts from the project document:

- Add intermediate features: priorities, tags, search, filter, sort
- Add advanced features: recurring tasks, due dates, reminders/notifications
- Introduce full event-driven architecture using Kafka (or Redpanda-compatible)
- Use Dapr sidecar for Pub/Sub, State management, Bindings (cron), Secrets, Service Invocation
- First deploy locally on Minikube with Dapr + self-hosted Kafka/Redpanda
- Then deploy to production-grade Kubernetes: prefer Oracle Cloud Always Free OKE (4 OCPUs, 24 GB RAM, no time limit), fallback Azure AKS ($200 credit) or GKE ($300 credit)
- Use Redpanda Cloud Serverless (free tier) or Strimzi operator for Kafka
- Set up GitHub Actions CI/CD pipeline
- Add basic monitoring/logging (Prometheus/Grafana or cloud-native)

Core principles to enforce:
- Loose coupling via Dapr → never hard-code Kafka clients or DB connections in app code
- Event-driven first: every important state change must publish an event
- Safety: never lose events, never send duplicate reminders, never create infinite recurring loops
- Cost control: prefer always-free tiers (Oracle OKE, Redpanda free serverless, Neon free PostgreSQL)
- Hackathon pragmatism: fallbacks for every external service (e.g. if Redpanda access blocked → Strimzi)
- Build on Phase III (MCP tools, agent logic) and Phase IV (Helm charts, Minikube)

Required sections: 1-10 (Core Identity, Non-Negotiables, Prioritization, Preferred Patterns, Anti-Patterns, Success Looks Like, Failure Modes, Sacred Dependencies, Personality Guide, Evolution Rules)

## Response snapshot

Created Phase V constitution v4.0.0 at `.specify/memory/constitution.md` with 12 sections:

1. **Core Identity & Tone of Voice** — warm, professional, Roman Urdu-friendly
2. **Absolute Non-Negotiables** — 6 rules: Dapr abstraction sacred, events after commit, safety (no lost events/duplicates/infinite loops), cost control (always-free first), hackathon pragmatism (fallbacks), user isolation preserved
3. **Prioritization Ladder** — event safety > Dapr abstraction > cost control > features > CI/CD > polish
4. **Strongly Preferred Patterns** — 10 patterns (Dapr Pub/Sub, Redpanda Cloud, Oracle OKE, Helm values, event-first design, etc.)
5. **Strongly Discouraged** — 11 anti-patterns (direct Kafka imports, events before commit, hardcoded secrets, infinite loops, etc.)
6. **Success Looks Like** — 6 measurable outcome areas (features, events, Dapr, cloud, CI/CD, monitoring)
7. **Failure Modes** — 10 failure modes with severity and mitigation
8. **Sacred Dependencies** — 3 tiers: Phase V (Kafka, Dapr, OKE, GitHub Actions, Prometheus), Phase IV (Minikube, Helm), Phase III (FastAPI, SQLModel, Neon)
9. **Personality Guide** — 5 tone examples with Roman Urdu warmth
10. **Evolution Rules** — 6 triggers for constitution updates
11. **Enforcement** — agent-to-section mapping
12. **SDD Workflow** — inherited spec-driven development rules

Also updated CLAUDE.md Active Technologies and Recent Changes sections.

## Outcome

- Impact: MAJOR constitution amendment (v3.0.0 → v4.0.0) establishing Phase V governance
- Tests: none (governance document)
- Files: .specify/memory/constitution.md, CLAUDE.md
- Next prompts: Begin Phase V feature implementation with /sp.specify for priorities feature
- Reflection: Constitution successfully bridges Phase IV local deployment to Phase V cloud deployment while maintaining backward compatibility with Phase III application stack

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): N/A (governance document)
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Implement first feature (priorities) using the new constitution's SDD workflow
