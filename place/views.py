from rest_framework import generics, permissions, filters, status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from reservation.models import Booking
from .permissions import HasBookedPlace
from .serializers import PlaceSerializer, PlaceListSerializer, CommentSerializer, CommentCreateSerializer
from django.shortcuts import render, get_object_or_404
from .models import Place, Comment
from .forms import PlaceSearchForm


class PlaceListCreateView(generics.ListCreateAPIView):
    """
    List all verified and active places (GET)
    Allow authenticated hotel owners to create a place (POST)
    """
    queryset = Place.objects.filter(is_active=True, is_verified=True)
    serializer_class = PlaceSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ["category", "price_per_night", "num_persons"]
    ordering_fields = ["price_per_night", "num_rooms", "num_persons"]
    ordering = ["-id"]  # Default sorting (latest places)
    search_fields = ["name", "description", "address"]

    def perform_create(self, serializer):
        """Allow only authenticated hotel owners to create a place"""
        if self.request.user.role != "owner":
            raise PermissionError("Only hotel owners can create places")
        serializer.save(owner=self.request.user)


class CommentListCreateView(generics.ListCreateAPIView):
    queryset = Comment.objects.filter(parent=None)
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, HasBookedPlace]

    def get_queryset(self):
        place_id = self.kwargs['place_id']
        return Comment.objects.filter(place_id=place_id, parent=None).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CommentCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CommentCreateSerializer(data=request.data)
        if serializer.is_valid():
            place = serializer.validated_data['place']
            user = request.user

            # Check if user has paid booking for this place
            has_booked = Booking.objects.filter(user=user, place=place, is_paid=True).exists()
            if not has_booked:
                return Response({'detail': 'You must have booked this place to comment.'},
                                status=status.HTTP_403_FORBIDDEN)

            Comment.objects.create(
                user=user,
                place=place,
                content=serializer.validated_data['content']
            )
            return Response({'detail': 'Comment created.'}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReplyCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, comment_id):
        parent_comment = get_object_or_404(Comment, id=comment_id)
        user = request.user
        place = parent_comment.place

        # Check if user has a booking for the same place
        has_booked = Booking.objects.filter(user=user, place=place, is_paid=True).exists()
        if not has_booked:
            return Response({'detail': 'You must have booked this place to reply.'},
                            status=status.HTTP_403_FORBIDDEN)

        content = request.data.get('content')
        if not content:
            return Response({'detail': 'Content is required.'}, status=status.HTTP_400_BAD_REQUEST)

        Comment.objects.create(
            user=user,
            place=place,
            content=content,
            parent=parent_comment
        )
        return Response({'detail': 'Reply created.'}, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_comment(request, comment_id):
    try:
        comment = Comment.objects.get(id=comment_id, user=request.user)
        comment.delete()
        return Response({"message": "Deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
    except Comment.DoesNotExist:
        return Response({"error": "You can only delete your own comments."}, status=status.HTTP_403_FORBIDDEN)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_comments_view(request):
    user = request.user
    comments = Comment.objects.filter(user=user).select_related('place')
    serializer = CommentSerializer(comments, many=True, context={'request': request})
    return Response(serializer.data)


class PlaceDetailUpdateView(generics.RetrieveUpdateDestroyAPIView):
    """Allow hotel owners to view and update their own place"""
    queryset = Place.objects.all()
    serializer_class = PlaceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        place = super().get_object()
        if self.request.user != place.owner:
            raise PermissionDenied("You are not the owner of this place.")
        return place

    def delete(self, request, *args, **kwargs):
        place = self.get_object()
        if place.bookings.filter(is_paid=True).exists():
            return Response({"error": "Cannot delete place with paid bookings."}, status=400)
        return super().delete(request, *args, **kwargs)


def place_detail(request, place_id):
    place = get_object_or_404(Place, id=place_id)
    return render(request, 'place_detail.html', {'place': place})


def search_places(request):
    form = PlaceSearchForm(request.GET)  # Bind form with query parameters
    places = Place.objects.filter(is_active=True, is_verified=True)

    if form.is_valid():
        name = form.cleaned_data.get('name')
        category = form.cleaned_data.get('category')
        address = form.cleaned_data.get('address')
        min_price = form.cleaned_data.get('min_price')
        max_price = form.cleaned_data.get('max_price')
        amenities = form.cleaned_data.get('amenities')

        if name:
            places = places.filter(name__icontains=name)
        if category:
            places = places.filter(category=category)
        if address:
            places = places.filter(address__icontains=address)
        if min_price is not None:
            places = places.filter(price_per_night__gte=min_price)
        if max_price is not None:
            places = places.filter(price_per_night__lte=max_price)
        if amenities:
            for amenity in amenities:
                places = places.filter(amenities__icontains=amenity)

    return render(request, "search.html", {"form": form, "places": places})


class OwnerPlacesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'owner':
            return Response({'detail': 'Only hotel owners can access this data.'}, status=status.HTTP_403_FORBIDDEN)

        places = Place.objects.filter(owner=request.user)
        serializer = PlaceListSerializer(places, many=True)
        return Response(serializer.data)


def place_detail_page(request, pk):
    return render(request, 'update_place_detail.html')





