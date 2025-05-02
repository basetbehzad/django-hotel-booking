from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.conf import settings
from django.utils import timezone

from place.models import Place
from account.models import User
from datetime import datetime, timedelta


class ActiveBookingManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(
            is_cancelled=False
        ).exclude(
            cancellation_request__status='approved'
        )


class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name="bookings")
    start_date = models.DateField()
    end_date = models.DateField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    stripe_session_id = models.CharField(max_length=255, blank=True, null=True)
    rating = models.PositiveSmallIntegerField(null=True, blank=True,
                                              validators=[MinValueValidator(1), MaxValueValidator(5)])
    rated_at = models.DateTimeField(null=True, blank=True)
    is_cancelled = models.BooleanField(default=False)
    objects = ActiveBookingManager()
    all_objects = models.Manager()

    class Meta:
        base_manager_name = 'objects'

    @property
    def can_rate(self):
        """Check if booking can be rated (must be past, paid, and not rated)"""
        now = timezone.now().date()
        return (
                self.end_date < now and  # Stay must be completed
                self.is_paid and  # Must be paid
                not self.rating  # Not already rated
        )

    def save(self, *args, **kwargs):
        # Ensure start_date is before end_date
        if self.start_date >= self.end_date:
            raise ValueError("Start date must be before end date")
        # Ensure booking duration is between 1 and 7 days
        duration = (self.end_date - self.start_date).days
        if duration < 1 or duration > 7:
            raise ValueError("Booking must be between 1 and 7 days")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} booked {self.place.id} from {self.start_date} to {self.end_date}"


class DeletedReservation(models.Model):
    reservation_id = models.IntegerField()
    user = models.CharField(max_length=255)  # Store the username or email
    hotel = models.CharField(max_length=255)  # Store hotel name or ID
    check_in = models.DateField()
    check_out = models.DateField()
    deleted_at = models.DateTimeField(auto_now_add=True)  # Timestamp of deletion

    def __str__(self):
        return f"Deleted Reservation {self.reservation_id} - {self.user}"


class CancellationRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('refunded', 'Refunded'),
    ]

    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,  # Prevent booking deletion
        related_name='cancellation_request'
    )
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)

    def get_refund_amount(self):
        now = timezone.now()
        time_diff = (self.booking.start_date - now.date()).days * 24 + (
                self.booking.start_date - now.date()).seconds / 3600

        if time_diff < 24:
            return 0  # No refund
        elif 24 <= time_diff < 72:
            return self.booking.total_price / 2  # 50% refund
        else:
            return self.booking.total_price  # Full refund

    def can_auto_approve(self):
        return self.get_refund_amount() > 0

    def save(self, *args, **kwargs):
        if self.status == 'approved':
            self.booking.is_cancelled = True
            self.booking.save(update_fields=['is_cancelled'])
        super().save(*args, **kwargs)
