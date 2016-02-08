# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trips', '0006_auto_20150321_1413'),
    ]

    operations = [
        migrations.CreateModel(
            name='JacketSubscribe',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200, verbose_name=b'Nome')),
                ('email', models.CharField(max_length=200, verbose_name=b'Email')),
            ],
            options={
                'verbose_name': 'Contatto',
                'verbose_name_plural': 'Mailing List Giacca',
            },
        ),
    ]
