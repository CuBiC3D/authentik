# Generated by Django 3.0.7 on 2020-06-24 19:57

import django.db.models.deletion
from django.db import migrations, models

import authentik.lib.utils.time


class Migration(migrations.Migration):

    dependencies = [
        ("authentik_crypto", "0002_create_self_signed_kp"),
        ("authentik_sources_saml", "0002_auto_20200523_2329"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="samlsource",
            name="auto_logout",
        ),
        migrations.RenameField(
            model_name="samlsource",
            old_name="idp_url",
            new_name="sso_url",
        ),
        migrations.RenameField(
            model_name="samlsource",
            old_name="idp_logout_url",
            new_name="slo_url",
        ),
        migrations.AddField(
            model_name="samlsource",
            name="temporary_user_delete_after",
            field=models.TextField(
                default="days=1",
                help_text="Time offset when temporary users should be deleted. This only applies if your IDP uses the NameID Format 'transient', and the user doesn't log out manually. (Format: hours=1;minutes=2;seconds=3).",
                validators=[authentik.lib.utils.time.timedelta_string_validator],
                verbose_name="Delete temporary users after",
            ),
        ),
        migrations.AlterField(
            model_name="samlsource",
            name="signing_kp",
            field=models.ForeignKey(
                help_text="Certificate Key Pair of the IdP which Assertion's Signature is validated against.",
                on_delete=django.db.models.deletion.PROTECT,
                to="authentik_crypto.CertificateKeyPair",
                verbose_name="Singing Keypair",
            ),
        ),
        migrations.AlterField(
            model_name="samlsource",
            name="slo_url",
            field=models.URLField(
                blank=True,
                default=None,
                help_text="Optional URL if your IDP supports Single-Logout.",
                null=True,
                verbose_name="SLO URL",
            ),
        ),
        migrations.AlterField(
            model_name="samlsource",
            name="sso_url",
            field=models.URLField(
                help_text="URL that the initial Login request is sent to.",
                verbose_name="SSO URL",
            ),
        ),
    ]