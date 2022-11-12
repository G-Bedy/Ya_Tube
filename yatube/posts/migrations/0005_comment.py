# Generated by Django 2.2.16 on 2022-11-07 19:05

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0004_post_image'),
    ]

    operations = [
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField(help_text='Введите текст комментария', verbose_name='Текст комментария')),
                ('pub_date', models.DateTimeField(auto_now_add=True, verbose_name='Дата публикации')),
                ('author', models.ForeignKey(blank=True, help_text='Текст поста', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='posts.Group', verbose_name='текст поста')),
                ('post', models.ForeignKey(help_text='Текст поста', on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='posts.Post', verbose_name='текст поста')),
            ],
        ),
    ]