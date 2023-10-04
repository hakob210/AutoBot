import requests
import re
from bs4 import BeautifulSoup
import requests.exceptions
import json
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

TOKEN = '6119325701:AAEZpJmSGdi_KJ7CAKnTpE5ibKaPJ3dIX6o'

def get_cars():
    try:
        cars_dict = {}

        headers = {
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
        }

        url = "https://auto.am/"
        r = requests.get(url=url, headers=headers)

        soup = BeautifulSoup(r.text, "lxml")
        cards = soup.find_all("div", class_="card")

        for car in cards:
            car_name = car.find("span", class_="card-title bold").text.strip()
            car_year = car.find("div", class_="card-content").find("span", class_="bold").text.strip()
            car_price = car.find("p", class_="price right").text.strip()
            car_url = f'https://auto.am/{car.find("a")["href"]}'
            car_id = car_url.split("/")[-1]

            cars_dict[car_id] = {
                "car_name": car_name,
                "car_year": car_year,
                "car_price": car_price,
                "car_url": car_url
            }

        with open("cars_dict.json", "w") as file:
            json.dump(cars_dict, file, indent=5, ensure_ascii=False)

    except requests.exceptions.RequestException:
        print("Request error")

    except json.JSONDecodeError:
        print("JSON error")

    except Exception:
        print("Error")

def search_cars(query):
    with open("cars_dict.json", "r") as file:
        cars_dict = json.load(file)

    results = []
    query = query.lower()

    year_range_match = re.match(r'(\d{4})-(\d{4})', query)
    if year_range_match:
        start_year, end_year = int(year_range_match.group(1)), int(year_range_match.group(2))
        for car_id, car_info in cars_dict.items():
            car_year = int(re.search(r'\d{4}', car_info["car_year"]).group())
            if start_year <= car_year <= end_year:
                results.append(f"{car_info['car_name']} ({car_info['car_year']}) - {car_info['car_price']}\n{car_info['car_url']}")

    price_range_match = re.match(r'([$€£¥֏]?[\s\d,]+)\s?[-–]\s?([$€£¥֏]?[\s\d,]+)', query)
    if price_range_match:
        start_price = parse_price(price_range_match.group(1))
        end_price = parse_price(price_range_match.group(2))
        for car_id, car_info in cars_dict.items():
            car_price = parse_price(car_info["car_price"])
            if start_price <= car_price <= end_price:
                results.append(f"{car_info['car_name']} ({car_info['car_year']}) - {car_info['car_price']}\n{car_info['car_url']}")

    if not year_range_match and not price_range_match:
        for car_id, car_info in cars_dict.items():
            car_name = car_info["car_name"]
            car_year = car_info["car_year"]

            if query in car_name.lower() or query in car_year.lower():
                results.append(f"{car_name} ({car_year}) - {car_info['car_price']}\n{car_info['car_url']}")

    return results

def parse_price(price_str):
    price_str = re.sub(r'[$€£¥֏\s]', '', price_str)
    try:
        return float(price_str)
    except ValueError:
        return 0.0

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Բարի գալուստ AutoBot! Այստեղ դուք կարող եք փնտրել և գտնել մեքենաներ, որոնք կարող եք գնել։ \nՄեքենա գտնելու համար կարող եք․ \n1. Մուտքագրել մեքենայի անվանումը (օր․ Nissan, Audi, BMW...) \n2.Մուտքագրել մեքենայի գինը (օր․ $ 15 000 - $ 30 000) \n3. Մուտքագրել մեքենայի տարեթիվը (օր․ 2023, 2002-2008...)")

def handle_text(update: Update, context: CallbackContext):
    query = update.message.text

    try:
        results = search_cars(query)

        if results:
            for result in results:
                update.message.reply_text(result)
        else:
            update.message.reply_text("Նման մեքենա չի գտնվել։")
    except Exception:
        update.message.reply_text("Ծրագրային սխալ, խնդրում ենք փորձել մի փոքր ուշ։")

def main():
    get_cars()

    updater = Updater(token=TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("Start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()