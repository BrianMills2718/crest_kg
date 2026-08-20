from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import json
import os
from datetime import datetime

# Base URL configuration
BASE_URL = "https://www.cia.gov"
SEARCH_BASE_URL = "https://www.cia.gov/readingroom/advanced-search-view"

def setup_driver():
    options = Options()
    # Uncomment if you want to run headless (no browser window)
    # options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Create a new ChromeDriver service
    service = Service()  # Specify path if needed
    
    # Create the driver
    driver = webdriver.Chrome(service=service, options=options)
    
    # Set a user agent
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {
        "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    return driver

def construct_search_url(keyword, page_num):
    """
    Constructs the URL for search results page
    page_num is 0-based (first page is 0, second page is 1, etc.)
    """
    params = {
        'keyword': keyword,
        'page': str(page_num)
    }
    url = f"{SEARCH_BASE_URL}?keyword={keyword}&page={page_num}"
    return url

def extract_document_links(driver):
    """Extract document links from the current search results page"""
    # Wait for the table to load
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, "views-table"))
        )
        print("Table loaded successfully")
    except Exception as e:
        print(f"Error waiting for table: {e}")
        return []

    # Parse the page
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # Find the table
    table = soup.find('table', class_='views-table')
    if not table:
        print("Could not find results table")
        return []
    
    # Extract links from table rows
    doc_links = []
    rows = table.find_all('tr')
    
    print(f"Found {len(rows)-1} rows in the results table")  # -1 for header row
    
    for row in rows[1:]:  # Skip header row
        title_cell = row.find('td', class_='views-field-label')
        if title_cell:
            link_tag = title_cell.find('a', href=True)
            if link_tag and link_tag['href'].startswith('/readingroom/document/'):
                title = link_tag.text.strip()
                url = BASE_URL + link_tag['href']
                doc_links.append({'title': title, 'url': url})
                print(f"Found document: {title[:50]}... -> {url}")
    
    return doc_links

def extract_document_content(driver, doc_url):
    """Extract metadata and full text from a document page"""
    print(f"\nVisiting document page: {doc_url}")
    driver.get(doc_url)
    
    # Wait for content to load
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, "documentFirstHeading"))
        )
    except Exception as e:
        print(f"Error loading document page: {e}")
        return None
    
    time.sleep(2)  # Give extra time for page to fully load
    
    # Parse the page
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # Extract document details
    doc_data = {
        'url': doc_url,
        'title': '',
        'metadata': {},
        'body_text': ''
    }
    
    # Extract title
    title_tag = soup.find('h1', class_='documentFirstHeading')
    if title_tag:
        doc_data['title'] = title_tag.text.strip()
        print(f"Title: {doc_data['title']}")
    
    # Extract metadata fields
    metadata_fields = soup.find_all('div', class_='field-label-inline')
    for field in metadata_fields:
        field_label = field.find('div', class_='field-label')
        field_item = field.find('div', class_='field-item')
        
        if field_label and field_item:
            # Clean up field name (remove colon and spaces)
            field_name = field_label.text.strip().replace(':', '')
            field_value = field_item.text.strip()
            doc_data['metadata'][field_name] = field_value
    
    # Extract body text
    body_container = soup.find('div', class_='field-name-body')
    if body_container:
        body_item = body_container.find('div', class_='field-item')
        if body_item:
            doc_data['body_text'] = body_item.get_text(separator='\n', strip=True)
            print(f"Extracted {len(doc_data['body_text'])} characters of body text")
    
    return doc_data

def search_and_extract(keyword, num_pages=105):
    """
    Search for documents with the given keyword and extract content
    from all documents found in the first num_pages of results
    """
    driver = setup_driver()
    all_documents = []
    
    try:
        for page_num in range(num_pages):
            search_url = construct_search_url(keyword, page_num)
            print(f"\n--- Scraping search results page {page_num+1} ---")
            print(f"URL: {search_url}")
            
            driver.get(search_url)
            time.sleep(3)  # Wait for page to load
            
            # Extract document links from this page
            doc_links = extract_document_links(driver)
            
            if not doc_links:
                print(f"No document links found on page {page_num+1}")
                continue
            
            print(f"Found {len(doc_links)} document links on page {page_num+1}")
            
            # Process each document
            for i, doc_link in enumerate(doc_links):
                print(f"\nProcessing document {i+1}/{len(doc_links)}")
                doc_data = extract_document_content(driver, doc_link['url'])
                
                if doc_data:
                    all_documents.append(doc_data)
                    # Save each document as we go to avoid losing data if there's an error
                    save_progress(all_documents, keyword, i+1, page_num+1)
                
                # Sleep to avoid overloading the server
                time.sleep(2)
            
            # Sleep between pages
            if page_num < num_pages - 1:
                time.sleep(5)
    
    finally:
        driver.quit()
    
    return all_documents

def save_progress(documents, keyword, doc_num, page_num):
    """Save the current progress to a file"""
    # Create output directory if it doesn't exist
    os.makedirs('cia_documents', exist_ok=True)
    
    # Create a timestamp for the filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save as JSON
    filename = f"cia_documents/{keyword}_page{page_num}_doc{doc_num}_{timestamp}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(documents, f, indent=2)
    
    print(f"Saved progress to {filename}")

def main():
    keyword = "disinformation"
    num_pages = 2  # Number of search result pages to process
    
    print(f"Starting to scrape CIA documents about '{keyword}'...")
    documents = search_and_extract(keyword, num_pages)
    
    print(f"\n--- SCRAPING COMPLETE ---")
    print(f"Successfully scraped {len(documents)} documents")
    
    # Final save with all documents
    if documents:
        os.makedirs('cia_documents', exist_ok=True)
        final_filename = f"cia_documents/{keyword}_complete_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(final_filename, 'w', encoding='utf-8') as f:
            json.dump(documents, f, indent=2)
        print(f"All data saved to {final_filename}")

if __name__ == "__main__":
    main()