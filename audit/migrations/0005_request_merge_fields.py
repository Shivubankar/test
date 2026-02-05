from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("audit", "0004_standardcontrol_control_objective"),
    ]

    operations = [
        migrations.AddField(
            model_name="request",
            name="merged_into",
            field=models.ForeignKey(
                blank=True,
                help_text="Parent request this request was merged into.",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="merged_children",
                to="audit.request",
            ),
        ),
        migrations.AlterField(
            model_name="request",
            name="status",
            field=models.CharField(
                choices=[
                    ("OPEN", "Open"),
                    ("READY_FOR_REVIEW", "Ready for Review"),
                    ("COMPLETED", "Completed"),
                    ("MERGED", "Closed \u2013 Merged"),
                ],
                default="OPEN",
                max_length=20,
            ),
        ),
    ]
