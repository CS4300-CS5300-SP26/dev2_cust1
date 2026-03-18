"""
Management command to run all tests (Django unit + Behave BDD) with coverage.

Uses 'coverage run' as a subprocess so that module-level imports and class
definitions are measured correctly.

Usage:
    python manage.py test_all
"""

import subprocess
import sys

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Run all Django unit tests and Behave BDD tests with coverage"

    def handle(self, *args, **options):
        failures = 0

        # 1. Django unit tests (fresh coverage data)
        self.stdout.write(self.style.HTTP_INFO("\n========== Django Unit Tests ==========\n"))
        result = subprocess.run(
            [sys.executable, "-m", "coverage", "run", "manage.py", "test", "core", "--verbosity=2", "--no-input"],
        )
        if result.returncode:
            failures += 1

        # 2. Behave BDD tests (append to existing coverage data)
        self.stdout.write(self.style.HTTP_INFO("\n========== Behave BDD Tests ==========\n"))
        result = subprocess.run(
            [sys.executable, "-m", "coverage", "run", "--append", "manage.py", "behave", "--no-input"],
        )
        if result.returncode:
            failures += 1

        # 3. Coverage report
        self.stdout.write(self.style.HTTP_INFO("\n========== Coverage Report ==========\n"))
        subprocess.run([sys.executable, "-m", "coverage", "report"])

        if failures:
            self.stdout.write(self.style.ERROR(f"\n✗ {failures} test suite(s) had failures."))
            sys.exit(1)
        else:
            self.stdout.write(self.style.SUCCESS("\n✓ All tests passed."))
