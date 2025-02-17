SOURCES = {
    "строительство": {
        "Dzen": "https://dzen.ru/topic/stroitelstvo?tab=articles",
    },
    "архитектура": {
        "Dzen": "https://dzen.ru/topic/arhitektura?tab=articles",
        "Archdaily": "https://archdaily.ru/?bpage=1&bcpp=12#wbb1",  # Селекторы для парсинга:
                                                                     # - заголовок: span.description
                                                                     # - дата: span.date[data-timestamp]
                                                                     # - ссылка: a.wb-blog-item[href]
                                                                     # - картинка: div.blog-item-thumbnail[style]
    },
}
