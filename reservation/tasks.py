from datetime import timedelta
from celery import shared_task
from django.utils.timezone import now
from django.apps import apps

from reservation.models import DeletedReservation


@shared_task
def auto_cancel_unpaid_bookings():
    """
    This task cancels unpaid bookings if they are not paid within a certain time (e.g., 10 minutes).
    """
    Booking = apps.get_model('reservation', 'Booking')
    expiration_time = now() - timedelta(minutes=10)  # Set expiration time (10 minutes)
    unpaid_bookings = Booking.objects.filter(is_paid=False, created_at__lt=expiration_time)

    count = unpaid_bookings.count()
    if count > 0:
        for reservation in unpaid_bookings:
            # Save details before deletion
            DeletedReservation.objects.create(
                reservation_id=reservation.id,
                user=reservation.user.username if reservation.user else "Unknown",
                hotel=reservation.hotel.name if reservation.hotel else "Unknown",
                check_in=reservation.check_in_date,
                check_out=reservation.check_out_date
            )

            # Delete the reservation
            reservation.delete()

        return f"{count} unpaid bookings were canceled."

    return "No unpaid bookings to cancel."
