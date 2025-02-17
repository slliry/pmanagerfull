import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urlunparse
import re

def normalize_url(url):
    """
    Преобразует ссылку в нормализованный вид (без параметров и лишних данных).
    """
    parsed = urlparse(url)
    # Оставляем только основные части URL (протокол, хост, путь)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))

def parse_dzen_with_pagination(base_url):
    """
    Парсинг Dzen с поддержкой пагинации.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36"
    }
    articles = []
    seen_links = set()  # Хранилище для проверки уникальности ссылок
    page = 1

    while True:
        # Формируем URL для текущей страницы
        url = f"{base_url}&page={page}"
        print(f"Запрос к {url}")  # Отладка

        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Ошибка при подключении к {url}, статус {response.status_code}")
            break

        soup = BeautifulSoup(response.content, 'html.parser')

        # Парсим текущую страницу
        links = soup.select('a[data-testid="card-article-link"]')
        titles = soup.select('div[data-testid="card-article-title"]')
        descriptions = soup.select('div[data-testid="card-part-description"]')
        dates = soup.select('div.desktop2--meta__meta-3m span')

        if not links:  # Если статей больше нет, прекращаем
            print("Статьи закончились.")
            break

        page_articles = []  # Список для статей текущей страницы

        for link, title, description, date in zip(links, titles, descriptions, dates):
            link_url = link.get("href")
            if link_url and not link_url.startswith("http"):
                link_url = "https://dzen.ru" + link_url

            # Нормализуем ссылку и проверяем, была ли она уже обработана
            link_url = normalize_url(link_url)
            if link_url in seen_links:
                print(f"Повторяющаяся ссылка: {link_url}, пропускаем.")
                continue

            seen_links.add(link_url)  # Добавляем в множество обработанных ссылок

            title_text = title.get_text(strip=True) if title else "Без заголовка"
            description_text = description.get_text(strip=True) if description else "Без описания"
            published_date = date.get_text(strip=True) if date else "Без даты"

            page_articles.append({
                "title": title_text,
                "description": description_text,
                "link": link_url,
                "published_date": published_date,
            })

        if not page_articles:  # Если на странице ничего нового, прекращаем
            print(f"На странице {page} нет новых статей. Завершаем.")
            break

        articles.extend(page_articles)
        page += 1

    return articles

def parse_archdaily_with_pagination(base_url, max_pages=2):
    """
    Функция парсинга страницы Archdaily с поддержкой пагинации.
    Args:
        base_url: Базовый URL для парсинга
        max_pages: Максимальное количество страниц для парсинга
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36"
    }
    all_articles = []
    
    # Получаем базовый URL без параметров
    base_url = 'https://archdaily.ru/'

    for page in range(1, max_pages + 1):
        # Формируем URL для текущей страницы
        current_url = f"{base_url}?bpage={page}&bcpp=12#wbb1"
        print(f"Парсинг страницы {page}: {current_url}")
        
        try:
            response = requests.get(current_url, headers=headers)
            response.raise_for_status()  # Проверяем статус ответа
            
            soup = BeautifulSoup(response.content, 'html.parser')
            items = soup.select('a.wb-blog-item')
            
            if not items:
                print(f"Статьи не найдены на странице {page}")
                break
                
            for item in items:
                # Извлекаем заголовок
                title_elem = item.select_one('span.description')
                title = title_elem.get_text(strip=True) if title_elem else "Без заголовка"
                
                # Извлекаем дату
                date_elem = item.select_one('span.date[data-timestamp]')
                published_date = date_elem.get('data-timestamp') if date_elem else "Без даты"
                
                # Получаем ссылку
                link_url = item.get('href')
                if link_url and not link_url.startswith('http'):
                    link_url = 'https://archdaily.ru' + link_url
                    
                # Получаем ссылку на изображение
                img_elem = item.select_one('div.blog-item-thumbnail')
                img_url = ''
                if img_elem and 'style' in img_elem.attrs:
                    style = img_elem['style']
                    img_match = re.search(r"url\('([^']+)'\)", style)
                    if img_match:
                        img_url = img_match.group(1)
                        if not img_url.startswith('http'):
                            img_url = 'https://archdaily.ru/' + img_url.lstrip('/')

                all_articles.append({
                    "title": title,
                    "description": title,  # Используем заголовок как описание
                    "link": link_url,
                    "published_date": published_date,
                    "image_url": img_url
                })
                
        except Exception as e:
            print(f"Ошибка при парсинге страницы {page}: {str(e)}")
            break
            
    return all_articles

def parse_archdaily(url):
    """
    Функция парсинга страницы Archdaily с извлечением ссылок, заголовков и дат публикации.
    """
    return parse_archdaily_with_pagination(url)

def fetch_news_by_topic(topic, sources):
    """
    Парсинг новостей по всем источникам для заданной темы.
    """
    all_articles = []
    for source, url in sources.items():
        articles = []
        if source == "Dzen":
            articles = parse_dzen_with_pagination(url)  # Возвращаем пагинацию для Dzen
        elif source == "Archdaily":
            articles = parse_archdaily(url)  # Этот парсер уже включает пагинацию
            
        for article in articles:
            article["source"] = source
            article["topic"] = topic
            all_articles.append(article)
    return all_articles
