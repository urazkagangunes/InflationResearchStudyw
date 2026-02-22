import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime
import os

# --- Configuration ---
BASE_URL = "https://mopas.com.tr"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}


def get_category_links():
    """Finds all department links on the homepage."""
    print("Step 1: Fetching category links from homepage...")
    response = requests.get(BASE_URL, headers=HEADERS)
    category_urls = []

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        all_links = soup.find_all("a")

        for link in all_links:
            href = link.get("href")
            if href and "/c/" in href:
                if href.startswith("http"):
                    full_url = href
                else:
                    full_url = BASE_URL + href

                if full_url not in category_urls:
                    category_urls.append(full_url)

        print(f"Found {len(category_urls)} categories.")
        return category_urls
    else:
        print("Failed to load homepage.")
        return []


def scrape_entire_market():
    """Crawls through categories and pages to scrape all products."""
    categories = get_category_links()
    all_products_data = []

    # The slice has been removed. It will now loop through ALL categories.
    for category_index, category_url in enumerate(categories):
        print(f"\n--- Scanning Category {category_index + 1}/{len(categories)}: {category_url} ---")

        page_num = 0

        while True:
            page_url = f"{category_url}?q=%3Arelevance&page={page_num}"
            print(f"  Loading Page {page_num + 1}...")

            response = requests.get(page_url, headers=HEADERS)

            if response.status_code != 200:
                print(f"  Failed to load page {page_num + 1}. Moving to next category.")
                break

            soup = BeautifulSoup(response.content, "html.parser")
            products = soup.find_all("div", class_="card")

            if len(products) == 0:
                print(f"  No more items found on page {page_num + 1}. Category finished.")
                break

            items_scraped_this_page = 0
            for product in products:
                try:
                    # 1. Extract raw text
                    title_tag = product.find("a", class_="product-title")
                    title = title_tag.text.strip() if title_tag else ""

                    price_tag = product.find("span", class_="sale-price")
                    raw_price = price_tag.text.strip() if price_tag else ""

                    quantity_tag = product.find("p", class_="quantity")
                    quantity = quantity_tag.text.strip().replace('\xa0', ' ').replace('&nbsp;', ' ').replace('&nbsp',
                                                                                                             ' ') if quantity_tag else ""

                    # 2. Process and format the data
                    if title:
                        full_name = f"{title} {quantity}".strip()
                        clean_price = raw_price.replace('₺', '').replace('.', '').replace(',', '.').strip()

                        all_products_data.append({
                            "name": full_name,
                            "price": clean_price
                        })
                        items_scraped_this_page += 1

                except Exception as e:
                    pass

            print(f"  Scraped {items_scraped_this_page} items.")
            page_num += 1
            time.sleep(2)


            # --- Save the Final Data ---
            if all_products_data:
                df = pd.DataFrame(all_products_data)

                today_date = datetime.now().strftime("%Y-%m-%d")

                # 1. Tell Python to create the 'data' folder if it accidentally gets deleted
                os.makedirs("data", exist_ok=True)

                # 2. Add 'data/' to the beginning of the filename
                filename = f"data/mopas_prices_{today_date}.csv"

                df.to_csv(filename, index=False, encoding='utf-8-sig')

                print(f"\nSUCCESS! Scraped a total of {len(all_products_data)} items.")
                print(f"Data saved to {filename}")
            else:
                print("\nNo data was collected.")


# Run the crawler
scrape_entire_market()