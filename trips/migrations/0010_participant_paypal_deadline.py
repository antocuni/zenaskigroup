# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trips', '0009_auto_20171220_0058'),
    ]

    operations = [
        migrations.AddField(
            model_name='participant',
            name='paypal_deadline',
            field=models.DateTimeField(null=True, verbose_name=b'Scadenza Paypal', blank=True),
        ),
    ]
