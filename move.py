import os
import shutil

os.makedirs('backend/analytics', exist_ok=True)
open('backend/analytics/__init__.py', 'w').close()

for f in ['streaks.py', 'metrics.py', 'charts.py']:
    src = f'backend/{f}'
    dst = f'backend/analytics/{f}'
    if os.path.exists(src):
        shutil.move(src, dst)

if os.path.exists('backend/analytics.py'):
    shutil.move('backend/analytics.py', 'backend/reports.py')
