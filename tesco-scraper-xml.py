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
    writer.writerow(["Timestamp", "URL", "Name", "Size", "Price", "Clubcard", "Ingredients", "Nutrition"])

# === Start scraping ===
for i, url in enumerate(product_urls, start=1):
    print(f"[{i}/{len(product_urls)}] Scraping: {url}")
    name = size = price = clubcard = ingredients = nutrition = "N/A"

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
                size = driver.find_element(By.XPATH, "//h3[contains(text(),'Net Contents')]/following-sibling::*[1]").text.strip()
            except:
                try:
                    desc_block = driver.find_element(By.CSS_SELECTOR, ".product-description")
                    size = desc_block.text.strip()
                except:
                    size = "N/A"

            try:
                price = driver.find_element(By.CSS_SELECTOR, '[data-testid="price-per-sellable-unit"]').text.strip()
            except:
                try:
                    price = driver.find_element(By.CSS_SELECTOR, "p.styled__PriceText-sc-v0qv7n-1").text.strip()
                except:
                    price = "N/A"

            try:
                clubcard = driver.find_element(By.CSS_SELECTOR, "p.styled__ContentText-sc-1d7lp92-9").text.strip()
            except:
                clubcard = "N/A"

            try:
                ing_section = driver.find_element(By.XPATH, "//h3[contains(text(),'Ingredients')]/following-sibling::*[1]")
                ingredients = ing_section.text.strip()
            except:
                ingredients = "N/A"

            try:
                nutrition_table = driver.find_element(By.CSS_SELECTOR, "table.product_info-table")
                headers = nutrition_table.find_elements(By.CSS_SELECTOR, "thead th")
                header_text = "\t".join(h.text.strip() for h in headers)
                rows = nutrition_table.find_elements(By.CSS_SELECTOR, "tbody tr")
                row_data = []
                for row in rows:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    row_text = "\t".join(cell.text.strip() for cell in cells)
                    row_data.append(row_text)
                nutrition = header_text + "\n" + "\n".join(row_data)
            except:
                nutrition = "N/A"

            break  # Exit retry loop if successful

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
                name = size = price = clubcard = ingredients = nutrition = "SCRAPE_FAIL"
                break

    timestamp = datetime.datetime.now().isoformat()
    row = [timestamp, url, name, size, price, clubcard, ingredients, nutrition]

    # Save to output CSV immediately
    with open(output_file, "a", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(row)

    # Log basic info
    with open(log_file, "a", encoding="utf-8") as log:
        log.write(f"{timestamp} | {url} | {name[:40]}...\n")

print("✅ Scraping completed.")
driver.quit()
