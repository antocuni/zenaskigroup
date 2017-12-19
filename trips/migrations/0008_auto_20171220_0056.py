# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trips', '0007_jacketsubscribe'),
    ]

    operations = [
        migrations.AlterField(
            model_name='member',
            name='balance',
            field=models.DecimalField(default=0, verbose_name=b'Credito', max_digits=10, decimal_places=2),
        ),
        migrations.AlterField(
            model_name='moneytransfer',
            name='value',
            field=models.DecimalField(verbose_name=b'Valore', max_digits=10, decimal_places=2),
        ),
        migrations.AlterField(
            model_name='participant',
            name='deposit',
            field=models.DecimalField(verbose_name=b'Caparra', max_digits=10, decimal_places=2),
        ),
        migrations.AlterField(
            model_name='trip',
            name='deposit',
            field=models.DecimalField(default=20, verbose_name=b'Caparra', max_digits=10, decimal_places=2),
        ),
    ]
