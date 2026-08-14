#!/usr/bin/env bash
# The one way to run this repo's test suite.
#
# The dependency set lives here rather than in each contributor's shell
# history: omitting --with matplotlib makes twelve value-added tests fail
# with a ModuleNotFoundError that reads like a real regression.
set -euo pipefail
cd "$(dirname "$0")/.."
exec uv run --no-project \
  --with pytest --with pandas --with numpy --with scipy \
  --with statsmodels --with patsy --with matplotlib \
  python -m pytest tests/ "$@"
