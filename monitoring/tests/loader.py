"""Helper that loads a Lambda handler.py by path, because all three modules share the name handler."""

import importlib.util
import sys
import types
from pathlib import Path

LAMBDA_ROOT = Path(__file__).resolve().parent.parent / "lambda"


def load_handler(function_folder):
    """Import lambda/<function_folder>/handler.py as a uniquely named module.

    Args:
        function_folder: Folder name under monitoring/lambda, for example probe.

    Returns:
        The loaded module.
    """
    if "boto3" not in sys.modules and importlib.util.find_spec("boto3") is None:
        sys.modules["boto3"] = types.ModuleType("boto3")
        sys.modules["boto3"].client = None
    path = LAMBDA_ROOT / function_folder / "handler.py"
    spec = importlib.util.spec_from_file_location(f"{function_folder}_handler", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
