import os
import json
import glob
import time
from llm_client import call_llm, get_model

# Function to read and load CIA documents
def load_documents(limit=5):
    """Load CIA documents from the JSON files in the cia_documents directory."""
    documents = []
    json_files = glob.glob("cia_documents/*.json")
    
    print(f"Found {len(json_files)} document files")
    
    for file_path in json_files[:1]:  # Just take the first file, as it contains all documents
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                # Each file contains a list of documents
                if isinstance(data, list):
                    # Take only the specified number of documents
                    documents.extend(data[:limit])
                    print(f"Loaded {len(data[:limit])} documents from {file_path}")
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
    
    return documents

# Function to truncate text to a specific character limit
def truncate_text(text, max_length=15000):
    """Truncate text to a maximum length to avoid API limits."""
    if len(text) > max_length:
        return text[:max_length] + "... [TRUNCATED]"
    return text

# Function to create a knowledge graph from a CIA document using Gemini
def create_knowledge_graph(document, index):
    """Generate a knowledge graph for a single document using llm_client."""
    model = get_model("graph_building", use_performance=False)
    
    # Extract relevant document information
    title = document.get('title', 'Untitled')
    metadata = document.get('metadata', {})
    body_text = document.get('body_text', '')
    
    # Create a summary of the document to be processed
    doc_summary = f"Document Title: {title}\n\n"
    doc_summary += "Metadata:\n"
    for key, value in metadata.items():
        doc_summary += f"- {key}: {value}\n"
    
    doc_summary += "\nContent:\n"
    doc_summary += truncate_text(body_text)
    
    # Prepare the prompt for Gemini
    prompt = f"""
    Analyze the following CIA document and create a knowledge graph in JSON format. 
    Extract entities (people, organizations, locations, events, concepts) and their relationships.
    
    For each entity:
    - Identify its type (person, organization, location, event, concept)
    - Record any attributes mentioned (like roles, dates, descriptors)
    
    For each relationship:
    - Identify the source entity
    - Identify the target entity
    - Describe the relationship type (e.g., "works for", "located in", "participated in")
    
    Format the response as a JSON object with two arrays: "entities" and "relationships".
    
    Entity format:
    {{
      "id": "unique_identifier",
      "name": "entity_name",
      "type": "person|organization|location|event|concept",
      "attributes": {{"key1": "value1", "key2": "value2"}}
    }}
    
    Relationship format:
    {{
      "source": "source_entity_id",
      "target": "target_entity_id",
      "type": "relationship_type",
      "attributes": {{"key1": "value1", "key2": "value2"}}
    }}
    
    CIA Document to analyze:
    {doc_summary}
    """
    
    print(f"\nProcessing document {index+1}: {title}")

    try:
        response = call_llm(
            model,
            [{"role": "user", "content": prompt}],
            response_format={"type": "json_schema", "json_schema": {"name": "knowledge_graph", "schema": {"type": "object"}}},
            task="sam_gov.crest_kg",
            trace_id=f"sam_gov.crest_kg/document_{index + 1}",
            max_budget=0,
        )

        # Parse and return the JSON response
        kg_data = json.loads(response.content)
        print(f"Successfully created knowledge graph with {len(kg_data.get('entities', []))} entities and {len(kg_data.get('relationships', []))} relationships")
        return kg_data
    
    except Exception as e:
        print(f"Error generating knowledge graph: {e}")
        return {"entities": [], "relationships": []}

# Function to merge multiple knowledge graphs
def merge_knowledge_graphs(knowledge_graphs):
    """Merge multiple knowledge graphs into one."""
    merged_kg = {"entities": [], "relationships": []}
    entity_ids = set()
    
    # Helper function to generate a unique ID
    def get_unique_id(entity_id, entity_name):
        counter = 1
        unique_id = entity_id
        while unique_id in entity_ids:
            unique_id = f"{entity_id}_{counter}"
            counter += 1
        return unique_id
    
    # Merge entities
    for kg in knowledge_graphs:
        for entity in kg.get("entities", []):
            entity_id = entity.get("id")
            entity_name = entity.get("name")
            
            # Generate a unique ID if needed
            if entity_id in entity_ids:
                entity["id"] = get_unique_id(entity_id, entity_name)
            
            entity_ids.add(entity["id"])
            merged_kg["entities"].append(entity)
    
    # Merge relationships
    for kg in knowledge_graphs:
        merged_kg["relationships"].extend(kg.get("relationships", []))
    
    return merged_kg

# Main function
def main(num_documents=5):
    """Main function to create knowledge graphs from CIA documents."""
    print(f"Starting knowledge graph creation for {num_documents} CIA documents")
    
    # Load documents
    documents = load_documents(limit=num_documents)
    if not documents:
        print("No documents found. Exiting.")
        return
    
    print(f"Processing {len(documents)} documents")
    
    # Create knowledge graphs
    knowledge_graphs = []
    for i, doc in enumerate(documents):
        if i >= num_documents:
            break
            
        kg = create_knowledge_graph(doc, i)
        knowledge_graphs.append(kg)
        
        # Save individual knowledge graph
        output_file = f"cia_kg_document_{i+1}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(kg, f, indent=2)
        print(f"Saved knowledge graph to {output_file}")
        
        # Add a delay to avoid API rate limits
        if i < len(documents) - 1:
            time.sleep(2)
    
    # Merge all knowledge graphs
    if knowledge_graphs:
        merged_kg = merge_knowledge_graphs(knowledge_graphs)
        
        # Save merged knowledge graph
        output_file = f"cia_kg_merged_{len(knowledge_graphs)}_documents.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(merged_kg, f, indent=2)
        print(f"\nSaved merged knowledge graph to {output_file}")
        print(f"Final knowledge graph contains {len(merged_kg['entities'])} entities and {len(merged_kg['relationships'])} relationships")

if __name__ == "__main__":
    # Change this number to process more or fewer documents
    NUM_DOCUMENTS = 5
    main(NUM_DOCUMENTS)
