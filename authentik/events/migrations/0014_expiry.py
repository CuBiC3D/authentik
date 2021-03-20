# Generated by Django 3.1.7 on 2021-03-18 16:01

from datetime import timedelta

from django.apps.registry import Apps
from django.db import migrations, models
from django.db.backends.base.schema import BaseDatabaseSchemaEditor

import authentik.events.models


def update_expires(apps: Apps, schema_editor: BaseDatabaseSchemaEditor):
    db_alias = schema_editor.connection.alias

    Event = apps.get_model("authentik_events", "event")
    for event in Event.objects.using(db_alias).all():
        event.expires = event.created + timedelta(days=365)
        event.save()


class Migration(migrations.Migration):

    dependencies = [
        ("authentik_events", "0013_auto_20210209_1657"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="expires",
            field=models.DateTimeField(
                default=authentik.events.models.default_event_duration
            ),
        ),
        migrations.AddField(
            model_name="event",
            name="expiring",
            field=models.BooleanField(default=True),
        ),
        migrations.RunPython(update_expires),
    ]