from django.db import models

class News(models.Model):
    title = models.CharField(max_length=500, verbose_name='Заголовок')  # Увеличена длина
    content = models.TextField(blank=True, verbose_name='Содержание')
    source = models.CharField(max_length=255, verbose_name='Источник')  # Увеличена длина
    topic = models.CharField(max_length=255, verbose_name='Тема')   # Увеличена длина
    link = models.URLField(max_length=1000, verbose_name='Ссылка')  # Ограничение на длину URL остаётся
    published_date = models.CharField(max_length=100, verbose_name='Дата публикации')  # Храним дату как строку
    image_url = models.URLField(max_length=1000, blank=True, null=True, verbose_name='URL изображения')  # Добавляем поле для ссылки на изображение
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Новость'
        verbose_name_plural = 'Новости'
        ordering = ['-created_at']

    def __str__(self):
        return self.title
