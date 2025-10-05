#!/usr/bin/env python
"""
Script per eseguire i test di django-sonar con un riepilogo chiaro.
"""

import sys
import subprocess

def run_tests():
    """Esegue tutti i test e mostra un riepilogo"""
    
    print("=" * 70)
    print("DJANGO SONAR - TEST SUITE")
    print("=" * 70)
    print()
    
    test_modules = [
        ('test_middleware_basic', 'Basic Middleware Functionality', 4),
        ('test_middleware_requests', 'HTTP Request Types', 10),
        ('test_middleware_data_capture', 'Data Capture', 11),
        ('test_middleware_exclusions', 'Path Exclusions', 4),
        ('test_middleware_helpers', 'Helper Methods', 5),
    ]
    
    total_tests = sum(count for _, _, count in test_modules)
    print(f"Running {total_tests} tests across {len(test_modules)} modules...\n")
    
    # Esegui tutti i test
    result = subprocess.run(
        ['python', 'manage.py', 'test', 'django_sonar.tests', '-v', '2'],
        capture_output=False
    )
    
    print("\n" + "=" * 70)
    print("TEST MODULES:")
    print("=" * 70)
    for module, description, count in test_modules:
        print(f"  ✓ {module:<30} {description:<30} ({count} tests)")
    
    print("\n" + "=" * 70)
    print(f"TOTAL: {total_tests} tests")
    print("=" * 70)
    
    return result.returncode

if __name__ == '__main__':
    sys.exit(run_tests())
