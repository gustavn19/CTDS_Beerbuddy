from bs4 import BeautifulSoup
import sqlite3
import requests
import pandas as pd

# Global headers for the requests
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36"
}


test_url = "https://www.ratebeer.com/beer/uerige-doppel-sticke/46158/"

def scrape_beer_data(url):
    page = 1
    try:
        response = requests.get(url, headers=headers)
        
        print(response.text)  # Print raw HTML content

        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        # Find header with algorithm rating
        print(soup)
        if page == 1:
            alg_rating = soup.find("div", lass="MuiTypography-root Text___StyledTypographyTypeless-bukSfn pzIrn colorized__WrappedComponent-hrwcZr iMppQo MuiTypography-body2")
            alg_rating = alg_rating.get_text(strip=True) if alg_rating else None
            print(alg_rating)
    except requests.RequestException as e:
        print(f"Request failed for page {page}: {e}")
        return []

scrape_beer_data(test_url)
