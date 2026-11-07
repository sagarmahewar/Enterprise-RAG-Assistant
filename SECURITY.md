# Security Baseline

## Security goals

- Prevent untrusted document content from overriding assistant behavior.
- Limit retrieval to authorized document scopes.
- Protect local environment and data-at-rest.
- Avoid secret leakage and unsafe defaults.

## Threat model (initial)

1. **Prompt injection via uploaded documents**
   - Malicious instructions embedded in content.
2. **Data leakage across documents/sessions**
   - Unauthorized retrieval due to missing filters.
3. **Abusive uploads**
   - Oversized/unsupported/malformed files.
4. **Output hallucination without source grounding**
   - Responses not supported by retrieved evidence.
5. **Operational misconfiguration**
   - Running with debug modes, weak defaults, exposed services.

## Security controls

## 1. Input and upload protection

- Strict MIME and extension allowlist (PDF/DOCX/TXT).
- File size limits and parser timeout protections.
- Reject encrypted/unsupported document variants with explicit errors.
- Normalize/strip dangerous embedded content (scripts/macros are never executed).

## 2. Prompt-injection resilience

- System policy and app policy are immutable in prompt hierarchy.
- Retrieved text treated strictly as **data**, never as executable instruction.
- Pattern-based and heuristic checks for known injection phrases.
- Context builder excludes risky directives from retrieval payload when flagged.

## 3. Authorization design (document-level)

- Every document and chunk carries `acl_tags`/owner scope metadata.
- Retrieval queries must include authorization constraints.
- Post-retrieval filtering verifies chunk scope again before answer generation.

## 4. Secrets and configuration hygiene

- No credentials in source control.
- Environment variables for runtime config only.
- `.env.example` without secret values.
- Secret scanning in CI (where feasible with free tooling).

## 5. Error handling and observability

- User-safe error messages; internal details only in logs.
- Structured logging with trace IDs.
- No broad exception swallowing in core pipelines.

## 6. Dependency and supply-chain hygiene

- Pin dependencies with reproducible lock files.
- Use trusted package sources only.
- Run periodic vulnerability checks with free tooling.

## Security test strategy

- Unit tests for validator and policy checks.
- Integration tests for unauthorized retrieval rejection.
- Adversarial prompt-injection test set in evaluation pipeline.
- Regression tests for citation grounding behavior.

## Security non-goals (initial release)

- Multi-tenant internet-exposed deployment hardening.
- Enterprise SSO/RBAC integration.
- Hardware enclave/advanced key management.

These can be added in later ADR-driven iterations.
