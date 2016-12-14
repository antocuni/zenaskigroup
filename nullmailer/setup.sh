# https://github.com/unbit/uwsgi.it/blob/master/snippets/nullmailer.md

ROOT=${1:-/var/spool}
mkdir $ROOT/nullmailer
mkdir $ROOT/nullmailer/queue
mkdir $ROOT/nullmailer/tmp
mkfifo $ROOT/nullmailer/trigger

echo make sure to make the appropriate symlinks:
echo   - /etc/nullmailer/remotes
echo   - /etc/nullmailer/defaulthost
echo   - ~/vassals/nullmailer.ini --> uwsgi.ini
