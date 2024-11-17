from bs4 import BeautifulSoup
import requests
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from urllib.parse import urljoin

# Global headers for the requests
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36"
}

# Function to scrape main genres, subgenres, and their URLs
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

# Function to scrape beers from subgenre
# Initialize the WebDriver (use the path to your WebDriver)
driver_path = "path/to/chromedriver"  # Replace with your WebDriver path
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Run in headless mode
# selenium 4
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))

def scrape_beers_from_subgenre(subgenre_url):
    # Load the URL
    driver.get(subgenre_url)
    
    try:
        # Wait for the table to load (adjust timeout as needed)
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
        print(f"Error: {e}")
        return None

    finally:
        driver.quit()  # Close the browser after scraping

# Example usage
style_url = "https://www.ratebeer.com/beerstyles/"

# Scrape beer styles and their links
beer_styles = scrape_beer_styles_with_links(style_url)

# Use the first subgenre under "Anglo-American Ales"
test_subgenre_url = beer_styles["Anglo-American Ales"][0]["url"]

# Scrape beers from the subgenre
beers = scrape_beers_from_subgenre(test_subgenre_url)

# Print the first 10 urls

print(beers.iloc[0, 2])  # Display the first url


