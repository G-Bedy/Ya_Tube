# Generated by Django 2.2.16 on 2022-11-05 19:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0002_auto_20221004_1834'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='post',
            options={'ordering': ('-pub_date', 'author'), 'verbose_name': 'Пост', 'verbose_name_plural': 'Посты'},
        ),
    ]
