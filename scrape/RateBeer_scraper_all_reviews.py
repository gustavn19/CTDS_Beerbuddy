import requests
from bs4 import BeautifulSoup
import csv
import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Define the base URL for RateBeer beer ratings
base_url = "https://www.ratebeer.com/beer-ratings/0/{}/"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36"
}

# Set up SQLite database
db_conn = sqlite3.connect("beer_data.db")
cursor = db_conn.cursor()

# Create table
cursor.execute("""
CREATE TABLE IF NOT EXISTS beers (
    name TEXT,
    link TEXT,
    rating TEXT,
    brewery TEXT,
    location TEXT,
    description TEXT,
    reviewer TEXT,
    reviewer_profile TEXT
)
""")
db_conn.commit()

def save_to_db(data):
    cursor.executemany("""
    INSERT INTO beers (name, link, rating, brewery, location, description, reviewer, reviewer_profile)
    VALUES (:name, :link, :rating, :brewery, :location, :description, :reviewer, :reviewer_profile)
    """, data)
    db_conn.commit()

def scrape_beer_data(page_number):
    if page_number == 1:
        url = "https://www.ratebeer.com/beer-ratings/"
    else:
        url = base_url.format(page_number)
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        table = soup.find("table", class_="table")
        
        if not table:
            return []
        
        beers = []
        for row in table.find_all("tr"):
            try:
                beer_name_tag = row.find("a", style="font-size:20px; font-weight:bold;")
                beer_name = beer_name_tag.get_text(strip=True) if beer_name_tag else None
                beer_link = beer_name_tag["href"] if beer_name_tag else None
                if beer_link:
                    beer_link = "https://www.ratebeer.com" + beer_link  # Construct full URL

                rating_tag = row.find("span", class_="uas")
                rating = rating_tag.get_text(strip=True) if rating_tag else None

                brewery_tag = row.find("a", href=lambda href: href and "/brewers/" in href)
                brewery = brewery_tag.get_text(strip=True) if brewery_tag else None
                location_tag = row.find("span", class_="small", style="color:#8b8b8b;")
                location = location_tag.get_text(strip=True) if location_tag else None

                description_tag = row.find("div", style="color:#666;")
                description = description_tag.get_text(strip=True) if description_tag else None

                reviewer_tag = row.find("a", class_="small", href=lambda href: href and "/user/" in href)
                reviewer = reviewer_tag.get_text(strip=True) if reviewer_tag else None
                reviewer_link = reviewer_tag["href"] if reviewer_tag else None
                
                # Only add rows with essential info
                if beer_name:
                    beers.append({
                        "name": beer_name,
                        "brewery": brewery,
                        "location": location,
                        "rating": rating,
                        "description": description,
                        "link": beer_link,
                        "reviewer": reviewer,
                        "reviewer_profile": reviewer_link
                    })
                    
            except AttributeError:
                continue
        return beers

    except requests.RequestException as e:
        print(f"Request failed for page {page_number}: {e}")
        return []

def scrape_all_pages_concurrently(page_limit=10, max_workers=5, chunk_size=100):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(scrape_beer_data, page): page for page in range(1, page_limit + 1)}
        scraped_count = 0
        
        for future in as_completed(futures):
            page = futures[future]
            try:
                beers = future.result()
                if beers:
                    save_to_db(beers)
                    scraped_count += len(beers)
                    print(f"Page {page}: {len(beers)} beers scraped. Total: {scraped_count}")
                # Sleep to prevent overwhelming the server

            except Exception as e:
                print(f"Scraping failed for page {page}: {e}")

# Scrape with robust handling
scrape_all_pages_concurrently(page_limit=100000, max_workers=8)

# Close the database connection
db_conn.close()

