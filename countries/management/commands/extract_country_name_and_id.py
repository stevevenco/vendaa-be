import json
from pathlib import Path
from django.core.management.base import BaseCommand
from countries.models import Country  # update with your actual app name


class Command(BaseCommand):
    help = "Export all countries to a JSON file with {country_name: uuid}"

    def handle(self, *args, **kwargs):
        data = {country.name.lower(): str(country.uuid) for country in Country.objects.all()}

        output_path = Path("countries_staging.json")
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

        self.stdout.write(self.style.SUCCESS(f"Exported {len(data)} countries to {output_path}"))
