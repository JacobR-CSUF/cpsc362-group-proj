# Code Linting with Flake8

This project uses flake8 for Python code linting to maintain code quality and consistency across the team.

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

This will install flake8 along with all other project dependencies.

### 2. Verify Installation
```bash
flake8 --version
```

## Running Flake8

### Option 1: Cross-platform Python Script (Recommended)
```bash
python scripts/lint.py
```

This script works on Windows, macOS, and Linux.

### Option 2: Direct Command
```bash
# Lint specific files
flake8 apps/api/app/main.py

# Lint entire apps directory
flake8 apps/

# Lint with custom options
flake8 apps/ --max-line-length=88
```

### Platform-Specific Commands

#### Windows (PowerShell)
```powershell
# Activate virtual environment first
.\.venv\Scripts\Activate.ps1
flake8 apps/
```

#### macOS/Linux (Bash/Zsh)
```bash
# Activate virtual environment first
source .venv/bin/activate
flake8 apps/
```

## Configuration

The project includes a `.flake8` configuration file with the following settings:
- Max line length: 88 characters
- Excludes common directories (venv, __pycache__, etc.)
- Ignores some common formatting conflicts with Black formatter

## Integration with VS Code

1. Install the "Python" extension (which includes flake8 support)
2. flake8 will automatically run when you open Python files
3. Errors will be highlighted in the editor

## Pre-commit Hook (Optional)

To automatically run flake8 before commits, you can set up a pre-commit hook:

```bash
pip install pre-commit
```

Then create a `.pre-commit-config.yaml` file in the project root if needed.

## Common Issues

### "flake8 command not found"
- Make sure you've activated your virtual environment
- Ensure flake8 is installed: `pip install flake8`

### "Permission denied" on Windows
- Run PowerShell as Administrator, or
- Change execution policy: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`