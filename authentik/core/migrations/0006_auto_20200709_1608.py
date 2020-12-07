# Generated by Django 3.0.8 on 2020-07-09 16:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentik_core", "0005_token_intent"),
    ]

    operations = [
        migrations.AlterField(
            model_name="source",
            name="slug",
            field=models.SlugField(
                help_text="Internal source name, used in URLs.", unique=True
            ),
        ),
    ]