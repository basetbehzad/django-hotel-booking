from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Place(models.Model):
    CATEGORY_CHOICES = [
        ('hotel', 'Hotel'),
        ('motel', 'Motel'),
        ('room', 'Room'),
        ('house', 'House'),
    ]

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="places")
    name = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    address = models.CharField(max_length=255)
    num_rooms = models.PositiveIntegerField()
    num_persons = models.PositiveIntegerField()
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    amenities = models.TextField(help_text="Comma separated list of amenities")
    is_verified = models.BooleanField(default=False)  # Admin must verify
    is_active = models.BooleanField(default=True)  # Owner can disable listings
    created_at = models.DateTimeField(auto_now_add=True)
    average_rating = models.FloatField(default=0.0)

    def update_average_rating(self):
        ratings = self.bookings.filter(rating__isnull=False).values_list('rating', flat=True)
        if ratings:
            self.average_rating = sum(ratings) / len(ratings)
        else:
            self.average_rating = 0.0
        self.save()

    def __str__(self):
        return self.name


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    place = models.ForeignKey(Place, on_delete=models.CASCADE)
    content = models.TextField()
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.get_display_name()} on {self.place.name}"
