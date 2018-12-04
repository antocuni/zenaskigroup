# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('ipn', '0007_auto_20160219_1135'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('trips', '0010_participant_paypal_deadline'),
    ]

    operations = [
        migrations.CreateModel(
            name='PayPalTransaction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('amount', models.DecimalField(max_digits=10, decimal_places=2)),
                ('quantity', models.IntegerField()),
                ('deadline', models.DateTimeField()),
                ('is_paid', models.BooleanField(default=False)),
                ('ipn', models.ForeignKey(to='ipn.PayPalIPN')),
                ('trip', models.ForeignKey(to='trips.Trip')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Transazione PayPal',
                'verbose_name_plural': 'Transazioni PayPal',
            },
        ),
        migrations.RemoveField(
            model_name='participant',
            name='paypal_deadline',
        ),
        migrations.AddField(
            model_name='participant',
            name='paypal_transaction',
            field=models.DateTimeField(null=True, verbose_name=b'PayPal', blank=True),
        ),
    ]
