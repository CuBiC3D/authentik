# Generated by Django 3.1.4 on 2020-12-27 12:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentik_events", "0008_auto_20201220_1651"),
    ]

    operations = [
        migrations.AlterField(
            model_name="event",
            name="action",
            field=models.TextField(
                choices=[
                    ("login", "Login"),
                    ("login_failed", "Login Failed"),
                    ("logout", "Logout"),
                    ("user_write", "User Write"),
                    ("suspicious_request", "Suspicious Request"),
                    ("password_set", "Password Set"),
                    ("token_view", "Token View"),
                    ("invitation_used", "Invite Used"),
                    ("authorize_application", "Authorize Application"),
                    ("source_linked", "Source Linked"),
                    ("impersonation_started", "Impersonation Started"),
                    ("impersonation_ended", "Impersonation Ended"),
                    ("policy_execution", "Policy Execution"),
                    ("policy_exception", "Policy Exception"),
                    ("property_mapping_exception", "Property Mapping Exception"),
                    ("configuration_error", "Configuration Error"),
                    ("model_created", "Model Created"),
                    ("model_updated", "Model Updated"),
                    ("model_deleted", "Model Deleted"),
                    ("update_available", "Update Available"),
                    ("custom_", "Custom Prefix"),
                ]
            ),
        ),
    ]