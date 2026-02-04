import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from audit.models import Standard, StandardControl


class Command(BaseCommand):
    help = "Seed ISO/IEC 42001:2023 controls from checklist CSV."

    def add_arguments(self, parser):
        parser.add_argument(
            "--csv",
            default="/Users/shivakumarsh/Desktop/ISO 42001 tool checklist.csv",
            help="Absolute path to the ISO 42001 checklist CSV.",
        )
        parser.add_argument(
            "--yes",
            action="store_true",
            help="Skip confirmation prompt.",
        )

    def handle(self, *args, **options):
        csv_path = Path(options["csv"])
        if not csv_path.exists():
            raise CommandError(f"CSV not found: {csv_path}")

        rows = []
        with csv_path.open(newline="", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            required_fields = [
                "Standard",
                "Control Type",
                "Clause / Annex Section",
                "Domain / Control Area",
                "Control ID",
                "Control Title",
                "Control Description",
            ]
            missing = [field for field in required_fields if field not in reader.fieldnames]
            if missing:
                raise CommandError(f"Missing columns in CSV: {', '.join(missing)}")

            for row in reader:
                if not row.get("Control ID"):
                    raise CommandError("Encountered a row with empty Control ID.")
                rows.append(row)

        if not rows:
            raise CommandError("CSV has no control rows to import.")

        standard_name = "ISO/IEC 42001:2023"
        standard, _ = Standard.objects.get_or_create(name=standard_name)

        self.stdout.write(f"CSV rows: {len(rows)}")
        self.stdout.write(f"Target standard: {standard.name}")
        self.stdout.write("Planned action: upsert standard controls from CSV.")

        if not options["yes"]:
            confirm = input("Type 'seed' to proceed: ").strip().lower()
            if confirm != "seed":
                self.stdout.write(self.style.WARNING("Aborted. No changes made."))
                return

        created = 0
        updated = 0

        with transaction.atomic():
            for row in rows:
                control_id = row["Control ID"]
                defaults = {
                    "title": row["Control Title"],
                    "control_description": row["Control Description"],
                    "domain": row["Domain / Control Area"],
                    "standard_reference": row["Clause / Annex Section"],
                    "default_testing_type": row["Control Type"],
                    "is_active": True,
                }

                obj, was_created = StandardControl.objects.update_or_create(
                    standard=standard,
                    control_id=control_id,
                    defaults=defaults,
                )
                if was_created:
                    created += 1
                else:
                    updated += 1

        total = StandardControl.objects.filter(standard=standard).count()
        self.stdout.write(self.style.SUCCESS("Seeding complete."))
        self.stdout.write(f"Created: {created}")
        self.stdout.write(f"Updated: {updated}")
        self.stdout.write(f"Total controls for {standard.name}: {total}")

        if total != len(rows):
            raise CommandError(
                "Total controls in DB does not match CSV row count. "
                "Please review for duplicates or pre-existing controls."
            )
