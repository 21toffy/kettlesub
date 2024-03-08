set -o errexit

pip install -r requiremennts.txt

python manage.py collectstatic --no-input

celery -A chrome_extention worker --loglevel=info
