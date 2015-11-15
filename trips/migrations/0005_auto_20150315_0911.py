# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trips', '0004_participant_sublist'),
    ]

    operations = [
        migrations.AddField(
            model_name='participant',
            name='with_reservation',
            field=models.BooleanField(default=False, verbose_name=b'Con riserva?'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='trip',
            name='allow_extra_seats',
            field=models.BooleanField(default=False, verbose_name=b'Consenti iscrizioni con riserva?'),
            preserve_default=True,
        ),
    ]
