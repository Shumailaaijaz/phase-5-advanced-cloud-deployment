---
name: responsive-tester
description: Test responsive design across common breakpoints and suggest improvements. Use when validating UI pages/components for mobile/tablet/desktop layout issues and consistency with UI specs.
allowed-tools: Read, Glob, Grep
---

# Responsive Tester

## Purpose
Test responsive design across all breakpoints and suggest improvements.

## Used by
- orchestrator
- constitution-keeper
- frontend-specialist

## Procedure
1. Identify pages/components to validate.
2. Check spec requirements for breakpoints and states.
3. Review Tailwind class usage patterns and layout structure.
4. Report issues + concrete fixes (prefer minimal diffs).

## Output format
- Findings grouped by breakpoint (mobile/sm/md/lg/xl).
- Reference relevant files and spec sections.
