# Generated by Django 4.1.5 on 2023-12-04 12:23

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("assetsData", "0004_profile_login_type"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="main_catagory",
            name="Consumable_type",
        ),
    ]
