#!/usr/bin/env python3
"""
Fix import statements in duilio-code-studio
Replaces 'from src.' with proper relative imports or path adjustments
"""

import re
from pathlib import Path

def fix_imports_in_file(file_path: Path):
    """Fix imports in a single file."""
    try:
        content = file_path.read_text(encoding='utf-8')
        original = content
        
        # Skip if already has sys.path adjustment
        if 'sys.path.insert(0' in content or 'sys.path.insert(0' in content:
            # Check if it needs the import statement
            if 'import sys' not in content and 'from src.' in content:
                # Add sys import and path adjustment at the top after other imports
                lines = content.split('\n')
                import_idx = 0
                for i, line in enumerate(lines):
                    if line.strip().startswith('import ') or line.strip().startswith('from '):
                        import_idx = i
                    elif line.strip() and not line.strip().startswith('#') and import_idx > 0:
                        break
                
                # Insert sys.path adjustment after imports
                insert_idx = import_idx + 1
                if 'from pathlib import Path' not in content:
                    lines.insert(insert_idx, 'from pathlib import Path')
                    insert_idx += 1
                if 'import sys' not in content:
                    lines.insert(insert_idx, 'import sys')
                    insert_idx += 1
                
                lines.insert(insert_idx, '')
                lines.insert(insert_idx + 1, '# Add parent directory to path for imports')
                lines.insert(insert_idx + 2, 'sys.path.insert(0, str(Path(__file__).parent.parent))')
                lines.insert(insert_idx + 3, '')
                content = '\n'.join(lines)
        
        # Replace 'from src.' with 'from core.' or appropriate relative import
        # This is a simple replacement - more sophisticated logic could be added
        content = re.sub(r'from src\.core\.', 'from core.', content)
        content = re.sub(r'from src\.utils\.', 'from utils.', content)
        content = re.sub(r'from src\.services\.', 'from services.', content)
        content = re.sub(r'from src\.api\.', 'from api.', content)
        content = re.sub(r'from src\.chat\.', 'from chat.', content)
        content = re.sub(r'from src\.middleware\.', 'from middleware.', content)
        
        # But keep src.main and src.database if they exist (they might be in different locations)
        # Actually, let's be more careful - only replace if we added the path adjustment
        if content != original:
            # Add path adjustment if not present and has src imports
            if 'sys.path.insert(0' not in content and ('from core.' in content or 'from utils.' in content):
                lines = content.split('\n')
                # Find first non-comment, non-empty line after initial comments
                insert_idx = 0
                for i, line in enumerate(lines):
                    if line.strip() and not line.strip().startswith('#'):
                        if 'import' in line or 'from' in line:
                            insert_idx = i
                            break
                
                # Find end of imports
                for i in range(insert_idx, len(lines)):
                    if lines[i].strip() and not (lines[i].strip().startswith('import') or 
                                                  lines[i].strip().startswith('from') or
                                                  lines[i].strip().startswith('#')):
                        insert_idx = i
                        break
                
                # Add necessary imports and path adjustment
                if 'from pathlib import Path' not in content:
                    lines.insert(insert_idx, 'from pathlib import Path')
                    insert_idx += 1
                if 'import sys' not in content:
                    lines.insert(insert_idx, 'import sys')
                    insert_idx += 1
                
                lines.insert(insert_idx, '')
                lines.insert(insert_idx + 1, '# Add parent directory to path for imports')
                lines.insert(insert_idx + 2, 'sys.path.insert(0, str(Path(__file__).parent.parent))')
                content = '\n'.join(lines)
            
            file_path.write_text(content, encoding='utf-8')
            return True
        return False
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False

def main():
    """Fix all Python files in src directory."""
    src_dir = Path(__file__).parent / 'src'
    fixed_count = 0
    
    for py_file in src_dir.rglob('*.py'):
        if fix_imports_in_file(py_file):
            print(f"Fixed: {py_file.relative_to(src_dir.parent)}")
            fixed_count += 1
    
    print(f"\n✅ Fixed {fixed_count} files")

if __name__ == '__main__':
    main()
