from django.urls import path
from .views import PlaceListCreateView, search_places, place_detail, OwnerPlacesAPIView, \
    PlaceDetailUpdateView, place_detail_page, CommentListCreateView, CommentCreateView, ReplyCreateView, delete_comment, \
    my_comments_view

app_name = 'place'
urlpatterns = [
    path('api/places/', PlaceListCreateView.as_view(), name='place-list-create'),
    path('api/places/<int:pk>/', PlaceDetailUpdateView.as_view(), name='api_place-detail'),
    path('api/places/<int:place_id>/comments/', CommentListCreateView.as_view(), name='place-comments'),
    path('api/comments/create/', CommentCreateView.as_view(), name='comment-create'),
    path('api/comments/<int:comment_id>/reply/', ReplyCreateView.as_view(), name='comment-reply'),
    path('api/user/comments/', my_comments_view),
    path('api/user/places/', OwnerPlacesAPIView.as_view(), name='owner-places'),
    path('places/<int:pk>/detail/', place_detail_page, name='update_place-detail-page'),
    path('place/<int:place_id>/', place_detail, name='place_detail'),
    path("search/", search_places, name="search_places"),
    path('api/comments/<int:comment_id>/delete/', delete_comment, name="delete_comment"),

]
