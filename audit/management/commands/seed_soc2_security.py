from django.core.management.base import BaseCommand

from audit.models import Standard, StandardControl


class Command(BaseCommand):
    help = "Seed SOC 2 Security (Trust Services Criteria) controls (idempotent)."

    def handle(self, *args, **options):
        standard, _ = Standard.objects.get_or_create(
            name="SOC 2",
            defaults={"description": "SOC 2 Trust Services Criteria - Security"},
        )

        controls = [
            # CC1 – Control Environment
            {
                "control_id": "CC1.1",
                "title": "Integrity and ethical values are defined and enforced",
                "control_description": "Integrity and ethical values are established, communicated, and enforced across the organization.",
                "domain": "CC1 – Control Environment",
            },
            {
                "control_id": "CC1.2",
                "title": "Board oversight of internal control",
                "control_description": "The board provides independent oversight of internal control and security governance.",
                "domain": "CC1 – Control Environment",
            },
            {
                "control_id": "CC1.3",
                "title": "Organizational structure and authority defined",
                "control_description": "Organizational structure, reporting lines, and authorities are defined to support security objectives.",
                "domain": "CC1 – Control Environment",
            },
            {
                "control_id": "CC1.4",
                "title": "Commitment to competence",
                "control_description": "The organization demonstrates a commitment to competence through hiring, training, and performance expectations.",
                "domain": "CC1 – Control Environment",
            },
            {
                "control_id": "CC1.5",
                "title": "Accountability for internal control",
                "control_description": "Individuals are held accountable for internal control responsibilities and security outcomes.",
                "domain": "CC1 – Control Environment",
            },
            # CC2 – Communication & Information
            {
                "control_id": "CC2.1",
                "title": "Internal communication of information security objectives",
                "control_description": "Information security objectives and responsibilities are communicated internally to relevant personnel.",
                "domain": "CC2 – Communication & Information",
            },
            {
                "control_id": "CC2.2",
                "title": "External communication with customers and regulators",
                "control_description": "External communications relevant to security are managed with customers, regulators, and other parties.",
                "domain": "CC2 – Communication & Information",
            },
            {
                "control_id": "CC2.3",
                "title": "Information quality and relevance ensured",
                "control_description": "Information used for security decisions is relevant, timely, accurate, and complete.",
                "domain": "CC2 – Communication & Information",
            },
            # CC3 – Risk Assessment
            {
                "control_id": "CC3.1",
                "title": "Risks to security objectives identified",
                "control_description": "Risks to achieving security objectives are identified and evaluated.",
                "domain": "CC3 – Risk Assessment",
            },
            {
                "control_id": "CC3.2",
                "title": "Fraud risk considered",
                "control_description": "Fraud risk and the potential impact on security objectives are considered in risk assessments.",
                "domain": "CC3 – Risk Assessment",
            },
            {
                "control_id": "CC3.3",
                "title": "Changes impacting internal control assessed",
                "control_description": "Changes in the business or environment are evaluated for their impact on internal control.",
                "domain": "CC3 – Risk Assessment",
            },
            # CC4 – Monitoring Activities
            {
                "control_id": "CC4.1",
                "title": "Ongoing evaluations of controls",
                "control_description": "Ongoing evaluations are performed to determine whether controls operate effectively.",
                "domain": "CC4 – Monitoring Activities",
            },
            {
                "control_id": "CC4.2",
                "title": "Independent evaluations performed",
                "control_description": "Independent evaluations of controls are conducted at appropriate intervals.",
                "domain": "CC4 – Monitoring Activities",
            },
            {
                "control_id": "CC4.3",
                "title": "Control deficiencies communicated and remediated",
                "control_description": "Control deficiencies are identified, communicated, and remediated in a timely manner.",
                "domain": "CC4 – Monitoring Activities",
            },
            # CC5 – Control Activities
            {
                "control_id": "CC5.1",
                "title": "Control activities designed to mitigate risks",
                "control_description": "Control activities are designed and implemented to mitigate identified risks.",
                "domain": "CC5 – Control Activities",
            },
            {
                "control_id": "CC5.2",
                "title": "Policies and procedures established",
                "control_description": "Policies and procedures are established and maintained to support control activities.",
                "domain": "CC5 – Control Activities",
            },
            {
                "control_id": "CC5.3",
                "title": "Segregation of duties enforced",
                "control_description": "Segregation of duties is enforced to reduce the risk of error or unauthorized actions.",
                "domain": "CC5 – Control Activities",
            },
            # CC6 – Logical & Physical Access
            {
                "control_id": "CC6.1",
                "title": "Logical access restricted to authorized users",
                "control_description": "Logical access to systems and data is restricted to authorized users.",
                "domain": "CC6 – Logical & Physical Access",
            },
            {
                "control_id": "CC6.2",
                "title": "User access provisioning and deprovisioning",
                "control_description": "User access is provisioned, modified, and revoked based on authorized requests.",
                "domain": "CC6 – Logical & Physical Access",
            },
            {
                "control_id": "CC6.3",
                "title": "Access reviews performed periodically",
                "control_description": "Periodic access reviews are performed to validate appropriateness of user access.",
                "domain": "CC6 – Logical & Physical Access",
            },
            {
                "control_id": "CC6.4",
                "title": "Physical access to systems restricted",
                "control_description": "Physical access to systems and facilities is restricted to authorized personnel.",
                "domain": "CC6 – Logical & Physical Access",
            },
            {
                "control_id": "CC6.5",
                "title": "Network access controls implemented",
                "control_description": "Network access controls are implemented to protect systems and data.",
                "domain": "CC6 – Logical & Physical Access",
            },
            {
                "control_id": "CC6.6",
                "title": "Authentication mechanisms enforced",
                "control_description": "Authentication mechanisms are enforced to validate user identities before access is granted.",
                "domain": "CC6 – Logical & Physical Access",
            },
            # CC7 – System Operations
            {
                "control_id": "CC7.1",
                "title": "Security incidents detected and monitored",
                "control_description": "Security events are detected, monitored, and analyzed for potential incidents.",
                "domain": "CC7 – System Operations",
            },
            {
                "control_id": "CC7.2",
                "title": "Incident response procedures established",
                "control_description": "Incident response procedures are established, maintained, and tested.",
                "domain": "CC7 – System Operations",
            },
            {
                "control_id": "CC7.3",
                "title": "Root cause analysis performed",
                "control_description": "Root cause analysis is performed to identify underlying issues and prevent recurrence.",
                "domain": "CC7 – System Operations",
            },
            {
                "control_id": "CC7.4",
                "title": "System vulnerabilities identified and remediated",
                "control_description": "System vulnerabilities are identified, assessed, and remediated in a timely manner.",
                "domain": "CC7 – System Operations",
            },
            # CC8 – Change Management
            {
                "control_id": "CC8.1",
                "title": "Changes authorized and approved",
                "control_description": "Changes are authorized, approved, and documented before implementation.",
                "domain": "CC8 – Change Management",
            },
            {
                "control_id": "CC8.2",
                "title": "Changes tested prior to deployment",
                "control_description": "Changes are tested and validated prior to deployment to production.",
                "domain": "CC8 – Change Management",
            },
            # CC9 – Risk Mitigation
            {
                "control_id": "CC9.1",
                "title": "Vendor and third-party risks managed",
                "control_description": "Vendor and third-party risks are assessed and managed throughout the relationship lifecycle.",
                "domain": "CC9 – Risk Mitigation",
            },
            {
                "control_id": "CC9.2",
                "title": "Third-party performance monitored",
                "control_description": "Third-party performance is monitored to ensure security obligations are met.",
                "domain": "CC9 – Risk Mitigation",
            },
        ]

        created_count = 0
        for control in controls:
            _, created = StandardControl.objects.get_or_create(
                standard=standard,
                control_id=control["control_id"],
                defaults={
                    "title": control["title"],
                    "control_description": control["control_description"],
                    "domain": control["domain"],
                    "is_active": True,
                },
            )
            if created:
                created_count += 1

        self.stdout.write("SOC 2 Security seeding completed: 32 controls ensured.")
