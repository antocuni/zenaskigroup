# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trips', '0003_member_trusted'),
    ]

    operations = [
        migrations.AddField(
            model_name='participant',
            name='sublist',
            field=models.CharField(default='Online', max_length=20, verbose_name=b'Lista'),
            preserve_default=False,
        ),
    ]
