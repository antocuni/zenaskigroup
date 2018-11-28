# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trips', '0015_auto_20181128_1125'),
    ]

    operations = [
        migrations.AlterField(
            model_name='participant',
            name='trip',
            field=models.ForeignKey(to='trips.Trip', null=True),
        ),
        migrations.AlterField(
            model_name='paypaltransaction',
            name='trip',
            field=models.ForeignKey(default=None, to='trips.Trip'),
            preserve_default=False,
        ),
    ]
