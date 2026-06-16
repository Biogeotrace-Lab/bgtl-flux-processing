set -e

echo Building docs.

cd docs;
make html;
cd ..

rsync -avz --delete ./docs/build/html/ bgtl-ec-tower-server:/data/docs/fluxy/
