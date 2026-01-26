# reporter.py
from typing import List
from models import SyntaxError


def print_analysis_report(errors: List[SyntaxError], original: str, fixed: str):
    """
    Print analysis report with detected errors and template comparison.
    
    This function generates a comprehensive report showing:
    - All detected syntax errors with details
    - Original template content
    - Fixed template content
    
    Args:
        errors: List of SyntaxError objects detected in the template
        original: Original template string
        fixed: Fixed template string after applying corrections
    """
    print("\n" + "="*80)
    print("Jinja2 Template Static Syntax Analysis Report")
    print("="*80)
    
    if errors:
        # Sort errors by line number and column for logical ordering
        sorted_errors = sorted(errors, key=lambda e: (e.line, e.col))
        print(f"\n✗ Detected {len(sorted_errors)} syntax error(s) (in order of appearance):\n")
        
        # Print each error with detailed information
        for i, error in enumerate(sorted_errors, 1):
            print(f"{i}. 【{error.rule}】")
            print(f"   Line {error.line}, Column {error.col}")
            print(f"   Description: {error.description}")
            print(f"   Original: {error.original}")
            print(f"   Suggestion: {error.suggestion}")
            print()
    else:
        print("\n✓ No syntax errors detected!\n")
    
    # Display original template
    print("\n" + "="*80)
    print("Original Template:")
    print("="*80)
    print(original)
    
    # Display fixed template
    print("\n" + "="*80)
    print("Fixed Template:")
    print("="*80)
    print(fixed)
    print("\n" + "="*80 + "\n")
