# Generated by Django 5.2.1 on 2025-05-24 17:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uniescolar', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='aula',
            name='descricao',
            field=models.TextField(),
        ),
    ]
