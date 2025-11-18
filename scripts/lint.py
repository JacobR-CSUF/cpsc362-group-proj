#!/usr/bin/env python3
"""
Cross-platform script to run flake8 linting on the project.
This script works on Windows, macOS, and Linux.
"""
import subprocess
import sys
import os


def run_flake8():
    """Run flake8 on the project files."""
    try:
        # Change to project root directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        os.chdir(project_root)

        print("Running flake8 linting...")

        # Run flake8 on the apps directory
        result = subprocess.run([
            sys.executable, "-m", "flake8",
            "apps/",
            "--max-line-length=88",
            "--exclude=__pycache__,migrations,venv,.venv,env,.env"
        ], capture_output=True, text=True)

        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)

        if result.returncode == 0:
            print("✅ No linting errors found!")
        else:
            print("❌ Linting errors found. Please fix them before committing.")

        return result.returncode

    except FileNotFoundError:
        print("❌ Error: flake8 not found.")
        print("Please install it with: pip install -r requirements.txt")
        return 1
    except Exception as e:
        print(f"❌ Error running flake8: {e}")
        return 1


if __name__ == "__main__":
    exit_code = run_flake8()
    sys.exit(exit_code)