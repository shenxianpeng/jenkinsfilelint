# Contributing

Contributions are welcome! Here's how to get started.

## Setup

```bash
pip install -e ".[dev]"
pre-commit install
```

Run pre-commit before submitting:

```bash
pre-commit run --all-files
```

## Testing

```bash
pytest tests/ -v --cov=jenkinsfilelint
```

## Conventions

- Follow [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `chore:`, etc.)
- Keep PRs focused — one logical change per PR.
- Update the README if your change affects usage or configuration.
