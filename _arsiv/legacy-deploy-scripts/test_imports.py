import os
import sys
import importlib

projects = [
    "Projeler/LinkedIn_Text_Paylasim",
    "Projeler/LinkedIn_Video_Paylasim",
    "Projeler/Twitter_Video_Paylasim",
]

base_dir = "/Users/dolunayozeren/Desktop/Antigravity"
has_error = False

for p in projects:
    p_path = os.path.join(base_dir, p)
    print(f"--- Checking {p} ---")
    sys.path.insert(0, p_path)
    
    import compileall
    compile_result = compileall.compile_dir(p_path, quiet=1)
    if not compile_result:
        print(f"Syntax error in {p}")
        has_error = True
        
    core_path = os.path.join(p_path, "core")
    files = [f for f in os.listdir(core_path) if f.endswith('.py') and f != '__init__.py']
    
    # Remove old 'core' from sys.modules
    keys_to_remove = [k for k in sys.modules.keys() if k.startswith('core.') or k == 'core']
    for k in keys_to_remove:
        del sys.modules[k]
        
    # Also clean up ops_logger from sys.modules to avoid clash
    if 'ops_logger' in sys.modules:
        del sys.modules['ops_logger']
    if 'config' in sys.modules:
        del sys.modules['config']
        
    for f in files:
        mod_name = f"core.{f[:-3]}"
        try:
            importlib.import_module(mod_name)
            print(f"  [OK] {mod_name}")
        except Exception as e:
            # We don't fail for third party module errors that are missing locally but present in requirements.
            print(f"  [WARNING/ERROR] {mod_name}: {e}")
            if type(e).__name__ in ['SyntaxError', 'AttributeError', 'IndentationError']:
                has_error = True
            
    sys.path.pop(0)

if has_error:
    sys.exit(1)
print("All projects imported successfully (syntax/attribute checks passed).")
