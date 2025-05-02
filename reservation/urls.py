from django.urls import path
from reservation.views import BookingListCreateView, BookingCalendarView, booking_calendar, booking_calendar_view, \
    booking_detail_view, FakePaymentSuccessView, payment_success, ReservationDetailView, reservation_detail_view, \
    download_reservation_pdf, UserBookingListView, DeleteUnpaidBookingView, RateBookingView, CancellationRequestView, \
    CancellationAdminView, CancelBookingFormView

app_name = 'reservation'
urlpatterns = [
    path('api/bookings/', BookingListCreateView.as_view(), name='booking-list-create'),
    path('api/places/<int:place_id>/calendar/', BookingCalendarView.as_view(), name='booking_calendar'),
    path("api/calendar/<int:place_id>/", booking_calendar, name="booking-calendar"),
    path("place/<int:place_id>/calendar/", booking_calendar_view, name="hotel-booking-calendar"),
    path("booking/<int:pk>/", booking_detail_view, name="booking-detail"),
    path('api/bookings/<int:booking_id>/payment-success/', FakePaymentSuccessView.as_view(),
         name='fake-payment-success'),
    path('booking/<int:booking_id>/success/', payment_success, name='payment-success'),
    path('api/reservation/<int:pk>/', ReservationDetailView.as_view(), name='api-reservation-detail'),
    path('api/user/bookings/', UserBookingListView.as_view(), name='user-bookings'),
    path('api/booking/<int:pk>/delete/', DeleteUnpaidBookingView.as_view(), name='booking-delete'),
    path('api/bookings/<int:booking_id>/rate/', RateBookingView.as_view(), name='rate-booking'),
    path('reservation/<int:pk>/', reservation_detail_view, name='reservation-detail'),
    path('reservation/<int:pk>/download/', download_reservation_pdf, name='download_reservation_pdf'),
    path('api/bookings/<int:booking_id>/cancel/', CancellationRequestView.as_view(), name='cancel-booking'),
    path('api/admin/cancellations/<int:cancellation_id>/', CancellationAdminView.as_view(), name='admin-cancellation'),
    path('booking/<int:booking_id>/cancel-form/', CancelBookingFormView.as_view(), name='cancel-booking-form'),

]
