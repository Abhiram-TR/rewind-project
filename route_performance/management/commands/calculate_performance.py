from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from route_performance.utils import RoutePerformanceCalculator

class Command(BaseCommand):
    help = 'Calculate route performance metrics for a date range'

    def add_arguments(self, parser):
        parser.add_argument(
            '--start-date',
            type=str,
            help='Start date in YYYY-MM-DD format (default: 30 days ago)',
        )
        parser.add_argument(
            '--end-date',
            type=str,
            help='End date in YYYY-MM-DD format (default: today)',
        )
        parser.add_argument(
            '--period',
            type=str,
            choices=['daily', 'weekly', 'monthly'],
            default='daily',
            help='Period type for calculations (default: daily)',
        )

    def handle(self, *args, **options):
        # Parse dates
        if options['start_date']:
            start_date = timezone.datetime.strptime(options['start_date'], '%Y-%m-%d').date()
        else:
            start_date = date.today() - timedelta(days=30)
        
        if options['end_date']:
            end_date = timezone.datetime.strptime(options['end_date'], '%Y-%m-%d').date()
        else:
            end_date = date.today()
        
        period_type = options['period']
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Starting performance calculation from {start_date} to {end_date} ({period_type})'
            )
        )
        
        try:
            # Bulk calculate performance metrics
            routes_processed = RoutePerformanceCalculator.bulk_calculate_performance(
                start_date=start_date,
                end_date=end_date,
                period_type=period_type
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully processed {routes_processed} routes'
                )
            )
            
            # Show summary of top and bottom performers
            top_performers = RoutePerformanceCalculator.get_top_performers(
                limit=5, start_date=start_date, end_date=end_date
            )
            
            underperformers = RoutePerformanceCalculator.get_underperformers(
                limit=5, start_date=start_date, end_date=end_date
            )
            
            self.stdout.write('\n' + self.style.SUCCESS('Top 5 Performers:'))
            for i, route in enumerate(top_performers, 1):
                self.stdout.write(
                    f"{i}. Route {route['route_no']}: ₹{route['avg_epkm']} EPKM "
                    f"(₹{route['total_revenue']} revenue, {route['trip_count']} trips)"
                )
            
            self.stdout.write('\n' + self.style.WARNING('Bottom 5 Performers:'))
            for i, route in enumerate(underperformers, 1):
                self.stdout.write(
                    f"{i}. Route {route['route_no']}: ₹{route['avg_epkm']} EPKM "
                    f"(₹{route['total_revenue']} revenue, {route['trip_count']} trips)"
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error calculating performance: {str(e)}')
            )