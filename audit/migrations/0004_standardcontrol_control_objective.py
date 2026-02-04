from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("audit", "0003_engagementcontrol_evidence_required_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="standardcontrol",
            name="control_objective",
            field=models.TextField(blank=True, help_text="Control objective"),
        ),
    ]
