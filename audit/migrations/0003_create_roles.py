from django.db import migrations


def create_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    roles = {
        'Admin': {
            'audit': {
                'engagement': ['add', 'change', 'delete', 'view'],
                'controlrequirement': ['add', 'change', 'delete', 'view'],
                'request': ['add', 'change', 'delete', 'view'],
            },
            'auth': {
                'user': ['add', 'change', 'delete', 'view'],
            }
        },
        'Control Assessor': {
            'audit': {
                'engagement': ['add', 'change', 'view'],
                'controlrequirement': ['add', 'change', 'view'],
                'request': ['add', 'change', 'view'],
            }
        },
        'Control Reviewer': {
            'audit': {
                'engagement': ['view'],
                'controlrequirement': ['view'],
                'request': ['change', 'view'],
            }
        },
        'Client': {
            'audit': {
                'engagement': ['view'],
                'controlrequirement': ['view'],
                'request': ['change', 'view'],  # needed for evidence upload
            }
        }
    }

    for role_name, app_perms in roles.items():
        group, _ = Group.objects.get_or_create(name=role_name)
        perms_to_add = []
        for app_label, models_perms in app_perms.items():
            for model_name, actions in models_perms.items():
                try:
                    ct = ContentType.objects.get(app_label=app_label, model=model_name)
                except ContentType.DoesNotExist:
                    continue
                for action in actions:
                    codename = f"{action}_{model_name}"
                    perm = Permission.objects.filter(codename=codename, content_type=ct).first()
                    if perm:
                        perms_to_add.append(perm)
        group.permissions.set(perms_to_add)
        group.save()


def remove_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    for name in ['Admin', 'Control Assessor', 'Control Reviewer', 'Client']:
        Group.objects.filter(name=name).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('audit', '0002_controlrequirement_year'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(create_groups, remove_groups),
    ]
