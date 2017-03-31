# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-22 02:53
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library_sys', '0014_bookitem_available'),
    ]

    operations = [
        migrations.AlterField(
            model_name='book',
            name='activated',
            field=models.BooleanField(default=True, help_text='Caso desmarque esta opção\n                                        o registro não aparecerá no site.', verbose_name='ativo'),
        ),
        migrations.AlterField(
            model_name='book',
            name='available',
            field=models.BooleanField(default=True, help_text="Caso desmarque esta opção\n                                        o registro aparecerá no site, porém,\n                                        como 'indisponível'.", verbose_name='disponível'),
        ),
    ]