echo "RUNNING isort"
isort $(dirname $0)
echo "RUNNING black"
black $(dirname $0) --line-length 120