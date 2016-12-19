#SRC=antocuni.eu:/accounts/antoniocuni/www/zenaskigroup.it/zenaskigroup/project.db
SRC=uwsgi.it:www/zenaskigroup/project.db
scp $SRC backup-`date -I`.db
