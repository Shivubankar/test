# Generated manually for RequestDocument structure update

from django.db import migrations, models
import django.db.models.deletion


def backfill_document_fields(apps, schema_editor):
    """Backfill engagement and standard fields from linked_control or request"""
    RequestDocument = apps.get_model('audit', 'RequestDocument')
    
    for doc in RequestDocument.objects.all():
        # Backfill engagement
        if not doc.engagement:
            if doc.linked_control:
                doc.engagement = doc.linked_control.engagement
            elif doc.request and doc.request.linked_control:
                doc.engagement = doc.request.linked_control.engagement
        
        # Backfill standard
        if not doc.standard:
            if doc.linked_control and doc.linked_control.standard_control:
                doc.standard = doc.linked_control.standard_control.standard
            elif doc.request and doc.request.linked_control and doc.request.linked_control.standard_control:
                doc.standard = doc.request.linked_control.standard_control.standard
        
        # Only save if we updated something
        if doc.engagement or doc.standard:
            doc.save(update_fields=['engagement', 'standard'])


def reverse_backfill(apps, schema_editor):
    """Reverse migration - no action needed"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('audit', '0022_add_signoff_boolean_fields'),
    ]

    operations = [
        # Add standard field (nullable first)
        migrations.AddField(
            model_name='requestdocument',
            name='standard',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='documents',
                to='audit.standard'
            ),
        ),
        # Backfill engagement and standard
        migrations.RunPython(backfill_document_fields, reverse_backfill),
        # Make engagement non-nullable
        migrations.AlterField(
            model_name='requestdocument',
            name='engagement',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='documents',
                to='audit.engagement'
            ),
        ),
        # Update doc_type choices (simplify to evidence/workpaper only)
        migrations.AlterField(
            model_name='requestdocument',
            name='doc_type',
            field=models.CharField(
                choices=[('evidence', 'Evidence'), ('workpaper', 'Workpaper')],
                default='workpaper',
                max_length=20
            ),
        ),
    ]
