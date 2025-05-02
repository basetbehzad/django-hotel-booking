from rest_framework import serializers
from .models import Place, Comment


class PlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Place
        fields = ['id', 'name', 'description', 'average_rating', 'address', 'price_per_night', 'is_active']
        read_only_fields = ['id', 'is_verified']


class PlaceListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Place
        fields = ['id', 'name', 'created_at', 'is_verified', 'is_active']


class CommentSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    replies = serializers.SerializerMethodField()
    place_name = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'user', 'place', 'place_name', 'content', 'parent', 'created_at', 'replies']

    def get_replies(self, obj):
        # Nested replies (up to your desired depth)
        replies = obj.replies.all()
        return CommentSerializer(replies, many=True, context=self.context).data

    def get_place_name(self, obj):
        return obj.place.name if obj.place else None


class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['content', 'place']
