---
name: spec-writer
description: Create detailed specs in /specs with UI/UX requirements, API contracts, and database schema. Use when new features need implementable SDD artifacts (spec.md/plan.md/tasks.md) or when existing specs need refinement.
allowed-tools: Read, Write, Edit, Glob, Grep
---

# Spec Writer

## Purpose
Create detailed specs with UI/UX requirements, API contracts, and database schema.

## Used by
- spec-manager
- orchestrator

## Procedure
1. Identify the target feature folder under `/specs/<feature-name>/`.
2. Draft or update:
   - `spec.md` (requirements + acceptance criteria)
   - `plan.md` (architecture decisions + tradeoffs)
   - `tasks.md` (ordered tasks + validation)
3. Ensure specs are implementable:
   - Explicit API request/response shapes
   - Error cases with status codes
   - DB tables/fields/constraints/indexes
   - UI states (loading/empty/error/success)
4. Keep diffs small and avoid speculative requirements.

## Output format
- Create/update markdown files under `/specs/` only.
- Include clear acceptance criteria checklists.
