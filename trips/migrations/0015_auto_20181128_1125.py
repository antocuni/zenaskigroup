# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trips', '0014_paypaltransaction_is_pending'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='paypaltransaction',
            name='is_paid',
        ),
        migrations.RemoveField(
            model_name='paypaltransaction',
            name='is_pending',
        ),
        migrations.AddField(
            model_name='paypaltransaction',
            name='status',
            field=models.IntegerField(default=0, choices=[(0, 'pending'), (1, 'canceled'), (2, 'waiting_ipn'), (3, 'paid'), (4, 'failed')]),
        ),
        migrations.AlterField(
            model_name='paypaltransaction',
            name='trip',
            field=models.ForeignKey(to='trips.Trip', null=True),
        ),
    ]


