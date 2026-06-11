import re

def refactor_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Find all top-level const DOM selectors
    dom_vars = []
    
    # We will replace 'const x = document.getElementById(...);'
    # with 'let x;'
    # and collect 'x = document.getElementById(...);' to put inside init
    
    def repl(m):
        var_name = m.group(1)
        dom_vars.append(m.group(0).replace("const ", ""))
        return f"let {var_name};"
        
    content = re.sub(r'^const (\w+)\s*=\s*document\.getElementById.*$', repl, content, flags=re.MULTILINE)
    
    # Find init function and insert assignments
    assignments = "\n  ".join(dom_vars)
    init_func_pattern = r'(export async function init[A-Za-z]+\(\) \{)'
    replacement = f"\\1\n  {assignments}"
    content = re.sub(init_func_pattern, replacement, content)
    
    # Replace Auto-init at bottom
    auto_init_pattern = r'// Auto-init.*$'
    new_auto_init = """// Auto-init
document.addEventListener('DOMContentLoaded', () => {
  init""" + ("Goals" if "goals.js" in filepath else "Projects") + """();
});"""
    content = re.sub(r'// Auto-init.*', new_auto_init, content, flags=re.DOTALL)
    
    with open(filepath, 'w') as f:
        f.write(content)

refactor_file('frontend/js/goals.js')
refactor_file('frontend/js/projects.js')
