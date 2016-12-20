#SRC=antocuni.eu:/accounts/antoniocuni/www/zenaskigroup.it/zenaskigroup/project.db
SRC=uwsgi.it:www/zenaskigroup/project.db
DST=backup/project-`date -Im`.db
scp $SRC $DST
mv project.db /tmp
cp $DST project.db
echo $DST copied to project.db
