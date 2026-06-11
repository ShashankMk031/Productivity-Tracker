import os

dirs = [
    'backend/database',
    'backend/services',
    'backend/routes',
    'backend/utils',
    'backend/schemas'
]

for d in dirs:
    os.makedirs(d, exist_ok=True)
    open(f'{d}/__init__.py', 'w').close()
