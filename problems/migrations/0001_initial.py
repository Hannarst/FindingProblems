# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-08-08 11:58
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Challenge',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datetime', models.DateTimeField()),
                ('name', models.TextField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Problem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.TextField(max_length=200)),
                ('content', models.TextField()),
                ('difficulty', models.IntegerField(choices=[(0, 'Very Easy'), (1, 'Easy'), (2, 'Average'), (3, 'Difficult'), (4, 'Very Difficult')])),
                ('execution_time_limit', models.FloatField()),
                ('solution', models.TextField()),
                ('private', models.BooleanField(default=True)),
            ],
        ),
        migrations.AddField(
            model_name='challenge',
            name='problems',
            field=models.ManyToManyField(to='problems.Problem'),
        ),
        migrations.AddField(
            model_name='category',
            name='problems',
            field=models.ManyToManyField(to='problems.Problem'),
        ),
    ]
