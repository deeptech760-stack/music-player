# Contributing to Music Player

Thank you for your interest in contributing to Music Player! This document provides guidelines for contributing to the project.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct:
- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive criticism
- Respect differing opinions and experiences

## How to Contribute

### Reporting Bugs

Before reporting a bug, please check if it has already been reported in the [Issues](https://github.com/deeptech760-stack/music-player/issues).

When reporting a bug, please include:
- **OS and version** (Windows 10/11, macOS, Linux distro)
- **Python version** (`python --version`)
- **Steps to reproduce** the issue
- **Expected behavior** vs **actual behavior**
- **Screenshots** (if applicable)
- **Logs** (check `~/.local/share/MusicPlayer/logs/` or console output)

### Suggesting Features

Feature requests are welcome! Please open an issue with:
- Clear description of the feature
- Use case / motivation
- Possible implementation approach (optional)

### Pull Requests

1. **Fork** the repository
2. **Create a branch** for your feature/fix: `git checkout -b feature/amazing-feature`
3. **Make your changes** following the coding standards below
4. **Run tests** to ensure nothing breaks: `pytest tests/ -v`
5. **Commit your changes** with clear messages
6. **Push to your fork** and open a Pull Request

## Development Setup

### Prerequisites

- Python 3.11+
- VLC Media Player (for audio playback - install from [videolan.org](https://www.videolan.org/vlc/))
- Git

### Installation

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/music-player.git
cd music-player

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -e .  # Install in development mode
```

### Running the Application

```bash
# Development run
python -m src.main

# Or use the convenience scripts
./run.sh        # Linux/macOS
run.bat         # Windows
```

### Running Tests

```bash
# All tests
pytest tests/ -v

# Backend only
pytest tests/backend/ -v

# Frontend only
pytest tests/frontend/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

## Coding Standards

### Python Style

- Follow [PEP 8](https://pep8.org/) style guide
- Use [Black](https://black.readthedocs.io/) for formatting: `black src/ tests/`
- Use [Ruff](https://docs.astral.sh/ruff/) for linting: `ruff src/ tests/`
- Type hints are **required** for all new code
- Run [mypy](https://mypy-lang.org/) for type checking: `mypy src/`

### Architecture

Follow the existing architecture defined in `AGENTS.md`:

- **Backend** (`src/backend/`): Business logic, database, services
- **Frontend** (`src/frontend/`): UI components, views, styles
- **Interfaces** (`src/backend/services/interfaces.py`): Abstract base classes
- **Main** (`src/main.py`): Application entry point (wiring only)

### Commit Messages

Use conventional commit format:
```
type(scope): short description

Longer description if needed

Fixes #123
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Formatting, missing semicolons, etc.
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance tasks

Examples:
```
feat(library): add support for OPUS audio format
fix(playback): handle VLC initialization failure gracefully
docs(readme): update installation instructions for Windows
```

### Pull Request Checklist

Before submitting a PR, ensure:

- [ ] Code follows style guidelines (Black, Ruff, mypy pass)
- [ ] Tests pass (`pytest tests/ -v`)
- [ ] New code has type hints
- [ ] Documentation updated if needed
- [ ] Commit messages follow convention
- [ ] No private data in commits (API keys, passwords, local paths)
- [ ] PR description explains the change and why

## Project Structure

```
music-player/
├── src/
│   ├── backend/
│   │   ├── services/     # Business logic (Library, Playback, Queue, Playlist, Settings)
│   │   ├── models/       # Data models (Song, Album, Artist, etc.)
│   │   ├── utils/        # Utilities (metadata, files, database)
│   │   └── exceptions.py # Custom exceptions
│   ├── frontend/
│   │   ├── ui/           # Main views (Songs, Albums, Artists, etc.)
│   │   ├── components/   # Reusable UI components
│   │   └── resources/    # QSS styles, icons
│   └── main.py           # Entry point
├── tests/
│   ├── backend/
│   └── frontend/
├── docs/                 # Documentation
├── requirements.txt      # Python dependencies
├── pyproject.toml        # Project metadata
├── setup.py              # Setuptools config
├── LICENSE               # MIT License
├── README.md             # This file
├── CONTRIBUTING.md       # This file
├── CHANGELOG.md          # Version history
├── .gitignore            # Git ignore rules
└── AGENTS.md             # Architecture documentation
```

## Getting Help

- Open a [GitHub Discussion](https://github.com/deeptech760-stack/music-player/discussions) for questions
- Check existing [Issues](https://github.com/deeptech760-stack/music-player/issues) for known problems
- Review `AGENTS.md` for architecture details

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).