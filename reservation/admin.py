from django.contrib import admin
from django.db.models import Sum
from datetime import date, timedelta
from reservation.models import Booking, DeletedReservation, CancellationRequest


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'place',
        'start_date',
        'end_date',
        'total_price',
        'is_paid',
        'is_cancelled',
        'rating',
        'created_at',
    )
    list_filter = (
        'is_paid',
        'is_cancelled',
        'start_date',
        'end_date',
        'created_at',
        'place',
        'place__owner'
    )
    search_fields = (
        'user__username',
        'user__email',
        'place__title',
        'stripe_session_id',
        'place__name'
    )
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'stripe_session_id', 'can_rate', 'rated_at', 'total_price')
    date_hierarchy = 'start_date'

    # Allow editing payment and cancellation status directly in list view
    list_editable = ('is_paid', 'is_cancelled')

    # Show this calculated property in admin
    def can_rate(self, obj):
        return obj.can_rate

    can_rate.boolean = True  # show as icon
    can_rate.short_description = "Can Rate?"

    # Optional: Add custom action
    actions = ['mark_as_paid', 'mark_as_cancelled']

    def mark_as_paid(self, request, queryset):
        updated = queryset.update(is_paid=True)
        self.message_user(request, f"{updated} bookings marked as paid.")

    mark_as_paid.short_description = "Mark selected bookings as paid"

    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(is_cancelled=True)
        self.message_user(request, f"{updated} bookings marked as cancelled.")

    mark_as_cancelled.short_description = "Mark selected bookings as cancelled"

    def changelist_view(self, request, extra_context=None):
        # This is only triggered when viewing the Booking admin changelist
        response = super().changelist_view(request, extra_context=extra_context)
        if hasattr(response, 'context_data') and 'cl' in response.context_data:
            queryset = response.context_data['cl'].queryset

            today = date.today()
            week_ago = today - timedelta(days=7)
            month_start = today.replace(day=1)

            income_today = queryset.filter(is_paid=True, start_date=today).aggregate(total=Sum("total_price"))[
                               "total"] or 0
            income_week = queryset.filter(is_paid=True, start_date__gte=week_ago).aggregate(total=Sum("total_price"))[
                              "total"] or 0
            income_month = \
            queryset.filter(is_paid=True, start_date__gte=month_start).aggregate(total=Sum("total_price"))["total"] or 0
            income_total = queryset.filter(is_paid=True).aggregate(total=Sum("total_price"))["total"] or 0

            response.context_data.update({
                "summary_daily_income": income_today,
                "summary_weekly_income": income_week,
                "summary_monthly_income": income_month,
                "summary_total_income": income_total,
            })

        return response


@admin.register(DeletedReservation)
class DeletedReservationAdmin(admin.ModelAdmin):
    list_display = (
        'reservation_id',
        'user',
        'hotel',
        'check_in',
        'check_out',
        'deleted_at',
    )
    list_filter = (
        'deleted_at',
        'hotel',
    )
    search_fields = (
        'reservation_id',
        'user',
        'hotel',
    )
    ordering = ('-deleted_at',)
    readonly_fields = (
        'reservation_id',
        'user',
        'hotel',
        'check_in',
        'check_out',
        'deleted_at',
    )

    def has_add_permission(self, request):
        return False  # Admin shouldn't manually add logs

    def has_change_permission(self, request, obj=None):
        return False  # Logs should not be editable


@admin.register(CancellationRequest)
class CancellationRequestAdmin(admin.ModelAdmin):
    list_display = (
        'booking_id',
        'get_user',
        'get_place',
        'status',
        'created_at',
        'processed_at',
        'processed_by',
        'refund_amount',
        'auto_approve',
    )
    list_filter = (
        'status',
        'created_at',
        'processed_by',
    )
    search_fields = (
        'booking__user__username',
        'booking__place__name',
    )
    readonly_fields = (
        'booking',
        'reason',
        'created_at',
        'get_refund_amount',
    )
    actions = ['approve_requests', 'reject_requests']

    def get_user(self, obj):
        return obj.booking.user.username

    get_user.short_description = "User"

    def get_place(self, obj):
        return obj.booking.place.name

    get_place.short_description = "Place"

    def refund_amount(self, obj):
        return f"{obj.get_refund_amount():.2f}"

    refund_amount.short_description = "Refund Amount"

    def auto_approve(self, obj):
        return obj.can_auto_approve()

    auto_approve.boolean = True
    auto_approve.short_description = "Auto Approve Eligible?"

    def approve_requests(self, request, queryset):
        count = queryset.update(status='approved')
        self.message_user(request, f"{count} cancellation requests approved.")

    approve_requests.short_description = "Approve selected cancellation requests"

    def reject_requests(self, request, queryset):
        count = queryset.update(status='rejected')
        self.message_user(request, f"{count} cancellation requests rejected.")

    reject_requests.short_description = "Reject selected cancellation requests"


