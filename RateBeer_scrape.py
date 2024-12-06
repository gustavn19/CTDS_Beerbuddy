import logging
import sqlite3
import warnings
import requests
import multiprocessing as mp
import pandas as pd
from urllib.parse import urljoin
import os
import time
import gc

# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    StaleElementReferenceException,
)
from selenium.webdriver.remote.remote_connection import LOGGER as selenium_logger

# WebDriver Manager
from webdriver_manager.chrome import ChromeDriverManager

# Multiprocessing imports
from multiprocessing import Pool
from functools import partial

# BeautifulSoup for HTML parsing
from bs4 import BeautifulSoup

# Suppress Python warnings
warnings.filterwarnings("ignore")

# Global headers for the requests
headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/86.0.4240.111 Safari/537.36"
    )
}

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Suppress WebDriver Manager logs
logging.getLogger("webdriver_manager").setLevel(logging.ERROR)
os.environ['WDM_LOG'] = '0'

# Set up SQLite database
db_conn = sqlite3.connect("beer_data.db")
cursor = db_conn.cursor()



# Initialize the WebDriver (use the path to your WebDriver)
def initialize_selenium_driver():

    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
    browser = webdriver.Chrome(options=options)
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_experimental_option(
        "prefs", {
            # block image loading
            "profile.managed_default_content_settings.images": 2,
        }
    )
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

    return driver

# Function to handle the cookie banner
def handle_cookie_banner(driver):
    try:
        # Wait for the cookie banner to appear
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "onetrust-button-group"))
        )
        # Click the dismiss or accept button
        cookie_button = driver.find_element(By.ID, "onetrust-reject-all-handler")
        cookie_button.click()
    except Exception as e:
        pass

# Set reviews per page to 100
def set_reviews_per_page_100(driver):
    try:
        # Handle any potential cookie banners
        handle_cookie_banner(driver)

        # Wait for the dropdown toggle to appear
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'MuiTablePagination-select')]"))
        )

        # Click the dropdown toggle to open the menu
        dropdown_toggle = driver.find_element(By.XPATH, "//div[contains(@class, 'MuiTablePagination-select')]")
        dropdown_toggle.click()

        # Wait for the dropdown options to appear
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//li[contains(@class, 'MuiMenuItem-root') and text()='100']"))
        )

        # Click the "100" option
        option_100 = driver.find_element(By.XPATH, "//li[contains(@class, 'MuiMenuItem-root') and text()='100']")
        option_100.click()
        #logging.info("Set reviews per page to 100.")
        
    except Exception as e:
        logging.error(f"Error setting reviews per page: {e}")
    
# Function to save data to the database   
def initialize_database():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS beers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        brewery TEXT,
        subgenre,
        abv REAL,
        location TEXT,
        rating REAL,
        average_rating REAL,
        reviewer TEXT,
        review_date TEXT,
        review_text TEXT,
        algorithm_rating REAL,
        total_reviews INTEGER
    )
    """)
    db_conn.commit()

# Update the function to save reviews
def save_to_db(reviews, subgenre):
    for review in reviews:
        review['subgenre'] = subgenre

    cursor.executemany("""
    INSERT INTO beers (
        name,
        brewery,
        subgenre,
        location,
        review_date,
        rating,
        average_rating,
        abv,
        review_text,
        reviewer,
        algorithm_rating,
        total_reviews
    ) 
    VALUES (
        :Name, 
        :Brewer,
        :subgenre,
        :Location, 
        :Date, 
        :Rating, 
        :Average_rating, 
        :ABV, 
        :Text, 
        :Reviewer, 
        :Algorithm_rating, 
        :Total_reviews
    )
    """, reviews)
    db_conn.commit()

# Function to save reviews into the database
def save_reviews_to_db(reviews, subgenre):
    try:
        if reviews:
            save_to_db(reviews, subgenre)  # Save reviews using the updated function
            #logging.info(f"Saved {len(reviews)} reviews to the database.")
        else:
            logging.error("No reviews to save for subgenre: {subgenre}")
    except Exception as e:
        logging.error(f"Error saving reviews to database: {e}")

# Function to extract the options from the dropdowns
def extract_select(driver):

    countries = []
    styles = []
    
    try:
        # Extract options for the StyleMenu
        select_element = Select(driver.find_element(By.ID, "StyleMenu"))
        for option in select_element.options:
            if option.text == "All Styles" or option.text == "---":
                continue
            styles.append((option.get_attribute("name"), option.text))  # (name, text)

        # Extract options for the CountryMenu
        select_element = Select(driver.find_element(By.ID, "CountryMenu"))
        for option in select_element.options:
            if option.text == "All Countries" or option.text == "---":
                continue
            if option.text == "United States":
                countries.append(("us", "United States"))  # (name, text)
            else:
                countries.append((option.get_attribute("name"), option.text))  # (name, text)
        
    except Exception as e:
        logging.error(f"Error extracting selects: {e}")
    return styles, countries

# Function to scrape the beers for a given style and country    
def scrape_style_country(driver, url, style, country):   
    driver.get(url)
    try:
        # Wait for table body to load, ensuring data is present
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "tbody"))
        )
        #logging.info("Table loaded successfully.")
        table = driver.find_element(By.CLASS_NAME, "table")
        
        # Extract table rows
        rows = table.find_element(By.TAG_NAME, "tbody").find_elements(By.TAG_NAME, "tr")
        data = []

        for row in rows[1:]:
            # Extract data from each row
            cells = row.find_elements(By.TAG_NAME, "td")
            row_data = {
                "Name": cells[1].find_element(By.TAG_NAME, "a").text.strip(),
                "Count": cells[2].text,
                "ABV": cells[3].text,
                "Score": cells[4].text,
                "Country": country,
                "Style": style,
                "URL": cells[1].find_element(By.TAG_NAME, "a").get_attribute("href")
            }
            if int(cells[2].text) > 10:
                data.append(row_data)
    except Exception as e:
        logging.error(f"Error extracting table for {style} in {country}")
        
        # Return an empty list if no data is found
        return []

    return data

# Helper to extract text from an element
def extract_text(element, xpath, default="Unknown"):
    try:
        return element.find_element(By.XPATH, xpath).text.strip()
    except Exception:
        return default

# Helper to click a button and handle scrolling
def click_button(driver, button_xpath):
    try:
        button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, button_xpath))
        )

        driver.execute_script("arguments[0].scrollIntoView(false);", button)
        button.click()
        return True
    except Exception as e:
        #logging.error(f"Error clicking button: {e}")
        return False

# Extract the algorithm rating
def get_algorithm_rating(driver):
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[contains(@class, 'BeerRatingsWidget')]//div[contains(@class, 'MuiTypography-root')]")
            )
        )
        return driver.find_element(
            By.XPATH, "//div[contains(@class, 'BeerRatingsWidget')]//div[contains(@class, 'MuiTypography-root')]"
        ).text.strip()
    except Exception as e:
        logging.error(f"Error extracting algorithm rating: {e}")
        return None

# Extract reviews from a page
def extract_reviews_from_page(driver, name, brewer_name, avg_score, abv, alg_rating, count, show_review):
    reviews = []
    try:
        parent_div = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((
                    By.XPATH, 
                    "(//div[contains(@class, 'MuiPaper-root') and contains(@class, 'Paper___StyledMPaper-MfXTu') and contains(@class, 'MuiPaper-elevation1') and contains(@class, 'MuiPaper-rounded') and .//div[contains(@class, 'pt-4 pb-3')] and .//div[contains(@class, 'fj-sb fa-c')]]//div[.//div[contains(@class, 'py-4')]])[1]"
                ))
            )

        review_elements = parent_div.find_elements(By.XPATH, ".//div[contains(@class, 'py-4')]")

        for review_element in review_elements:
            try:
                reviewer_name = extract_text(review_element, ".//a/span[1]")
                review_location = extract_text(
                    review_element,
                    ".//div[contains(@class, 'MuiTypography-root Text___StyledTypographyTypeless-bukSfn')]"
                )

                review_rating = extract_text(
                    review_element,
                    ".//span[contains(@class, 'MuiTypography-root Text___StyledTypographyTypeless-bukSfn') and contains(@class, 'MuiTypography-subtitle1')]"
                )

                review_date = extract_text(
                    review_element,
                    ".//span[contains(@class, 'MuiTypography-root Text___StyledTypographyTypeless-bukSfn') and contains(@class, 'MuiTypography-root Text___StyledTypographyTypeless-bukSfn kbrPIo colorized__WrappedComponent-hrwcZr gRvDpm ml-3 MuiTypography-caption')]"
                )

                review_text = extract_review_text(driver, review_element)

                if show_review:
                    print(reviewer_name, brewer_name, review_location, review_rating, review_date, review_text)
                    print("=" * 40)

                review = {
                    "Name": name,
                    "Brewer": brewer_name,
                    "Reviewer": reviewer_name,
                    "Location": review_location,
                    "Date": review_date,
                    "Rating": review_rating,
                    "Average_rating": avg_score,
                    "ABV": abv,
                    "Text": review_text,
                    "Algorithm_rating": alg_rating,
                    "Total_reviews": count
                }
                reviews.append(review)
            except Exception as e:
                logging.error(f"Error extracting a single review: {e}")
    except Exception as e:
        logging.error(f"Error extracting reviews from page: {e}")
    return reviews

# Helper to extract review text
def extract_review_text(driver, review_element):
    try:
        read_more_button = review_element.find_element(
            By.XPATH, ".//button[.//span[@class='MuiButton-label']]"
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", read_more_button)
        read_more_button.click()
        
        expanded_text = review_element.find_element(
                By.XPATH, ".//div[contains(@class, 'MuiTypography-root Text___StyledTypographyTypeless-bukSfn pzIrn colorized__WrappedComponent-hrwcZr hwjOn BeerReviewListItem___StyledText-kMbsdb gCtEHi pre-wrap MuiTypography-body1')]"
            ).text.strip()
        
        return expanded_text

    except Exception as e:
        collapsed_text = review_element.find_element(
            By.XPATH, ".//div[contains(@class, 'LinesEllipsis')]"
        ).text.strip()
        
        return collapsed_text

# Main scraping function
def scrape_reviews(driver, beer, show_review = False):
    name = beer["Name"]
    url = beer["URL"]
    count = beer["Count"]
    abv = beer["ABV"]
    avg_score = beer["Score"]

    driver.get(url)

    try:
        alg_rating = get_algorithm_rating(driver)
        brewer_name = extract_text(driver, "//div[@class='fj-sb fa-s mb-3']//a")
    except Exception as e:
        logging.error(f"Error extracting initial data: {e}")
        return {"Algorithm Rating": None, "Reviews": []}

    reviews = []
    page_count = 0
    while page_count <= int(count) // 100:
        set_reviews_per_page_100(driver)
        reviews.extend(
            extract_reviews_from_page(
                driver, name, brewer_name, avg_score, abv, alg_rating, count, show_review
            )
        )
        
        if not click_button(driver, "//button[@title='Next page' and @aria-label='Next page']"):
            break
        page_count += 1

    return reviews

# Function to scrape a single beer 
def scrape_single_beer(beer, subgenre):
    driver = initialize_selenium_driver()  # Create a new Selenium WebDriver instance
    try:
        reviews = scrape_reviews(driver, beer)  # Collect reviews for the beer
        save_reviews_to_db(reviews, subgenre)  # Save reviews to the database
        #logging.info(f"Scraped {beer['Name']} with {len(reviews)} reviews")  # Log the successful scrape
        return beer['Name']
    finally:
        driver.quit()  # Ensure the WebDriver is closed

# Function to scrape all beers for a given subgenre
def scrape_all_beers_multiprocessed(beers, subgenre):
    # Create a pool of worker processes
    
    num_processes = min(len(beers), mp.cpu_count() - 2)  # Adjust for available CPUs
    #num_processes = 1
    with Pool(num_processes) as pool:
        scrape_func = partial(scrape_single_beer, subgenre=subgenre)
        
        # Convert the DataFrame rows into dictionaries for easier multiprocessing
        beer_list = pd.DataFrame(beers).to_dict('records')
        
        # Run the function on each beer in parallel
        results = pool.map(scrape_func, beer_list)

country_url = r"https://www.ratebeer.com/top/all"

from tqdm import tqdm

top_countries = [
    ('germany', 'Germany'), ('czech-republic', 'Czech Republic'), ('us', 'United States'), 
    ('china', 'China'), ('belgium', 'Belgium'), ('england', 'England'), 
    ('russia', 'Russia'), ('ireland', 'Ireland'), ('australia', 'Australia'), 
    ('mexico', 'Mexico'), ('canada', 'Canada'), ('netherlands', 'Netherlands'), 
    ('austria', 'Austria'), ('poland', 'Poland'), ('spain', 'Spain'), 
    ('brazil', 'Brazil'), ('thailand', 'Thailand'), ('france', 'France'), 
    ('italy', 'Italy'), ('hungary', 'Hungary'), ('south-africa', 'South Africa'), 
    ('denmark', 'Denmark'), ('slovak-republic', 'Slovak Republic'), ('romania', 'Romania'), 
    ('croatia', 'Croatia'), ('argentina', 'Argentina'), ('portugal', 'Portugal')
]

# Main driver code
if __name__ == "__main__":
    
    initialize_database()

    mainDriver = initialize_selenium_driver()

    logging.info("Loading all countries and styles...")
    # Load the main page
    mainDriver.get(country_url)

    # Get all countries and styles
    actual_styles, countries = extract_select(mainDriver)
    mainDriver.quit()

    logging.info("Scraping all countries for all styles")
    
    # Reverse countries
    #countries = top_countries[::-1]
    
    last_country = "United States"
    last_style = "English Strong Ale"
    styles = []
    # Make countries start after last country
    for i, country in enumerate(countries):
        if country[1] == last_country:
            countries = countries[i:]
            break
    
    # Make styles start after last style
    for i, style in enumerate(actual_styles):
        if style[1] == last_style:
            styles = actual_styles[i:]
            break
    
    if styles == []:
        styles = actual_styles
        
    print(countries)
    print(styles)
    
    for country in countries:
        # Check if the country matches the criteria
        for style in tqdm(styles):
            if "Saké" not in style[1]:
                tqdm.write(f"Scraping {country[1]} for {style[1]}")
                style_name, style_text = style
                style_country_driver = initialize_selenium_driver()
                country_name, country_text = country   
                url = f"https://www.ratebeer.com/top/{style_name}/{country_name}"
                
                beers = scrape_style_country(style_country_driver, url, style=style_text, country=country_text)
                
                if beers == []:
                    style_country_driver.quit()
                    continue
                
                style_country_driver.quit()
                scrape_all_beers_multiprocessed(beers, style_text)
                
                gc.collect()
        
        styles = actual_styles
            
            
        
        
        