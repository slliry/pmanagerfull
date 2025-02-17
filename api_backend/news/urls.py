from django.urls import path
from .views import NewsListAPIView, FetchNewsAPIView

urlpatterns = [
    path('', NewsListAPIView.as_view(), name='news_list_api'),
    path('fetch/', FetchNewsAPIView.as_view(), name='fetch_news_api'),
]