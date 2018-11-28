# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trips', '0012_auto_20181128_0111'),
    ]

    operations = [
        migrations.AlterField(
            model_name='participant',
            name='paypal_transaction',
            field=models.ForeignKey(to='trips.PayPalTransaction', null=True),
        ),
    ]
