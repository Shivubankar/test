from django.core.management.base import BaseCommand

from audit.models import Standard, StandardControl


class Command(BaseCommand):
    help = "Seed ISO/IEC 27001:2022 Annex A controls (idempotent)."

    def handle(self, *args, **options):
        standard, _ = Standard.objects.get_or_create(
            name="ISO/IEC 27001:2022",
            defaults={"description": "ISO/IEC 27001:2022 Information Security Management System"},
        )

        controls = [
            # Organizational (A.5.1 - A.5.37)
            {"control_id": "A.5.1", "title": "Policies for information security", "domain": "Organizational"},
            {"control_id": "A.5.2", "title": "Information security roles and responsibilities", "domain": "Organizational"},
            {"control_id": "A.5.3", "title": "Segregation of duties", "domain": "Organizational"},
            {"control_id": "A.5.4", "title": "Management responsibilities", "domain": "Organizational"},
            {"control_id": "A.5.5", "title": "Contact with authorities", "domain": "Organizational"},
            {"control_id": "A.5.6", "title": "Contact with special interest groups", "domain": "Organizational"},
            {"control_id": "A.5.7", "title": "Threat intelligence", "domain": "Organizational"},
            {"control_id": "A.5.8", "title": "Information security in project management", "domain": "Organizational"},
            {"control_id": "A.5.9", "title": "Inventory of information and other associated assets", "domain": "Organizational"},
            {"control_id": "A.5.10", "title": "Acceptable use of information and other associated assets", "domain": "Organizational"},
            {"control_id": "A.5.11", "title": "Return of assets", "domain": "Organizational"},
            {"control_id": "A.5.12", "title": "Classification of information", "domain": "Organizational"},
            {"control_id": "A.5.13", "title": "Labelling of information", "domain": "Organizational"},
            {"control_id": "A.5.14", "title": "Information transfer", "domain": "Organizational"},
            {"control_id": "A.5.15", "title": "Access control", "domain": "Organizational"},
            {"control_id": "A.5.16", "title": "Identity management", "domain": "Organizational"},
            {"control_id": "A.5.17", "title": "Authentication information", "domain": "Organizational"},
            {"control_id": "A.5.18", "title": "Access rights", "domain": "Organizational"},
            {"control_id": "A.5.19", "title": "Information security in supplier relationships", "domain": "Organizational"},
            {"control_id": "A.5.20", "title": "Addressing information security within supplier agreements", "domain": "Organizational"},
            {"control_id": "A.5.21", "title": "Managing information security in the ICT supply chain", "domain": "Organizational"},
            {"control_id": "A.5.22", "title": "Monitoring, review and change management of supplier services", "domain": "Organizational"},
            {"control_id": "A.5.23", "title": "Information security for use of cloud services", "domain": "Organizational"},
            {"control_id": "A.5.24", "title": "Information security incident management planning and preparation", "domain": "Organizational"},
            {"control_id": "A.5.25", "title": "Assessment and decision on information security events", "domain": "Organizational"},
            {"control_id": "A.5.26", "title": "Response to information security incidents", "domain": "Organizational"},
            {"control_id": "A.5.27", "title": "Learning from information security incidents", "domain": "Organizational"},
            {"control_id": "A.5.28", "title": "Collection of evidence", "domain": "Organizational"},
            {"control_id": "A.5.29", "title": "Information security during disruption", "domain": "Organizational"},
            {"control_id": "A.5.30", "title": "ICT readiness for business continuity", "domain": "Organizational"},
            {"control_id": "A.5.31", "title": "Legal, statutory, regulatory and contractual requirements", "domain": "Organizational"},
            {"control_id": "A.5.32", "title": "Intellectual property rights", "domain": "Organizational"},
            {"control_id": "A.5.33", "title": "Protection of records", "domain": "Organizational"},
            {"control_id": "A.5.34", "title": "Privacy and protection of PII", "domain": "Organizational"},
            {"control_id": "A.5.35", "title": "Independent review of information security", "domain": "Organizational"},
            {"control_id": "A.5.36", "title": "Compliance with policies, rules and standards for information security", "domain": "Organizational"},
            {"control_id": "A.5.37", "title": "Documented operating procedures", "domain": "Organizational"},
            # People (A.6.1 - A.6.8)
            {"control_id": "A.6.1", "title": "Screening", "domain": "People"},
            {"control_id": "A.6.2", "title": "Terms and conditions of employment", "domain": "People"},
            {"control_id": "A.6.3", "title": "Information security awareness, education and training", "domain": "People"},
            {"control_id": "A.6.4", "title": "Disciplinary process", "domain": "People"},
            {"control_id": "A.6.5", "title": "Responsibilities after termination or change of employment", "domain": "People"},
            {"control_id": "A.6.6", "title": "Confidentiality or non-disclosure agreements", "domain": "People"},
            {"control_id": "A.6.7", "title": "Remote working", "domain": "People"},
            {"control_id": "A.6.8", "title": "Information security event reporting", "domain": "People"},
            # Physical (A.7.1 - A.7.14)
            {"control_id": "A.7.1", "title": "Physical security perimeters", "domain": "Physical"},
            {"control_id": "A.7.2", "title": "Physical entry", "domain": "Physical"},
            {"control_id": "A.7.3", "title": "Securing offices, rooms and facilities", "domain": "Physical"},
            {"control_id": "A.7.4", "title": "Physical security monitoring", "domain": "Physical"},
            {"control_id": "A.7.5", "title": "Protecting against physical and environmental threats", "domain": "Physical"},
            {"control_id": "A.7.6", "title": "Working in secure areas", "domain": "Physical"},
            {"control_id": "A.7.7", "title": "Clear desk and clear screen", "domain": "Physical"},
            {"control_id": "A.7.8", "title": "Equipment siting and protection", "domain": "Physical"},
            {"control_id": "A.7.9", "title": "Security of assets off-premises", "domain": "Physical"},
            {"control_id": "A.7.10", "title": "Storage media", "domain": "Physical"},
            {"control_id": "A.7.11", "title": "Supporting utilities", "domain": "Physical"},
            {"control_id": "A.7.12", "title": "Cabling security", "domain": "Physical"},
            {"control_id": "A.7.13", "title": "Equipment maintenance", "domain": "Physical"},
            {"control_id": "A.7.14", "title": "Secure disposal or re-use of equipment", "domain": "Physical"},
            # Technological (A.8.1 - A.8.34)
            {"control_id": "A.8.1", "title": "User endpoint devices", "domain": "Technological"},
            {"control_id": "A.8.2", "title": "Privileged access rights", "domain": "Technological"},
            {"control_id": "A.8.3", "title": "Information access restriction", "domain": "Technological"},
            {"control_id": "A.8.4", "title": "Access to source code", "domain": "Technological"},
            {"control_id": "A.8.5", "title": "Secure authentication", "domain": "Technological"},
            {"control_id": "A.8.6", "title": "Capacity management", "domain": "Technological"},
            {"control_id": "A.8.7", "title": "Protection against malware", "domain": "Technological"},
            {"control_id": "A.8.8", "title": "Management of technical vulnerabilities", "domain": "Technological"},
            {"control_id": "A.8.9", "title": "Configuration management", "domain": "Technological"},
            {"control_id": "A.8.10", "title": "Information deletion", "domain": "Technological"},
            {"control_id": "A.8.11", "title": "Data masking", "domain": "Technological"},
            {"control_id": "A.8.12", "title": "Data leakage prevention", "domain": "Technological"},
            {"control_id": "A.8.13", "title": "Information backup", "domain": "Technological"},
            {"control_id": "A.8.14", "title": "Redundancy of information processing facilities", "domain": "Technological"},
            {"control_id": "A.8.15", "title": "Logging", "domain": "Technological"},
            {"control_id": "A.8.16", "title": "Monitoring activities", "domain": "Technological"},
            {"control_id": "A.8.17", "title": "Clock synchronization", "domain": "Technological"},
            {"control_id": "A.8.18", "title": "Use of privileged utility programs", "domain": "Technological"},
            {"control_id": "A.8.19", "title": "Installation of software on operational systems", "domain": "Technological"},
            {"control_id": "A.8.20", "title": "Network security", "domain": "Technological"},
            {"control_id": "A.8.21", "title": "Security of network services", "domain": "Technological"},
            {"control_id": "A.8.22", "title": "Segregation of networks", "domain": "Technological"},
            {"control_id": "A.8.23", "title": "Web filtering", "domain": "Technological"},
            {"control_id": "A.8.24", "title": "Use of cryptography", "domain": "Technological"},
            {"control_id": "A.8.25", "title": "Secure development life cycle", "domain": "Technological"},
            {"control_id": "A.8.26", "title": "Application security requirements", "domain": "Technological"},
            {"control_id": "A.8.27", "title": "Secure system architecture and engineering principles", "domain": "Technological"},
            {"control_id": "A.8.28", "title": "Secure coding", "domain": "Technological"},
            {"control_id": "A.8.29", "title": "Security testing in development and acceptance", "domain": "Technological"},
            {"control_id": "A.8.30", "title": "Outsourced development", "domain": "Technological"},
            {"control_id": "A.8.31", "title": "Separation of development, test and production environments", "domain": "Technological"},
            {"control_id": "A.8.32", "title": "Change management", "domain": "Technological"},
            {"control_id": "A.8.33", "title": "Test information", "domain": "Technological"},
            {"control_id": "A.8.34", "title": "Protection of information systems during audit testing", "domain": "Technological"},
        ]

        created_count = 0
        skipped_count = 0
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
                created_count += 1
            else:
                skipped_count += 1

        self.stdout.write("ISO/IEC 27001:2022 seeding completed")
        self.stdout.write(f"Created: {created_count}")
        self.stdout.write(f"Skipped: {skipped_count}")
        self.stdout.write("Total controls: 93")
