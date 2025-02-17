from django.contrib import admin
from .models import News

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'topic', 'source', 'created_at')
    search_fields = ('title', 'topic', 'source')
    list_filter = ('topic', 'source', 'created_at')
    def title(self, obj):
        return obj.title
    def topic(self, obj):
        return obj.topic
    def source(self, obj):
        return obj.source
    def created_at(self, obj):
        return obj.created_at
    title.short_description = 'Title'
    topic.short_description = 'Topic'
    source.short_description = 'Source'
    created_at.short_description = 'Created At'