"""External SDK checker driver; the image retains only production code."""
from pathlib import Path
import importlib.util
spec=importlib.util.spec_from_file_location('external_bluff_check','/checks/check.py')
checker=importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)
checker.ROOT=Path('/app')
checker.check_agent()
