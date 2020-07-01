# Generated by Django 3.0.7 on 2020-06-13 15:28

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("passbook_flows", "0005_provider_flows"),
    ]

    operations = [
        migrations.CreateModel(
            name="OTPTimeStage",
            fields=[
                (
                    "stage_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="passbook_flows.Stage",
                    ),
                ),
                ("digits", models.IntegerField(choices=[(6, "Six"), (8, "Eight")])),
            ],
            options={
                "verbose_name": "OTP Time (TOTP) Setup Stage",
                "verbose_name_plural": "OTP Time (TOTP) Setup Stages",
            },
            bases=("passbook_flows.stage",),
        ),
    ]