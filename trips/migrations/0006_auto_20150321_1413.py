# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('trips', '0005_auto_20150315_0911'),
    ]

    operations = [
        migrations.AlterField(
            model_name='participant',
            name='registered_by',
            field=models.ForeignKey(verbose_name=b'Iscritto da', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]
