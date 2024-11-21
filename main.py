import json
from dotenv import load_dotenv
import os
import requests
from terminaltables import AsciiTable
from typing import Dict


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


def print_statistics(source: str, statistics: Dict[str, Dict[str, int]]) -> None:
    table_data = [['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']]

    for language, data in statistics.items():
        if source == "SuperJob":
            table_data.append([language, data["vacancies_found"], data["vacancies_processed"], data["average_salary"]])
        elif source == "HeadHunter":
            table_data.append(
                [language, data['found_count'], data['processed_count'], f"{data['average_salary']:.2f} ₽"])
        else:
            raise ValueError("Неизвестный источник статистики.")

    def load_vacancies(language, url):
        total_salary = 0
        total_vacancies_with_salary = 0
        page = 0

        while True:
            params = {
                "text": language,
                "area": 1,  # Москва
                "per_page": 100,
                "page": page
            }

            try:
                print(f"Загрузка вакансий для языка: {language}, Страница: {page}")
                response = requests.get(url, params=params)

                if response.ok:
                    response_json = response.json()
                    found_count = response_json['found']

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

        return total_salary, total_vacancies_with_salary, found_count

    def calculate_average_salary(total_salary, total_vacancies_with_salary):
        if total_vacancies_with_salary:
            return total_salary / total_vacancies_with_salary
        return 0


    def main():
        url = "https://api.hh.ru/vacancies"
        results = {language: {'average_salary': 0, 'found_count': 0, 'processed_count': 0} for language in LANGUAGES}

        for language in LANGUAGES:
            total_salary, total_vacancies_with_salary, found_count = load_vacancies(language, url)
            results[language]['found_count'] = found_count
            results[language]['processed_count'] = total_vacancies_with_salary
            results[language]['average_salary'] = calculate_average_salary(total_salary, total_vacancies_with_salary)

        table_title = f"{source} Moscow"
        table = AsciiTable(table_data, title=table_title)
        print(table.table)

    print_statistics(statistics)
    def load_environment_variables():
        load_dotenv()

    def fetch_vacancies(url, headers, params):
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()

    def process_vacancies(programming_languages, url, headers):
        statistics = {}

        for language in programming_languages:
            total_vacancies_found = 0
            total_vacancies_processed = 0
            total_salary = 0
            params = {
                "keywords": language,
                "town": 4,  # Москва
                "count": 100
            }

            page = 0
            while True:
                page += 1
                params["page"] = page

                try:
                    response_superjob = fetch_vacancies(url, headers, params)
                    total_vacancies_found += response_superjob.get('total', 0)

                    if not response_superjob.get('objects'):
                        break

                    for vacancy in response_superjob.get('objects', []):
                        expected_salary = predict_rub_salary_sj(vacancy)

                        if expected_salary:
                            total_vacancies_processed += 1
                            total_salary += expected_salary

                except requests.exceptions.RequestException as e:
                    print(f"Ошибка при запросе для {language}, Страница {page}: {e}")
                    break

            average_salary = total_salary / total_vacancies_processed if total_vacancies_processed else 0

            statistics[language] = {
                "vacancies_found": total_vacancies_found,
                "vacancies_processed": total_vacancies_processed,
                "average_salary": average_salary
            }

        return statistics

        load_dotenv()

    def fetch_vacancies(url, headers, params):
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()

    def process_vacancies(programming_languages, url, headers):
        statistics = {}

        for language in programming_languages:
            total_vacancies_found = 0
            total_vacancies_processed = 0
            total_salary = 0
            params = {
                "keywords": language,
                "town": 4,  # Используем id города
                "count": 100
            }

            page = 0
            while True:
                page += 1
                params["page"] = page

                try:
                    response_json_superjob = fetch_vacancies(url, headers, params)
                    total_vacancies_found += response_json_superjob.get('total', 0)

                    if not response_json_superjob.get('objects'):
                        break

                    for vacancy in response_json_superjob.get('objects', []):
                        expected_salary = predict_rub_salary_sj(vacancy)

                        if expected_salary:
                            total_vacancies_processed += 1
                            total_salary += expected_salary

                except requests.exceptions.RequestException as e:
                    print(f"Ошибка при запросе для {language}, Страница {page}: {e}")
                    break

            average_salary = total_salary / total_vacancies_processed if total_vacancies_processed else 0

            statistics[language] = {
                "vacancies_found": total_vacancies_found,
                "vacancies_processed": total_vacancies_processed,
                "average_salary": average_salary
            }

        return statistics


        load_environment_variables()

        url = "https://api.superjob.ru/2.0/vacancies/"
        api_key = os.environ.get('SUPERJOB_TOKEN')
        headers = {
            "X-Api-App-Id": api_key
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

        statistics = process_vacancies(programming_languages, url, headers)
        print_statistics_table(statistics)

        load_environment_variables()

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

        statistics = process_vacancies(programming_languages, url, headers)
        print_statistics(statistics)

    if __name__ == '__main__':
        main()
