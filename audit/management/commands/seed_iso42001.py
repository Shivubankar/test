from django.core.management.base import BaseCommand

from audit.models import Standard, StandardControl


class Command(BaseCommand):
    help = "Seed ISO/IEC 42001:2023 AI Management System controls (idempotent)."

    def handle(self, *args, **options):
        standard, _ = Standard.objects.get_or_create(
            name="ISO/IEC 42001:2023",
            defaults={"description": "Artificial Intelligence Management System (AIMS)"},
        )

        controls = [
            # Clause 4 – Context
            {
                "control_id": "AI.4.1",
                "title": "AI context and stakeholders",
                "control_description": "Identify internal and external stakeholders and define the AI-related context relevant to governance.",
                "domain": "Context",
            },
            {
                "control_id": "AI.4.2",
                "title": "AIMS scope definition",
                "control_description": "Define and maintain the scope of the AI management system, including boundaries and applicability.",
                "domain": "Context",
            },
            {
                "control_id": "AI.4.3",
                "title": "AI use case inventory",
                "control_description": "Maintain an inventory of AI use cases, owners, and intended purposes.",
                "domain": "Context",
            },
            {
                "control_id": "AI.4.4",
                "title": "AI risk landscape",
                "control_description": "Identify AI-specific risks across the organization and document relevant external factors.",
                "domain": "Context",
            },
            # Clause 5 – Leadership
            {
                "control_id": "AI.5.1",
                "title": "AI governance roles",
                "control_description": "Assign governance roles and responsibilities for AI oversight and decision-making.",
                "domain": "Leadership",
            },
            {
                "control_id": "AI.5.2",
                "title": "AI policy approval",
                "control_description": "Establish, approve, and communicate an AI policy aligned to organizational objectives.",
                "domain": "Leadership",
            },
            {
                "control_id": "AI.5.3",
                "title": "Accountability for AI outcomes",
                "control_description": "Ensure accountability for AI system outcomes is defined and enforced.",
                "domain": "Leadership",
            },
            # Clause 6 – Planning
            {
                "control_id": "AI.6.1",
                "title": "AI risk assessment method",
                "control_description": "Define and apply a consistent method for assessing AI risks.",
                "domain": "Planning",
            },
            {
                "control_id": "AI.6.2",
                "title": "AI risk treatment plans",
                "control_description": "Develop and maintain treatment plans for identified AI risks.",
                "domain": "Planning",
            },
            {
                "control_id": "AI.6.3",
                "title": "Bias and fairness planning",
                "control_description": "Plan controls to identify, measure, and mitigate bias and fairness risks.",
                "domain": "Planning",
            },
            {
                "control_id": "AI.6.4",
                "title": "Legal and ethical risk planning",
                "control_description": "Identify legal, ethical, and regulatory risks related to AI use cases and plan mitigations.",
                "domain": "Planning",
            },
            {
                "control_id": "AI.6.5",
                "title": "AI objectives and metrics",
                "control_description": "Set measurable AI governance objectives and track progress against them.",
                "domain": "Planning",
            },
            # Clause 7 – Support
            {
                "control_id": "AI.7.1",
                "title": "AI competence and training",
                "control_description": "Ensure personnel involved in AI have appropriate competence and training.",
                "domain": "Support",
            },
            {
                "control_id": "AI.7.2",
                "title": "AI awareness",
                "control_description": "Maintain awareness of AI risks, responsibilities, and acceptable use across relevant roles.",
                "domain": "Support",
            },
            {
                "control_id": "AI.7.3",
                "title": "AI documentation control",
                "control_description": "Manage AI-related documentation and records with proper versioning and retention.",
                "domain": "Support",
            },
            {
                "control_id": "AI.7.4",
                "title": "Data stewardship",
                "control_description": "Define data ownership and stewardship for AI datasets and pipelines.",
                "domain": "Support",
            },
            # Clause 8 – Operation
            {
                "control_id": "AI.8.1",
                "title": "AI lifecycle management",
                "control_description": "Manage AI systems through defined lifecycle stages from design to retirement.",
                "domain": "Operation",
            },
            {
                "control_id": "AI.8.2",
                "title": "Data quality governance",
                "control_description": "Establish controls for data quality, lineage, and provenance used by AI systems.",
                "domain": "Operation",
            },
            {
                "control_id": "AI.8.3",
                "title": "Model validation and testing",
                "control_description": "Perform validation and testing to confirm AI models meet intended performance and risk criteria.",
                "domain": "Operation",
            },
            {
                "control_id": "AI.8.4",
                "title": "Human oversight",
                "control_description": "Implement human oversight mechanisms appropriate to AI impact and risk.",
                "domain": "Operation",
            },
            {
                "control_id": "AI.8.5",
                "title": "AI change management",
                "control_description": "Control and document changes to AI models, data, and configurations.",
                "domain": "Operation",
            },
            {
                "control_id": "AI.8.6",
                "title": "Third-party AI controls",
                "control_description": "Assess and manage risks from third-party AI services and components.",
                "domain": "Operation",
            },
            # Clause 9 – Performance Evaluation
            {
                "control_id": "AI.9.1",
                "title": "AI monitoring and metrics",
                "control_description": "Monitor AI systems using defined metrics for performance, safety, and drift.",
                "domain": "Performance evaluation",
            },
            {
                "control_id": "AI.9.2",
                "title": "Internal AI audits",
                "control_description": "Conduct periodic internal audits of the AI management system.",
                "domain": "Performance evaluation",
            },
            {
                "control_id": "AI.9.3",
                "title": "Management review",
                "control_description": "Perform management reviews of AI governance effectiveness and outcomes.",
                "domain": "Performance evaluation",
            },
            # Clause 10 – Improvement
            {
                "control_id": "AI.10.1",
                "title": "AI incident management",
                "control_description": "Detect, report, and manage AI-related incidents and failures.",
                "domain": "Improvement",
            },
            {
                "control_id": "AI.10.2",
                "title": "Corrective actions",
                "control_description": "Implement corrective actions for AI control deficiencies and risk events.",
                "domain": "Improvement",
            },
            {
                "control_id": "AI.10.3",
                "title": "Continuous improvement",
                "control_description": "Continuously improve the AI management system based on lessons learned.",
                "domain": "Improvement",
            },
        ]

        for control in controls:
            StandardControl.objects.get_or_create(
                standard=standard,
                control_id=control["control_id"],
                defaults={
                    "title": control["title"],
                    "control_description": control["control_description"],
                    "domain": control["domain"],
                    "is_active": True,
                },
            )

        self.stdout.write("ISO/IEC 42001:2023 seeding completed.")
