
set -e

rm -r build dist;
python3 -m build --wheel;

scp dist/*.whl bgtl-ec-tower-server:$DIR

