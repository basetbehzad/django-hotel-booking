from django.contrib import admin
from django.db.models import Count
from django.utils.timezone import now
from place.models import Place, Comment
from reservation.models import Booking


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'owner',
        'category',
        'price_per_night',
        'is_verified',
        'is_active',
        'average_rating',
        'created_at',
    )
    list_filter = (
        'category',
        'is_verified',
        'is_active',
        'created_at',
    )
    search_fields = (
        'name',
        'owner__username',
        'owner__email',
        'address',
    )
    readonly_fields = (
        'created_at',
        'average_rating',
    )
    list_editable = (
        'is_verified',
        'is_active',
    )
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    fieldsets = (
        (None, {
            'fields': (
                'owner',
                'name',
                'description',
                'category',
                'address',
                ('num_rooms', 'num_persons'),
                'price_per_night',
                'amenities',
            )
        }),
        ('Status & Meta', {
            'fields': (
                'is_verified',
                'is_active',
                'average_rating',
                'created_at',
            )
        }),
    )

    actions = ['verify_places', 'deactivate_places']

    def verify_places(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f"{updated} places verified.")

    verify_places.short_description = "Mark selected places as verified"

    def deactivate_places(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} places deactivated.")

    deactivate_places.short_description = "Deactivate selected places"

    def changelist_view(self, request, extra_context=None):
        today = now().date()
        first_day_month = today.replace(day=1)
        first_day_year = today.replace(month=1, day=1)

        # Monthly top 3 places
        month_data = (
            Booking.objects
            .filter(created_at__date__gte=first_day_month)
            .values('place__name')
            .annotate(bookings=Count('id'))
            .order_by('-bookings')[:3]
        )

        # Yearly top 3 places
        year_data = (
            Booking.objects
            .filter(created_at__date__gte=first_day_year)
            .values('place__name')
            .annotate(bookings=Count('id'))
            .order_by('-bookings')[:3]
        )

        # Format for template
        top_month_places = [{'name': entry['place__name'], 'bookings': entry['bookings']} for entry in month_data]
        top_year_places = [{'name': entry['place__name'], 'bookings': entry['bookings']} for entry in year_data]

        if extra_context is None:
            extra_context = {}

        extra_context['top_month_places'] = top_month_places
        extra_context['top_year_places'] = top_year_places

        return super().changelist_view(request, extra_context=extra_context)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'place',
        'short_content',
        'is_reply',
        'created_at',
    )
    list_filter = (
        'created_at',
        'place',
    )
    search_fields = (
        'user__username',
        'place__name',
        'content',
    )
    ordering = ('-created_at',)
    list_select_related = ('user', 'place', 'parent')
    readonly_fields = ('created_at',)

    def short_content(self, obj):
        return (obj.content[:50] + '...') if len(obj.content) > 50 else obj.content

    short_content.short_description = 'Content'

    def is_reply(self, obj):
        return obj.parent is not None

    is_reply.boolean = True
    is_reply.short_description = 'Is Reply?'

    def has_add_permission(self, request):
        return False  # Comments should be added via the app
