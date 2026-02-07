---
name: spec-validator
description: Validate spec completeness and consistency with the project constitution. Use when reviewing /specs artifacts for missing acceptance criteria, unclear contracts, security/auth gaps, or inconsistencies between spec/plan/tasks.
allowed-tools: Read, Glob, Grep
---

# Spec Validator

## Purpose
Validate spec completeness, consistency with constitution, and quality.

## Used by
- constitution-keeper
- orchestrator

## Validation checklist
- Specs present: `spec.md` plus `plan.md`/`tasks.md` as applicable.
- Requirements are testable (clear acceptance criteria).
- API contracts are explicit (paths, verbs, schemas, status codes).
- Data model is explicit (tables, constraints, ownership/isolation rules).
- AuthN/AuthZ rules are explicit (JWT claims, ownership checks).
- UI requirements include responsive + states (loading/empty/error).
- No contradictions across documents.

## Output format
- `PASS` or `NEEDS_REFINEMENT`
- Bullet list of issues with exact file paths.
- Questions to resolve, not assumptions.
