from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from audit.models import (
    Standard,
    StandardControl,
    EngagementControl,
    Request,
    RequestDocument,
)


class Command(BaseCommand):
    help = "Delete ISO/IEC 42001 standard and all related data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--yes",
            action="store_true",
            help="Skip confirmation prompt.",
        )

    def handle(self, *args, **options):
        standards_qs = Standard.objects.filter(name__icontains="42001")

        if not standards_qs.exists():
            self.stdout.write(self.style.WARNING("No ISO/IEC 42001 standards found."))
            return

        standard_names = list(standards_qs.values_list("name", flat=True))

        standard_controls_qs = StandardControl.objects.filter(
            standard__in=standards_qs
        )
        engagement_controls_qs = EngagementControl.objects.filter(
            standard_control__in=standard_controls_qs
        )
        requests_qs = Request.objects.filter(linked_control__in=engagement_controls_qs)

        documents_qs = RequestDocument.objects.filter(
            Q(standard__in=standards_qs)
            | Q(linked_control__in=engagement_controls_qs)
            | Q(request__in=requests_qs)
        ).distinct()

        workpaper_docs_qs = documents_qs.filter(doc_type="workpaper")

        self.stdout.write("ISO/IEC 42001 standards to delete:")
        for name in standard_names:
            self.stdout.write(f"  - {name}")

        self.stdout.write("")
        self.stdout.write("Planned deletions:")
        self.stdout.write(f"  Standards: {standards_qs.count()}")
        self.stdout.write(f"  Standard Controls: {standard_controls_qs.count()}")
        self.stdout.write(f"  Engagement Controls: {engagement_controls_qs.count()}")
        self.stdout.write(f"  Requests: {requests_qs.count()}")
        self.stdout.write(f"  Documents: {documents_qs.count()}")
        self.stdout.write(f"  Workpapers: {workpaper_docs_qs.count()}")

        if not options["yes"]:
            self.stdout.write("")
            confirm = input(
                "Type 'delete' to confirm deletion of ISO/IEC 42001 data: "
            ).strip()
            if confirm.lower() != "delete":
                self.stdout.write(self.style.WARNING("Aborted. No changes made."))
                return

        with transaction.atomic():
            documents_qs.delete()
            requests_qs.delete()
            engagement_controls_qs.delete()
            standard_controls_qs.delete()
            standards_qs.delete()

        self.stdout.write(self.style.SUCCESS("ISO/IEC 42001 data deleted."))
