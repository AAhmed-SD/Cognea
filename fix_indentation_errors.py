#!/usr/bin/env python3
"""
Comprehensive Indentation Error Fixer

This script fixes indentation errors caused by incorrect `pass` statements
that were added by the MyPy fixer.
"""

import os
import re
import ast
from typing import List, Tuple

def find_python_files_with_errors() -> List[str]:
    """Find all Python files with indentation errors."""
    error_files = []
    
    # Check all Python files in the workspace
    for root, dirs, files in os.walk('.'):
        # Skip virtual environment and other non-source directories
        if 'venv' in root or '__pycache__' in root or '.git' in root:
            continue
            
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                if has_indentation_error(filepath):
                    error_files.append(filepath)
    
    return error_files

def has_indentation_error(filepath: str) -> bool:
    """Check if a Python file has indentation errors."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        return False
    except (SyntaxError, IndentationError):
        return True
    except Exception:
        return False

def fix_function_pass_statements(content: str) -> str:
    """Fix incorrect pass statements after function definitions."""
    lines = content.split('\n')
    fixed_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check if this line is a function definition
        if re.match(r'^\s*(def|async def)\s+\w+\(.*\):\s*$', line.strip()):
            fixed_lines.append(line)
            i += 1
            
            # Check if the next line is an incorrectly indented pass
            if i < len(lines):
                next_line = lines[i]
                if next_line.strip() == 'pass':
                    # Get the indentation of the function definition
                    func_indent = len(line) - len(line.lstrip())
                    # Add proper indentation for the pass statement
                    fixed_lines.append(' ' * (func_indent + 4) + 'pass')
                    i += 1
                else:
                    # Keep the original next line
                    continue
        else:
            fixed_lines.append(line)
            i += 1
    
    return '\n'.join(fixed_lines)

def fix_class_pass_statements(content: str) -> str:
    """Fix incorrect pass statements after class definitions."""
    lines = content.split('\n')
    fixed_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check if this line is a class definition
        if re.match(r'^\s*class\s+\w+.*:\s*$', line.strip()):
            fixed_lines.append(line)
            i += 1
            
            # Check if the next line is an incorrectly indented pass
            if i < len(lines):
                next_line = lines[i]
                if next_line.strip() == 'pass':
                    # Get the indentation of the class definition
                    class_indent = len(line) - len(line.lstrip())
                    # Add proper indentation for the pass statement
                    fixed_lines.append(' ' * (class_indent + 4) + 'pass')
                    i += 1
                else:
                    # Keep the original next line
                    continue
        else:
            fixed_lines.append(line)
            i += 1
    
    return '\n'.join(fixed_lines)

def fix_if_else_pass_statements(content: str) -> str:
    """Fix incorrect pass statements after if/else/try/except blocks."""
    lines = content.split('\n')
    fixed_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check if this line is an if/else/try/except/with statement
        if re.match(r'^\s*(if|elif|else|try|except|finally|with|for|while)\s+.*:\s*$', line.strip()) or \
           re.match(r'^\s*(else|finally):\s*$', line.strip()):
            fixed_lines.append(line)
            i += 1
            
            # Check if the next line is an incorrectly indented pass
            if i < len(lines):
                next_line = lines[i]
                if next_line.strip() == 'pass':
                    # Get the indentation of the control statement
                    control_indent = len(line) - len(line.lstrip())
                    # Add proper indentation for the pass statement
                    fixed_lines.append(' ' * (control_indent + 4) + 'pass')
                    i += 1
                else:
                    # Keep the original next line
                    continue
        else:
            fixed_lines.append(line)
            i += 1
    
    return '\n'.join(fixed_lines)

def fix_file_indentation(filepath: str) -> bool:
    """Fix indentation errors in a single file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # Apply all fixes
        content = original_content
        content = fix_function_pass_statements(content)
        content = fix_class_pass_statements(content)
        content = fix_if_else_pass_statements(content)
        
        # Only write if content changed
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Verify the fix worked
            try:
                ast.parse(content)
                print(f"✅ Fixed: {filepath}")
                return True
            except (SyntaxError, IndentationError) as e:
                print(f"❌ Still has errors after fix: {filepath} - {e}")
                # Restore original content if fix didn't work
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(original_content)
                return False
        else:
            print(f"ℹ️  No changes needed: {filepath}")
            return True
            
    except Exception as e:
        print(f"❌ Error processing {filepath}: {e}")
        return False

def main():
    """Main function to fix all indentation errors."""
    print("🔍 Finding Python files with indentation errors...")
    
    error_files = find_python_files_with_errors()
    
    if not error_files:
        print("✅ No indentation errors found!")
        return
    
    print(f"📝 Found {len(error_files)} files with indentation errors:")
    for file in error_files:
        print(f"   - {file}")
    
    print("\n🔧 Fixing indentation errors...")
    
    fixed_count = 0
    for filepath in error_files:
        if fix_file_indentation(filepath):
            fixed_count += 1
    
    print(f"\n📊 Summary:")
    print(f"   Files processed: {len(error_files)}")
    print(f"   Files fixed: {fixed_count}")
    print(f"   Files still with errors: {len(error_files) - fixed_count}")
    
    # Check for remaining errors
    remaining_errors = find_python_files_with_errors()
    if remaining_errors:
        print(f"\n⚠️  Files still with indentation errors:")
        for file in remaining_errors:
            print(f"   - {file}")
    else:
        print("\n🎉 All indentation errors fixed!")

if __name__ == "__main__":
    main()