from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import Count
from django.utils.timezone import now

from reservation.models import Booking
from .models import User, Profile


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'
    fields = ('full_name', 'phone_number', 'address')
    extra = 0


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    list_display = (
        'username',
        'email',
        'role',
        'is_active',
        'is_staff',
        'last_login',
    )
    list_filter = (
        'role',
        'is_active',
        'is_staff',
        'is_superuser',
    )
    search_fields = (
        'username',
        'email',
        'profile__full_name',
        'profile__phone_number',
    )
    ordering = ('-date_joined',)
    readonly_fields = ('last_login', 'date_joined')

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('email', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    def get_inline_instances(self, request, obj=None):
        if obj is not None:
            return super().get_inline_instances(request, obj)
        return []

    def changelist_view(self, request, extra_context=None):
        today = now().date()
        first_day_month = today.replace(day=1)
        first_day_year = today.replace(month=1, day=1)

        # Bookings this month
        month_data = (
            Booking.objects
            .filter(created_at__date__gte=first_day_month)
            .values('user__username')
            .annotate(bookings=Count('id'))
            .order_by('-bookings')[:3]
        )

        # Bookings this year
        year_data = (
            Booking.objects
            .filter(created_at__date__gte=first_day_year)
            .values('user__username')
            .annotate(bookings=Count('id'))
            .order_by('-bookings')[:3]
        )

        # Format for template
        top_month_users = [{'username': entry['user__username'], 'bookings': entry['bookings']} for entry in month_data]
        top_year_users = [{'username': entry['user__username'], 'bookings': entry['bookings']} for entry in year_data]

        if extra_context is None:
            extra_context = {}

        extra_context['top_month_users'] = top_month_users
        extra_context['top_year_users'] = top_year_users

        return super().changelist_view(request, extra_context=extra_context)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'full_name',
        'phone_number',
        'address',
    )
    search_fields = (
        'user__username',
        'full_name',
        'phone_number',
    )
