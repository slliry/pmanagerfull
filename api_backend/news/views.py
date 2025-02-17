from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import News
from .serializers import NewsSerializer, CreateNewsSerializer
from .parsers import fetch_news_by_topic, normalize_url
from .sources import SOURCES

class NewsListAPIView(APIView):
    def get(self, request):
        news = News.objects.all()
        serializer = NewsSerializer(news, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = CreateNewsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class FetchNewsAPIView(APIView):
    def post(self, request):
        fetched_news = []
        for topic, sources in SOURCES.items():
            articles = fetch_news_by_topic(topic, sources)
            for article in articles:
                # Нормализуем ссылку перед проверкой
                article["link"] = normalize_url(article["link"])

                # Ищем новость по ссылке
                news = News.objects.filter(link=article["link"]).first()

                if news:
                    # Проверяем, изменилась ли дата публикации или другие поля
                    if (news.published_date != article["published_date"] or
                        news.title != article["title"] or
                        news.content != article.get("description", "") or
                        news.image_url != article.get("image_url", "")):
                        
                        news.published_date = article["published_date"]
                        news.title = article["title"]
                        news.content = article.get("description", "")
                        news.image_url = article.get("image_url", "")
                        news.save()
                        print(f"Обновлена новость для ссылки {article['link']}")
                else:
                    # Создаём новую запись
                    news = News.objects.create(
                        title=article["title"],
                        content=article.get("description", ""),
                        source=article["source"],
                        topic=article["topic"],
                        link=article["link"],
                        published_date=article["published_date"],
                        image_url=article.get("image_url", "")
                    )
                fetched_news.append(news)

        serializer = NewsSerializer(fetched_news, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
