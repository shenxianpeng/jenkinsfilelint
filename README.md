# Jenkinsfile Lint

[![CI](https://github.com/shenxianpeng/jenkinsfilelint/actions/workflows/main.yml/badge.svg)](https://github.com/shenxianpeng/jenkinsfilelint/actions/workflows/main.yml)


A Python-based Jenkinsfile linter that validates Jenkinsfiles using Jenkins API or performs basic syntax checking.

## Features

- Validates Jenkinsfiles using Jenkins REST API
- Falls back to basic syntax checking when Jenkins is not available
- Works as a pre-commit hook
- Supports both command-line usage and environment variables for configuration
- No mandatory Jenkins credentials required (but recommended for full validation)

## Installation

### Using pip

```bash
pip install -e .
```

### Using pre-commit

Add this to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/shenxianpeng/jenkinsfilelint
    rev: main  # or specific version tag
    hooks:
      - id: jenkinsfile-lint
```

## Usage

### Command Line

Basic usage (performs syntax check only):

```bash
jenkinsfilelint path/to/Jenkinsfile
```

With Jenkins validation (using environment variables):

```bash
export JENKINS_URL=https://your-jenkins-instance.com
export JENKINS_USER=your-username
export JENKINS_TOKEN=your-api-token

jenkinsfilelint path/to/Jenkinsfile
```

With Jenkins validation (using command-line arguments):

```bash
jenkinsfilelint path/to/Jenkinsfile \
  --jenkins-url https://your-jenkins-instance.com \
  --username your-username \
  --token your-api-token
```

Validate multiple files:

```bash
jenkinsfilelint Jenkinsfile Jenkinsfile.prod tests/Jenkinsfile
```

### Environment Variables

- `JENKINS_URL`: Your Jenkins server URL
- `JENKINS_USER`: Your Jenkins username (optional if anonymous read access is enabled)
- `JENKINS_TOKEN`: Your Jenkins API token (optional if anonymous read access is enabled)

### Pre-commit Hook

Create or update `.pre-commit-config.yaml` in your repository:

```yaml
repos:
  - repo: local
    hooks:
      - id: jenkinsfile-lint
        name: Lint Jenkinsfile
        description: Validate Jenkinsfile
        entry: jenkinsfilelint
        language: python
        types: [file]
        files: ^(Jenkinsfile(\..*)?|.*\.groovy)$
```

Then install the pre-commit hook:

```bash
pre-commit install
```

## How It Works

1. **With Jenkins API**: When Jenkins credentials are provided, the linter sends the Jenkinsfile to your Jenkins instance's `/pipeline-model-converter/validate` endpoint for full validation.

2. **Without Jenkins API**: When Jenkins credentials are not provided, the linter performs basic syntax checking to ensure the file is not empty and contains expected pipeline declarations.

## Requirements

- Python 3.6+
- requests library

## License

MIT License
