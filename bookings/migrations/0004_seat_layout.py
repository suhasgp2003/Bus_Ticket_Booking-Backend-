# Generated manually for seat-position metadata.

from django.db import migrations, models


def populate_seat_layout(apps, schema_editor):
    Seat = apps.get_model('bookings', 'Seat')
    seat_counts = {}

    for seat in Seat.objects.all().order_by('bus_id', 'id'):
        seat_index = seat_counts.get(seat.bus_id, 0) + 1
        seat_counts[seat.bus_id] = seat_index
        column = (seat_index - 1) % 4 + 1
        seat.row = (seat_index - 1) // 4 + 1
        seat.column = column
        seat.seat_type = 'window' if column in (1, 4) else 'aisle'
        seat.save(update_fields=['row', 'column', 'seat_type'])


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0003_booking'),
    ]

    operations = [
        migrations.AddField(
            model_name='seat',
            name='row',
            field=models.PositiveIntegerField(default=1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='seat',
            name='column',
            field=models.PositiveIntegerField(default=1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='seat',
            name='seat_type',
            field=models.CharField(choices=[('window', 'Window'), ('aisle', 'Aisle')], default='window', max_length=10),
            preserve_default=False,
        ),
        migrations.RunPython(populate_seat_layout, migrations.RunPython.noop),
    ]
