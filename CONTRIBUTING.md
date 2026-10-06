# Contributing to AutoRAG

Thank you for your interest in contributing to **AutoRAG**! We welcome community contributions to make autonomous RAG optimization faster, more robust, and more accessible.

---

## 🧭 Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md). Please report unacceptable behavior following the guidelines therein.

---

## 🛠️ Getting Started

### 1. Fork & Clone
1. Fork the repository on GitHub: `https://github.com/Ashishds/autorag-platform`.
2. Clone your fork locally:
   ```bash
   git clone https://github.com/<YOUR-USERNAME>/autorag-platform.git
   cd autorag-platform
   ```

### 2. Environment Setup
* **Backend**:
  ```bash
  cd backend
  uv sync
  cp .env.example .env
  uv run alembic upgrade head
  ```
* **Frontend**:
  ```bash
  cd frontend
  npm install
  cp .env.example .env.local
  ```

---

## 🌿 Branch & Commit Guidelines

* **Branch Naming**:
  * Features: `feature/<short-description>`
  * Bug fixes: `fix/<short-description>`
  * Documentation: `docs/<short-description>`
* **Commit Messages**: Follow [Conventional Commits](https://www.conventionalcommits.org/):
  * `feat: add hybrid search weight parameter`
  * `fix: handle cohere rerank rate limit gracefully`
  * `docs: update quickstart instructions`

---

## 🧪 Testing & Code Quality

Before opening a pull request, ensure all linters and tests pass:

```bash
cd backend

# Format and linting checks
uv run ruff check .
uv run ruff format --check .

# Run test suites
uv run pytest tests/unit
uv run pytest tests/adversarial
```

---

## 📬 Pull Request Process

1. Create a pull request against the `main` branch.
2. Provide a clear description of the problem solved and changes introduced.
3. Link any related issues (e.g. `Fixes #12`).
4. Ensure your PR keeps the non-bypassable guardrails intact:
   * **Faithfulness gate** ($\ge 0.50$)
   * **Adversarial anchors** must maintain 100% pass rate.
5. Once submitted, maintainers will review your contribution!
