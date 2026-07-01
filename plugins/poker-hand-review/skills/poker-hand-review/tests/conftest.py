import os
import sys

HERE = os.path.dirname(__file__)
SCRIPTS = os.path.abspath(os.path.join(HERE, "..", "scripts"))
FIXTURE_DIR = os.path.join(HERE, "fixtures")

# make the skill's scripts importable as plain modules
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)
