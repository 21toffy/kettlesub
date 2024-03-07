echo "  BUILD START"
python3.11 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

python3.11 manage.py collectstatic --noinput --clear

deactivate

echo "  BUILD END"
