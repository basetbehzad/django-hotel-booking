from rest_framework.permissions import BasePermission
from reservation.models import Booking


class HasBookedPlace(BasePermission):
    def has_permission(self, request, view):
        place_id = request.data.get('place') or view.kwargs.get('place_id')
        if not place_id:
            return False
        return Booking.objects.filter(user=request.user, place_id=place_id, is_paid=True).exists()
