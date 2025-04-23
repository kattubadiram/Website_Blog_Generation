from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

def setup_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=options)

def test_contact_form(driver):
    print("🔍 Checking Contact Form...")
    driver.get("https://preeticapital.com/contact-182/")
    time.sleep(2)

    driver.find_element(By.NAME, "your-name").send_keys("John Tester")
    driver.find_element(By.NAME, "your-email").send_keys("john@test.com")
    driver.find_element(By.NAME, "your-phone").send_keys("1234567890")
    driver.find_element(By.NAME, "your-message").send_keys("Automated test of contact form.")
    driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()

    time.sleep(3)
    return "Thank you for your message. It has been sent." in driver.page_source

def test_feedback_form(driver):
    print("🔍 Checking Feedback Form...")
    driver.get("https://preeticapital.com/feedback/")
    time.sleep(2)

    driver.find_element(By.NAME, "your-name").send_keys("Jane Feedback")
    driver.find_element(By.NAME, "rating").send_keys("4")  # Optional, just sends a value
    driver.find_element(By.NAME, "your-message").send_keys("Automated test of feedback form.")
    driver.find_element(By.NAME, "your-email").send_keys("feedback@test.com")
    driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()

    time.sleep(3)
    return "Thank you for your message. It has been sent." in driver.page_source

def run_monitoring():
    driver = setup_driver()
    results = {}

    try:
        results["Contact Form"] = test_contact_form(driver)
        results["Feedback Form"] = test_feedback_form(driver)
    finally:
        driver.quit()

    print("\n📋 Daily Form Status Report:")
    for form, status in results.items():
        print(f"- {form}: {'✅ Working' if status else '❌ Failed'}")

if __name__ == "__main__":
    run_monitoring()
