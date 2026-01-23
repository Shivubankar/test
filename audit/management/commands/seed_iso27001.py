from django.core.management.base import BaseCommand

from audit.models import Standard, StandardControl


class Command(BaseCommand):
    help = "Seed ISO 27001:2022 standard and controls (idempotent)."

    def handle(self, *args, **options):
        standard, standard_created = Standard.objects.get_or_create(
            name="ISO 27001:2022",
            defaults={"description": "ISO/IEC 27001:2022 Information Security Management System"},
        )

        controls = [
            {
                "control_id": "A.5.1",
                "title": "Information security policies",
                "control_description": "Information security policy and supporting policies are defined, approved, published, and communicated.",
                "domain": "Organizational controls",
                "default_testing_type": "Inquiry/Inspection",
            },
            {
                "control_id": "A.5.2",
                "title": "Information security roles and responsibilities",
                "control_description": "Information security roles and responsibilities are defined and allocated.",
                "domain": "Organizational controls",
                "default_testing_type": "Inquiry/Inspection",
            },
            {
                "control_id": "A.6.1",
                "title": "Screening",
                "control_description": "Background verification checks are carried out in accordance with laws and regulations prior to employment.",
                "domain": "People controls",
                "default_testing_type": "Inquiry/Inspection",
            },
            {
                "control_id": "A.6.2",
                "title": "Terms and conditions of employment",
                "control_description": "Employment terms and conditions define information security responsibilities.",
                "domain": "People controls",
                "default_testing_type": "Inquiry/Inspection",
            },
            {
                "control_id": "A.7.1",
                "title": "Physical security perimeters",
                "control_description": "Security perimeters are defined and used to protect areas containing information and information processing facilities.",
                "domain": "Physical controls",
                "default_testing_type": "Observation/Inspection",
            },
            {
                "control_id": "A.8.1",
                "title": "User access management",
                "control_description": "A formal user access management process is implemented to assign, modify, and revoke access rights.",
                "domain": "Technological controls",
                "default_testing_type": "Inquiry/Inspection",
            },
            {
                "control_id": "A.8.2",
                "title": "Privileged access rights",
                "control_description": "Allocation and use of privileged access rights are restricted and controlled.",
                "domain": "Technological controls",
                "default_testing_type": "Inquiry/Inspection",
            },
            {
                "control_id": "A.8.3",
                "title": "Information access restriction",
                "control_description": "Access to information and other associated assets is restricted in accordance with applicable access control policy.",
                "domain": "Technological controls",
                "default_testing_type": "Inquiry/Inspection",
            },
            {
                "control_id": "A.12.1",
                "title": "Operational procedures and responsibilities",
                "control_description": "Operating procedures are documented, maintained, and made available to all users who need them.",
                "domain": "Technological controls",
                "default_testing_type": "Inquiry/Inspection",
            },
            {
                "control_id": "A.12.6",
                "title": "Technical vulnerability management",
                "control_description": "Information about technical vulnerabilities is obtained, assessed, and addressed in a timely manner.",
                "domain": "Technological controls",
                "default_testing_type": "Inquiry/Inspection",
            },
        ]

        created_controls = 0
        for control in controls:
            _, created = StandardControl.objects.get_or_create(
                standard=standard,
                control_id=control["control_id"],
                defaults={
                    "title": control["title"],
                    "control_description": control["control_description"],
                    "domain": control["domain"],
                    "default_testing_type": control["default_testing_type"],
                    "is_active": True,
                },
            )
            if created:
                created_controls += 1

        if standard_created:
            self.stdout.write(self.style.SUCCESS("Created Standard: ISO 27001:2022"))
        else:
            self.stdout.write(self.style.WARNING("Standard already exists: ISO 27001:2022"))

        self.stdout.write(
            self.style.SUCCESS(f"Seeded ISO 27001 controls. Created {created_controls} new controls.")
        )
