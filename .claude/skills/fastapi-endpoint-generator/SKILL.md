---
name: fastapi-endpoint-generator
description: Create production-ready FastAPI CRUD endpoints with strict per-user isolation and correct error handling. Use when implementing endpoints specified under /specs/api/*.
allowed-tools: Read, Write, Edit, Glob, Grep
---

# FastAPI Endpoint Generator

## Purpose
Create FastAPI CRUD endpoints with user isolation and error handling.

## Used by
- full-stack-backend

## Requirements
- Endpoints must match `/specs/api/*` exactly.
- All queries must be scoped by authenticated user.
- Return correct status codes and error payloads.

## Output format
- Implement under `/backend` only.
- Include minimal tests if the project has an established test stack.
