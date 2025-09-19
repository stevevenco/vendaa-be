import requests
from django.core.management.base import BaseCommand
from countries.models import Country

class Command(BaseCommand):
    help = 'Fetches country data from an API and populates the Country table.'

    def handle(self, *args, **options):
        url = "https://meterservices.01101960.xyz/api/method/meter_services.v1.get_countries"
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an exception for bad status codes
            data = response.json()

            if data.get("response", {}).get("status") == "success":
                countries_data = data.get("response", {}).get("data", {})
                for name, details in countries_data.items():
                    currency = details.get("currency")
                    if currency:
                        country, created = Country.objects.update_or_create(
                            name=name,
                            defaults={'currency': currency}
                        )
                        if created:
                            self.stdout.write(self.style.SUCCESS(f"Successfully created Country: {name}"))
                        else:
                            self.stdout.write(self.style.SUCCESS(f"Successfully updated Country: {name}"))
            else:
                self.stderr.write(self.style.ERROR("Failed to fetch country data: API status was not 'success'"))

        except requests.exceptions.RequestException as e:
            self.stderr.write(self.style.ERROR(f"Error fetching data from API: {e}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"An unexpected error occurred: {e}"))
