import json
from dotenv import load_dotenv
import os
import requests
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

results = {language: {'found_count': 0, 'processed_count': 0, 'average_salary': 0} for language in LANGUAGES}


def predict_rub_salary_hh(salary):
    if salary is None or salary['currency'] != 'RUR':
        return None
    if salary['from'] is not None and salary['to'] is not None:
        return (salary['from'] + salary['to']) / 2
    elif salary['from'] is not None:
        return salary['from'] * 1.2
    elif salary['to'] is not None:
        return salary['to'] * 0.8
    else:
        return None


def predict_rub_salary_sj(vacancy):
    payment_from = vacancy.get('payment_from')
    payment_to = vacancy.get('payment_to')
    agreement = vacancy.get('agreement', False)

    if agreement:
        return None

    if vacancy.get('currency', 'rub') != 'rub':
        return None

    if payment_from is not None and payment_to is not None:
        return (payment_from + payment_to) / 2
    elif payment_from is not None:
        return payment_from * 1.2
    elif payment_to is not None:
        return payment_to * 0.8
    else:
        return None


def print_statistics_table(statistics):
    table_data = [['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']]

    for language, data in statistics.items():
        table_data.append([language, data["vacancies_found"], data["vacancies_processed"], data["average_salary"]])

    table = AsciiTable(table_data, title="SuperJob Moscow")
    print(table.table)


def main():
    url = "https://api.hh.ru/vacancies"
    results = {language: {'average_salary': 0, 'found_count': 0, 'processed_count': 0} for language in LANGUAGES}

    for language in LANGUAGES:
        total_salary = 0
        total_vacancies_with_salary = 0
        page = 0

        while True:
            params = {
                "text": language,
                "area": 1,
                "per_page": 100,
                "page": page
            }

            try:
                print(f"Загрузка вакансий для языка: {language}, Страница: {page}")
                response = requests.get(url, params=params)

                if response.ok:
                    response_json = response.json()
                    results[language]['found_count'] = response_json['found']

                    for vacancy in response_json['items']:
                        salary = vacancy['salary']
                        rub_salary = predict_rub_salary_hh(salary)
                        if rub_salary:
                            total_salary += rub_salary
                            total_vacancies_with_salary += 1

                    if len(response_json['items']) < 100:
                        break
                    page += 1
                else:
                    print(f"Ошибка при загрузке вакансий для языка {language}: {response.status_code}")
                    break
            except requests.exceptions.RequestException as e:
                print(f"Произошла ошибка при запросе для {language}, Страница {page}: {e}")
                break

        if any(total_vacancies_with_salary):
            results[language]['average_salary'] = total_salary / total_vacancies_with_salary
        results[language]['processed_count'] = total_vacancies_with_salary

    table_data = [['Язык программирования', 'Найдено вакансий', 'Обработано вакансий', 'Средняя зарплата']]
    for lang, info in results.items():
        table_data.append([lang, info['found_count'], info['processed_count'], f"{info['average_salary']:.2f} ₽"])

    table = AsciiTable(table_data, title="HeadHunter Moscow")
    print(table.table)

    # SUPERJOB
    url = "https://api.superjob.ru/2.0/vacancies/"
    API_KEY = os.environ.get('SUPERJOB_TOKEN')
    headers = {
        "X-Api-App-Id": API_KEY
    }

    programming_languages = [
        'JavaScript',
        'Java',
        'Python',
        'Ruby',
        'PHP',
        'C++',
        'CSS',
        'C#',
        'C',
    ]

    statistics = {}

    for language in programming_languages:
        total_vacancies_found = 0
        total_vacancies_processed = 0
        total_salary = 0
        params = {
            "keywords": language,
            "town": 4,
            "count": 100
        }

        page = 0
        while True:
            page += 1
            params["page"] = page
            response = requests.get(url, headers=headers, params=params)

            if response.ok:
                pass
                response_json_superjob = response.json()
                total_vacancies_found += response_json_superjob.get('total', 0)

                if not response_json_superjob.get('objects'):
                    break

                for vacancy in response_json_superjob.get('objects', []):
                    expected_salary = predict_rub_salary_sj(vacancy)

                    if expected_salary:
                        total_vacancies_processed += 1
                        total_salary += expected_salary
            else:
                print(f"Ошибка при запросе: {response.status_code}")
                break

        average_salary = total_salary / total_vacancies_processed if any(total_vacancies_processed) else 0

        statistics[language] = {
            "vacancies_found": total_vacancies_found,
            "vacancies_processed": total_vacancies_processed,
            "average_salary": average_salary
        }

    print_statistics_table(statistics)


if __name__ == "__main__":
    load_dotenv()
    main()
