---
name: nextjs-page-generator
description: Generate polished Next.js (App Router) pages and components using Tailwind + shadcn/ui, with JWT-protected data fetching flows. Use when implementing UI pages specified in /specs/ui/* and feature specs.
allowed-tools: Read, Write, Edit, Glob, Grep
---

# Next.js Page Generator

## Purpose
Generate beautiful Next.js pages and components (App Router) with JWT-protected data fetching.

## Used by
- full-stack-frontend

## Requirements
- Follow `/specs/ui/*` and `/specs/features/*`.
- Mobile-first responsive UI.
- Handle loading/empty/error states.

## Output format
- Implement frontend-only changes under `/frontend`.
- Keep styling consistent with shadcn/ui conventions.
