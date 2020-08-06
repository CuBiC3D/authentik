# Generated by Django 3.0.8 on 2020-08-01 17:52

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("passbook_providers_app_gw", "0002_auto_20200726_1745"),
    ]

    operations = [
        migrations.AlterField(
            model_name="applicationgatewayprovider",
            name="external_host",
            field=models.TextField(
                validators=[
                    django.core.validators.URLValidator(schemes=("http", "https"))
                ]
            ),
        ),
        migrations.AlterField(
            model_name="applicationgatewayprovider",
            name="internal_host",
            field=models.TextField(
                validators=[
                    django.core.validators.URLValidator(schemes=("http", "https"))
                ]
            ),
        ),
    ]