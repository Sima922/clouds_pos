from django.core.management.base import BaseCommand
from reports.models import SalesReport

class Command(BaseCommand):
    help = 'Generates daily sales reports'

    def handle(self, *args, **options):
        report = SalesReport.generate_daily_report()
        self.stdout.write(self.style.SUCCESS(
            f'Successfully generated daily report for {report.report_date}'
        ))