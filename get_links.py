from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import os

# Install Chrome WebDriver if you don't have it:
# Download from: https://sites.google.com/a/chromium.org/chromedriver/downloads
# Note: The WebDriver version should match your Chrome browser version

# Base URL configuration
BASE_URL = "https://www.cia.gov"
SEARCH_URL = "https://www.cia.gov/readingroom/advanced-search-view?keyword=disinformation"

def setup_driver():
    options = Options()
    # options.add_argument("--headless")  # Run in headless mode - uncomment if you don't want to see the browser
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")  # Try to avoid detection
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Create a new ChromeDriver service
    service = Service()  # Put path to chromedriver here if needed
    
    # Create the driver
    driver = webdriver.Chrome(service=service, options=options)
    
    # Set a user agent
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {
        "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    return driver

def extract_document_links(driver):
    # Wait up to 30 seconds for the table to load
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, "views-table"))
        )
        print("Table found! Extracting links...")
    except Exception as e:
        print(f"Error waiting for table: {e}")
        # Save page source for debugging
        with open("page_after_wait.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print("Saved page source to page_after_wait.html")
        return []

    # Parse the page with BeautifulSoup after JavaScript execution
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # Find the table
    table = soup.find('table', class_='views-table')
    if not table:
        print("Could not find table in parsed HTML")
        return []
    
    # Find all rows
    rows = table.find_all('tr')
    print(f"Found {len(rows)-1} rows in the table")  # -1 for header row
    
    # Extract document links
    doc_links = []
    for row in rows[1:]:  # Skip header row
        title_cell = row.find('td', class_='views-field-label')
        if title_cell:
            link = title_cell.find('a', href=True)
            if link and link['href'].startswith('/readingroom/document/'):
                full_url = BASE_URL + link['href']
                title = link.text.strip()
                doc_links.append((title, full_url))
                print(f"Found document: {title[:50]}... -> {full_url}")
    
    return doc_links

def main():
    driver = setup_driver()
    try:
        print(f"Opening search URL: {SEARCH_URL}")
        driver.get(SEARCH_URL)
        
        # Give the page time to load
        time.sleep(5)
        
        # Save initial page source for debugging
        with open("initial_page.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        
        # Extract document links
        doc_links = extract_document_links(driver)
        
        print(f"\nFound {len(doc_links)} document links")
        if doc_links:
            print("\nFirst 5 documents:")
            for i, (title, url) in enumerate(doc_links[:5]):
                print(f"{i+1}. {title[:50]}... -> {url}")
        
    finally:
        print("Closing browser...")
        driver.quit()

if __name__ == "__main__":
    main()