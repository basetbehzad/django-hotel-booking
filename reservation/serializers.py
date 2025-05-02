from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers
from reservation.models import Booking, CancellationRequest


class BookingSerializer(serializers.ModelSerializer):
    place_name = serializers.CharField(source='place.title', read_only=True)
    can_rate = serializers.SerializerMethodField()
    current_date = serializers.SerializerMethodField()
    is_cancelled = serializers.BooleanField(read_only=True)
    cancellation_status = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = ['id', 'place', 'start_date', 'end_date', 'total_price', 'is_paid', 'created_at', 'user', 'rating',
                  'can_rate', 'place_name', 'current_date', 'cancellation_status', 'is_cancelled']
        read_only_fields = ['id', 'created_at', 'user', 'total_price']


    def get_can_rate(self, obj):
        return obj.can_rate

    def get_current_date(self, obj):
        return timezone.now().date()

    def get_cancellation_status(self, obj):
        if hasattr(obj, 'cancellation_request'):
            return obj.cancellation_request.status
        return None

    def validate(self, data):
        """Ensure that the booking dates follow the rules."""
        place = data['place']
        start_date = data['start_date']
        end_date = data['end_date']

        if start_date >= end_date:
            raise serializers.ValidationError("Booking must be at least one full day.")

        max_duration = timedelta(days=7)
        if (end_date - start_date) > max_duration:
            raise serializers.ValidationError("You can only book for a maximum of 7 days.")

        overlapping_bookings = Booking.objects.filter(
            place=place,
            start_date__lt=end_date,
            end_date__gt=start_date
        )

        if overlapping_bookings.exists():
            unpaid = overlapping_bookings.filter(is_paid=False)
            if unpaid.exists():
                raise serializers.ValidationError("These dates are already requested and waiting for payment.")
            else:
                raise serializers.ValidationError("These dates are already booked.")

        return data


class BookingCalendarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['start_date', 'end_date', 'is_paid']


class BookingDetailSerializer(serializers.ModelSerializer):
    place_name = serializers.CharField(source='place.name')
    user_full_name = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            'id', 'place_name', 'user_full_name', 'start_date',
            'end_date', 'total_price', 'is_paid', 'created_at'
        ]

    def get_user_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"


class BookingListSerializer(serializers.ModelSerializer):
    place_name = serializers.CharField(source='place.name')

    class Meta:
        model = Booking
        fields = ['id', 'place_name', 'start_date', 'end_date', 'is_paid']


class BookingRatingSerializer(serializers.Serializer):
    rating = serializers.IntegerField(
        min_value=1,
        max_value=5,
        required=True
    )


class CancellationRequestSerializer(serializers.ModelSerializer):
    place_name = serializers.SerializerMethodField()
    start_date = serializers.SerializerMethodField()
    end_date = serializers.SerializerMethodField()

    class Meta:
        model = CancellationRequest
        fields = [
            'id', 'place_name', 'start_date', 'end_date',
            'reason', 'status', 'created_at'
        ]


    def get_place_name(self, obj):
        return obj.booking.place.name if obj.booking else "Deleted Place"

    def get_start_date(self, obj):
        return obj.booking.start_date if obj.booking else None

    def get_end_date(self, obj):
        return obj.booking.end_date if obj.booking else None


class CancellationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CancellationRequest
        fields = ['reason']
