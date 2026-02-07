---
name: design-system-generator
description: Generate consistent color schemes, typography, spacing, and reusable components guidance for Tailwind + shadcn/ui. Use when defining or refining UI design system tokens and component conventions in specs.
allowed-tools: Read, Write, Edit, Glob, Grep
---

# Design System Generator

## Purpose
Generate consistent color schemes, typography, spacing, and reusable components (Tailwind/shadcn/ui).

## Used by
- spec-manager
- full-stack-frontend

## Procedure
1. Inspect existing Tailwind/shadcn configuration (if any).
2. Propose design tokens:
   - color palette (semantic tokens)
   - typography scale
   - spacing scale
   - radii, shadows, borders
3. Map tokens to shadcn/ui component usage.
4. Ensure accessibility considerations (contrast, focus states).

## Output format
- Prefer updating UI specs under `/specs/ui/*` (not implementation) unless explicitly asked to code.
