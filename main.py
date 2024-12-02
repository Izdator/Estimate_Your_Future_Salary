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


def predict_rub_salary(salary_from, salary_to, currency):
    if currency not in ['RUR', 'rub']:
        return 0

    expected_salary = 0

    if salary_from and salary_to:
        expected_salary = (salary_from + salary_to) / 2
    elif salary_from:
        expected_salary = salary_from * 1.2
    elif salary_to:
        expected_salary = salary_to * 0.8

    return expected_salary


def calculate_average_salary(total_salary, total_vacancies_with_salary):
    return total_salary / total_vacancies_with_salary if total_vacancies_with_salary else 0


def print_statistics_table(statistics, title):
    vacancy_table = [['Язык программирования', 'Найдено вакансий', 'Обработано вакансий', 'Средняя зарплата']]
    for lang, info in statistics.items():
        vacancy_table.append(
            [lang, info['vacancies_found'], info['vacancies_processed'], f"{info['average_salary']:.2f} ₽"])

    table = AsciiTable(vacancy_table, title=title)
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
            salary = vacancy.get('salary')
            if not salary:
                continue

            salary_from = salary.get('from')
            salary_to = salary.get('to')
            currency = salary.get('currency')

            expected_salary = predict_rub_salary(salary_from, salary_to, currency)

            if expected_salary:
                total_vacancies_processed += 1
                total_salary += expected_salary

        if params_hh['page'] >= response_hh['pages'] - 1:
            break

        params_hh['page'] += 1
        response_hh = fetch_vacancies('https://api.hh.ru/vacancies', headers, params_hh)

    return total_vacancies_found, total_vacancies_processed, total_salary


def process_sj_vacancies(language, url, headers):
    total_vacancies_processed = 0
    total_salary = 0

    params_sj = {
        'keywords': language,
        'town': 4,  # Используем id города
        'count': 100
    }

    page = 0
    response_sj = fetch_vacancies(url, headers, params_sj)
    total_vacancies_found = response_sj.get('total', 0)

    while True:
        page += 1
        params_sj['page'] = page

        if not response_sj.get('objects'):
            break

        for vacancy in response_sj.get('objects', []):
            salary_from = vacancy.get('payment_from')
            salary_to = vacancy.get('payment_to')
            currency = vacancy.get('currency')

            expected_salary = predict_rub_salary(salary_from, salary_to, currency)

            if expected_salary:
                total_vacancies_processed += 1
                total_salary += expected_salary

        response_sj = fetch_vacancies(url, headers, params_sj)

    return total_vacancies_found, total_vacancies_processed, total_salary


def process_vacancies(programming_languages, url, headers):
    statistics_hh = {}
    statistics_sj = {}

    for language in programming_languages:
        total_vacancies_found_hh, total_vacancies_processed_hh, total_salary_hh = process_hh_vacancies(language,
                                                                                                       headers)
        statistics_hh[language] = {
            'vacancies_found': total_vacancies_found_hh,
            'vacancies_processed': total_vacancies_processed_hh,
            'average_salary': calculate_average_salary(total_salary_hh, total_vacancies_processed_hh)
        }

        total_vacancies_found_sj, total_vacancies_processed_sj, total_salary_sj = process_sj_vacancies(language, url,
                                                                                                       headers)
        statistics_sj[language] = {
            'vacancies_found': total_vacancies_found_sj,
            'vacancies_processed': total_vacancies_processed_sj,
            'average_salary': calculate_average_salary(total_salary_sj, total_vacancies_processed_sj)
        }

    return statistics_hh, statistics_sj


def main():
    load_dotenv()

    url = "https://api.superjob.ru/2.0/vacancies/"
    api_key = os.environ.get('SUPERJOB_TOKEN')
    headers = {
        "X-Api-App-Id": api_key
    }

    statistics_hh, statistics_sj = process_vacancies(LANGUAGES, url, headers)

    print_statistics_table(statistics_hh, title="Статистика вакансий на HeadHunter")
    print_statistics_table(statistics_sj, title="Статистика вакансий на SuperJob")


if __name__ == '__main__':
    main()