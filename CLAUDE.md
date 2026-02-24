# CLAUDE.md

## Project Overview

ABCDs Detector evaluates video ads against YouTube's ABCD framework (Attract, Brand, Connect, Direct) using Google AI. It combines Video Intelligence API annotations with Gemini LLM analysis to produce automated creative assessments. The project includes both a CLI pipeline (`main.py`) and a FastAPI web application (`web_app.py`).

## Tech Stack

- **Language:** Python 3.11+
- **Web framework:** FastAPI + Uvicorn
- **Database:** SQLAlchemy + Alembic (SQLite for dev, PostgreSQL for prod)
- **Cloud:** Google Cloud (Vertex AI, Video Intelligence API, Cloud Storage, BigQuery)
- **Auth:** Google OAuth + session-based auth with JWT
- **Billing:** Stripe integration
- **Video processing:** FFmpeg, moviepy, yt-dlp
- **Container:** Docker (Python 3.11-slim base)

## Getting Started

```bash
# Install dependencies
pip install -r requirements.txt

# Install dev tools
pip install -e ".[dev]"

# Copy env file and fill in values
cp .env.example .env

# Initialize the database
python -c "from db import init_db; init_db()"

# Run database migrations
alembic upgrade head

# Run the web app
uvicorn web_app:app --host 0.0.0.0 --port 8080

# Run the CLI pipeline
python main.py --project_id=<GCP_PROJECT> --bucket_name=<BUCKET> --brand_name=<BRAND>
```

## Running Tests

```bash
pytest                    # run all tests
pytest tests/             # same (testpaths configured in pyproject.toml)
pytest tests/test_web_app.py  # run a specific test file
pytest -v --tb=short      # verbose with short tracebacks (default via addopts)
```

Test configuration is in `pyproject.toml` under `[tool.pytest.ini_options]`. Tests are in the `tests/` directory.

## Linting & Formatting

```bash
ruff check .              # lint
ruff check --fix .        # lint and auto-fix
ruff format .             # format code
pyink .                   # alternative formatter (Google style)
pylint <file>             # static analysis
```

**Style rules (from `pyproject.toml`):**
- Line length: 80 characters
- Indent width: 2 spaces
- Target: Python 3.11
- Docstring convention: Google style
- Formatter: ruff (with preview enabled) / pyink

## Project Structure

```
abcds-detector/
  main.py                    # CLI entry point for ABCD assessment pipeline
  web_app.py                 # FastAPI web application (primary web interface)
  configuration.py           # Configuration class with all runtime parameters
  models.py                  # Data models (VideoAssessment, Feature types, enums)
  db.py                      # SQLAlchemy database models (User, Render, CreditTransaction)
  auth.py                    # Authentication (Google OAuth, JWT sessions)
  billing.py                 # Stripe billing integration
  admin.py                   # Admin routes
  credits.py                 # Credit system logic
  scene_detector.py          # Video scene detection
  report_service.py          # PDF/report generation
  utils.py                   # CLI argument parsing and config builder

  features_repository/       # Feature definitions (ABCD rubrics)
    long_form_abcd_features.py   # Long-form video ABCD features
    shorts_features.py           # YouTube Shorts features
    creative_intelligence_features.py  # Creative intelligence features
    feature_configs_handler.py   # Feature config loading

  evaluation_services/        # Video evaluation pipeline
    video_evaluation_service.py       # Core evaluation orchestration
    confidence_calibration_service.py # Confidence scoring

  creative_providers/         # Video source integrations
    creative_provider_proto.py     # Provider interface
    creative_provider_factory.py   # Factory pattern
    creative_provider_registry.py  # Provider registration
    gcs_creative_provider.py       # Google Cloud Storage provider
    youtube_creative_provider.py   # YouTube URL provider

  annotations_evaluation/     # Video Intelligence API annotation processing
  helpers/                    # Utility functions (generic_helpers, annotations_helpers)
  prompts/                    # LLM prompt templates
  custom_evaluation/          # Custom evaluation function implementations
  llms_evaluation/            # LLM-based evaluation logic

  alembic/                    # Database migrations
  tests/                      # Test suite (pytest)
  static/                     # Static web assets
  scripts/                    # Utility scripts
  docs/                       # Documentation
```

## Key Environment Variables

See `.env.example` for the full list. Critical ones:

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | DB connection string (default: `sqlite:///data/app.db`) |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | Google OAuth credentials |
| `SESSION_SECRET` | Session signing key (must be random in prod) |
| `STRIPE_SECRET_KEY` / `STRIPE_WEBHOOK_SECRET` | Stripe billing |
| `ABCD_KG_API_KEY` | Google Knowledge Graph API key |
| `ENVIRONMENT` | `development` or `production` |
| `IMAGEIO_FFMPEG_EXE` | Path to FFmpeg binary |
| `PUBLIC_BASE_URL` | Public URL for OAuth redirects and report links |

## Database

- **Dev:** SQLite at `data/app.db` (auto-created)
- **Prod:** PostgreSQL via `DATABASE_URL` env var
- **Migrations:** Alembic (`alembic upgrade head` / `alembic revision --autogenerate -m "description"`)
- **Models:** `db.py` defines User, Render, CreditTransaction, FeatureFeedback, ProcessedStripeEvent

## Docker

```bash
docker build -t abcds-detector .
docker run -p 8080:8080 --env-file .env abcds-detector
```

The container runs `uvicorn web_app:app` on port 8080 with a health check at `/health`.

## Common Patterns

- **Configuration:** All runtime params flow through the `Configuration` class in `configuration.py`
- **Feature definitions:** Add/remove features in `features_repository/` files; the pipeline picks them up automatically
- **Creative providers:** Implement `creative_provider_proto.CreativeProviderProto` and register in `creative_provider_registry.py`
- **Custom evaluation:** Add custom eval functions in `custom_evaluation/` that return the standard `VIDEO_RESPONSE_SCHEMA` format
- **Feature grouping:** Features can be grouped by `full_video` or `first_5_secs_video` for batched LLM calls, or set to `no_grouping` for individual evaluation

## Code Style Conventions

- **License header:** Apache 2.0 copyright header required on all `.py` files
- **Indentation:** 2 spaces (not 4)
- **Line length:** 80 characters max
- **Quotes:** Majority-rules (via pyink)
- **Docstrings:** Google style
- **Type hints:** Expected on function signatures
- **Naming:** modules `snake_case.py`, classes `PascalCase`, functions/vars `snake_case`, constants `UPPER_SNAKE_CASE`
- **Commits:** Conventional Commits format — `type(scope): message` (e.g. `feat(abcd): add Shorts evaluation`)

## Pre-commit Hooks

```bash
pre-commit install          # set up hooks
pre-commit run --all-files  # run manually
```

Configured hooks include: copyright header checks, ruff, pyink, pylint, pytype, mdformat, commitizen, trailing whitespace, JSON/YAML validation.

## CI/CD

GitHub Actions workflows in `.github/workflows/`:
- **ci.yml** — runs ruff lint/format checks and pytest on every PR
- **deploy.yml** — deploys to Google Cloud Run on pushes to main
