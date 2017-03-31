# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-17 18:28
from __future__ import unicode_literals

from django.db import migrations, models
import library_sys.models


class Migration(migrations.Migration):

    dependencies = [
        ('library_sys', '0003_auto_20170317_1518'),
    ]

    operations = [
        migrations.AddField(
            model_name='book',
            name='cover_height',
            field=models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='altura da capa'),
        ),
        migrations.AddField(
            model_name='book',
            name='cover_width',
            field=models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='largura da capa'),
        ),
        migrations.AlterField(
            model_name='book',
            name='cover',
            field=models.ImageField(blank=True, height_field=models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='altura da capa'), null=True, upload_to=library_sys.models.Book.get_upload_to_image, verbose_name='capa', width_field=models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='largura da capa')),
        ),
    ]
