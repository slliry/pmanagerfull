from rest_framework import serializers
from .models import News

class NewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        fields = ['id', 'title', 'content', 'source', 'topic', 'link', 'created_at', 'published_date', 'image_url']

class CreateNewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        fields = ['title', 'content', 'source', 'topic', 'link', 'published_date', 'image_url']