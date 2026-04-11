import re
import os
import glob

def refactor_file(file_path, project_name):
    with open(file_path, 'r') as f:
        content = f.read()

    if "ops_logger" in content:
        # Already done or partially done
        # Let's clean it anyway
        pass

    module_name = os.path.basename(file_path).replace('.py', '').title().replace('_', '')
    
    # 1. Replace import logging with ops_logger import
    # Some files might not have import logging, but most do.
    if "import logging" in content:
        imports_replacement = f"""from ops_logger import get_ops_logger
ops = get_ops_logger("{project_name}", "{module_name}")"""
        content = re.sub(r'import logging\s*\n', imports_replacement + '\n', content)
    else:
        # Add to top of file after imports
        content = f"""from ops_logger import get_ops_logger
ops = get_ops_logger("{project_name}", "{module_name}")\n""" + content

    # 2. Replace logging.info(...) -> ops.info(...)
    content = re.sub(r'logging\.info\((.*?)\)', r'ops.info(\1)', content)
    
    # 3. Replace logging.warning(...) -> ops.warning(...)
    content = re.sub(r'logging\.warning\((.*?)\)', r'ops.warning(\1)', content)
    
    # 4. Replace logging.error(..., exc_info=True) -> ops.error(..., exception=e)
    # We will try to extract the exception variable if it's in the f-string e.g. {e}
    # For simplicity, we just pass the string as the title to ops.error
    
    def repl_error(match):
        args = match.group(1)
        # remove exc_info=True
        cleaned_args = re.sub(r',\s*exc_info=True', '', args)
        
        # If the string contains {e}, and exception is thrown as 'e', we can guess `exception=e`
        if '{e}' in cleaned_args or ' e}' in cleaned_args or ': {e}' in cleaned_args:
             return f'ops.error({cleaned_args}, exception=e)'
        return f'ops.error({cleaned_args})'

    content = re.sub(r'logging\.error\((.*?)\)', repl_error, content)
    
    with open(file_path, 'w') as f:
        f.write(content)
    print(f"Refactored {file_path}")

projects = [
    ("Projeler/LinkedIn_Text_Paylasim", "LinkedIn_Text_Paylasim"),
    ("Projeler/LinkedIn_Video_Paylasim", "LinkedIn_Video_Paylasim"),
    ("Projeler/Twitter_Video_Paylasim", "Twitter_Video_Paylasim"),
]

for p_dir, p_name in projects:
    core_dir = os.path.join("/Users/dolunayozeren/Desktop/Antigravity", p_dir, "core")
    for filepath in glob.glob(os.path.join(core_dir, "*.py")):
        # Skip __init__.py
        if os.path.basename(filepath) == "__init__.py":
            continue
        refactor_file(filepath, p_name)

