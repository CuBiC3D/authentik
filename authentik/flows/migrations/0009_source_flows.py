# Generated by Django 3.0.6 on 2020-05-23 15:47

from django.apps.registry import Apps
from django.db import migrations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor

from authentik.flows.models import FlowDesignation
from authentik.stages.prompt.models import FieldTypes

FLOW_POLICY_EXPRESSION = """# This policy ensures that this flow can only be used when the user
# is in a SSO Flow (meaning they come from an external IdP)
return ak_is_sso_flow"""
PROMPT_POLICY_EXPRESSION = """# Check if we've not been given a username by the external IdP
# and trigger the enrollment flow
return 'username' not in context.get('prompt_data', {})"""


def create_default_source_enrollment_flow(
    apps: Apps, schema_editor: BaseDatabaseSchemaEditor
):
    Flow = apps.get_model("authentik_flows", "Flow")
    FlowStageBinding = apps.get_model("authentik_flows", "FlowStageBinding")
    PolicyBinding = apps.get_model("authentik_policies", "PolicyBinding")

    ExpressionPolicy = apps.get_model(
        "authentik_policies_expression", "ExpressionPolicy"
    )

    PromptStage = apps.get_model("authentik_stages_prompt", "PromptStage")
    Prompt = apps.get_model("authentik_stages_prompt", "Prompt")
    UserWriteStage = apps.get_model("authentik_stages_user_write", "UserWriteStage")
    UserLoginStage = apps.get_model("authentik_stages_user_login", "UserLoginStage")

    db_alias = schema_editor.connection.alias

    # Create a policy that only allows this flow when doing an SSO Request
    flow_policy, _ = ExpressionPolicy.objects.using(db_alias).update_or_create(
        name="default-source-enrollment-if-sso",
        defaults={"expression": FLOW_POLICY_EXPRESSION},
    )

    # This creates a Flow used by sources to enroll users
    # It makes sure that a username is set, and if not, prompts the user for a Username
    flow, _ = Flow.objects.using(db_alias).update_or_create(
        slug="default-source-enrollment",
        designation=FlowDesignation.ENROLLMENT,
        defaults={
            "name": "Welcome to authentik!",
        },
    )
    PolicyBinding.objects.using(db_alias).update_or_create(
        policy=flow_policy, target=flow, defaults={"order": 0}
    )

    # PromptStage to ask user for their username
    prompt_stage, _ = PromptStage.objects.using(db_alias).update_or_create(
        name="Welcome to authentik! Please select a username.",
    )
    prompt, _ = Prompt.objects.using(db_alias).update_or_create(
        field_key="username",
        defaults={
            "label": "Username",
            "type": FieldTypes.TEXT,
            "required": True,
            "placeholder": "Username",
        },
    )
    prompt_stage.fields.add(prompt)

    # Policy to only trigger prompt when no username is given
    prompt_policy, _ = ExpressionPolicy.objects.using(db_alias).update_or_create(
        name="default-source-enrollment-if-username",
        defaults={"expression": PROMPT_POLICY_EXPRESSION},
    )

    # UserWrite stage to create the user, and login stage to log user in
    user_write, _ = UserWriteStage.objects.using(db_alias).update_or_create(
        name="default-source-enrollment-write"
    )
    user_login, _ = UserLoginStage.objects.using(db_alias).update_or_create(
        name="default-source-enrollment-login"
    )

    binding, _ = FlowStageBinding.objects.using(db_alias).update_or_create(
        target=flow,
        stage=prompt_stage,
        defaults={"order": 0, "re_evaluate_policies": True},
    )
    PolicyBinding.objects.using(db_alias).update_or_create(
        policy=prompt_policy, target=binding, defaults={"order": 0}
    )

    FlowStageBinding.objects.using(db_alias).update_or_create(
        target=flow, stage=user_write, defaults={"order": 1}
    )
    FlowStageBinding.objects.using(db_alias).update_or_create(
        target=flow, stage=user_login, defaults={"order": 2}
    )


def create_default_source_authentication_flow(
    apps: Apps, schema_editor: BaseDatabaseSchemaEditor
):
    Flow = apps.get_model("authentik_flows", "Flow")
    FlowStageBinding = apps.get_model("authentik_flows", "FlowStageBinding")
    PolicyBinding = apps.get_model("authentik_policies", "PolicyBinding")

    ExpressionPolicy = apps.get_model(
        "authentik_policies_expression", "ExpressionPolicy"
    )

    UserLoginStage = apps.get_model("authentik_stages_user_login", "UserLoginStage")

    db_alias = schema_editor.connection.alias

    # Create a policy that only allows this flow when doing an SSO Request
    flow_policy, _ = ExpressionPolicy.objects.using(db_alias).update_or_create(
        name="default-source-authentication-if-sso",
        defaults={
            "expression": FLOW_POLICY_EXPRESSION,
        },
    )

    # This creates a Flow used by sources to authenticate users
    flow, _ = Flow.objects.using(db_alias).update_or_create(
        slug="default-source-authentication",
        designation=FlowDesignation.AUTHENTICATION,
        defaults={
            "name": "Welcome to authentik!",
        },
    )
    PolicyBinding.objects.using(db_alias).update_or_create(
        policy=flow_policy, target=flow, defaults={"order": 0}
    )

    user_login, _ = UserLoginStage.objects.using(db_alias).update_or_create(
        name="default-source-authentication-login"
    )
    FlowStageBinding.objects.using(db_alias).update_or_create(
        target=flow, stage=user_login, defaults={"order": 0}
    )


class Migration(migrations.Migration):

    dependencies = [
        ("authentik_flows", "0008_default_flows"),
        ("authentik_policies", "0001_initial"),
        ("authentik_policies_expression", "0001_initial"),
        ("authentik_stages_prompt", "0001_initial"),
        ("authentik_stages_user_write", "0001_initial"),
        ("authentik_stages_user_login", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_default_source_enrollment_flow),
        migrations.RunPython(create_default_source_authentication_flow),
    ]