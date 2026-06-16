
set -e

DIR="/data/pypackages/"

rm -r build dist || echo Directories do not exist;
PIP_TIMEOUT=2 PIP_RETRIES=1 python3 -m build --wheel;
scp dist/*.whl bgtl-ec-tower-server:$DIR

