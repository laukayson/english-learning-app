from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import StaleElementReferenceException
import time

# Set up the browser
options = Options()
options.add_argument("--headless")
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

driver.get("https://tinyurl.com/49kj3jns")

# Wait for the page to load and the input field to be available
time.sleep(3)

try:
    # Find the input field by its role attribute
    input_field = driver.find_element(By.CSS_SELECTOR, "[role='textbox']")
    input_field.send_keys("Hello, World!")
    input_field.send_keys(Keys.RETURN)

    # Dynamically wait for output to finish generating
    last_text = ""
    stable_count = 0
    max_wait = 30  # maximum seconds to wait
    start_time = time.time()
    while time.time() - start_time < max_wait:
        message_contents = driver.find_elements(By.TAG_NAME, "message-content")
        if not message_contents:
            time.sleep(0.01)
            continue
        last_message = message_contents[-1]
        divs = last_message.find_elements(By.TAG_NAME, "div")
        if not divs:
            time.sleep(0.01)
            continue
        div = divs[0]
        p_tags = div.find_elements(By.TAG_NAME, "p")
        if p_tags:
            result_text = "\n".join([p.text for p in p_tags])
            # Print only the new part as it appears
            if result_text.startswith(last_text):
                new_part = result_text[len(last_text):]
                if new_part:
                    print(new_part, end="", flush=True)
            else:
                # If the text changed in a non-linear way, print the whole thing
                print(result_text)
            if result_text == last_text:
                stable_count += 1
            else:
                stable_count = 0
                last_text = result_text
            if stable_count >= 3:  # text hasn't changed for ~1.5 seconds
                print()  # finish with a newline
                break
        time.sleep(0.01)
    else:
        print("Timed out waiting for output.")
except StaleElementReferenceException:
    pass  # Suppress stale element errors
except Exception as e:
    print("Input field not found or another error occurred.")

driver.quit()