from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login
from rest_framework_simplejwt.tokens import RefreshToken

from place.models import Place
from reservation.models import Booking, CancellationRequest
from .serializers import UserRegisterSerializer, UserProfileSerializer
from django.contrib.auth import get_user_model
from django.views.generic import TemplateView
from django.db.models import Sum, Q
from datetime import datetime, timedelta
from calendar import month_name

User = get_user_model()


class RegisterUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer


class SessionLoginView(APIView):
    authentication_classes = []  # Disable JWT auth for this endpoint
    permission_classes = []

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return Response({'status': 'success'}, status=status.HTTP_200_OK)

        return Response(
            {'detail': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response({"detail": "Logout successful."}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"error": "Invalid token or already blacklisted."}, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class ProfilePageView(TemplateView):
    template_name = 'profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['cancellations'] = CancellationRequest.objects.filter(
                booking__user=self.request.user
            )
        return context


class OwnerIncomeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        places = Place.objects.filter(owner=user)
        today = datetime.now().date()

        # Current month and year for monthly calculations
        current_month = today.month
        current_year = today.year

        # Helper function to filter bookings
        def filter_bookings(queryset, start_date=None, end_date=None):
            qs = queryset.filter(
                place__in=places,
                is_paid=True
            )
            if start_date:
                qs = qs.filter(start_date__gte=start_date)
            if end_date:
                qs = qs.filter(start_date__lte=end_date)
            return qs

        # Total Income Calculations
        ## Daily - today only
        total_daily = filter_bookings(
            Booking.objects,
            start_date=today,
            end_date=today
        ).aggregate(total=Sum('total_price'))['total'] or 0

        ## Weekly - last 7 days including today
        weekly_start = today - timedelta(days=6)
        total_weekly = filter_bookings(
            Booking.objects,
            start_date=weekly_start,
            end_date=today
        ).aggregate(total=Sum('total_price'))['total'] or 0

        ## Monthly - current month only
        first_day_of_month = today.replace(day=1)
        last_day_of_month = today.replace(day=28) + timedelta(days=4)  # Handle all months
        last_day_of_month = last_day_of_month - timedelta(days=last_day_of_month.day)

        total_monthly = filter_bookings(
            Booking.objects,
            start_date=first_day_of_month,
            end_date=last_day_of_month
        ).aggregate(total=Sum('total_price'))['total'] or 0

        # Per-Place Earnings
        place_earnings = []
        for place in places:
            # Daily income for this place (today only)
            daily_income = filter_bookings(
                place.bookings.all(),
                start_date=today,
                end_date=today
            ).aggregate(total=Sum('total_price'))['total'] or 0

            # Weekly income for this place (last 7 days)
            weekly_income = filter_bookings(
                place.bookings.all(),
                start_date=weekly_start,
                end_date=today
            ).aggregate(total=Sum('total_price'))['total'] or 0

            # Monthly income for this place (current month)
            monthly_income = filter_bookings(
                place.bookings.all(),
                start_date=first_day_of_month,
                end_date=last_day_of_month
            ).aggregate(total=Sum('total_price'))['total'] or 0

            place_earnings.append({
                "place_id": place.id,
                "place_name": place.name,
                "daily_income": daily_income,
                "weekly_income": weekly_income,
                "monthly_income": monthly_income,
                "month_name": month_name[current_month]  # Add month name
            })

        return Response({
            "total_income": {
                "daily": total_daily,
                "weekly": total_weekly,
                "monthly": total_monthly,
                "month_name": month_name[current_month]
            },
            "place_incomes": place_earnings
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    return Response({
        "id": request.user.id,
        "username": request.user.username,
        "email": request.user.email
    })