#!/usr/bin/env python3
"""
Comprehensive test runner for the crypto-fiat payment processor
Runs unit tests, integration tests, security tests, and performance tests
"""
import asyncio
import subprocess
import sys
import os
import logging
from pathlib import Path
import argparse
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

def run_command(command: str, cwd: str = ".", check: bool = True) -> bool:
    """
    Runs a shell command and prints its output.
    Returns True if successful, False otherwise.
    """
    logger.info(f"Running: {command}")
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=check,
            capture_output=True,
            text=True,
            cwd=cwd
        )
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
        logger.error(f"Command not found: {command.split(' ')[0]}")
        return False

def run_unit_tests():
    """Run unit tests with coverage"""
    commands = [
        (
            "pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing --cov-fail-under=80",
            "Unit Tests with Coverage"
        ),
        (
            "pytest tests/test_domain_value_objects.py -v",
            "Domain Value Objects Tests"
        ),
        (
            "pytest tests/test_bitcoin_service.py -v",
            "Bitcoin Service Tests"
        ),
        (
            "pytest tests/test_auth.py -v",
            "Authentication Tests"
        )
    ]
    
    results = []
    for command, description in commands:
        results.append(run_command(command, description))
    
    return all(results)

def run_integration_tests():
    """Run integration tests"""
    commands = [
        (
            "pytest tests/ -m integration -v",
            "Integration Tests"
        ),
        (
            "pytest tests/ -m 'not unit and not performance' -v",
            "End-to-End Tests"
        )
    ]
    
    results = []
    for command, description in commands:
        results.append(run_command(command, description))
    
    return all(results)

def run_security_tests():
    """Run security tests"""
    commands = [
        (
            "bandit -r app/ -f json -o security-report.json",
            "Security Vulnerability Scan (Bandit)"
        ),
        (
            "safety check --json --output safety-report.json",
            "Dependency Security Check (Safety)"
        ),
        (
            "pytest tests/ -k security -v",
            "Security-focused Tests"
        )
    ]
    
    results = []
    for command, description in commands:
        results.append(run_command(command, description))
    
    return all(results)

def run_performance_tests():
    """Run performance tests"""
    commands = [
        (
            "pytest tests/ -m performance -v",
            "Performance Tests"
        ),
        (
            "python -m pytest tests/test_bitcoin_service.py::TestBitcoinServicePerformance -v",
            "Bitcoin Service Performance Tests"
        )
    ]
    
    results = []
    for command, description in commands:
        results.append(run_command(command, description))
    
    return all(results)

def run_code_quality_checks():
    """Run code quality checks"""
    commands = [
        (
            "black --check app/ tests/",
            "Code Formatting Check (Black)"
        ),
        (
            "ruff check app/ tests/",
            "Linting Check (Ruff)"
        ),
        (
            "mypy app/",
            "Type Checking (MyPy)"
        )
    ]
    
    results = []
    for command, description in commands:
        results.append(run_command(command, description))
    
    return all(results)

def run_database_tests():
    """Run database-specific tests"""
    commands = [
        (
            "pytest tests/ -k database -v",
            "Database Tests"
        ),
        (
            "pytest tests/ -k migration -v",
            "Migration Tests"
        )
    ]
    
    results = []
    for command, description in commands:
        results.append(run_command(command, description))
    
    return all(results)

def run_financial_tests():
    """Run financial calculation and compliance tests"""
    commands = [
        (
            "pytest tests/test_domain_value_objects.py::TestMoney -v",
            "Money Value Object Tests"
        ),
        (
            "pytest tests/ -k 'fee or exchange or compliance' -v",
            "Financial Logic Tests"
        ),
        (
            "pytest tests/ -k 'decimal or precision' -v",
            "Financial Precision Tests"
        )
    ]
    
    results = []
    for command, description in commands:
        results.append(run_command(command, description))
    
    return all(results)

def generate_test_report():
    """Generate comprehensive test report"""
    logger.info(f"\n{'='*60}")
    logger.info("GENERATING TEST REPORT")
    logger.info(f"{'='*60}")
    
    # Generate coverage report
    run_command(
        "coverage html --directory=htmlcov",
        "Generate HTML Coverage Report"
    )
    
    # Generate test results summary
    run_command(
        "pytest tests/ --junitxml=test-results.xml",
        "Generate JUnit XML Report"
    )
    
    logger.info("\n📊 Test Reports Generated:")
    logger.info("- HTML Coverage Report: htmlcov/index.html")
    logger.info("- JUnit XML Report: test-results.xml")
    logger.info("- Security Report: security-report.json")
    logger.info("- Safety Report: safety-report.json")

def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description="Comprehensive test runner")
    parser.add_argument("--unit", action="store_true", help="Run unit tests")
    parser.add_argument("--integration", action="store_true", help="Run integration tests")
    parser.add_argument("--security", action="store_true", help="Run security tests")
    parser.add_argument("--performance", action="store_true", help="Run performance tests")
    parser.add_argument("--quality", action="store_true", help="Run code quality checks")
    parser.add_argument("--database", action="store_true", help="Run database tests")
    parser.add_argument("--financial", action="store_true", help="Run financial tests")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--report", action="store_true", help="Generate test report")
    
    args = parser.parse_args()
    
    if not any(vars(args).values()):
        args.all = True  # Default to running all tests
    
    logger.info("🚀 Starting Crypto-Fiat Payment Processor Test Suite")
    logger.info(f"Python: {sys.version}")
    logger.info(f"Working Directory: {os.getcwd()}")
    
    start_time = time.time()
    all_passed = True
    
    # Run selected test suites
    if args.all or args.quality:
        if not run_code_quality_checks():
            all_passed = False
    
    if args.all or args.unit:
        if not run_unit_tests():
            all_passed = False
    
    if args.all or args.financial:
        if not run_financial_tests():
            all_passed = False
    
    if args.all or args.database:
        if not run_database_tests():
            all_passed = False
    
    if args.all or args.security:
        if not run_security_tests():
            all_passed = False
    
    if args.all or args.integration:
        if not run_integration_tests():
            all_passed = False
    
    if args.all or args.performance:
        if not run_performance_tests():
            all_passed = False
    
    if args.all or args.report:
        generate_test_report()
    
    end_time = time.time()
    total_duration = end_time - start_time
    
    logger.info(f"\n{'='*60}")
    logger.info("TEST SUITE SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"Total Duration: {total_duration:.2f} seconds")
    
    if all_passed:
        logger.info("🎉 ALL TESTS PASSED!")
        sys.exit(0)
    else:
        logger.error("💥 SOME TESTS FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    main()
