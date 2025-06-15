import os
import threading
import time

from typing import Optional

import pandas as pd
import requests

from bs4 import BeautifulSoup
import json

from g4f.client import Client
from g4f.Provider import (OpenaiChat, Blackbox, Yqcloud,
                          DeepInfra, FreeGpt,
                          WeWordle, PollinationsAI, Copilot)
from g4f.providers.retry_provider import IterListProvider

from concurrent.futures import ThreadPoolExecutor
from threading import Lock

file_lock = Lock()

MAX_ALLOWED_URLS = 4

selectors = {
    'title': {'class_': ['product-card__title title-sm']},
    'brand': {'class_': ['product-card__prod-value']},
    'country': {'class_': ['product-card__prod-value d-flex align-items-center gap-1 color-gray']},
    'article': {'class_': ['product-card__articul-value color-gray']},
}


def parse(soup: BeautifulSoup) -> Optional[dict]:
    try:
        title_elem = soup.find(**selectors['title'])
        brand_elem = soup.find(**selectors['brand'])
        country_elem = soup.find(**selectors['country'])
        article_elem = soup.find(**selectors['article'])

        if not all([title_elem, brand_elem, country_elem, article_elem]):
            print("Не все обязательные элементы найдены на странице")
            return None

        data = {
            'title': title_elem.get_text(strip=True) if title_elem else '',
            'brand': brand_elem.get_text(strip=True) if brand_elem else '',
            'country': country_elem.get_text(strip=True) if country_elem else '',
            'article': article_elem.get_text(strip=True) if article_elem else '',
            'meta_title': f'Купить {title_elem.get_text(strip=True)} | Dental First' if title_elem else '',
            'meta_description': f'{title_elem.get_text(strip=True)} в интернет-магазине Dental First. Каталог включает '
                                f'стоматологические товары в широком диапазоне цен. Помощь специалистов, быстрая '
                                f'доставка по всей России.| Dental First' if title_elem else ''
        }
        return data

    except Exception as e:
        print(f"Ошибка при парсинге: {e}")
        return None


# Отдельная функция парсинга описания товара
def description(soup: BeautifulSoup) -> Optional[dict]:
    data = soup.find_all('div', itemprop='description')
    base_desc = detail_desc = ''  # начальное описание товара
    base_desc_finish = False  # начальное описание пока не заполнено
    for paragraphs in data:
        for item in paragraphs.find_all(['p', 'h2', 'ol', 'ul']):
            if ('vadim-p' not in item.get('class', [])
                    and not base_desc_finish
                    and len(base_desc) > 0):
                base_desc, base_desc_finish = base_desc + '\n', True
            if base_desc_finish == False and 'vadim-p' in item.get('class', []):
                base_desc += item.text + '\n'
            else:
                if any(cls in item.get('class', []) for cls in ('vadim-p', 'vadim-h2')):
                    detail_desc += '#' + item.text + '\n' if item.name == 'h2' else item.text + '\n'
                elif item.name == 'ol':
                    for li in item.find_all('li'):
                        detail_desc += li.text + '\n'
                elif item.name == 'h2' and 'vadim-h2-green' in item.get('class', []):
                    detail_desc += '#' + item.text + '\n'
                elif item.name == 'ul' and "komplekt" in item.get('class', []):
                    for li in item.find_all('li'):
                        detail_desc += li.text + '\n'
    data = {'base_desc': base_desc, 'detail_desc': detail_desc}
    return data

# Генерация уникального текста на основе
def generate_uniq_text(base_data: dict, detail_data: dict) -> Optional[str]:

# Специальная переменная, показывающая итог выполнения функции в условиях лимита времени
    result = [None]

    try:
        def worker():
            try:
                prompt = ('Нужно сгенерировать новый текст о товаре за счет перефразирования исходного текста'
                          ' и новых добавлений в текст. Генерироваться текст должен на основе следующих пунктов:\n'
                          f'1. Если возможно, необходимо переформулировать это название товара: {base_data["title"]}. Требования:\n'
                          '- новое название не должно превышать 65 символов;\n'
                          '- из названия должны быть убраны несущественные знаки.\n'
                          f'2. Существенно изменить это базовое описание товара: {detail_data["base_desc"]}. Требование: '
                          'количество символов в новом описании должно быть в пределах 120-320 символов\n'
                          f'3. Существенно изменить это детализированное описание товара: {detail_data["detail_desc"]}\n. '
                          'Требования:\n'
                          '- описание должно иметь ту же структуру, то есть заглавие абзаца со знаком "#" спереди и ниже '
                          'его текст;\n'
                          '- заглавия абзацев желательно тоже перефразировать;\n'
                          '- можно изменить количество абзацев, то есть объединить по смыслу или наоборот разделить. Например, если'
                          ' в старом варианте были абзацы "Подготовка к работе" и "Подключение", то в новом варианте их можно '
                          'соединить в один абзац "Подготовка перед использованием". Или если в старом варианте был один абзац '
                          '"Хранение и транспортирование", то в новом варианте можно разделить на два отдельных абзаца.\n'
                          '4. Сгенерировать краткий слоган применительно к данному товару\n'
                          '5. Сгенерировать не более 10 ключевых слов, относящиеся к товару. Требования:\n'
                          '- ключевые слова должны опираться на статистику https://wordstat.yandex.ru;'
                          '- игнорировать ключевые слова на подобии "купить", "в стоматологии"\n\n'
                          'В результате ты мне должен выдать ответ в JSON-формате, чтобы я мог его преобразовать в словарь. '
                          'Твой ответ должен быть только в JSON-формате без каких-либо обрамляющих символов или '
                          'Markdown-разметки. Строго соблюдай синтаксис JSON: все строки в кавычках, запятые между полями, '
                          'экранируй специальные символы. Не добавляй никакого текста кроме JSON. '
                          'JSON-формат должен быть следующий:\n'
                          '{"title": <новое сгенерированное название>, '
                          '"base_desc": <новое базовое описание товара>,'
                          '"detail_desc": <новое детальное описание товара>,'
                          '"short": <краткий слоган товара>,'
                          '"keywords": <ключевые слова через запятую>}')
                client = Client()

                new_text = client.chat.completions.create(
                    model='gpt-4',
                    messages=[{'role': 'user', 'content': prompt}],
                    web_search=False,

                    # Порядок вызова AI от более стабильных и надежных к менее надежным
                    best_provider=IterListProvider([
                        OpenaiChat, Blackbox, Yqcloud,  # более надежные AI
                        # DeepInfra, FreeGpt,  # менее надежные
                        # WeWordle, PollinationsAI, Copilot  # крайний вариант
                    ]),
                    timeout=5,
                )
                result[0] = new_text.choices[0].message.content
            except:  # дополнительная перестраховка, если что-то пойдет не так (но возможно лишнее)
                pass

        thread = threading.Thread(target=worker)
        thread.start()
        thread.join(25)  # общее время на выполнение операции 25 сек
        if thread.is_alive():
            print('Превышено ожидаемое время работы нейросети')
            return None
        return result[0]
    except Exception as e:
        print(f'Ошибка подключения к нейросети: {e}')
    return None


def safe_save_to_excel(table_data):
    with file_lock:
        try:
            if os.path.exists('products.xlsx'):
                df = pd.read_excel('products.xlsx')
            else:
                df = pd.DataFrame()

            df = pd.concat([df, pd.DataFrame(table_data)], ignore_index=True)
            df.to_excel('products.xlsx', index=False)
        except Exception as e:
            print(f"Ошибка сохранения: {e}")


def script(url: str):
    try:
        print(f'Начата обработка: {url}')
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        base_data, detail_data = parse(soup), description(soup)
        text = generate_uniq_text(base_data, detail_data)
        dct_AI = json.loads(text)

        table_data = {
            'URL': url,
            'DF Номенклатура': [dct_AI['title']],
            'Бренд': [base_data['brand']],
            'Страна': [base_data['country']],
            'DF Артикул': [base_data['article']],
            'DF META TITLE': [base_data['meta_title']],
            'DF KEYWORDS': [dct_AI['keywords']],
            'DF Meta Description': [base_data['meta_description']],
            'DF <h2>': [dct_AI['short']],
            'DF верхнее описание': [dct_AI['base_desc']],
            'DF основное описание': [dct_AI['detail_desc']]
        }

        safe_save_to_excel(table_data)
        print(f'Завершено: {url}')
        return True

    except Exception as e:
        print(f'Ошибка в {url}: {e}')


def main():
    try:
        user_input = input('Введите URL через запятую (максимум 4): ')

        begin = time.time()  # засекаем начало выполнения скрипта
        urls = [url.strip() for url in user_input.split(',') if url.strip()]

        if not urls:
            print('Не введено ни одного URL')
            return

        if len(urls) > MAX_ALLOWED_URLS:
            print(f'Ошибка: превышено максимальное количество URL ({MAX_ALLOWED_URLS})')
            print('Пожалуйста, запустите скрипт несколько раз для обработки всех URL')
            return

        print(f'Обрабатываю {len(urls)} URL:')
        for url in urls:
            print(f'- {url}')

        with ThreadPoolExecutor(max_workers=len(urls)) as executor:
            results = list(executor.map(script, urls))

        print('Все задачи завершены! Результаты:')
        for url, result in zip(urls, results):
            print(f'{url}: {"Успех" if result else "Ошибка"}')
        end_time = time.time() - begin
        print(f'Общее время выполнения операций над {len(urls)} URL составило {round(end_time, 2)} сек')
    except KeyboardInterrupt:
        print('\nПрервано пользователем')
        os._exit(1)  # принудительное завершение программы пользователем
    except Exception as e:
        print(f'Критическая ошибка: {e}')


if __name__ == "__main__":
    main()