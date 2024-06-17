import argparse
import asyncio
import json
import logging
import os
import time
from datetime import datetime
from enum import Enum
from dotenv import load_dotenv

import telegram
from selenium.webdriver.chrome.options import Options
from selenium import webdriver

import requests

FAR_FAR_AWAY_IN_THE_FUTURE = datetime(2050, 1, 1)
HTTP_UNAUTHORIZED = 401
MAX_BROWSER_REQUEST_UPDATE_ATTEMPS = 10
SELENIUM_IMPLICIT_WAIT = 10
WAIT_SECONDS_BEETWEEN_ITERATIONS = 60 * 5


class UnauthorizedException(Exception):
    pass


class DoctorNotFound(Exception):
    pass


logger = logging.getLogger(__name__)

def send_message(message: str, token: str) -> None:
    logger.info(message)

    async def _send(message):
        bot = telegram.Bot(token=token)
        await bot.send_message(chat_id=658553143, text=message)

    asyncio.run(_send(message))


def get_browser(hostname:str, port: int) -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("enable-automation")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-dev-shm-usage")
    options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    options.set_capability("browserName", "chrome")
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")

    return webdriver.Remote(command_executor=f"http://{hostname}:{port}", options=options)

class Place(Enum):
    NUEVA_CBA = "NUEVA CBA"
    CERRO = "CERRO"


def get_doctor_data(browser: webdriver.Chrome, name: str, place: Place):
    """Searches for a doctor and returns the payload needed to get the appointments"""
    browser.get("https://miportal.sanatorioallende.com/portal/p/turnos/new/asistente")

    search_doctor_input = browser.find_element("id", "inputElementoBuscadorPortal")
    search_doctor_input.send_keys(name)
    browser.implicitly_wait(SELENIUM_IMPLICIT_WAIT)
    selector = browser.find_element("xpath", f"//*[contains(text(), '{name}')]")
    (selector
        .find_element("xpath", "./..")
        .find_element("xpath", f"//*[contains(text(), '{place.value}')]")
        .click()
     )
    browser.find_element("xpath", f"//*[contains(text(), 'SELECCIONAR')]").click()

    request = find_request(browser, 'ObtenerPrimerTurnoAsignableParaPortalWebConParticular')
    doctor_payload = json.loads(request.get('postData', '{}'))
    if not doctor_payload:
        raise DoctorNotFound(f"Doctor {name} not found")

    return doctor_payload


def find_request(browser: webdriver.Chrome, url: str):
    """Finds a request sent in the browser logs.

    This will only allow us to access the request payload (not the response)
    This works because we enabled logging capabilities with
        options.set_capability(
           "goog:loggingPrefs", {"performance": "ALL"}
    )
    """
    attempts = 1

    while attempts < MAX_BROWSER_REQUEST_UPDATE_ATTEMPS:
        logs = browser.get_log("performance")
        for log in logs:
            if 'message' in log:
                message = json.loads(log['message'])
                message = message.get('message', {})
                if message.get('method') == 'Network.requestWillBeSent':
                    request = message.get('params', {}).get('request', {})
                    if request.get('url', '').endswith(url):
                        return request

        time.sleep(1)


def get_auth(browser: webdriver.Chrome):
    """Gets the auth header from the browser requests.

    This will allow us to make requests without having to use selenium
    """

    request = find_request(browser, 'ObtenerTurnosParaPortalPorFiltro')
    auth_header = request.get('headers', {}).get('Authorization')
    if not auth_header:
        raise Exception('No auth found')

    return auth_header


def login(browser: webdriver.Chrome, user: str, password: str):
    # Open the login page URL
    browser.get("https://miportal.sanatorioallende.com/auth/loginPortal")

    # Find the email and password fields
    email_field = browser.find_element("name", "inputNroDocumento")
    password_field = browser.find_element("name", "inputPassword")

    # Enter the email and password
    email_field.send_keys(user)
    password_field.send_keys(password)

    # Find the login button and click it
    login_button = browser.find_element("xpath", "//button[@type='submit']")
    login_button.click()


def get_appointment_dates(data: list[dict]) -> list[datetime]:
    """Parses the appointments from the response data to get the appointment dates"""
    appointments = []
    for turno in data['PrimerosTurnosDeCadaRecurso']:
        if not turno['Atiende']:
            continue

        date = turno['Fecha'].split('T')[0]
        date = datetime.strptime(date, '%Y-%m-%d')
        hora = turno['Hora']
        if not hora:
            continue

        hora = datetime.strptime(hora, '%H:%M')
        date_and_time = date.replace(hour=hora.hour, minute=hora.minute)

        appointments.append(date_and_time)

    return appointments


def search_best_date_appointment(auth_header: dict, doctor_data: dict):
    """Searches the best date for an appointment with the given doctor"""
    response = requests.post(
        "https://miportal.sanatorioallende.com/backend/api/DisponibilidadDeTurnos/ObtenerPrimerTurnoAsignableDeCadaRecursoDelServicioParaPortalWebConParticular",
        headers={'authorization': auth_header},
        json=doctor_data)

    if response.status_code == HTTP_UNAUTHORIZED:
        raise UnauthorizedException()

    appointments = get_appointment_dates(response.json())
    if not appointments:
        return

    return min(appointments)


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )
    logging.getLogger('seleniumwire').setLevel(logging.CRITICAL)
    logging.getLogger('seleniumwire.handler').setLevel(logging.CRITICAL)
    logging.getLogger('seleniumwire.server').setLevel(logging.CRITICAL)
    logging.getLogger('seleniumwire.request').setLevel(logging.CRITICAL)


def main(browser: webdriver.Chrome, user: str, password: str, doctor_name: str, place: Place):
    logger.info("Logging-in")

    login(browser, user, password)
    auth = get_auth(browser)

    doctor = get_doctor_data(browser, doctor_name, place)
    browser.close()

    send_message(f'Will start looking for a better appointment for doctor {doctor_name} at {place}')

    best_date = FAR_FAR_AWAY_IN_THE_FUTURE
    while True:
        try:
            logger.info('Processing')

            best_date_so_far = search_best_date_appointment(auth, doctor)
            if not best_date_so_far:
                logger.error('No hay turnos')
                break

            if best_date_so_far > best_date:
                send_message(f'Lost better date: {best_date_so_far}')
                best_date = best_date_so_far
                send_message(f'New better date: {best_date_so_far}')

            if best_date_so_far < best_date:
                best_date = best_date_so_far
                send_message(f'Found better date: {best_date_so_far}')

            time.sleep(WAIT_SECONDS_BEETWEEN_ITERATIONS)

        except UnauthorizedException:
            logger.info("We were logged-out, logging in again")
            browser = get_browser()
            login(browser, user, password)
            auth = get_auth(browser)
            browser.close()
            continue
        except Exception as e:
            raise e

def get_value(args, name) -> str:
    """Get a value from the args or the environment variables"""
    arg_env_map = {
        'hostname': 'HOSTNAME',
        'port': 'PORT',
        'username': 'USERNAME',
        'password': 'PASSWORD',
        'telegram_token': 'TELEGRAM_TOKEN',
        'doctor_name': 'DOCTOR_NAME',
        'place': 'PLACE',
    }

    if name not in args:
        raise ValueError(f'Invalid arg {name}')

    value = args[name]
    if value:
        return value
    else:
        value = os.getenv(arg_env_map[name])
        if not value:
            raise ValueError(f"{name} is required")
        return value


if __name__ == '__main__':
    setup_logging()
    parser = argparse.ArgumentParser()
    parser.add_argument('--hostname', type=str, default='localhost')
    parser.add_argument('--port', type=int, default=4444)
    parser.add_argument('--username', type=str)
    parser.add_argument('--password', type=str)
    parser.add_argument('--telegram_token', type=str)
    parser.add_argument('--doctor_name', type=str)
    parser.add_argument('--place', type=str)

    args_dict = vars(parser.parse_args())

    load_dotenv()

    hostname = get_value(args_dict, 'hostname')
    port = get_value(args_dict, 'port')
    username = get_value(args_dict, 'username')
    password = get_value(args_dict, 'password')
    telegram_token = get_value(args_dict, 'telegram_token')
    doctor_name = get_value(args_dict, 'doctor_name')
    place = get_value(args_dict, 'place')
    if place in Place.__members__:
        place = Place[place]
    else:
        raise ValueError(f"Invalid place {place}. Must be one of {', '.join(Place.__members__)}")

    driver = get_browser(hostname, port)


    try:
        main(driver, username , password, doctor_name, place)

    except Exception as e:
        logger.error(e)
        driver.quit()

    except KeyboardInterrupt:
        driver.quit()
        logger.info("Exiting")