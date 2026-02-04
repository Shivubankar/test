from django.db import transaction
from django.core.management.base import BaseCommand, CommandError

from audit.models import Standard, StandardControl


class Command(BaseCommand):
    help = "Replace ISO/IEC 42001:2023 controls with Annex A list."

    def add_arguments(self, parser):
        parser.add_argument(
            "--yes",
            action="store_true",
            help="Skip confirmation prompt.",
        )

    def handle(self, *args, **options):
        standard_name = "ISO/IEC 42001:2023"
        standard, _ = Standard.objects.get_or_create(name=standard_name)

        controls_data = [
            {
                "control_id": "A.2.2",
                "control_title": "AI policy",
                "control_description": "The organization shall document a policy for the development or use of AI systems.",
                "control_objective": "To provide management direction and support for AI systems according to business requirements.",
            },
            {
                "control_id": "A.2.3",
                "control_title": "Alignment with other organizational policies",
                "control_description": "The organization shall determine where other policies can be affected by or apply to, the organization's objectives with respect to AI systems.",
                "control_objective": "To provide management direction and support for AI systems according to business requirements.",
            },
            {
                "control_id": "A.2.4",
                "control_title": "Review of the AI policy",
                "control_description": "The AI policy shall be reviewed at planned intervals or additionally as needed to ensure its suitability, adequacy and continuing effectiveness.",
                "control_objective": "To provide management direction and support for AI systems according to business requirements.",
            },
            {
                "control_id": "A.3.2",
                "control_title": "AI roles and responsibilities",
                "control_description": "Roles and responsibilities for AI shall be defined and allocated according to the needs of the organization.",
                "control_objective": "To establish accountability within the organization to uphold its responsible approach for the implementation, operation and management of AI systems.",
            },
            {
                "control_id": "A.3.3",
                "control_title": "Reporting of concerns",
                "control_description": "The organization shall define and put in place a process to report concerns about the organization's role with respect to an AI system throughout its life cycle.",
                "control_objective": "To establish accountability within the organization to uphold its responsible approach for the implementation, operation and management of AI systems.",
            },
            {
                "control_id": "A.4.2",
                "control_title": "Resource documentation",
                "control_description": "The organization shall identify and document relevant resources required for the activities at given AI system life cycle stages and other AI-related activities relevant for the organization.",
                "control_objective": "To ensure that the organization accounts for the resources (including AI system components and assets) of the AI system in order to fully understand and address risks and impacts.",
            },
            {
                "control_id": "A.4.3",
                "control_title": "Data resources",
                "control_description": "As part of resource identification, the organization shall document information about the data resources utilized for the AI system.",
                "control_objective": "To ensure that the organization accounts for the resources (including AI system components and assets) of the AI system in order to fully understand and address risks and impacts.",
            },
            {
                "control_id": "A.4.4",
                "control_title": "Tooling resources",
                "control_description": "As part of resource identification, the organization shall document information about the tooling resources utilized for the AI system.",
                "control_objective": "To ensure that the organization accounts for the resources (including AI system components and assets) of the AI system in order to fully understand and address risks and impacts.",
            },
            {
                "control_id": "A.4.5",
                "control_title": "System and computing resources",
                "control_description": "As part of resource identification, the organization shall document information about the system and computing resources utilized for the AI system.",
                "control_objective": "To ensure that the organization accounts for the resources (including AI system components and assets) of the AI system in order to fully understand and address risks and impacts.",
            },
            {
                "control_id": "A.4.6",
                "control_title": "Human resources",
                "control_description": "As part of resource identification, the organization shall document information about the human resources and their competences utilized for the development, deployment, operation, change management, maintenance, transfer and decommissioning, as well as verification and integration of the AI system.",
                "control_objective": "To ensure that the organization accounts for the resources (including AI system components and assets) of the AI system in order to fully understand and address risks and impacts.",
            },
            {
                "control_id": "A.6.1.2",
                "control_title": "Objectives for responsible development of AI system",
                "control_description": "The organization shall identify and document objectives to guide the responsible development of AI systems, and take those objectives into account and integrate measures to achieve them in the development life cycle.",
                "control_objective": "To ensure that the organization implements processes for the responsible design and development of AI systems.",
            },
            {
                "control_id": "A.6.1.3",
                "control_title": "Processes for responsible design and development",
                "control_description": "The organization shall define and document the specific processes for the responsible design and development of the AI system.",
                "control_objective": "To ensure that the organization implements processes for the responsible design and development of AI systems.",
            },
            {
                "control_id": "A.6.2.2",
                "control_title": "AI system requirements and specification",
                "control_description": "The organization shall specify and document requirements for new AI systems or material enhancements to existing systems.",
                "control_objective": "To ensure that the organization implements processes for the responsible design and development of AI systems.",
            },
            {
                "control_id": "A.6.2.3",
                "control_title": "Documentation of AI system design and development",
                "control_description": "The organization shall document the AI system design and development based on organizational objectives, documented requirements and specification criteria.",
                "control_objective": "To ensure that the organization implements processes for the responsible design and development of AI systems.",
            },
            {
                "control_id": "A.6.2.4",
                "control_title": "AI system verification and validation",
                "control_description": "The organization shall define and document verification and validation measures for the AI system and specify criteria for their use.",
                "control_objective": "To ensure that the organization implements processes for the responsible design and development of AI systems.",
            },
            {
                "control_id": "A.6.2.5",
                "control_title": "AI system deployment",
                "control_description": "The organization shall document a deployment plan and ensure that appropriate requirements are met prior to deployment.",
                "control_objective": "To ensure that the organization implements processes for the responsible design and development of AI systems.",
            },
            {
                "control_id": "A.6.2.6",
                "control_title": "AI system operation and monitoring",
                "control_description": "The organization shall define and document the necessary elements for the ongoing operation of the AI system. At the minimum, this should include system and performance monitoring, repairs, updates and support.",
                "control_objective": "To ensure that the organization implements processes for the responsible design and development of AI systems.",
            },
            {
                "control_id": "A.6.2.7",
                "control_title": "AI system technical documentation",
                "control_description": "The organization shall determine what AI system technical documentation is needed for each relevant category of interested parties, such as users, partners, supervisory authorities, and provide the technical documentation to them in the appropriate form.",
                "control_objective": "To ensure that the organization implements processes for the responsible design and development of AI systems.",
            },
            {
                "control_id": "A.6.2.8",
                "control_title": "AI system recording of event logs",
                "control_description": "The organization shall determine at which phases of the AI system life cycle, record keeping of event logs should be enabled, but at the minimum when the AI system is in use.",
                "control_objective": "To ensure that the organization implements processes for the responsible design and development of AI systems.",
            },
            {
                "control_id": "A.7.2",
                "control_title": "Data for development and enhancement of AI system",
                "control_description": "The organization shall define, document and implement data management processes related to the development of AI systems.",
                "control_objective": "To ensure that the organization understands the role and impacts of data in AI systems in the application and development, provision or use of AI systems throughout their life cycles.",
            },
            {
                "control_id": "A.7.3",
                "control_title": "Acquisition of data",
                "control_description": "The organization shall determine and document details about the acquisition and selection of the data used in AI systems.",
                "control_objective": "To ensure that the organization understands the role and impacts of data in AI systems in the application and development, provision or use of AI systems throughout their life cycles.",
            },
            {
                "control_id": "A.7.4",
                "control_title": "Quality of data for AI systems",
                "control_description": "The organization shall define and document requirements for data quality and ensure that data used to develop and operate the AI system meet those requirements.",
                "control_objective": "To ensure that the organization understands the role and impacts of data in AI systems in the application and development, provision or use of AI systems throughout their life cycles.",
            },
            {
                "control_id": "A.7.5",
                "control_title": "Data provenance",
                "control_description": "The organization shall define and document a process for recording the provenance of data used in its AI systems over the life cycles of the data and the AI system.",
                "control_objective": "To ensure that the organization understands the role and impacts of data in AI systems in the application and development, provision or use of AI systems throughout their life cycles.",
            },
            {
                "control_id": "A.7.6",
                "control_title": "Data preparation",
                "control_description": "The organization shall define and document its criteria for selecting data preparations and the data preparation methods to be used.",
                "control_objective": "To ensure that the organization understands the role and impacts of data in AI systems in the application and development, provision or use of AI systems throughout their life cycles.",
            },
            {
                "control_id": "A.8.2",
                "control_title": "System documentation and information for users",
                "control_description": "The organization shall determine and provide the necessary information to users of the AI system.",
                "control_objective": "To ensure that relevant interested parties have the necessary information to understand and assess the risks and their impacts (both positive and negative).",
            },
            {
                "control_id": "A.8.3",
                "control_title": "External reporting",
                "control_description": "The organization shall provide capabilities for interested parties to report adverse impacts of the AI system.",
                "control_objective": "To ensure that relevant interested parties have the necessary information to understand and assess the risks and their impacts (both positive and negative).",
            },
            {
                "control_id": "A.8.4",
                "control_title": "Communication of incidents",
                "control_description": "The organization shall determine and document a plan for communicating incidents to users of the AI system.",
                "control_objective": "To ensure that relevant interested parties have the necessary information to understand and assess the risks and their impacts (both positive and negative).",
            },
            {
                "control_id": "A.8.5",
                "control_title": "Information for interested parties",
                "control_description": "The organization shall determine and document their obligations to reporting information about the AI system to interested parties.",
                "control_objective": "To ensure that relevant interested parties have the necessary information to understand and assess the risks and their impacts (both positive and negative).",
            },
            {
                "control_id": "A.9.2",
                "control_title": "Processes for responsible use of AI systems",
                "control_description": "The organization shall define and document the processes for the responsible use of AI systems.",
                "control_objective": "To ensure that the organization uses AI systems responsibly and per organizational policies.",
            },
            {
                "control_id": "A.9.3",
                "control_title": "Objectives for responsible use of AI system",
                "control_description": "The organization shall identify and document objectives to guide the responsible use of AI systems.",
                "control_objective": "To ensure that the organization uses AI systems responsibly and per organizational policies.",
            },
            {
                "control_id": "A.9.4",
                "control_title": "Intended use of the AI system",
                "control_description": "The organization shall ensure that the AI system is used according to the intended uses of the AI system and its accompanying documentation.",
                "control_objective": "To ensure that the organization uses AI systems responsibly and per organizational policies.",
            },
            {
                "control_id": "A.10.2",
                "control_title": "Allocating responsibilities",
                "control_description": "The organization shall ensure that responsibilities within their AI system life cycle are allocated between the organization, its partners, suppliers, customers and third parties.",
                "control_objective": "To ensure that the organization understands its responsibilities and remains accountable, and risks are appropriately apportioned when third parties are involved at any stage of the AI system life cycle.",
            },
            {
                "control_id": "A.10.3",
                "control_title": "Suppliers",
                "control_description": "The organization shall establish a process to ensure that its usage of services, products or materials provided by suppliers aligns with the organization's approach to the responsible development and use of AI systems.",
                "control_objective": "To ensure that the organization understands its responsibilities and remains accountable, and risks are appropriately apportioned when third parties are involved at any stage of the AI system life cycle.",
            },
            {
                "control_id": "A.10.4",
                "control_title": "Customers",
                "control_description": "The organization shall ensure that its responsible approach to the development and use of AI systems considers their customer expectations and needs.",
                "control_objective": "To ensure that the organization understands its responsibilities and remains accountable, and risks are appropriately apportioned when third parties are involved at any stage of the AI system life cycle.",
            },
        ]

        if not controls_data:
            raise CommandError("No Annex A controls provided.")

        self.stdout.write(f"Target standard: {standard.name}")
        self.stdout.write(f"Planned controls: {len(controls_data)}")
        self.stdout.write("Planned action: delete existing ISO/IEC 42001 controls and insert Annex A list.")
        self.stdout.write(f"Target standard: {standard.name}")
        self.stdout.write("Planned action: upsert standard controls from CSV.")

        if not options["yes"]:
            confirm = input("Type 'seed' to proceed: ").strip().lower()
            if confirm != "seed":
                self.stdout.write(self.style.WARNING("Aborted. No changes made."))
                return

        with transaction.atomic():
            StandardControl.objects.filter(standard=standard).delete()
            StandardControl.objects.bulk_create(
                [
                    StandardControl(
                        standard=standard,
                        control_id=item["control_id"],
                        title=item["control_title"],
                        control_description=item["control_description"],
                        control_objective=item["control_objective"],
                        domain="",
                        standard_reference="",
                        default_testing_type="",
                        is_active=True,
                    )
                    for item in controls_data
                ]
            )

        total = StandardControl.objects.filter(standard=standard).count()
        self.stdout.write(self.style.SUCCESS("Seeding complete."))
        self.stdout.write(f"Total controls for {standard.name}: {total}")

        if total != len(controls_data):
            raise CommandError(
                "Total controls in DB does not match Annex A list count. "
                "Please review for duplicates or missing controls."
            )
