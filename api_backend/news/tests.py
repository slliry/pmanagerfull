from django.test import TestCase
from .models import News

class NewsModelTest(TestCase):
    def test_create_news(self):
        news = News.objects.create(
            title="Тестовая новость",
            content="Это тестовый контент",
            source="Dzen",
            topic="строительство",
            link="https://example.com/test-news"
        )
        self.assertEqual(str(news), "Тестовая новость")
        self.assertEqual(news.topic, "строительство")