import re
import os

def patch_file(filepath, init_func_name):
    with open(filepath, 'r') as f:
        content = f.read()

    # Find where the auto-init section is at the bottom
    # It might look like:
    # // Auto-init
    # function initializeGoals() {
    #   if (document.readyState === 'loading') {
    #     document.addEventListener('DOMContentLoaded', initGoals);
    #   } else {
    #     initGoals();
    #   }
    # }
    # initializeGoals();

    new_auto_init = f"""// Auto-init
document.addEventListener("DOMContentLoaded", () => {{
  {init_func_name}();
}});
"""
    
    # We strip the old auto-init
    content = re.sub(r'// Auto-init\n.*', new_auto_init, content, flags=re.DOTALL)
    
    with open(filepath, 'w') as f:
        f.write(content)

patch_file('frontend/js/goals.js', 'initGoals')
patch_file('frontend/js/projects.js', 'initProjects')
patch_file('frontend/js/reports.js', 'initReports')
