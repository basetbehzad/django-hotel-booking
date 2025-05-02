from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = (
        ('owner', 'Hotel Owner'),
        ('user', 'Normal User'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')

    def get_display_name(self):
        """Returns full name if available, otherwise username"""
        full_name = self.get_full_name()
        return full_name if full_name else self.username


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"
