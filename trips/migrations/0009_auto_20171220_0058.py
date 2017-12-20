# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trips', '0008_auto_20171220_0056'),
    ]

    operations = [
        migrations.AddField(
            model_name='trip',
            name='fb_album',
            field=models.URLField(verbose_name=b'Facebook album', blank=True),
        ),
        migrations.AddField(
            model_name='trip',
            name='fb_post',
            field=models.URLField(verbose_name=b'Facebook post', blank=True),
        ),
    ]
