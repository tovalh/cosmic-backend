#!/usr/bin/env python3
"""
Fix imports in cosmic simulation files to use relative imports
"""

import os
import re

def fix_imports_in_file(filepath):
    """Fix imports in a single file"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        # List of modules to make relative
        modules = [
            'brain', 'cells', 'world', 'objects', 'properties', 
            'interactions', 'discovery_system', 'evolution', 'cosmic_world'
        ]
        
        # Fix imports
        for module in modules:
            # Fix "from module import ..." to "from .module import ..."
            pattern = f'from {module} import'
            replacement = f'from .{module} import'
            content = re.sub(pattern, replacement, content)
            
            # Fix "import module" to "from . import module" (less common but possible)
            pattern = f'^import {module}$'
            replacement = f'from . import {module}'
            content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        
        # Write back
        with open(filepath, 'w') as f:
            f.write(content)
        
        print(f"Fixed imports in {filepath}")
        return True
        
    except Exception as e:
        print(f"Error fixing {filepath}: {e}")
        return False

def main():
    cosmic_dir = "/Users/cvalladares/PycharmProjects/CelulAI/cosmic-genesis-web/backend/cosmic"
    
    python_files = [
        'brain.py', 'cells.py', 'world.py', 'objects.py', 
        'properties.py', 'interactions.py', 'discovery_system.py', 
        'evolution.py'  # Don't fix cosmic_world.py as it's already fixed
    ]
    
    for filename in python_files:
        filepath = os.path.join(cosmic_dir, filename)
        if os.path.exists(filepath):
            fix_imports_in_file(filepath)
        else:
            print(f"File not found: {filepath}")

if __name__ == "__main__":
    main()