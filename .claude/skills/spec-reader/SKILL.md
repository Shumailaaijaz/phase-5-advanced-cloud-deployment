---
name: spec-reader
description: Read and parse all Spec-Kit Plus files in /specs to understand project requirements. Use when you need to inspect, summarize, or cross-reference existing specs (spec.md, plan.md, tasks.md) before planning or implementing.
allowed-tools: Read, Glob, Grep
---

# Spec Reader

## Purpose
Read and parse all Spec-Kit Plus files in `/specs/` to understand project requirements.

## Used by
- orchestrator
- spec-manager
- constitution-keeper
- all specialists

## Procedure
1. Discover available spec folders and files under `/specs`.
2. Read the relevant `spec.md`, `plan.md`, and `tasks.md` (if present).
3. Produce a structured summary:
   - Feature goals
   - In/out of scope
   - API contracts
   - Data model
   - UI requirements
   - Security/auth requirements
   - Acceptance criteria
4. Call out conflicts, ambiguity, or missing details, and propose *questions* (not guesses).

## Output format
- Bullet summary + a short “Open questions” section.
- Include code references to spec file paths (e.g., `specs/<feature>/spec.md`).
