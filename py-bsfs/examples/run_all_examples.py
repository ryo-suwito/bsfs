#!/usr/bin/env python3
"""
Run all BSFS examples

This script runs all the example demonstrations:
1. JSON CRUD operations
2. File backup and restore
3. Performance testing
"""

import sys
import importlib.util
from pathlib import Path

def run_example(example_name: str, example_path: Path):
    """Run a specific example"""
    print(f"\n{'='*60}")
    print(f"Running {example_name}")
    print(f"{'='*60}")
    
    try:
        # Load and run the example module
        spec = importlib.util.spec_from_file_location(example_name, example_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Run the main demo function
        if hasattr(module, 'demo_json_crud'):
            module.demo_json_crud()
        elif hasattr(module, 'demo_file_backup'):
            module.demo_file_backup()
        elif hasattr(module, 'demo_performance_test'):
            module.demo_performance_test()
        else:
            print(f"No demo function found in {example_name}")
            
    except Exception as e:
        print(f"❌ Error running {example_name}: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Run all examples"""
    examples_dir = Path(__file__).parent
    
    examples = [
        ("JSON CRUD Demo", examples_dir / "json_crud_demo.py"),
        ("File Backup Demo", examples_dir / "file_backup_demo.py"),
        ("Performance Test", examples_dir / "performance_test.py"),
    ]
    
    print("🚀 BSFS Examples Suite")
    print("This will run all BSFS demonstration examples")
    print("Each example creates temporary files and cleans up after itself")
    
    for example_name, example_path in examples:
        if example_path.exists():
            run_example(example_name, example_path)
        else:
            print(f"❌ Example not found: {example_path}")
    
    print(f"\n{'='*60}")
    print("✅ All examples completed!")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()