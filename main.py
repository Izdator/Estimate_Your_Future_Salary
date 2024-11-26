import os
import requests
from dotenv import load_dotenv
from terminaltables import AsciiTable

LANGUAGES = [
    'JavaScript',
    'Java',
    'Python',
    'Ruby',
    'PHP',
    'C++',
    'CSS',
    'C#',
    'C',
    'Go'
]


def predict_rub_salary(data):
    if data is None or data.get('currency') not in ['RUR', 'rub']:
        return 0

    payment_from = data.get('salary', {}).get('from')
    payment_to = data.get('salary', {}).get('to')

    if payment_from is not None and payment_to is not None:
        return (payment_from + payment_to) / 2
    elif payment_from is not None:
        return payment_from * 1.2
    elif payment_to is not None:
        return payment_to * 0.8

    return 0


def calculate_average_salary(total_salary, total_vacancies_with_salary):
    return total_salary / total_vacancies_with_salary if total_vacancies_with_salary else 0


def print_statistics_table(statistics, title):
    table_data = [['Язык программирования', 'Найдено вакансий', 'Обработано вакансий', 'Средняя зарплата']]
    for lang, info in statistics.items():
        table_data.append(
            [lang, info['vacancies_found'], info['vacancies_processed'], f"{info['average_salary']:.2f} ₽"])

    table = AsciiTable(table_data, title=title)
    print(table.table)


def fetch_vacancies(url, headers, params):
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()


def process_hh_vacancies(language, headers):
    total_vacancies_found = 0
    total_vacancies_processed = 0
    total_salary = 0

    params_hh = {
        'keywords': language,
        'per_page': 100,
        'page': 0
    }

    response_hh = fetch_vacancies('https://api.hh.ru/vacancies', headers, params_hh)
    total_vacancies_found = response_hh.get('found', 0)

    while True:
        for vacancy in response_hh.get('items', []):
            expected_salary = predict_rub_salary(vacancy)
            if expected_salary:
                total_vacancies_processed += 1
                total_salary += expected_salary

        # Проверяем, есть ли еще страницы
        if params_hh['page'] >= response_hh['pages'] - 1:
            break

        params_hh['page'] += 1
        response_hh = fetch_vacancies('https://api.hh.ru/vacancies', headers, params_hh)

    return total_vacancies_found, total_vacancies_processed, total_salary


def process_sj_vacancies(language, url, headers):
    total_vacancies_found = 0
    total_vacancies_processed = 0
    total_salary = 0

    params_sj = {
        'keywords': language,
        'town': 4,  # Используем id города
        'count': 100
    }

    page = 0
    while True:
        page += 1
        params_sj['page'] = page

        response_sj = fetch_vacancies(url, headers, params_sj)
        total_vacancies_found += response_sj.get('total', 0)

        if not response_sj.get('objects'):
            break

        for vacancy in response_sj.get('objects', []):
            expected_salary = predict_rub_salary(vacancy)
            if expected_salary:
                total_vacancies_processed += 1
                total_salary += expected_salary

    return total_vacancies_found, total_vacancies_processed, total_salary


def process_vacancies(programming_languages, url, headers):
    statistics = {}

    for language in programming_languages:
        # Обработка вакансий из HeadHunter
        total_vacancies_found_hh, total_vacancies_processed_hh, total_salary_hh = process_hh_vacancies(language,
                                                                                                       headers)

        # Обработка вакансий из SuperJob
        total_vacancies_found_sj, total_vacancies_processed_sj, total_salary_sj = process_sj_vacancies(language, url,
                                                                                                       headers)

        # Суммируем статистику
        total_vacancies_found = total_vacancies_found_hh + total_vacancies_found_sj
        total_vacancies_processed = total_vacancies_processed_hh + total_vacancies_processed_sj
        total_salary = total_salary_hh + total_salary_sj

        average_salary = calculate_average_salary(total_salary, total_vacancies_processed)

        statistics[language] = {
            'vacancies_found': total_vacancies_found,
            'vacancies_processed': total_vacancies_processed,
            'average_salary': average_salary
        }

    return statistics


def main():
    load_dotenv()

    url = "https://api.superjob.ru/2.0/vacancies/"
    api_key = os.environ.get('SUPERJOB_TOKEN')
    headers = {
        "X-Api-App-Id": api_key
    }

    statistics = process_vacancies(LANGUAGES, url, headers)
    print_statistics_table(statistics, title="Статистика вакансий")


if __name__ == '__main__':
    main()
