import os
import json
import time
import math
import random
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime
from pathlib import Path
import re

# Create necessary directories
os.makedirs("cia_ufo_documents", exist_ok=True)
os.makedirs("cia_ufo_output", exist_ok=True)

# Base URL configurations
BASE_URL = "https://www.cia.gov"
SEARCH_BASE_URL = "https://www.cia.gov/readingroom/advanced-search-view"
UFO_COLLECTION_ID = "72"

# Chrome setup
def setup_chrome_driver():
    """Set up Chrome WebDriver with appropriate options"""
    options = Options()
    # Comment out the headless option if you want to see the browser window
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Set user agent to mimic a regular browser
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    # Initialize the WebDriver
    service = Service()  # Specify path to chromedriver if needed
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def construct_ufo_collection_url(page_num=0):
    """Construct URL for the UFOs collection with pagination"""
    params = {
        'keyword': '',
        'im_field_collection[]': UFO_COLLECTION_ID,
        'label': '',
        'sm_field_document_number': '',
        'sm_field_original_classification': '',
        'ds_field_pub_date_op': '=',
        'ds_field_pub_date[value]': '',
        'ds_field_pub_date[min]': '',
        'ds_field_pub_date[max]': '',
        'sm_field_content_type': '',
        'sm_field_case_number': '',
    }
    
    if page_num > 0:
        params['page'] = str(page_num)
    
    # Convert params to URL query string
    query_parts = []
    for key, value in params.items():
        if isinstance(value, list):
            for val in value:
                query_parts.append(f"{key}={val}")
        else:
            query_parts.append(f"{key}={value}")
    
    query_string = "&".join(query_parts)
    return f"{SEARCH_BASE_URL}?{query_string}"

def extract_document_links(driver, page_num):
    """Extract document links from the search results page"""
    print(f"\nExtracting document links from page {page_num+1}...")
    
    # Wait for the table to load
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, "views-table"))
        )
        print("Search results table loaded successfully")
    except TimeoutException:
        print("Timeout waiting for search results table to load")
        # Save the page source for debugging
        with open(f"debug_page_{page_num}.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        return []
    
    # Parse the page with BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # Find the results table
    results_table = soup.find('table', class_='views-table')
    if not results_table:
        print(f"No results table found on page {page_num+1}")
        return []
    
    # Extract document links from table rows
    doc_links = []
    
    # Find all rows excluding the header
    rows = results_table.find_all('tr')[1:]  # Skip header row
    print(f"Found {len(rows)} rows in the results table")
    
    for i, row in enumerate(rows):
        # Find the first cell with the document title and link
        title_cell = row.find('td', class_='views-field-label')
        if title_cell:
            link_tag = title_cell.find('a', href=True)
            if link_tag and link_tag['href'].startswith('/readingroom/document/'):
                title = link_tag.text.strip()
                url = BASE_URL + link_tag['href']
                doc_links.append({
                    'title': title,
                    'url': url,
                    'position': i+1,
                    'search_page': page_num+1
                })
                print(f"  {i+1}. {title[:60]}... -> {url}")
    
    print(f"Extracted {len(doc_links)} document links from page {page_num+1}")
    return doc_links

def extract_document_details(driver, doc_url):
    """Extract metadata and content from a document page"""
    print(f"\nExtracting details from: {doc_url}")
    
    # Navigate to the document page
    driver.get(doc_url)
    
    # Wait for the document title to load
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, "documentFirstHeading"))
        )
    except TimeoutException:
        print(f"Timeout waiting for document page to load: {doc_url}")
        return None
    
    # Wait a bit more for the page to fully render
    time.sleep(2)
    
    # Parse the page with BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # Extract the document title
    title_tag = soup.find('h1', class_='documentFirstHeading')
    if not title_tag:
        print(f"Could not find document title: {doc_url}")
        return None
    
    doc_title = title_tag.text.strip()
    print(f"Document title: {doc_title}")
    
    # Create document object
    doc_data = {
        'url': doc_url,
        'title': doc_title,
        'metadata': {},
        'body_text': "",
        'pdf_url': None
    }
    
    # Extract metadata fields
    metadata_fields = soup.find_all('div', class_='field-label-inline')
    for field in metadata_fields:
        field_label = field.find('div', class_='field-label')
        field_item = field.find('div', class_='field-item')
        
        if field_label and field_item:
            # Clean up field name (remove colon and spaces)
            field_name = field_label.text.strip().replace(':', '').strip()
            field_value = field_item.text.strip()
            doc_data['metadata'][field_name] = field_value
            
            print(f"  Metadata: {field_name} = {field_value}")
    
    # Extract body text
    body_container = soup.find('div', class_='field-name-body')
    if body_container:
        body_item = body_container.find('div', class_='field-item')
        if body_item:
            doc_data['body_text'] = body_item.get_text(separator='\n', strip=True)
            text_preview = doc_data['body_text'][:100].replace('\n', ' ').strip()
            print(f"  Body text: {text_preview}...")
    
    # Extract PDF URL if available
    pdf_link = soup.find('a', href=lambda href: href and href.endswith('.pdf'))
    if pdf_link and 'href' in pdf_link.attrs:
        pdf_url = pdf_link['href']
        # Make absolute URL if it's relative
        if not pdf_url.startswith('http'):
            pdf_url = BASE_URL + pdf_url if not pdf_url.startswith('/') else BASE_URL + pdf_url
        doc_data['pdf_url'] = pdf_url
        print(f"  PDF URL: {pdf_url}")
    
    return doc_data

def scrape_ufo_collection(num_pages=5):
    """Main function to scrape the UFO collection"""
    print(f"Starting to scrape CIA's UFO collection - {num_pages} pages")
    
    # Initialize Chrome driver
    driver = setup_chrome_driver()
    
    # Create a timestamp for filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        all_documents = []
        all_document_links = []
        
        # Scrape each page of search results
        for page_num in range(num_pages):
            # Construct URL for this page
            page_url = construct_ufo_collection_url(page_num)
            print(f"\n--- Scraping search results page {page_num+1} ---")
            print(f"URL: {page_url}")
            
            # Load the page
            driver.get(page_url)
            time.sleep(3)  # Wait for page to load
            
            # Extract document links from this page
            doc_links = extract_document_links(driver, page_num)
            all_document_links.extend(doc_links)
            
            # Save progress of links
            links_filename = f"cia_ufo_output/ufo_document_links_{timestamp}.json"
            with open(links_filename, 'w', encoding='utf-8') as f:
                json.dump(all_document_links, f, indent=2)
            
            # Wait between pages to avoid rate limiting
            if page_num < num_pages - 1:
                print(f"Waiting before loading next page...")
                time.sleep(3)
        
        # Process each document
        for i, doc_link in enumerate(all_document_links):
            print(f"\n--- Processing document {i+1}/{len(all_document_links)} ---")
            
            # Extract document details
            doc_data = extract_document_details(driver, doc_link['url'])
            
            if doc_data:
                # Add the document to our collection
                all_documents.append(doc_data)
                
                # Save the individual document
                doc_id = doc_link['url'].split('/')[-1]
                doc_filename = f"cia_ufo_documents/doc_{doc_id}_{timestamp}.json"
                with open(doc_filename, 'w', encoding='utf-8') as f:
                    json.dump(doc_data, f, indent=2)
                
                # Save progress of all documents
                all_docs_filename = f"cia_ufo_output/ufo_all_documents_{timestamp}.json"
                with open(all_docs_filename, 'w', encoding='utf-8') as f:
                    json.dump(all_documents, f, indent=2)
            
            # Wait between document requests to avoid rate limiting
            if i < len(all_document_links) - 1:
                delay = random.uniform(2, 4)
                print(f"Waiting {delay:.1f} seconds before next document...")
                time.sleep(delay)
        
        print("\n--- Scraping complete ---")
        print(f"Scraped {len(all_documents)} documents")
        print(f"Document links saved to: {links_filename}")
        print(f"All documents saved to: {all_docs_filename}")
        
        return all_documents
    
    finally:
        # Clean up
        driver.quit()

def create_knowledge_graph(documents):
    """Create a knowledge graph from the scraped documents"""
    print("\nCreating knowledge graph from scraped documents...")
    
    entities = []
    relationships = []
    
    # Track entities to avoid duplicates
    entity_map = {}
    entity_id_counter = 0
    
    # Helper function to get or create entity
    def get_or_create_entity(name, entity_type):
        nonlocal entity_id_counter
        # Normalize name
        name = name.strip()
        if not name:
            return None
            
        # Check if entity already exists
        if name.lower() in entity_map:
            return entity_map[name.lower()]
            
        # Create new entity
        entity_id = f"e{entity_id_counter}"
        entity_id_counter += 1
        
        entity = {
            "id": entity_id,
            "name": name,
            "type": entity_type,
            "attributes": {}
        }
        
        entities.append(entity)
        entity_map[name.lower()] = entity_id
        return entity_id
    
    # Process each document
    for doc in documents:
        # Create document entity
        doc_id = get_or_create_entity(doc['title'], "document")
        if not doc_id:
            continue
            
        # Add metadata as attributes
        for key, value in doc.get('metadata', {}).items():
            if value:
                # Find the entity and update attributes
                for entity in entities:
                    if entity['id'] == doc_id:
                        entity['attributes'][key] = value
                        break
        
        # Process document text to extract entities
        text = doc.get('body_text', '')
        
        # Extract locations
        location_pattern = r"(?:in|at|near|from|to)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})"
        locations = re.findall(location_pattern, text)
        for location in set(locations):
            if len(location) > 3:  # Filter out short names
                location_id = get_or_create_entity(location, "location")
                if location_id:
                    relationships.append({
                        "source": doc_id,
                        "target": location_id,
                        "type": "mentions_location",
                        "attributes": {}
                    })
        
        # Extract dates
        date_pattern = r"(\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b)"
        dates = re.findall(date_pattern, text)
        for date in set(dates):
            date_id = get_or_create_entity(date, "time")
            if date_id:
                relationships.append({
                    "source": doc_id,
                    "target": date_id,
                    "type": "dated",
                    "attributes": {}
                })
        
        # Extract people (simple approach - may need refinement)
        person_pattern = r"Mr\.\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})|([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\s+(?:said|reported|observed|stated)"
        people = re.findall(person_pattern, text)
        for person_tuple in set(people):
            # Take the non-empty group
            person = person_tuple[0] if person_tuple[0] else person_tuple[1]
            if len(person) > 3:  # Filter out short names
                person_id = get_or_create_entity(person, "person")
                if person_id:
                    relationships.append({
                        "source": doc_id,
                        "target": person_id,
                        "type": "mentions_person",
                        "attributes": {}
                    })
        
        # Extract UFO-related terms
        ufo_terms = ["flying saucer", "UFO", "unidentified flying", "aerial phenomenon", 
                    "extraterrestrial", "alien", "spacecraft", "flying object"]
        
        for term in ufo_terms:
            if term.lower() in text.lower():
                term_id = get_or_create_entity(term, "concept")
                if term_id:
                    relationships.append({
                        "source": doc_id,
                        "target": term_id,
                        "type": "discusses",
                        "attributes": {}
                    })
    
    # Create knowledge graph
    kg = {
        "entities": entities,
        "relationships": relationships
    }
    
    # Save knowledge graph
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    kg_filename = f"cia_ufo_output/ufo_knowledge_graph_{timestamp}.json"
    with open(kg_filename, 'w', encoding='utf-8') as f:
        json.dump(kg, f, indent=2)
    
    print(f"Knowledge graph created with {len(entities)} entities and {len(relationships)} relationships")
    print(f"Knowledge graph saved to: {kg_filename}")
    
    return kg

def main():
    # Number of pages to scrape (adjust as needed)
    num_pages = 13  # Start with a small number for testing
    
    # Scrape the UFO collection
    documents = scrape_ufo_collection(num_pages)
    
    # Create knowledge graph
    if documents:
        kg = create_knowledge_graph(documents)
        print("\nProcess completed successfully!")
        return kg
    else:
        print("\nNo documents were scraped. Please check the script and try again.")
        return None

if __name__ == "__main__":
    main()