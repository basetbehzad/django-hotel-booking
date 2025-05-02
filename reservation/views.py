from datetime import timedelta, datetime

from django.db.models import Q
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.views.generic import TemplateView
from rest_framework.decorators import api_view, permission_classes
from rest_framework import generics, permissions, status
from rest_framework.generics import DestroyAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from rest_framework.response import Response
from place.models import Place
from reservation.models import Booking, CancellationRequest
from reservation.serializers import BookingSerializer, BookingCalendarSerializer, BookingDetailSerializer, \
    BookingListSerializer, BookingRatingSerializer, CancellationRequestSerializer, CancellationCreateSerializer
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound
from django.urls import reverse
from django.http import HttpResponse, Http404
from django.template.loader import render_to_string
import pdfkit
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class BookingListCreateView(generics.ListCreateAPIView):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Returns only non-cancelled bookings for the current user
        with optimized database queries
        """
        return (
            Booking.objects
            .filter(user=self.request.user)
            .filter(
                Q(cancellation_request__isnull=True) |  # No cancellation request
                ~Q(cancellation_request__status='approved')  # Or not approved
            )
            .select_related('place', 'cancellation_request')
            .order_by('-start_date')
        )

    def create(self, request, *args, **kwargs):
        try:
            place = Place.objects.get(id=request.data.get("place"))
        except Place.DoesNotExist:
            raise ValidationError({"place": "Place not found"})

        if not place.is_active:
            return Response(
                {"error": "This place is currently inactive for booking."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        start_date = serializer.validated_data['start_date']
        end_date = serializer.validated_data['end_date']
        nights = (end_date - start_date).days
        total_price = nights * place.price_per_night

        booking = serializer.save(
            user=request.user,
            total_price=total_price,
            place=place
        )

        return Response(
            BookingSerializer(booking).data,
            status=status.HTTP_201_CREATED
        )


class BookingCalendarView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, place_id):
        bookings = Booking.objects.filter(place_id=place_id)

        paid_dates = []
        pending_dates = []

        for booking in bookings:
            current_date = booking.start_date
            while current_date <= booking.end_date:
                date_str = current_date.strftime("%Y-%m-%d")
                if booking.is_paid:
                    paid_dates.append(date_str)
                else:
                    pending_dates.append(date_str)
                current_date += timedelta(days=1)

        return Response({
            "paid_dates": paid_dates,
            "pending_dates": pending_dates
        })


@api_view(["GET"])
@permission_classes([AllowAny])
def booking_calendar(request, place_id):
    bookings = Booking.objects.filter(place_id=place_id)
    serializer = BookingCalendarSerializer(bookings, many=True)

    paid_dates = []
    pending_dates = []

    for booking in serializer.data:
        start_date_str = booking["start_date"]
        end_date_str = booking["end_date"]
        is_paid = booking["is_paid"]

        # Convert strings to datetime objects
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

        current = start_date
        while current <= end_date:
            date_str = current.strftime('%Y-%m-%d')
            if is_paid:
                paid_dates.append(date_str)
            else:
                pending_dates.append(date_str)
            current += timedelta(days=1)

    return Response({
        "paid_dates": paid_dates,
        "pending_dates": pending_dates
    })


def booking_calendar_view(request, place_id):
    """
    Renders the booking calendar page for a specific hotel.
    """
    place = get_object_or_404(Place, id=place_id)  # Ensure the hotel exists
    return render(request, "calendar.html", {"place": place})


class FakePaymentSuccessView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, booking_id):
        booking = get_object_or_404(Booking, id=booking_id, user=request.user)
        booking.is_paid = True
        booking.save()

        return Response({
            'success': True,
            'redirect_url': reverse(
                'reservation:payment-success',
                kwargs={'booking_id': booking.id}
            )
        }, status=200)


def payment_success(request, booking_id):
    try:
        booking = Booking.objects.get(id=booking_id, user=request.user)
    except Booking.DoesNotExist:
        raise Http404("Booking does not exist or you don't have permission")

    return render(request, 'payment_success.html', {
        'booking_id': booking.id,
        'reservation_detail_url': reverse(
            'reservation:reservation-detail',
            kwargs={'pk': booking.id}
        )
    })


def booking_detail_view(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    return render(request, 'booking_detail.html', {'booking': booking})


class ReservationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        booking = get_object_or_404(Booking, id=pk, user=request.user)
        serializer = BookingDetailSerializer(booking)
        return Response(serializer.data)


def reservation_detail_view(request, pk):
    booking = get_object_or_404(Booking, id=pk, user=request.user)
    return render(request, 'reservation_detail.html', {'booking': booking})


def download_reservation_pdf(request, pk):
    booking = get_object_or_404(Booking, id=pk, user=request.user)

    # Render HTML template
    html_string = render_to_string('reservation_pdf.html', {
        'booking': booking,
        'STATIC_URL': settings.STATIC_URL,  # If you need static files
    })

    # PDF options
    options = {
        'page-size': 'A4',
        'margin-top': '0.5in',
        'margin-right': '0.5in',
        'margin-bottom': '0.5in',
        'margin-left': '0.5in',
        'encoding': "UTF-8",
        'quiet': '',
        'no-outline': None,
        'enable-local-file-access': '',  # Required to access local files
    }

    # Configure path to wkhtmltopdf
    # IMPORTANT: Adjust this path to where you installed wkhtmltopdf
    wkhtmltopdf_path = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'

    try:
        # Generate PDF
        pdf = pdfkit.from_string(
            html_string,
            False,
            options=options,
            configuration=pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
        )

        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Reservation_{booking.id}.pdf"'
        return response

    except Exception as e:
        logger.error(f"PDF generation error: {str(e)}")
        return HttpResponse(
            "Error generating PDF. Please try again later.",
            status=500
        )


class UserBookingListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        bookings = Booking.objects.filter(user=request.user).select_related('place')
        serializer = BookingListSerializer(bookings, many=True)
        return Response(serializer.data)


class DeleteUnpaidBookingView(DestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Booking.objects.all()

    def delete(self, request, *args, **kwargs):
        booking = self.get_object()
        if booking.user != request.user:
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        if booking.is_paid:
            return Response({'detail': 'Cannot delete paid bookings'}, status=status.HTTP_400_BAD_REQUEST)
        return super().delete(request, *args, **kwargs)


class RateBookingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, booking_id):
        booking = get_object_or_404(Booking, id=booking_id, user=request.user)

        if not booking.can_rate:
            return Response(
                {"detail": "This booking cannot be rated."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = BookingRatingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        booking.rating = serializer.validated_data['rating']
        booking.rated_at = timezone.now()
        booking.save()

        place = booking.place
        place.update_average_rating()

        return Response({
            "status": "success",
            "rating": booking.rating,
            "rated_at": booking.rated_at
        })


class CancellationRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, booking_id):
        booking = get_object_or_404(Booking, id=booking_id, user=request.user)

        # Check if cancellation is allowed
        if booking.start_date <= timezone.now().date():
            return Response(
                {"detail": "Cancellation is not allowed after stay has started."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if hasattr(booking, 'cancellation_request'):
            return Response(
                {"detail": "Cancellation request already exists for this booking."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = CancellationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cancellation = serializer.save(booking=booking)

        # Auto-approve if conditions are met
        if cancellation.can_auto_approve():
            cancellation.status = 'approved'
            cancellation.processed_at = timezone.now()
            cancellation.save()

        return Response(CancellationRequestSerializer(cancellation).data)


class CancellationAdminView(APIView):
    permission_classes = [IsAdminUser]

    def patch(self, request, cancellation_id):
        cancellation = get_object_or_404(CancellationRequest, id=cancellation_id)
        action = request.data.get('action')

        if action == 'approve':
            cancellation.status = 'approved'
        elif action == 'reject':
            cancellation.status = 'rejected'
        elif action == 'refund':
            cancellation.status = 'refunded'
        else:
            return Response(
                {"detail": "Invalid action"},
                status=status.HTTP_400_BAD_REQUEST
            )

        cancellation.processed_at = timezone.now()
        cancellation.processed_by = request.user
        cancellation.save()

        return Response(CancellationRequestSerializer(cancellation).data)


class CancelBookingFormView(TemplateView):
    template_name = 'cancel_form.html'
    permission_classes = [IsAuthenticated]

    def get_context_data(self, **kwargs):
        print(f"User {self.request.user.id} attempting to access booking {self.kwargs['booking_id']}")
        context = super().get_context_data(**kwargs)
        booking = get_object_or_404(
            Booking,
            id=self.kwargs['booking_id'],
            user=self.request.user
        )

        context['booking'] = {
            'place_name': booking.place.name,
            'start_date': booking.start_date.strftime('%Y-%m-%d'),
            'end_date': booking.end_date.strftime('%Y-%m-%d'),
            'total_price': str(booking.total_price),
            'id': booking.id
        }
        context['cancel_url'] = reverse('reservation:cancel-booking', kwargs={'booking_id': booking.id})
        return context

    def post(self, request, *args, **kwargs):
        # This handles form submission directly if needed
        booking_id = self.kwargs['booking_id']
        return redirect(reverse('cancel-booking', kwargs={'booking_id': booking_id}))
