# Generated by Django 2.1.3 on 2019-04-06 13:52

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Zufang',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('zone', models.CharField(max_length=20)),
                ('housetype', models.CharField(max_length=20)),
                ('houseurl', models.CharField(max_length=1000)),
                ('imgurl', models.CharField(max_length=1000)),
                ('housenum', models.PositiveIntegerField()),
                ('price', models.PositiveSmallIntegerField()),
                ('housearea', models.PositiveSmallIntegerField()),
                ('per_price', models.PositiveIntegerField()),
            ],
            options={
                'db_table': 'zufang',
                'managed': True,
            },
        ),
    ]
