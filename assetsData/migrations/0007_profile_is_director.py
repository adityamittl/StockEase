# Generated by Django 5.0.3 on 2024-03-22 13:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assetsData', '0006_alter_asset_type_final_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='is_director',
            field=models.BooleanField(default=False),
        ),
    ]
