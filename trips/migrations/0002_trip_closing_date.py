# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('trips', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='trip',
            name='closing_date',
            field=models.DateTimeField(default=datetime.datetime(2014, 11, 21, 18, 0), verbose_name=b'Chiusura iscrizioni'),
            preserve_default=False,
        ),
    ]
