import csv
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

VERBOSE = False  # Bật tắt log chi tiết


def is_captcha_present(driver):
    url = driver.current_url.lower()
    page_source = driver.page_source.lower()
    return "captcha" in url or "captcha" in page_source or "verify you are human" in page_source


def wait_for_captcha_to_be_solved(driver, check_interval=3):
    print("🔐 CAPTCHA phát hiện – vui lòng xử lý thủ công...")
    while True:
        time.sleep(check_interval)
        if not is_captcha_present(driver):
            print("✅ CAPTCHA đã được giải. Tiếp tục crawl...")
            break


def get_product_links_on_current_page(driver):
    items = driver.find_elements(By.CSS_SELECTOR, "div.s-main-slot div[data-component-type='s-search-result']")
    links = []
    for item in items:
        try:
            a_tag = item.find_element(By.CSS_SELECTOR, "a.a-link-normal.s-no-outline")
            href = a_tag.get_attribute("href")
            if href and "/dp/" in href:
                links.append(href.split("?")[0])
        except:
            continue
    return links


def go_to_next_page(driver):
    try:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight - 1000);")
        time.sleep(2)
        wait = WebDriverWait(driver, 15)
        next_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.s-pagination-next")))
        driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", next_button)
        time.sleep(5)
        if is_captcha_present(driver):
            wait_for_captcha_to_be_solved(driver)
        return True
    except Exception as e:
        if VERBOSE:
            print(f"❌ Không thể sang trang tiếp theo: {e}")
        return False


def get_product_price(driver):
    wait = WebDriverWait(driver, 5)
    try:
        price_range_element = driver.find_element(By.CSS_SELECTOR,
            "#corePrice_desktop > div > table > tbody > tr > td.a-span12 > span.a-price-range")
        price_range_text = " ".join(price_range_element.text.split())
        return price_range_text
    except:
        pass
    try:
        price_symbol = driver.find_element(By.CSS_SELECTOR, "span.a-price-symbol").text.strip()
        price_whole = driver.find_element(By.CSS_SELECTOR, "span.a-price-whole").text.strip()
        price_fraction = driver.find_element(By.CSS_SELECTOR, "span.a-price-fraction").text.strip()
        return f"{price_symbol}{price_whole}.{price_fraction}"
    except:
        pass
    try:
        return driver.find_element(By.CSS_SELECTOR, "span.a-offscreen").text.strip()
    except:
        pass
    return "N/A"


def crawl_product_details(driver):
    time.sleep(2)
    try:
        name = driver.find_element(By.ID, "productTitle").text.strip()
    except:
        name = "N/A"
    price = get_product_price(driver)
    try:
        rating_elem = driver.find_element(By.CSS_SELECTOR, "span.a-icon-alt")
        rating = rating_elem.get_attribute("innerText").split(" ")[0].strip()
    except:
        rating = "N/A"
    try:
        details_element = driver.find_element(By.XPATH,
            "//h3[contains(text(), 'Product details')]/following-sibling::div")
        details = details_element.text.strip()
    except:
        details = "N/A"
    try:
        image = driver.find_element(By.ID, "landingImage").get_attribute("src")
    except:
        image = "N/A"
    return {
        "Name": name,
        "Price": price,
        "Rating": rating,
        "Details": details,
        "Image": image,
        "Link": driver.current_url
    }


def crawl_amazon_list_first(driver, total_required=200):
    products = []
    visited_links = set()
    while len(products) < total_required:
        links = get_product_links_on_current_page(driver)
        for link in links:
            if link in visited_links or len(products) >= total_required:
                continue
            visited_links.add(link)

            driver.execute_script("window.open(arguments[0]);", link)
            driver.switch_to.window(driver.window_handles[-1])
            time.sleep(2)

            if is_captcha_present(driver):
                wait_for_captcha_to_be_solved(driver)

            try:
                product = crawl_product_details(driver)
                products.append(product)
                print(f"✅ Đã crawl xong sản phẩm {len(products)}")
            except:
                if VERBOSE:
                    print("⚠️ Lỗi khi crawl sản phẩm.")
            finally:
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                time.sleep(1)

        if len(products) >= total_required or not go_to_next_page(driver):
            break
    return products


def save_to_csv(products, filename="200.csv"):
    if not products:
        print("❌ Không có dữ liệu để lưu.")
        return
    keys = products[0].keys()
    with open(filename, "w", newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, keys)
        writer.writeheader()
        writer.writerows(products)
    print(f"✅ Đã lưu {len(products)} sản phẩm vào '{filename}'.")


def open_amazon_homepage():
    options = Options()
    options.add_argument("--window-size=1366,768")
    driver = webdriver.Chrome(options=options)
    driver.get("https://www.amazon.com/")
    if is_captcha_present(driver):
        wait_for_captcha_to_be_solved(driver)
    return driver


def search_new_topic(driver, topic):
    try:
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "twotabsearchtextbox"))
        )
        search_box.clear()
        search_box.send_keys(topic)
        search_box.submit()
        print(f"🔍 Đã tìm kiếm: {topic}")
        time.sleep(5)
    except Exception as e:
        print(f"❌ Lỗi khi tìm kiếm topic '{topic}': {e}")
        return False
    return True


if __name__ == "__main__":
    topics = [
        "boys shorts",
        "girls dresses",
        "girls shoes",
        "girl's briefs",
        "girl clothing"
    ]

    driver = open_amazon_homepage()

    for topic in topics:
        print(f"\n🚀 Bắt đầu crawl cho topic: {topic}")

        driver.get("https://www.amazon.com/")
        if is_captcha_present(driver):
            wait_for_captcha_to_be_solved(driver)

        if not search_new_topic(driver, topic):
            continue

        products = crawl_amazon_list_first(driver, total_required=200)

        filename = topic.lower().replace(" ", "_") + ".csv"
        save_to_csv(products, filename)

        print(f"✅ Hoàn tất topic: {topic}")

    print("\n🎉 Đã crawl xong toàn bộ các topic.")
    driver.quit()
