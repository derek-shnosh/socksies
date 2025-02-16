# pylint: disable=missing-module-docstring, wrong-import-position
# ruff: noqa: E402

import os
import sys
import importlib

# Ensure the project root is in sys.path.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import socksies

# Override the CONFIG_FILE via an environment variable.
sample_config_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "sample-config.yml")
)
os.environ["SOCKSIES_CONFIG"] = sample_config_path

# Reload socksies so that CONFIG_FILE is recalculated.
importlib.reload(socksies)
