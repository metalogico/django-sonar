#!/usr/bin/env python
"""Run the complete Django Sonar test suite with the active interpreter."""

import subprocess
import sys


def run_tests():
    print('=' * 70)
    print('DJANGO SONAR - COMPLETE TEST SUITE')
    print('=' * 70)
    return subprocess.run(
        [sys.executable, 'manage.py', 'test', 'django_sonar', '-v', '2'],
        check=False,
    ).returncode


if __name__ == '__main__':
    sys.exit(run_tests())
