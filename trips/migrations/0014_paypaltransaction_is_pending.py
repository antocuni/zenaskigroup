# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trips', '0013_auto_20181128_0113'),
    ]

    operations = [
        migrations.AddField(
            model_name='paypaltransaction',
            name='is_pending',
            field=models.BooleanField(default=True),
        ),
    ]
