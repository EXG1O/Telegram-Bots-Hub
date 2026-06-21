# Contributing

Thank you for considering contributing!<br>
We appreciate your help in making this [project](https://constructor.exg1o.org/) better.

## Requirements

- Linux
- [uv](https://docs.astral.sh/uv/) 0.10

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/EXG1O/Telegram-Bots-Hub.git
cd Telegram-Bots-Hub
```

### 2. Configure environment variables

Copy the `.env.example` file to `.env` and configure it with your settings:

```bash
cp .env.example .env
```

### 3. Set up environment and dependencies

```bash
uv sync --locked
source .venv/bin/activate
```

## Usage

To run the microservice:

```bash
uvicorn --reload main:app
```

## Code Formatting and Linting

We use **ruff** for code formatting and linting, and **mypy** for type checking.

### ruff

To format your code:

```bash
ruff format
```

To check your code for linting issues:

```bash
ruff check
```

To auto-fix issues:

```bash
ruff check --fix
```

### mypy

To run type checking:

```bash
mypy .
```

### Run all checks

To run all code quality checks (formatting, linting, and type checking) at once, use:

```bash
ruff format && ruff check --fix && mypy .
```

## Logs

All log files can be found in the `logs` directory.

## Pull Requests

When submitting a PR, ensure that:

1. Your code follows the project's coding standards.
2. Your changes are well-documented with clear commit messages.
3. Each PR should address a single issue or feature.
