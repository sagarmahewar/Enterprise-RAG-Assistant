# ADR-0002: Modular monolith with clean architecture

## Status

Accepted

## Context

The solution needs maintainability, extensibility, and portfolio-grade engineering without early distributed-system complexity.

## Decision

Use a modular monolith with clean architecture boundaries:

- domain
- application
- infrastructure
- interfaces (API/UI)

All external dependencies are accessed through provider interfaces.

## Consequences

- Clear separation of concerns.
- Easier unit and integration testing.
- Future migration to services remains possible through existing module contracts.
