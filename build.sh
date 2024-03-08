echo "  BUILD START"

python3 -m pip install --upgrade pip
python3 -m venv venv
source venv/bin/activate

pip install --disable-pip-version-check --upgrade -r requirements.txt --config-settings=build_ext --config-settings="-I/usr/include/mysql" --config-settings="-L/usr/lib/mysql" --config-settings="-lmysqlclient"

python manage.py collectstatic --noinput --clear
python manage.py migrate
deactivate

echo "  BUILD END"
