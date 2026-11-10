
# AGENTS.md: Generic AI Agent Guidance for Repositories


## Purpose

This file defines how agents should understand the repository, make changes safely, keep code quality high, and produce work that is maintainable, testable, and production-friendly.

It should be treated as the operational contract for AI-assisted development.

---

## Core Principles

1. **Understand before changing**
   - Read the relevant code, configuration, and documentation before editing.
   - Prefer adapting to established patterns over introducing new ones.
   - Do not assume architecture, conventions, or libraries; verify them first.

2. **Preserve correctness**
   - Favor safe, incremental changes.
   - Avoid broad refactors unless explicitly requested or clearly necessary.
   - Keep behavior stable unless the task requires a behavioral change.

3. **Prefer clarity over cleverness**
   - Use explicit, readable code.
   - Prefer straightforward implementations with strong typing and good naming.
   - Avoid over-abstraction, premature optimization, and opaque helper layers.

4. **Design for maintainability**
   - Keep modules focused.
   - Keep interfaces explicit.
   - Keep responsibilities separated.
   - Leave the codebase easier to understand than before.

5. **Be AI-friendly and human-friendly**
   - Write code that is easy to inspect, extend, and debug.
   - Add concise comments where intent may be unclear.
   - Follow patterns consistently so future agents and developers can reason locally.

---

## Critical First Steps

Before making changes:

1. Read the repository root documentation:
   - `README.md`
   - `pyproject.toml`
   - `AGENTS.md`
   - Any `docs/` files relevant to the task

2. Inspect project structure to identify:
   - application entrypoints
   - package layout
   - configuration files
   - test layout
   - scripts and tooling

3. Determine the active stack and conventions:
   - framework(s)
   - typing approach
   - linting and formatting tools
   - test framework
   - dependency management workflow

4. Search for existing implementations before creating new ones:
   - similar endpoints
   - similar services
   - similar schemas
   - similar UI patterns
   - similar tests

5. Confirm how the project is run and validated before editing anything substantial.

---

## Expected Technical Defaults

These defaults should be followed unless the repository clearly uses a different standard.

### Python Environment and Dependency Management

This project family uses **`uv`** as the default environment and package manager.

#### Rules
- Use `uv` for dependency installation, locking, and command execution.
- Do not introduce `pip`, `poetry`, or `conda` workflows unless the repository already depends on them.
- Prefer reproducible commands that work both locally and in CI.

#### Typical Commands

uv sync
uv add package-name
uv remove package-name
uv run pytest
uv run ruff check .
uv run ruff format .
uv run python -m module_name


#### Environment Guidance

* Keep dependencies declared in `pyproject.toml`.
* Respect existing dependency groups such as `dev`, `test`, or `docs`.
* Do not add packages without clear need.
* Prefer small, high-quality dependencies over heavy frameworks.

---

## Typing and Data Contracts

### Pydantic First

Use **Pydantic** for structured validation, parsing, and serialization whenever the project deals with:

* API request and response models
* configuration models
* internal typed contracts between layers
* task payloads
* structured outputs from LLM or automation workflows

### Rules

* Prefer explicit `BaseModel` schemas over untyped dictionaries.
* Validate at boundaries, not deep inside business logic.
* Use clear field names and descriptions when helpful.
* Keep schemas close to the domain they represent.
* Reuse shared schemas when the contract is truly shared.

### Example


from pydantic import BaseModel, Field


class CreateUserRequest(BaseModel):
    email: str = Field(..., description="User email")
    full_name: str = Field(..., min_length=1, max_length=200)
    is_active: bool = True


### Schema Guidance

* Separate external API schemas from persistence models when appropriate.
* Avoid leaking ORM entities directly across application layers.
* Use nested models only when they improve clarity.
* Keep serialization predictable and versionable.

---

## Project Architecture Guidance

Prefer a layered architecture with clear boundaries.

### Recommended Layers

* **API / entrypoints**: HTTP routes, CLI commands, event handlers
* **Schemas / contracts**: Pydantic models and typed interfaces
* **Services / use cases**: business logic
* **Persistence**: database access, repositories, storage adapters
* **Infrastructure**: external integrations, clients, configuration
* **Domain utilities**: core reusable logic with minimal side effects

### Rules

* Entry layers should be thin.
* Business logic should not live in route handlers or controllers.
* Persistence details should not leak into API contracts.
* External service clients should be wrapped behind stable interfaces when complexity justifies it.

### Avoid

* fat controllers
* hidden side effects
* circular imports
* giant utility modules
* duplicated business rules across layers

---

## Code Quality Standards

### General Standards

* Keep functions focused.
* Keep modules cohesive.
* Use descriptive names.
* Prefer explicit return values.
* Raise meaningful exceptions.
* Handle edge cases deliberately.

### Function Design

* Prefer small functions with a single clear job.
* Avoid very long functions unless there is a strong reason.
* Pass typed objects instead of loosely structured dictionaries where possible.

### Class Design

* Use classes when state or interface grouping improves clarity.
* Do not create classes only for style.
* Prefer composition over inheritance unless inheritance is clearly justified.

### Comments

* Comment intent, assumptions, and non-obvious decisions.
* Do not comment what the code already says clearly.
* Remove stale comments when behavior changes.

### Logging

* Use structured, meaningful logs.
* Log important state transitions, errors, retries, and external calls.
* Never log secrets, tokens, passwords, or private user data.

---

## Naming Conventions

* **Files / modules**: `snake_case`
* **Classes**: `PascalCase`
* **Functions / variables**: `snake_case`
* **Constants**: `UPPER_SNAKE_CASE`
* **Boolean names**: start with `is_`, `has_`, `can_`, `should_`

Use domain-specific names when possible.
Avoid vague names like:

* `data`
* `obj`
* `helper`
* `temp`
* `manager`

unless they are genuinely accurate in context.

---

## Testing Workflow

Testing is mandatory for non-trivial changes.

### Required Sequence

1. Make the smallest correct change.
2. Run the relevant test subset first.
3. Run the broader validation suite.
4. Update or add tests if behavior changed.
5. Ensure the repository is left in a passing state.

### Typical Commands


uv run pytest
uv run pytest tests/path/test_file.py
uv run ruff check .
uv run ruff format .


### Testing Principles

* Add tests for bug fixes.
* Add tests for new behavior.
* Prefer deterministic tests.
* Mock external services only at clear boundaries.
* Avoid brittle tests coupled to internal implementation details.

### Test Quality Rules

* Assert behavior, not incidental formatting.
* Keep fixtures readable.
* Reuse helpers where it improves clarity.
* Avoid giant integration tests when a focused unit or service test is enough.

---

## Linting, Formatting, and Static Analysis

Prefer repository-defined tools. If the repository does not specify them, default to:

* `ruff` for linting and formatting
* `pytest` for testing
* `mypy` or pyright if type checking is already part of the project

### Rules

* Run formatting before finalizing.
* Resolve lint warnings that matter; do not silence them casually.
* Avoid introducing code that degrades typing quality.
* Prefer improving type coverage over adding `Any` broadly.

---

## Git and Change Management

### Commit Rules

* Keep commits logically scoped.
* Use **semantic release keywords at the start of every commit message**.

  * Examples: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`, `perf:`, `ci:`
  * Optional scopes: `feat(api):`, `fix(auth):`, `refactor(core):`
  * Keep the first line concise; use the body for details if needed.
* One feature, one fix, or one refactor per commit when possible.
* Write professional commit messages.
* Do not mention AI tools in commit messages, PR text, or code comments unless explicitly requested.

### Commit Style

Examples:

* `feat(api): add validation for webhook payloads`
* `fix(scheduler): resolve race condition in background task`
* `refactor(user): isolate persistence layer`
* `docs(readme): clarify setup instructions`
* `test(service): add coverage for retry logic`

### Avoid

* `misc updates`
* `fix stuff`
* `AI changes`
* mixed unrelated edits in one commit

---

## Documentation Expectations

Update documentation when changes affect:

* setup or installation
* architecture
* configuration
* public APIs
* developer workflows
* operational behavior

### Documentation Rules

* **Do not create multiple documents for a single feature.**
* **Do not create new docs for changes to an already documented feature**; instead, **update the existing documentation**.
* Keep documentation **grouped by feature domain**, not by individual change.
* Prefer extending existing sections over duplicating content across files.
* Ensure documentation remains a single source of truth per feature.
* Remove or update outdated sections when behavior changes.

### Recommended Docs

* `README.md` for setup and project overview
* `docs/architecture.md` for system design
* `docs/development.md` for workflow and conventions
* `docs/api.md` for public interfaces

### Rule

If behavior changes and the docs become false, update the docs.

---

## Security Rules

Security takes priority over convenience.

### Mandatory Rules

* Never hardcode secrets.
* Read secrets from environment variables or approved secret stores.
* Validate all external input.
* Escape or sanitize user-controlled content where appropriate.
* Use parameterized database access through approved libraries or ORMs.
* Enforce authorization checks at the correct boundary.
* Minimize privilege by default.

### Sensitive Data

* Do not log secrets or personal data.
* Avoid returning internal error details to untrusted clients.
* Redact sensitive fields in logs and telemetry.

### Dependency Safety

* Prefer mature, maintained packages.
* Avoid unnecessary dependencies.
* Be cautious with code execution, template rendering, file uploads, and deserialization.

---

## API and Backend Guidance

If the repository contains APIs, prefer the following patterns.

### Route / Controller Rules

* Keep handlers thin.
* Validate input with Pydantic.
* Delegate business logic to services.
* Return stable response schemas.
* Handle expected errors explicitly.

### Example Pattern


from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

router = APIRouter()


class CreateItemRequest(BaseModel):
    name: str


class ItemResponse(BaseModel):
    id: int
    name: str


@router.post("/items", response_model=ItemResponse)
async def create_item(payload: CreateItemRequest) -> ItemResponse:
    item = await create_item_service(payload)
    return ItemResponse(id=item.id, name=item.name)


### Backend Rules

* Separate transport models from ORM models.
* Keep database sessions scoped and explicit.
* Handle retries and timeouts for external calls.
* Make idempotency explicit where relevant.

---

## LLM and Agent-Oriented Development Guidance

Because this file is designed for AI-assisted repositories, agents should optimize for traceability and predictable structure.

### Rules for AI-Friendly Code

* Prefer explicit schemas over implicit conventions.
* Prefer pure functions where possible.
* Keep state transitions understandable.
* Avoid magic behavior hidden in decorators, globals, or metaprogramming unless already central to the codebase.
* Make prompt templates, parsing logic, and model adapters modular.
* Validate structured LLM outputs with Pydantic.

### Prompt / Agent Layer Guidance

If the project includes AI agents, copilots, or LLM workflows:

* keep system prompts versioned and reviewable
* separate prompts from execution logic
* define structured outputs with schemas
* log model inputs and outputs safely when allowed
* support retries and validation failures explicitly
* avoid silent fallbacks that hide model errors

### Example Pattern


from pydantic import BaseModel


class ClassificationResult(BaseModel):
    label: str
    confidence: float


Use validated outputs instead of trusting raw model text.

---

## Configuration Management

### Rules

* Centralize configuration.
* Parse environment variables into typed config objects.
* Validate config at startup.
* Keep defaults safe and explicit.

### Example


from pydantic import BaseModel


class AppConfig(BaseModel):
    app_name: str = "my-app"
    debug: bool = False
    database_url: str


Avoid scattered `os.getenv()` calls across the codebase when a centralized config module is more maintainable.

---

## File and Folder Organization

Use the repository's existing structure if present. If creating a new Python project, prefer something close to:


.
├── AGENTS.md
├── README.md
├── pyproject.toml
├── uv.lock
├── src/
│   └── project_name/
│       ├── api/
│       ├── core/
│       ├── schemas/
│       ├── services/
│       ├── persistence/
│       ├── integrations/
│       └── main.py
├── tests/
├── scripts/
└── docs/


### Rules

* Keep source code under `src/` when practical.
* Keep tests mirrored and easy to locate.
* Avoid dumping unrelated scripts into the root.
* Group files by feature or domain when that improves navigation.

---

## Performance Guidance

* Optimize only where it matters.
* Measure before redesigning.
* Keep algorithms and queries reasonable.
* Use batching, caching, and async I/O only when they solve a real problem.

### Avoid

* premature micro-optimizations
* unnecessary concurrency
* overly abstract caching layers
* complex performance tricks without benchmarks

### Prefer

* clear data flow
* bounded queries
* explicit pagination
* careful external-call management

---

## What Agents Should Do

1. Read before editing.
2. Reuse established patterns.
3. Keep changes scoped.
4. Maintain typing quality.
5. Use Pydantic for contracts.
6. Use `uv` commands for Python workflows.
7. Add or update tests.
8. Update docs when needed.
9. Preserve security boundaries.
10. Leave clear, maintainable code.

---

## What Agents Should Avoid

1. Do not invent architecture without evidence from the repository.
2. Do not introduce heavy dependencies casually.
3. Do not hardcode secrets, paths, or environment-specific values.
4. Do not bypass validation or authorization.
5. Do not couple unrelated layers together.
6. Do not create giant utility files.
7. Do not add silent magic behavior that is hard to debug.
8. Do not leave dead code, commented-out code, or debug prints.
9. Do not weaken typing just to move faster.
10. Do not ship undocumented behavior changes.

---

## Quality Checklist

Before considering work complete, verify:

* [ ] Relevant files and docs were read first
* [ ] Change follows existing architecture and style
* [ ] `uv` workflow is respected
* [ ] Pydantic schemas are used where contracts matter
* [ ] New or changed behavior is tested
* [ ] Linting and formatting were run
* [ ] No secrets or unsafe logging were introduced
* [ ] Documentation was updated if needed
* [ ] Code is readable and locally understandable
* [ ] No unnecessary abstractions or dependencies were added

---

## Optional Project-Specific Section Template

Repositories can extend this generic base with a short project appendix such as:


## Project-Specific Notes

### Stack
- FastAPI
- SQLAlchemy
- PostgreSQL
- Redis

### Commands
- `uv run pytest`
- `uv run alembic upgrade head`
- `uv run python -m app.main`

### Critical Constraints
- All writes require audit logging
- Admin routes require RBAC checks
- External provider calls must use retry policy


This keeps the generic guidance reusable while allowing each repository to add concrete local rules.

---

## Final Note

The goal of this file is not to force a rigid style. The goal is to create a reliable default operating model for AI-assisted software development:

* typed
* testable
* maintainable
* secure
* explicit
* professional

When in doubt, choose the solution that is easiest to understand, easiest to validate, and easiest to maintain.
