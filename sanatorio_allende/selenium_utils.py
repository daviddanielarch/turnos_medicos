import json
import time

import urllib3
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeDriver
from selenium.webdriver.remote.webdriver import WebDriver

MAX_BROWSER_REQUEST_UPDATE_ATTEMPS = 10
MAX_BROWSER_RETRY_ATTEMPTS = 10


class SeleniumSettings:
    def __init__(self, hostname: str, port: int, implicit_wait: int):
        self.hostname = hostname
        self.port = port
        self.implicit_wait = implicit_wait


def get_browser(hostname: str, port: int) -> WebDriver:
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("enable-automation")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-dev-shm-usage")
    options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    options.set_capability("browserName", "chrome")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    )

    attempts = 1
    time_to_sleep = 2
    last_exception = None

    while attempts <= MAX_BROWSER_RETRY_ATTEMPTS:
        try:
            return webdriver.Remote(
                command_executor=f"http://{hostname}:{port}", options=options
            )
        except urllib3.exceptions.MaxRetryError as e:
            last_exception = e
            if attempts < MAX_BROWSER_RETRY_ATTEMPTS:
                time.sleep(time_to_sleep)
                time_to_sleep *= 2

            attempts += 1

    # If we get here, all retries failed
    raise last_exception or WebDriverException(
        "Failed to connect to browser after all retry attempts"
    )


def find_request(browser: WebDriver, url: str) -> dict:
    """Finds a request sent in the browser logs.

    This will only allow us to access the request payload (not the response)
    This works because we enabled logging capabilities with
        options.set_capability(
           "goog:loggingPrefs", {"performance": "ALL"}
    )
    """
    attempts = 1

    while attempts < MAX_BROWSER_REQUEST_UPDATE_ATTEMPS:
        # Remote driver doesn't have get_log method, so we need to use the ChromeDriver class
        logs = ChromeDriver.get_log(browser, "performance")  # type: ignore[arg-type]
        for log in logs:
            if "message" in log:
                message = json.loads(log["message"])
                message = message.get("message", {})
                if message.get("method") == "Network.requestWillBeSent":
                    request: dict = message.get("params", {}).get("request", {})
                    if request.get("url", "").endswith(url):
                        return request

        time.sleep(5)
        attempts += 1

    # If no request found, return empty dict
    return {}
