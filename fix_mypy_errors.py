#!/usr/bin/env python3
"""Script to systematically fix MyPy errors."""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple, Dict, Any

def read_mypy_errors(file_path: str) -> List[Tuple[str, int, str, str]]:
    """Read MyPy errors from file and parse them."""
    errors = []
    try:
        with open(file_path, 'r') as f:
            for line in f:
                if 'error:' in line:
                    parts = line.strip().split(':')
                    if len(parts) >= 4:
                        file_name = parts[0]
                        line_num = int(parts[1])
                        error_msg = ':'.join(parts[3:])
                        error_code = ''
                        if '[' in error_msg and ']' in error_msg:
                            error_code = error_msg.split('[')[-1].split(']')[0]
                        errors.append((file_name, line_num, error_msg, error_code))
    except FileNotFoundError:
        print(f"Error file {file_path} not found")
        return []
    return errors

def fix_no_untyped_def_errors(errors: List[Tuple[str, int, str, str]]) -> int:
    """Fix no-untyped-def errors by adding -> None annotations."""
    fixed_count = 0
    file_changes: Dict[str, List[Tuple[int, str]]] = {}
    
    for file_name, line_num, error_msg, error_code in errors:
        if error_code == 'no-untyped-def' and '-> None' in error_msg:
            if file_name not in file_changes:
                file_changes[file_name] = []
            file_changes[file_name].append((line_num, error_msg))
    
    for file_name, changes in file_changes.items():
        try:
            if not os.path.exists(file_name):
                continue
                
            with open(file_name, 'r') as f:
                lines = f.readlines()
            
            # Sort changes by line number in reverse order to avoid offset issues
            changes.sort(key=lambda x: x[0], reverse=True)
            
            for line_num, error_msg in changes:
                if line_num <= len(lines):
                    line = lines[line_num - 1]  # Convert to 0-based index
                    
                    # Check if it's a function definition that needs -> None
                    if 'def ' in line and '(' in line and ')' in line and '->' not in line:
                        # Find the end of the function signature
                        if line.strip().endswith(':'):
                            # Simple case: function definition on one line
                            new_line = line.rstrip().rstrip(':') + ' -> None:\n'
                            lines[line_num - 1] = new_line
                            fixed_count += 1
                        elif ')' in line:
                            # Function definition might span multiple lines
                            new_line = line.replace('):', ') -> None:')
                            if new_line != line:
                                lines[line_num - 1] = new_line
                                fixed_count += 1
            
            # Write back the modified file
            with open(file_name, 'w') as f:
                f.writelines(lines)
                
        except Exception as e:
            print(f"Error processing {file_name}: {e}")
    
    return fixed_count

def fix_empty_body_errors(errors: List[Tuple[str, int, str, str]]) -> int:
    """Fix empty-body errors by adding pass statements."""
    fixed_count = 0
    file_changes: Dict[str, List[int]] = {}
    
    for file_name, line_num, error_msg, error_code in errors:
        if error_code == 'empty-body':
            if file_name not in file_changes:
                file_changes[file_name] = []
            file_changes[file_name].append(line_num)
    
    for file_name, line_nums in file_changes.items():
        try:
            if not os.path.exists(file_name):
                continue
                
            with open(file_name, 'r') as f:
                lines = f.readlines()
            
            # Sort line numbers in reverse order
            line_nums.sort(reverse=True)
            
            for line_num in line_nums:
                if line_num <= len(lines):
                    line = lines[line_num - 1]
                    # If the line is a function/method definition, add pass on next line
                    if 'def ' in line and line.strip().endswith(':'):
                        # Check if next line is empty or just whitespace
                        if line_num < len(lines):
                            next_line = lines[line_num] if line_num < len(lines) else ""
                            if not next_line.strip():
                                # Get indentation from function definition
                                indent = len(line) - len(line.lstrip())
                                pass_line = ' ' * (indent + 4) + 'pass\n'
                                lines[line_num] = pass_line
                                fixed_count += 1
            
            # Write back the modified file
            with open(file_name, 'w') as f:
                f.writelines(lines)
                
        except Exception as e:
            print(f"Error processing {file_name}: {e}")
    
    return fixed_count

def main() -> None:
    """Main function to fix MyPy errors."""
    errors_file = "mypy_errors.txt"
    
    if not os.path.exists(errors_file):
        print(f"Error file {errors_file} not found. Run MyPy first.")
        sys.exit(1)
    
    print("Reading MyPy errors...")
    errors = read_mypy_errors(errors_file)
    print(f"Found {len(errors)} errors")
    
    # Fix no-untyped-def errors first (most common)
    print("\nFixing no-untyped-def errors...")
    fixed_untyped = fix_no_untyped_def_errors(errors)
    print(f"Fixed {fixed_untyped} no-untyped-def errors")
    
    # Fix empty-body errors
    print("\nFixing empty-body errors...")
    fixed_empty = fix_empty_body_errors(errors)
    print(f"Fixed {fixed_empty} empty-body errors")
    
    print(f"\nTotal fixes applied: {fixed_untyped + fixed_empty}")
    print("Re-run MyPy to see remaining errors.")

if __name__ == "__main__":
    main()