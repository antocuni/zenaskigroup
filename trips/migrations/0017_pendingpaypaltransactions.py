# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trips', '0016_auto_20181128_1136'),
    ]

    operations = [
        migrations.CreateModel(
            name='PendingPayPalTransactions',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ppt', models.ForeignKey(related_name='+', to='trips.PayPalTransaction')),
            ],
        ),
    ]
