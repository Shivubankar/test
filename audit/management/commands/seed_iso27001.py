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
            {"control_id": "A.5.1", "title": "Policies for information security", "domain": "Organizational controls"},
            {"control_id": "A.5.2", "title": "Information security roles and responsibilities", "domain": "Organizational controls"},
            {"control_id": "A.5.3", "title": "Segregation of duties", "domain": "Organizational controls"},
            {"control_id": "A.5.4", "title": "Management responsibilities", "domain": "Organizational controls"},
            {"control_id": "A.5.5", "title": "Contact with authorities", "domain": "Organizational controls"},
            {"control_id": "A.5.6", "title": "Contact with special interest groups", "domain": "Organizational controls"},
            {"control_id": "A.5.7", "title": "Threat intelligence", "domain": "Organizational controls"},
            {"control_id": "A.5.8", "title": "Information security in project management", "domain": "Organizational controls"},
            {"control_id": "A.5.9", "title": "Inventory of information and other associated assets", "domain": "Organizational controls"},
            {"control_id": "A.5.10", "title": "Acceptable use of information and other associated assets", "domain": "Organizational controls"},
            {"control_id": "A.5.11", "title": "Return of assets", "domain": "Organizational controls"},
            {"control_id": "A.5.12", "title": "Classification of information", "domain": "Organizational controls"},
            {"control_id": "A.5.13", "title": "Labelling of information", "domain": "Organizational controls"},
            {"control_id": "A.5.14", "title": "Information transfer", "domain": "Organizational controls"},
            {"control_id": "A.5.15", "title": "Access control", "domain": "Organizational controls"},
            {"control_id": "A.5.16", "title": "Identity management", "domain": "Organizational controls"},
            {"control_id": "A.5.17", "title": "Authentication information", "domain": "Organizational controls"},
            {"control_id": "A.5.18", "title": "Access rights", "domain": "Organizational controls"},
            {"control_id": "A.5.19", "title": "Information security in supplier relationships", "domain": "Organizational controls"},
            {"control_id": "A.5.20", "title": "Addressing information security within supplier agreements", "domain": "Organizational controls"},
            {"control_id": "A.5.21", "title": "Managing information security in the ICT supply chain", "domain": "Organizational controls"},
            {"control_id": "A.5.22", "title": "Monitoring, review and change management of supplier services", "domain": "Organizational controls"},
            {"control_id": "A.5.23", "title": "Information security for use of cloud services", "domain": "Organizational controls"},
            {"control_id": "A.5.24", "title": "Information security incident management planning and preparation", "domain": "Organizational controls"},
            {"control_id": "A.5.25", "title": "Assessment and decision on information security events", "domain": "Organizational controls"},
            {"control_id": "A.5.26", "title": "Response to information security incidents", "domain": "Organizational controls"},
            {"control_id": "A.5.27", "title": "Learning from information security incidents", "domain": "Organizational controls"},
            {"control_id": "A.5.28", "title": "Collection of evidence", "domain": "Organizational controls"},
            {"control_id": "A.5.29", "title": "Information security during disruption", "domain": "Organizational controls"},
            {"control_id": "A.5.30", "title": "ICT readiness for business continuity", "domain": "Organizational controls"},
            {"control_id": "A.5.31", "title": "Legal, statutory, regulatory and contractual requirements", "domain": "Organizational controls"},
            {"control_id": "A.5.32", "title": "Intellectual property rights", "domain": "Organizational controls"},
            {"control_id": "A.5.33", "title": "Protection of records", "domain": "Organizational controls"},
            {"control_id": "A.5.34", "title": "Privacy and protection of PII", "domain": "Organizational controls"},
            {"control_id": "A.5.35", "title": "Independent review of information security", "domain": "Organizational controls"},
            {"control_id": "A.5.36", "title": "Compliance with policies, rules and standards for information security", "domain": "Organizational controls"},
            {"control_id": "A.5.37", "title": "Documented operating procedures", "domain": "Organizational controls"},
        ]

        created_controls = 0
        for control in controls:
            _, created = StandardControl.objects.get_or_create(
                standard=standard,
                control_id=control["control_id"],
                defaults={
                    "title": control["title"],
                    "control_description": control["title"],
                    "domain": control["domain"],
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
