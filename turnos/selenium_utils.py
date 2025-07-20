import json
import time

from selenium.webdriver.chrome.options import Options
from selenium import webdriver

MAX_BROWSER_REQUEST_UPDATE_ATTEMPS = 10


def get_browser(hostname: str, port: int) -> webdriver.Chrome:
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

    return webdriver.Remote(
        command_executor=f"http://{hostname}:{port}", options=options
    )


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
            if "message" in log:
                message = json.loads(log["message"])
                message = message.get("message", {})
                if message.get("method") == "Network.requestWillBeSent":
                    request = message.get("params", {}).get("request", {})
                    if request.get("url", "").endswith(url):
                        return request

        time.sleep(1)
        attempts += 1
