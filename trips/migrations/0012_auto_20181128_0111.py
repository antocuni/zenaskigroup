# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trips', '0011_auto_20181128_0108'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paypaltransaction',
            name='ipn',
            field=models.ForeignKey(to='ipn.PayPalIPN', null=True),
        ),
    ]
