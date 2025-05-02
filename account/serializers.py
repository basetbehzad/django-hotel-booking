from rest_framework import serializers
from django.contrib.auth import get_user_model
from account.models import Profile
from reservation.models import CancellationRequest
from reservation.serializers import CancellationRequestSerializer, BookingSerializer

User = get_user_model()


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['full_name', 'phone_number', 'address']


# serializers.py
class UserProfileSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()
    cancellations = serializers.SerializerMethodField()
    bookings = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'profile', 'cancellations', 'bookings']
        read_only_fields = ['id']

    def get_bookings(self, obj):
        # Use the custom manager to exclude cancelled bookings
        bookings = obj.booking_set.all()  # This uses ActiveBookingManager
        return BookingSerializer(bookings, many=True).data

    def get_cancellations(self, obj):
        cancellations = CancellationRequest.objects.filter(booking__user=obj).select_related('booking',
                                                                                             'booking__place')
        serializer = CancellationRequestSerializer(cancellations, many=True)
        return serializer.data

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', {})

        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update profile fields
        profile = instance.profile
        for attr, value in profile_data.items():
            setattr(profile, attr, value)
        profile.save()

        return instance


class UserRegisterSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(required=False)  # Optional during registration

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'role', 'profile']
        read_only_fields = ['id']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        profile_data = validated_data.pop('profile', {})
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()

        # Create profile
        Profile.objects.create(user=user, **profile_data)

        return user
