import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv
import datetime

# === Setup ===
input_file = "url_test.csv"
output_file = "tesco_products_full.csv"
log_file = "tesco_scrape_log.txt"

def start_driver():
    options = uc.ChromeOptions()
    options.headless = False  # Set to True if you want headless scraping
    options.add_argument("--no-sandbox")
    return uc.Chrome(options=options)

driver = start_driver()

# === Read URLs ===
product_urls = []
with open(input_file, newline='', encoding='utf-8') as f:
    reader = csv.reader(f)
    for row in reader:
        if row and row[0].startswith("http"):
            product_urls.append(row[0])
product_urls = list(set(product_urls))  # Deduplicate

# === Write header once ===
with open(output_file, "w", newline='', encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Timestamp", "URL", "Name", "Size", "Price", "Ingredients", "Nutrition"])

# === Start scraping ===
for i, url in enumerate(product_urls, start=1):
    print(f"[{i}/{len(product_urls)}] Scraping: {url}")
    name = size = price = ingredients = nutrition = "N/A"

    for attempt in range(2):  # Retry logic
        try:
            driver.get(url)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "h1"))
            )

            actions = ActionChains(driver)
            actions.send_keys(Keys.PAGE_DOWN).perform()
            time.sleep(1)
            actions.send_keys(Keys.END).perform()
            time.sleep(2)

            try:
                name = driver.find_element(By.TAG_NAME, "h1").text.strip()
            except:
                name = "N/A"

            try:
                size = driver.find_element(By.CSS_SELECTOR, '[data-testid="product-pack-size"]').text.strip()
            except:
                try:
                    desc_block = driver.find_element(By.CSS_SELECTOR, ".product-description")
                    size = desc_block.text.strip()
                except:
                    size = "N/A"

            try:
                price = driver.find_element(By.CSS_SELECTOR, '[data-testid="price"]').text.strip()
            except:
                price = "N/A"

            try:
                ing_section = driver.find_element(By.XPATH, "//h3[contains(text(),'Ingredients')]/following-sibling::*[1]")
                ingredients = ing_section.text.strip()
            except:
                ingredients = "N/A"

            try:
                nutrition_table = driver.find_element(By.XPATH, "//h3[contains(text(),'Nutrition')]/following-sibling::table[1]")
                rows = nutrition_table.find_elements(By.TAG_NAME, "tr")
                nutrition = " | ".join([r.text.strip() for r in rows])
            except:
                nutrition = "N/A"

            break  # If successful, exit retry loop

        except Exception as e:
            print(f"❌ Error: {e}")
            if "no such window" in str(e) or "chrome not reachable" in str(e):
                print("🔁 Restarting browser...")
                try:
                    driver.quit()
                except:
                    pass
                driver = start_driver()
            else:
                name = size = price = ingredients = nutrition = "SCRAPE_FAIL"
                break

    timestamp = datetime.datetime.now().isoformat()
    row = [timestamp, url, name, size, price, ingredients, nutrition]

    # Save to output CSV immediately
    with open(output_file, "a", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(row)

    # Log basic info
    with open(log_file, "a", encoding="utf-8") as log:
        log.write(f"{timestamp} | {url} | {name[:40]}...\n")

print("✅ Scraping completed.")
driver.quit()