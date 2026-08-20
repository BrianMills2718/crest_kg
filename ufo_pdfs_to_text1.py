import os
import json
import re
import glob
from datetime import datetime
import subprocess
import sys

# Install required packages
subprocess.check_call([sys.executable, "-m", "pip", "install", "pytesseract", "pdf2image", "pillow"])

# Now import the packages
import pytesseract
from pdf2image import convert_from_path
from PIL import Image


# Ensure directories exist
os.makedirs("cia_ufo_output", exist_ok=True)

def load_documents():
    """Load previously scraped document data"""
    print("Loading previously scraped documents...")
    
    # Find the most recent documents file
    doc_files = glob.glob("cia_ufo_output/ufo_all_documents_*.json")
    if not doc_files:
        print("No document files found!")
        return []
    
    # Sort by modification time (most recent first)
    doc_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    most_recent_file = doc_files[0]
    
    print(f"Loading documents from: {most_recent_file}")
    with open(most_recent_file, 'r', encoding='utf-8') as f:
        documents = json.load(f)
    
    print(f"Loaded {len(documents)} documents")
    return documents

def perform_ocr_on_pdf(pdf_path):
    """Extract text from PDF using OCR"""
    print(f"Performing OCR on: {pdf_path}")
    
    try:
        # Check if Tesseract is installed and in PATH
        try:
            tesseract_version = pytesseract.get_tesseract_version()
            print(f"  Using Tesseract version: {tesseract_version}")
        except Exception as e:
            print(f"  Tesseract error: {e}")
            print("  Make sure Tesseract is installed and in your PATH")
            return None
        
        # Convert PDF to images
        print("  Converting PDF to images...")
        # Poppler is assumed to be on system PATH; no poppler_path=... needed
        images = convert_from_path(pdf_path, dpi=300)
        print(f"  Converted PDF to {len(images)} images")
        
        # Perform OCR on each image
        full_text = ""
        for i, image in enumerate(images):
            print(f"  Processing page {i+1}/{len(images)}...")
            text = pytesseract.image_to_string(image, lang='eng')
            full_text += f"\n\n--- Page {i+1} ---\n\n{text}"
        
        print("  OCR completed successfully")
        return full_text
    except Exception as e:
        print(f"  Error performing OCR: {e}")
        return None

def process_pdf_files():
    """Process previously downloaded PDF files with OCR"""
    print("\nProcessing downloaded PDF files using OCR...")
    
    # Load documents
    documents = load_documents()
    if not documents:
        return None
    
    # List of PDFs to process
    pdf_dir = "cia_ufo_pdfs"
    if not os.path.exists(pdf_dir):
        print(f"PDF directory '{pdf_dir}' not found!")
        return None
    
    pdf_files = glob.glob(f"{pdf_dir}/*.pdf")
    print(f"Found {len(pdf_files)} PDF files to process")
    
    # Process each PDF
    updated_documents = []
    for doc in documents:
        # Get PDF file path from document
        pdf_url = doc.get("pdf_url", "")
        if not pdf_url:
            print(f"No PDF URL for document: {doc.get('title', 'Unknown')}")
            updated_documents.append(doc)
            continue
        
        pdf_filename = os.path.basename(pdf_url)
        pdf_path = os.path.join(pdf_dir, pdf_filename.replace("DOC_", ""))
        
        # Check if PDF file exists
        if not os.path.exists(pdf_path):
            print(f"PDF file not found: {pdf_path}")
            updated_documents.append(doc)
            continue
        
        # Perform OCR on PDF
        ocr_text = perform_ocr_on_pdf(pdf_path)
        if ocr_text:
            # Add OCR text to document
            doc["ocr_text"] = ocr_text
            print(f"Added OCR text to document: {doc.get('title', 'Unknown')}")
            
            # Save individual document immediately
            doc_id = os.path.basename(pdf_path).replace(".pdf", "")
            doc_filename = f"cia_ufo_documents/doc_{doc_id}_ocr.json"
            with open(doc_filename, 'w', encoding='utf-8') as f:
                json.dump(doc, f, indent=2)
        
        updated_documents.append(doc)
        
        # Save progress after each document
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        progress_filename = f"cia_ufo_output/ufo_documents_ocr_progress_{timestamp}.json"
        with open(progress_filename, 'w', encoding='utf-8') as f:
            json.dump(updated_documents, f, indent=2)
    
    # Save final updated documents
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"cia_ufo_output/ufo_documents_with_ocr_{timestamp}.json"
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(updated_documents, f, indent=2)
    
    print(f"Updated documents saved to: {output_filename}")
    return updated_documents

def extract_entities_from_text(text):
    """Extract entities from document text"""
    entities = []
    
    # Extract locations
    location_pattern = r'(?:in|at|near|from|to|over)\s+([A-Z][a-z]+(?:,\s+[A-Z][a-z]+)?(?:\s+[A-Z][a-z]+){0,2})'
    locations = re.findall(location_pattern, text)
    for location in set(locations):
        if len(location) > 3:  # Filter out short names
            entities.append(("location", location.strip()))
    
    # Extract dates
    date_pattern = r'(\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?,\s+\d{4}\b|\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December),?\s+\d{4}\b|\b\d{1,2}/\d{1,2}/\d{2,4}\b)'
    dates = re.findall(date_pattern, text)
    for date in set(dates):
        entities.append(("time", date.strip()))
    
    # Extract people
    person_pattern = r"(?:Mr\.|Mrs\.|Ms\.|Dr\.|Professor|Col\.|Capt\.|Major|Gen\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})|([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\s+(?:reported|observed|stated|claimed|testified|said)"
    people = re.findall(person_pattern, text)
    for person_tuple in set(people):
        # Take the non-empty group
        person = person_tuple[0] if person_tuple[0] else person_tuple[1]
        if len(person) > 3:  # Filter out short names
            entities.append(("person", person.strip()))
    
    # Extract organizations
    org_pattern = r"([A-Z][a-z]*(?:\s+[A-Z][a-z]*)+\s+(?:Agency|Department|Bureau|Committee|Association|Institute|Organization|Corporation|Commission|Administration|Office|Group))|(?:NASA|FBI|CIA|USAF|RAF|DoD|Pentagon)"
    orgs = re.findall(org_pattern, text)
    for org in set(orgs):
        if len(org) > 3:  # Filter out short names
            entities.append(("organization", org.strip()))
    
    # Extract UFO-related terms
    ufo_terms = [
        "flying saucer", "UFO", "unidentified flying", "aerial phenomenon", 
        "extraterrestrial", "alien", "spacecraft", "flying object", "flying disk",
        "sighting", "radar", "object", "unexplained", "anomaly", "phenomena"
    ]
    
    for term in ufo_terms:
        if term.lower() in text.lower():
            entities.append(("concept", term))
    
    return entities

def create_knowledge_graph(documents_with_ocr):
    """Create a knowledge graph from documents with OCR text"""
    print("\nCreating knowledge graph from OCR text...")
    
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
    for doc in documents_with_ocr:
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
        text = doc.get('ocr_text', '')
        if not text:
            continue
        
        # Extract entities from text
        extracted_entities = extract_entities_from_text(text)
        
        # Add extracted entities to knowledge graph
        for entity_type, entity_name in extracted_entities:
            entity_id = get_or_create_entity(entity_name, entity_type)
            if entity_id:
                relationship_type = "mentions"
                if entity_type == "concept":
                    relationship_type = "discusses"
                elif entity_type == "person":
                    relationship_type = "mentions_person"
                elif entity_type == "location":
                    relationship_type = "mentions_location"
                elif entity_type == "organization":
                    relationship_type = "mentions_organization"
                elif entity_type == "time":
                    relationship_type = "dated"
                
                # Check if this relation already exists
                exists = False
                for rel in relationships:
                    if rel["source"] == doc_id and rel["target"] == entity_id and rel["type"] == relationship_type:
                        exists = True
                        break
                
                if not exists:
                    relationships.append({
                        "source": doc_id,
                        "target": entity_id,
                        "type": relationship_type,
                        "attributes": {}
                    })
    
    # Create knowledge graph
    kg = {
        "entities": entities,
        "relationships": relationships
    }
    
    # Save knowledge graph
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    kg_filename = f"cia_ufo_output/ufo_ocr_kg_{timestamp}.json"
    with open(kg_filename, 'w', encoding='utf-8') as f:
        json.dump(kg, f, indent=2)
    
    print(f"Knowledge graph created with {len(entities)} entities and {len(relationships)} relationships")
    print(f"Knowledge graph saved to: {kg_filename}")
    
    return kg

def main():
    print("\n==== CIA UFO Document OCR Processing ====\n")
    
    # First ensure Tesseract is available
    try:
        tesseract_version = pytesseract.get_tesseract_version()
        print(f"Tesseract OCR version: {tesseract_version}")
    except Exception as e:
        print("Tesseract OCR is not properly installed or not in PATH.")
        print("Please install Tesseract OCR:")
        print("1. Download from: https://github.com/UB-Mannheim/tesseract/wiki")
        print("2. Make sure to check 'Add to PATH' during installation")
        print("3. Restart your command prompt after installation")
        print("4. Run this script again")
        return
    
    # Process PDF files with OCR
    documents_with_ocr = process_pdf_files()
    
    # Create knowledge graph from OCR text
    if documents_with_ocr:
        kg = create_knowledge_graph(documents_with_ocr)
        print("\nProcess completed successfully!")
        return kg
    else:
        print("\nNo documents with OCR text available. Please check the script and try again.")
        return None

if __name__ == "__main__":
    main()