#!/usr/bin/env python3
"""
Fix remaining indentation errors that the first script couldn't handle.
"""

import os
import re
import ast

def fix_complex_indentation_errors():
    """Fix complex indentation errors in specific files."""
    
    # Files with known complex issues
    problem_files = [
        "./middleware/logging.py",
        "./middleware/rate_limit.py", 
        "./services/background_workers.py",
        "./services/cost_tracking.py",
        "./services/monitoring.py",
        "./services/performance.py",
        "./services/performance_monitor.py",
        "./services/redis_cache.py",
        "./services/redis_client.py",
        "./services/audit_dependency.py",
        "./services/ai/context_manager.py",
        "./services/notion/sync_manager.py",
        "./tests/test_auth_service_comprehensive.py",
        "./tests/test_notion_integration.py",
        "./tests/test_routes_comprehensive.py"
    ]
    
    for filepath in problem_files:
        if os.path.exists(filepath):
            print(f"🔧 Fixing {filepath}...")
            fix_file_complex(filepath)

def fix_file_complex(filepath: str) -> bool:
    """Fix complex indentation issues in a file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Pattern 1: Fix pass statements that are incorrectly placed after function definitions
        # This handles cases where pass is on the same line as the closing ):
        content = re.sub(
            r'(\s*def\s+[^:]+:\s*)\n\s*pass\s*\n',
            r'\1\n',
            content
        )
        
        # Pattern 2: Fix pass statements after multiline function definitions
        lines = content.split('\n')
        fixed_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Look for function definitions that span multiple lines
            if re.match(r'^\s*(def|async def)\s+', line) and line.strip().endswith(':'):
                # This is a complete function definition on one line
                fixed_lines.append(line)
                i += 1
                
                # Check if next line is a misplaced pass
                if i < len(lines) and lines[i].strip() == 'pass':
                    # Get indentation and add properly indented pass
                    func_indent = len(line) - len(line.lstrip())
                    fixed_lines.append(' ' * (func_indent + 4) + 'pass')
                    i += 1
                    continue
                    
            elif re.match(r'^\s*(def|async def)\s+', line) and not line.strip().endswith(':'):
                # This is a multiline function definition
                func_lines = [line]
                i += 1
                
                # Collect all lines until we find the closing ):
                while i < len(lines) and not lines[i].strip().endswith(':'):
                    func_lines.append(lines[i])
                    i += 1
                
                # Add the final line with :
                if i < len(lines):
                    func_lines.append(lines[i])
                    i += 1
                
                # Add all function definition lines
                fixed_lines.extend(func_lines)
                
                # Check if next line is a misplaced pass
                if i < len(lines) and lines[i].strip() == 'pass':
                    # Get indentation from the first line of function def
                    func_indent = len(func_lines[0]) - len(func_lines[0].lstrip())
                    fixed_lines.append(' ' * (func_indent + 4) + 'pass')
                    i += 1
                    continue
                    
            else:
                fixed_lines.append(line)
                i += 1
        
        content = '\n'.join(fixed_lines)
        
        # Pattern 3: Fix cases where pass is completely unindented after a function
        content = re.sub(
            r'(\s*def\s+[^:]+:\s*\n)pass\n',
            lambda m: m.group(1) + ' ' * (len(m.group(1).split('\n')[-2]) - len(m.group(1).split('\n')[-2].lstrip()) + 4) + 'pass\n',
            content
        )
        
        # Pattern 4: Remove duplicate pass statements
        content = re.sub(r'(\s+pass\s*\n)\s+pass\s*\n', r'\1', content)
        
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
                print(f"❌ Still has errors: {filepath} - {e}")
                # Try a more aggressive fix
                return fix_file_aggressive(filepath, original_content)
        else:
            print(f"ℹ️  No changes needed: {filepath}")
            return True
            
    except Exception as e:
        print(f"❌ Error processing {filepath}: {e}")
        return False

def fix_file_aggressive(filepath: str, original_content: str) -> bool:
    """More aggressive fix for stubborn files."""
    try:
        lines = original_content.split('\n')
        fixed_lines = []
        
        for i, line in enumerate(lines):
            # Skip lines that are just 'pass' at the start of the line (unindented)
            if line.strip() == 'pass' and not line.startswith(' '):
                # Look at previous line to determine if this should be indented
                if i > 0:
                    prev_line = lines[i-1].strip()
                    if prev_line.endswith(':'):
                        # This pass should be indented
                        prev_indent = len(lines[i-1]) - len(lines[i-1].lstrip())
                        fixed_lines.append(' ' * (prev_indent + 4) + 'pass')
                        continue
                # Otherwise skip this pass
                continue
            
            fixed_lines.append(line)
        
        content = '\n'.join(fixed_lines)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        try:
            ast.parse(content)
            print(f"✅ Aggressively fixed: {filepath}")
            return True
        except (SyntaxError, IndentationError) as e:
            print(f"❌ Still broken after aggressive fix: {filepath} - {e}")
            # Restore original
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(original_content)
            return False
            
    except Exception as e:
        print(f"❌ Error in aggressive fix for {filepath}: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Fixing remaining complex indentation errors...")
    fix_complex_indentation_errors()
    print("✅ Done!")