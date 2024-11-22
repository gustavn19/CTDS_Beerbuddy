from bs4 import BeautifulSoup
import sqlite3
import requests
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from urllib.parse import urljoin

# selenium 4
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

import logging
import time
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    StaleElementReferenceException,
)


# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Function to scrape beer styles with links
def scrape_beer_styles_with_links(url):
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")
    
    # Find all columns containing genres and subgenres
    columns = soup.find_all("div", class_="col-lg-4 col-xl-4 col-md-6")
    
    beer_styles = {}
    
    for column in columns:
        try:
            # Extract main genre (h3 element)
            genre = column.find("h3").get_text(strip=True)
            
            # Extract all subgenres (li > a elements inside the ul.styleGroup) with names and URLs
            subgenres = [
                {
                    "name": a.get_text(strip=True),
                    "url": "https://www.ratebeer.com" + a["href"]
                }
                for li in column.find_all("li")
                if (a := li.find("a"))  # Extract <a> tag from each <li>
            ]
            
            if genre and subgenres:
                beer_styles[genre] = subgenres
        except AttributeError:
            continue
    
    return beer_styles

# Function to scrape beers from a subgenre URL
def scrape_beers_from_subgenre(driver, subgenre_url):
    # Load the URL
    driver.get(subgenre_url)
    time.sleep(1)
    
    try:
        # Wait for table body to load, ensuring data is present
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "tbody"))
        )

        logging.info("Table loaded successfully.")
        
        table = driver.find_element(By.CLASS_NAME, "table-striped")
        
        # Extract table headers
        headers = [
            th.text.strip() for th in table.find_element(By.TAG_NAME, "thead").find_elements(By.TAG_NAME, "th")
        ]
        
        # Extract table rows
        rows = table.find_element(By.TAG_NAME, "tbody").find_elements(By.TAG_NAME, "tr")
        data = []
        
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            row_data = []
            
            for idx, cell in enumerate(cells):
                if idx == 1:  # Check if it's the second <td> (name column)
                    link_element = cell.find_element(By.TAG_NAME, "a")  # Get the <a> tag
                    name = link_element.text.strip()  # Extract the name
                    
                    # Extract the full href
                    href = link_element.get_attribute("href")
                    
                    # Ensure it is absolute
                    href = urljoin("https://www.ratebeer.com", href)
                    
                    row_data.append(name)  # Append the name
                    row_data.append(href)  # Append the href
                else:
                    row_data.append(cell.text.strip())  # Append the regular text
                    
            data.append(row_data)

        # Update headers to include the URL column
        headers.insert(2, "URL")  # Add "URL" header after the "Name" header

        # Create a DataFrame
        df = pd.DataFrame(data, columns=headers)
        return df

    except Exception as e:
        logging.error(f"Error: {e}")
        return None

# Centralized utility for extracting text with error handling
def safe_get_text(element, xpath, default=None):
    try:
        return element.find_element(By.XPATH, xpath).text.strip()
    except NoSuchElementException:
        logging.warning(f"Element not found for XPath: {xpath}")
        return default
    except Exception as e:
        logging.error(f"Error fetching text: {e}")
        return default

# Centralized utility for clicking buttons
def safe_click(driver, xpath, retries=3):
    for attempt in range(retries):
        try:
            button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, xpath)))
            button.click()
            return True
        except (NoSuchElementException, TimeoutException, StaleElementReferenceException) as e:
            logging.warning(f"Attempt {attempt + 1} failed for clicking XPath: {xpath}. Error: {e}")
            time.sleep(2)  # Wait and retry
    logging.error(f"Failed to click XPath after {retries} attempts: {xpath}")
    return False

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
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//li[contains(@class, 'MuiMenuItem-root') and text()='100']"))
        )

        # Click the "100" option
        option_100 = driver.find_element(By.XPATH, "//li[contains(@class, 'MuiMenuItem-root') and text()='100']")
        option_100.click()
        #logging.info("Set reviews per page to 100.")
        
    except Exception as e:
        logging.error(f"Error setting reviews per page: {e}")

# Function to scrape beer reviews
def scrape_reviews(driver, beer, show_review=False):
    name = beer["NAME"]
    url = beer["URL"]
    count = beer["COUNT"]
    abv = beer["ABV"]
    avg_score = beer["SCORE"]
    reviews = []

    
    driver.get(url)
    morePages = True
    page_count = 0

    # Extract the algorithm rating
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.XPATH, "//div[contains(@class, 'BeerRatingsWidget')]//div[contains(@class, 'MuiTypography-root') and contains(@class, 'Text___StyledTypographyTypeless-bukSfn')]")
        )
    )
    # Locate the element with the rating
    alg_rating = driver.find_element(
        By.XPATH, "//div[contains(@class, 'BeerRatingsWidget')]//div[contains(@class, 'MuiTypography-root') and contains(@class, 'Text___StyledTypographyTypeless-bukSfn')]"
    ).text.strip()

    # Locate the brewer name
    brewer_name = driver.find_element(
        By.XPATH, "//div[@class='fj-sb fa-s mb-3']//a"
    ).text.strip()


    while morePages:
        try:
            
            # Set reviews per page to 100
            set_reviews_per_page_100(driver)

            # Extract the algorithm rating
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[contains(@class, 'BeerRatingsWidget')]//div[contains(@class, 'MuiTypography-root') and contains(@class, 'Text___StyledTypographyTypeless-bukSfn')]")
                )
            )

            # Locate the element with the rating
            alg_rating_element = driver.find_element(
                By.XPATH, "//div[contains(@class, 'BeerRatingsWidget')]//div[contains(@class, 'MuiTypography-root') and contains(@class, 'Text___StyledTypographyTypeless-bukSfn')]"
            )

            # Extract the rating text
            alg_rating = alg_rating_element.text.strip()
            

            # Wait for the parent container to load
            parent_div = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((
                    By.XPATH, 
                    "(//div[contains(@class, 'MuiPaper-root') and contains(@class, 'Paper___StyledMPaper-MfXTu') and contains(@class, 'MuiPaper-elevation1') and contains(@class, 'MuiPaper-rounded') and .//div[contains(@class, 'pt-4 pb-3')] and .//div[contains(@class, 'fj-sb fa-c')]]//div[.//div[contains(@class, 'py-4')]])[1]"
                ))
            )

            # Find all div elements with class="py-4" within the parent element
            review_elements = parent_div.find_elements(By.XPATH, ".//div[contains(@class, 'py-4')]")

            #logging.info(f"{name}: Scraping page {page_count + 1}, reviews found: {len(review_elements)}. Currently collected {len(reviews)} reviews.")
            page_count += 1
            page_reviews = 0
            #print("=====================================")
            for review_element in review_elements:
                try:
                    # Extract reviewer name
                    reviewer_name = review_element.find_element(
                        By.XPATH, ".//a/span[1]"
                    ).text.strip()

                    # Extract review location
                    try:
                        review_location = review_element.find_element(
                            By.XPATH, ".//div[contains(@class, 'MuiTypography-root Text___StyledTypographyTypeless-bukSfn pzIrn colorized__WrappedComponent-hrwcZr hwjOn MuiTypography-body2')]"  # Update with the correct class if needed
                        ).text.strip()

                        review_location_short = review_location[:2]
                        review_location = review_location[2:]
                    except Exception as e:
                        review_location = "Unknown"
                        review_location_short = "Un"
                    
                    # TODO - Add IBV

                    # Extract review rating
                    review_rating = review_element.find_element(
                        By.XPATH, ".//span[contains(@class, 'MuiTypography-root Text___StyledTypographyTypeless-bukSfn pzIrn text-500 colorized__WrappedComponent-hrwcZr bRPQdN MuiTypography-subtitle1')]"  # Update with the correct class if needed
                    ).text.strip()

                    # Extract review date
                    review_date = review_element.find_element(
                        By.XPATH, ".//span[contains(@class, 'MuiTypography-root Text___StyledTypographyTypeless-bukSfn kbrPIo colorized__WrappedComponent-hrwcZr gRvDpm ml-3 MuiTypography-caption')]"  # Update with the correct class if needed
                    ).text.strip()

                    # Extract review text by first trying to press the "Read More" button
                    expand = False
                    try:
                        read_more_button = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, ".//button[contains(@class, 'MuiButtonBase-root MuiButton-root MuiButton-text Button___StyledMaterialButton-FZwYh bGOCJz colorized__WrappedComponent-apsCh kAVjHC -ml-3 MuiButton-textPrimary')]"))
                        )
                        driver.execute_script("arguments[0].scrollIntoView(true);", read_more_button)
                        
                        expand = True

                    except Exception as e:
                        logging.error(f"Error clicking read more button: {e}")
                        pass
                    
                    try:
                        if expand:
                            # Try to get the text when expanded
                            review_text = review_element.find_element(
                                By.XPATH, ".//div[contains(@class, 'MuiTypography-root Text___StyledTypographyTypeless-bukSfn pzIrn colorized__WrappedComponent-hrwcZr hwjOn BeerReviewListItem___StyledText-kMbsdb gCtEHi pre-wrap MuiTypography-body1')]"
                            ).text.strip()
                        else:
                            # Fallback to clamped text if not expanded
                            review_text = review_element.find_element(
                                By.XPATH, ".//div[contains(@class, 'LinesEllipsis  ')]"
                            ).text.strip()
                    except Exception as e:
                        # Log or print an error if neither option works
                        logging.error(f"Error extracting review text after expansion: {e}")
                        review_text = None
                    if show_review:
                        print(reviewer_name)
                        print(brewer_name)
                        print(review_location_short, review_location)
                        print(review_rating)
                        print(review_date)
                        print(review_text)
                        print("=====================================")
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
                    
                    # Debugging: Uncomment to limit the number of reviews per page
                    #page_reviews += 1
                    #if page_reviews >= 2:
                    #    break

                except Exception as e:
                    logging.error(f"Error extracting review: {e}")
            if page_count > int(count) // 100:
                morePages = False
            else:
                try:
                    # Click the next page button
                    next_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[@title='Next page' and @aria-label='Next page']"))
                    )
                    driver.execute_script("arguments[0].scrollIntoView(false);", next_button)
                    next_button.click()
                except Exception as e:
                    logging.error(f"Error clicking next page button: {e}")
                    morePages = False
        except Exception as e:
            logging.error(f"Error scraping the page for {name}: {e}")
            return {"Algorithm Rating": None, "Reviews": []}
    logging.info(f"{name}: Finished - Collected {len(reviews)} reviews")
    return reviews

# Function to save data to the database   
def initialize_database():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS beers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        link TEXT,
        brewery TEXT,
        genre,
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
def save_to_db(reviews, genre, subgenre):
    for review in reviews:
        review['genre'] = genre
        review['subgenre'] = subgenre

    cursor.executemany("""
    INSERT INTO beers (
        name,
        brewery,
        genre,
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
        :genre,
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
def save_reviews_to_db(reviews, genre, subgenre):
    try:
        if reviews:
            save_to_db(reviews, genre, subgenre)  # Save reviews using the updated function
            logging.info(f"Saved {len(reviews)} reviews to the database.")
        else:
            logging.error("No reviews to save for genre: {genre}, subgenre: {subgenre}")
    except Exception as e:
        logging.error(f"Error saving reviews to database: {e}")

import multiprocessing
from multiprocessing import Pool
from functools import partial

def scrape_single_beer(beer, genre, subgenre):
    driver = initialize_selenium_driver()  # Create a new Selenium WebDriver instance
    try:
        logging.info(f"Starting scrape for beer: {beer['NAME']}")
        reviews = scrape_reviews(driver, beer)  # Collect reviews for the beer
        save_reviews_to_db(reviews, genre, subgenre)  # Save reviews to the database
        logging.info(f"Completed scrape for beer: {beer['NAME']}")
        return beer['NAME']
    finally:
        driver.quit()  # Ensure the WebDriver is closed

# Main driver loop for scraping beers using multiprocessing
def scrape_all_beers_multiprocessed(beers, genre, subgenre):
    # Create a pool of worker processes
    num_processes = min(len(beers), multiprocessing.cpu_count() - 4)  # Adjust for available CPUs
    with Pool(num_processes) as pool:
        # Partially bind the function to fixed arguments (genre, subgenre)
        scrape_func = partial(scrape_single_beer, genre=genre, subgenre=subgenre)
        
        # Convert the DataFrame rows into dictionaries for easier multiprocessing
        beer_list = beers.to_dict('records')
        
        # Run the function on each beer in parallel
        results = pool.map(scrape_func, beer_list)

    logging.info(f"All beers scraped. Results: {results}")
# Initialize the WebDriver (use the path to your WebDriver)
def initialize_selenium_driver():
    # Initialize the Chrome WebDriver
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))

    return driver

# Set up SQLite database
db_conn = sqlite3.connect("beer_data.db")
cursor = db_conn.cursor()

# Global headers for the requests
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36"
}

# Main driver code
if __name__ == "__main__":
    # Initialize the database
    initialize_database()
    
    # Scrape beer styles and their links
    style_url = "https://www.ratebeer.com/beerstyles/"
    beer_styles = scrape_beer_styles_with_links(style_url)

    main_driver = initialize_selenium_driver()
    # Loop through each style
    for genre, subgenres in beer_styles.items():
        for subgenre in subgenres:
            print(f"Scraping subgenre: {subgenre['name']}")
            print(f"URL: {subgenre['url']}")
            beers = scrape_beers_from_subgenre(main_driver, subgenre["url"])
            scrape_all_beers_multiprocessed(beers, genre, subgenre["name"])
            
  
