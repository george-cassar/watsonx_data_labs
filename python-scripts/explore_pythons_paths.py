"""
Python Environment Explorer
===========================
Explores Python paths and lists installed packages in each directory.

This script helps diagnose Python package installation issues by:
1. Showing all Python paths (sys.path)
2. Listing directories that exist
3. Showing installed packages in each directory
4. Identifying site-packages locations

Usage:
    python explore_pythons_paths.py
"""

import sys
import site
import os
from pathlib import Path

def list_packages_in_directory(directory):
    """
    List Python packages/modules in a directory.
    
    Args:
        directory: Path to directory to scan
        
    Returns:
        list: List of package names found
    """
    packages = []
    
    try:
        if not os.path.exists(directory):
            return ["[Directory does not exist]"]
        
        if not os.path.isdir(directory):
            return ["[Not a directory]"]
        
        # List all items in directory
        items = os.listdir(directory)
        
        # Filter for Python packages
        for item in sorted(items):
            item_path = os.path.join(directory, item)
            
            # Check if it's a package directory (has __init__.py)
            if os.path.isdir(item_path):
                init_file = os.path.join(item_path, "__init__.py")
                if os.path.exists(init_file):
                    packages.append(f"📦 {item}/")
            
            # Check if it's a .py file (module)
            elif item.endswith('.py') and not item.startswith('_'):
                packages.append(f"📄 {item}")
            
            # Check if it's a .so file (compiled extension)
            elif item.endswith('.so'):
                packages.append(f"⚙️  {item}")
            
            # Check for egg-info or dist-info (installed packages)
            elif item.endswith(('.egg-info', '.dist-info')):
                pkg_name = item.replace('.egg-info', '').replace('.dist-info', '')
                # Remove version numbers
                pkg_name = pkg_name.split('-')[0]
                packages.append(f"📋 {pkg_name}")
        
        # Remove duplicates (from egg-info and dist-info)
        seen = set()
        unique_packages = []
        for pkg in packages:
            if pkg.startswith('📋'):
                pkg_name = pkg.split()[1]
                if pkg_name not in seen:
                    seen.add(pkg_name)
                    unique_packages.append(pkg)
            else:
                unique_packages.append(pkg)
        
        return unique_packages if unique_packages else ["[Empty directory]"]
        
    except PermissionError:
        return ["[Permission denied]"]
    except Exception as e:
        return [f"[Error: {str(e)}]"]

def explore_python_paths():
    """
    Main function to explore Python environment.
    """
    print("=" * 80)
    print("PYTHON ENVIRONMENT EXPLORER")
    print("=" * 80)
    print(f"\nPython Interpreter: {sys.executable}")
    print(f"Python Version: {sys.version}")
    print(f"Current Working Directory: {os.getcwd()}")
    
    # 1. Show all sys.path entries
    print("\n" + "=" * 80)
    print("ALL PYTHON PATHS (sys.path)")
    print("=" * 80)
    
    for idx, path in enumerate(sys.path, 1):
        if path == "":
            print(f"\n{idx}. [Current Directory]")
            print(f"    Path: {os.getcwd()}")
        else:
            print(f"\n{idx}. {path}")
        
        # Check if path exists
        if path and os.path.exists(path):
            print(f"    Status: ✓ EXISTS")
            
            # Determine path type
            if "site-packages" in path:
                path_type = "SITE-PACKAGES (Third-party packages)"
            elif "dist-packages" in path:
                path_type = "DIST-PACKAGES (System packages)"
            elif path.endswith(('.zip', '.jar')):
                path_type = "ARCHIVE (Compressed library)"
            elif "python3" in path.lower() or "lib-dynload" in path:
                path_type = "STANDARD LIBRARY"
            else:
                path_type = "CUSTOM PATH"
            
            print(f"    Type: {path_type}")
            
            # List packages if it's a directory
            if os.path.isdir(path) and not path.endswith(('.zip', '.jar')):
                packages = list_packages_in_directory(path)
                
                if len(packages) <= 10:
                    print(f"    Packages ({len(packages)}):")
                    for pkg in packages:
                        print(f"      - {pkg}")
                else:
                    print(f"    Packages ({len(packages)}): [Showing first 10]")
                    for pkg in packages[:10]:
                        print(f"      - {pkg}")
                    print(f"      ... and {len(packages) - 10} more")
        else:
            print(f"    Status: ✗ DOES NOT EXIST")
    
    # 2. Show site-packages locations
    print("\n" + "=" * 80)
    print("SITE-PACKAGES LOCATIONS")
    print("=" * 80)
    
    # Global site packages
    print("\n1. Global Site Packages:")
    try:
        for sp in site.getsitepackages():
            exists = "✓" if os.path.exists(sp) else "✗"
            print(f"   {exists} {sp}")
            if os.path.exists(sp):
                packages = list_packages_in_directory(sp)
                print(f"      Total packages: {len(packages)}")
    except AttributeError:
        print("   [Not available in this environment]")
    
    # User site packages
    print("\n2. User Site Packages:")
    user_sp = site.getusersitepackages()
    exists = "✓" if os.path.exists(user_sp) else "✗"
    print(f"   {exists} {user_sp}")
    if os.path.exists(user_sp):
        packages = list_packages_in_directory(user_sp)
        print(f"      Total packages: {len(packages)}")
    
    # 3. Check for common package locations
    print("\n" + "=" * 80)
    print("CHECKING COMMON PACKAGE LOCATIONS")
    print("=" * 80)
    
    common_locations = [
        "/home/spark/shared/python/lib/python3.11/site-packages",
        "/usr/local/lib/python3.11/site-packages",
        "/usr/lib/python3.11/site-packages",
        "/opt/ibm/third-party/libs/python3",
        "/opt/ibm/image-libs/python3",
    ]
    
    for location in common_locations:
        exists = os.path.exists(location)
        status = "✓ EXISTS" if exists else "✗ NOT FOUND"
        print(f"\n{status}: {location}")
        
        if exists and os.path.isdir(location):
            packages = list_packages_in_directory(location)
            print(f"   Total items: {len(packages)}")
            
            # Show first few packages
            if packages and packages[0] != "[Empty directory]":
                print(f"   Sample packages:")
                for pkg in packages[:5]:
                    print(f"     - {pkg}")
                if len(packages) > 5:
                    print(f"     ... and {len(packages) - 5} more")
    
    # 4. Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    total_paths = len([p for p in sys.path if p])
    existing_paths = len([p for p in sys.path if p and os.path.exists(p)])
    
    print(f"Total paths in sys.path: {total_paths}")
    print(f"Existing paths: {existing_paths}")
    print(f"Missing paths: {total_paths - existing_paths}")
    
    # Check for specific packages
    print("\n" + "=" * 80)
    print("CHECKING FOR SPECIFIC PACKAGES")
    print("=" * 80)
    
    packages_to_check = ['pandas', 'numpy', 'lxml', 'pyspark', 'requests', 'bs4']
    
    for pkg_name in packages_to_check:
        try:
            if pkg_name == 'bs4':
                import bs4
                pkg = bs4
            else:
                pkg = __import__(pkg_name)
            
            location = getattr(pkg, '__file__', 'Built-in')
            version = getattr(pkg, '__version__', 'Unknown')
            print(f"\n✓ {pkg_name}")
            print(f"   Version: {version}")
            print(f"   Location: {location}")
        except ImportError:
            print(f"\n✗ {pkg_name}: NOT INSTALLED")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    explore_python_paths()
