---
name: sqlmodel-schema-generator
description: Generate SQLModel models for User and Task with proper relationships, constraints, and strict user_id isolation (Neon Postgres). Use when translating approved DB specs into SQLModel code.
allowed-tools: Read, Write, Edit, Glob, Grep
---

# SQLModel Schema Generator

## Purpose
Generate SQLModel models for `User` and `Task` with proper relationships and `user_id` isolation.

## Used by
- database-specialist
- backend-specialist

## Requirements
- Every Task must be owned by exactly one User (`user_id` non-null FK).
- Queries must be filterable/indexed by `user_id`.
- Align with `/specs/database/*` and `/specs/api/*`.

## Output format
- When asked to implement, generate code under `/backend` only.
- Otherwise, propose schema changes as spec updates under `/specs/database/*`.
