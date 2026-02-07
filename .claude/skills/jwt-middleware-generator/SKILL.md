---
name: jwt-middleware-generator
description: Generate JWT verification middleware/dependency for FastAPI using shared BETTER_AUTH_SECRET. Use when wiring Better Auth-issued JWTs to FastAPI route protection and extracting the authenticated user id.
allowed-tools: Read, Write, Edit, Glob, Grep
---

# JWT Middleware Generator

## Purpose
Generate JWT verification middleware/dependency for FastAPI using shared `BETTER_AUTH_SECRET`.

## Used by
- full-stack-backend
- auth-specialist

## Requirements
- Verify JWT signature and standard claims (exp, iat) per spec.
- Extract authenticated identity (subject/user id) and make it available to routes.
- Enforce strict user isolation: `{user_id}` path params must match the JWT subject/claim.

## Output format
- Implement backend-only changes under `/backend` when explicitly requested.
- Otherwise, propose updates to `/specs/authentication.md` and `/specs/api/*`.
