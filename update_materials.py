"""Run the authorized local update stages in order."""
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parent
for script, arguments in [('ai_tag_materials.py', ['--check-config']), ('deduplicate_materials.py', ['--delete']), ('ai_tag_materials.py', []), ('export_materials.py', [])]:
    result = subprocess.run([sys.executable, '-X', 'utf8', str(root / script), *arguments], cwd=root)
    if result.returncode:
        sys.exit(result.returncode)
