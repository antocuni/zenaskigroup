# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.conf import settings
import annoying.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Member',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('balance', models.DecimalField(default=0, verbose_name=b'Credito', max_digits=5, decimal_places=2)),
                ('card_no', models.CharField(max_length=5, verbose_name=b'Numero tessera', blank=True)),
                ('user', annoying.fields.AutoOneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MoneyTransfer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField(default=datetime.date.today, verbose_name=b'Data')),
                ('value', models.DecimalField(verbose_name=b'Valore', max_digits=5, decimal_places=2)),
                ('description', models.CharField(default=b'Ricarica', max_length=200, verbose_name=b'Causale')),
                ('executed_by', models.ForeignKey(verbose_name=b'Eseguito da', to=settings.AUTH_USER_MODEL)),
                ('member', models.ForeignKey(verbose_name=b'Socio', to='trips.Member')),
            ],
            options={
                'verbose_name': 'Pagamento/ricarica',
                'verbose_name_plural': 'Pagamenti/ricariche',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Participant',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200, verbose_name=b'Nome')),
                ('deposit', models.DecimalField(verbose_name=b'Caparra', max_digits=5, decimal_places=2)),
                ('is_member', models.BooleanField(default=True, verbose_name=b'Socio?')),
                ('registered_by', models.ForeignKey(verbose_name=b'Iscritto da', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Partecipante',
                'verbose_name_plural': 'Partecipanti',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Trip',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField(verbose_name=b'Data')),
                ('destination', models.CharField(max_length=200, verbose_name=b'Destinazione')),
                ('seats', models.PositiveIntegerField(verbose_name=b'Numero di posti')),
                ('deposit', models.DecimalField(default=20, verbose_name=b'Caparra', max_digits=5, decimal_places=2)),
                ('poster', models.ImageField(upload_to=b'', verbose_name=b'Locandina')),
            ],
            options={
                'get_latest_by': 'date',
                'verbose_name': 'Gita',
                'verbose_name_plural': 'Gite',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='participant',
            name='trip',
            field=models.ForeignKey(to='trips.Trip'),
            preserve_default=True,
        ),
    ]
