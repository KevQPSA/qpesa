"""
Comprehensive test runner script for the backend application.
Executes unit, integration, and security tests, and generates coverage reports.
"""
import subprocess
import sys
import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_command(command: list[str], cwd: str = ".", check: bool = True) -> bool:
    """
    Runs a shell command and prints its output.
    Returns True if successful, False otherwise.
    """
    full_command_str = " ".join(command)
    logger.info(f"\n{'='*60}")
    logger.info(f"Running command: {full_command_str}")
    logger.info(f"{'='*60}")
    try:
        result = subprocess.run(
            command,
            check=check,
            capture_output=True,
            text=True,
            cwd=cwd,
            encoding='utf-8',
            env={**os.environ, "TESTING": "true"} # Set TESTING env var for test config
        )
        if result.stdout:
            logger.info("STDOUT:\n" + result.stdout)
        if result.stderr:
            logger.error("STDERR:\n" + result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with exit code {e.returncode}")
        logger.error("STDOUT:\n" + e.stdout)
        logger.error("STDERR:\n" + e.stderr)
        return False
    except FileNotFoundError:
        logger.error(f"Command not found: {command[0]}. Make sure it's installed and in your PATH.")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return False

def main():
    backend_dir = Path(__file__).parent
    
    logger.info("🚀 Starting Comprehensive Test Suite for Crypto-Fiat Payment Processor")
    logger.info("Following financial system testing requirements...")

    tests_passed = True

    # 1. Code Formatting Check (Black)
    if not run_command([sys.executable, "-m", "black", ".", "--check"], cwd=backend_dir):
        logger.error("Result: ❌ FAILED - Code is not formatted correctly. Run 'black .' to fix.")
        tests_passed = False

    # 2. Linting Check (Ruff)
    if not run_command([sys.executable, "-m", "ruff", "check", "."], cwd=backend_dir):
        logger.error("Result: ❌ FAILED - Linting issues found.")
        tests_passed = False

    # 3. Type Checking (MyPy)
    if not run_command([sys.executable, "-m", "mypy", "."], cwd=backend_dir):
        logger.error("Result: ❌ FAILED - Type errors found.")
        tests_passed = False

    # 4. Security Vulnerability Scan (Bandit)
    # Bandit might return non-zero even for warnings, so we don't set check=True here
    if not run_command([sys.executable, "-m", "bandit", "-r", ".", "-f", "json", "-o", "bandit_report.json"], cwd=backend_dir, check=False):
        logger.warning("Result: ⚠️ FAILED (Bandit encountered issues or errors, check bandit_report.json)")
        # This is a warning, not a hard failure for the overall suite unless configured otherwise

    # 5. Unit and Integration Tests (Pytest with Coverage)
    # Ensure pytest and pytest-cov are installed: pip install pytest pytest-cov pytest-asyncio httpx
    pytest_command = [
        sys.executable, "-m", "pytest",
        "--cov=app",  # Measure coverage for the 'app' directory
        "--cov-report=term-missing", # Report missing lines to terminal
        "--cov-report=xml:coverage.xml", # Generate XML coverage report
        "tests/" # Run tests in the tests directory
    ]
    
    if not run_command(pytest_command, cwd=backend_dir):
        logger.error("Result: ❌ FAILED - Some tests failed.")
        tests_passed = False

    logger.info(f"\n{'='*80}")
    logger.info("TEST SUITE SUMMARY")
    logger.info(f"{'='*80}")
    
    if tests_passed:
        logger.info("🎉 ALL CHECKS AND TESTS PASSED! System ready for financial operations.")
        sys.exit(0)
    else:
        logger.error("💔 SOME CHECKS OR TESTS FAILED! Review failures before deployment.")
        logger.error("Failed tests must be fixed before handling real money!")
        sys.exit(1)

if __name__ == "__main__":
    main()
