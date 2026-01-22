# Generated optimization migration

from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('route_performance', '0001_initial'),
        ('bus_route', '0001_initial'),  # Assuming bus_route has migrations
    ]

    operations = [
        # Add indexes to the existing bus_route models for better performance
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_trip_date_revenue ON bus_route_trip(date) WHERE revenue IS NOT NULL;",
            reverse_sql="DROP INDEX IF EXISTS idx_trip_date_revenue;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_trip_schedule_no ON bus_route_trip(schedule_no);",
            reverse_sql="DROP INDEX IF EXISTS idx_trip_schedule_no;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_schedule_route_no ON bus_route_schedule(route_no);",
            reverse_sql="DROP INDEX IF EXISTS idx_schedule_route_no;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_schedule_composite ON bus_route_schedule(schedule_no, trip_no);",
            reverse_sql="DROP INDEX IF EXISTS idx_schedule_composite;"
        ),
    ]