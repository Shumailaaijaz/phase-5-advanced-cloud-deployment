---
name: responsive-layout-designer
description: Design mobile-first responsive layouts for Todo list, forms, and auth pages. Use when defining breakpoints, layouts, component placement, and responsive behaviors in UI specs.
allowed-tools: Read, Write, Edit, Glob, Grep
---

# Responsive Layout Designer

## Purpose
Design mobile-first responsive layouts for Todo list, forms, auth pages.

## Used by
- spec-manager
- full-stack-frontend

## Procedure
1. Identify target page(s) and user flows.
2. Define breakpoints and layout rules:
   - mobile (base)
   - sm/md/lg/xl
3. Specify:
   - grids/stacks
   - navigation patterns
   - touch targets
   - empty/loading/error states layout
4. Provide implementation-ready UI spec sections (no code unless requested).

## Output format
- Update `/specs/ui/*.md` with:
  - page sections
  - states
  - responsive rules per breakpoint
