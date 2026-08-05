import sys
from pathlib import Path

# The repo root also has placeholder `engine/` and `config.py` modules
# (unused stubs). Put corsaapp first on sys.path so tests import the
# real implementation here, not the root-level stand-ins.
CORSAAPP_DIR = Path(__file__).resolve().parent
if str(CORSAAPP_DIR) not in sys.path:
    sys.path.insert(0, str(CORSAAPP_DIR))
