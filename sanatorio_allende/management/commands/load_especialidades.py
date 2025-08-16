import argparse
import json
import os
from typing import Any

from django.core.management.base import BaseCommand

from sanatorio_allende.models import Especialidad
from sanatorio_allende.services.data_loader import DataLoader


class Command(BaseCommand):
    help = "Load especialidades from JSON file into the database"

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--file",
            type=str,
            default="sanatorio_allende/data/especialidades.json",
            help="Path to the especialidades JSON file",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing especialidades before loading",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        file_path = options["file"]
        clear_existing = options["clear"]

        # Check if file exists
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        try:
            # Read JSON file
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            especialidades_data = data.get("Especialidades", [])

            if not especialidades_data:
                self.stdout.write(
                    self.style.WARNING("No especialidades found in JSON file")
                )
                return

            # Clear existing data if requested
            if clear_existing:
                deleted_count = Especialidad.objects.all().delete()[0]
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Deleted {deleted_count} existing especialidades"
                    )
                )

            data_loader = DataLoader()
            created_count, updated_count, skipped_count = (
                data_loader.load_especialidades(especialidades_data)
            )

            # Print summary
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully processed especialidades:\n"
                    f"  Created: {created_count}\n"
                    f"  Updated: {updated_count}\n"
                    f"  Skipped: {skipped_count}\n"
                    f"  Total: {created_count + updated_count}"
                )
            )

        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f"Invalid JSON file: {e}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error loading especialidades: {e}"))
