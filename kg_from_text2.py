import os
import json
import glob
import time
import re
import networkx as nx
import matplotlib.pyplot as plt
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
from llm_client import call_llm, get_model

# Load environment variables from .env file
load_dotenv()

class KnowledgeGraphCreator:
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or get_model("graph_building", use_performance=False)
        self.max_retries = 3
        self.retry_delay = 2
        self.max_text_length = 15000
        self.output_dir = "cia_kg_output"
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)

    def load_documents(self, limit: Optional[int] = 5) -> List[Dict[str, Any]]:
        """Load CIA documents from JSON files with proper error handling."""
        documents = []
        json_files = glob.glob("cia_documents/*.json")
        
        print(f"Found {len(json_files)} document files")
        
        for file_path in json_files[:1]:  # Just take the first file, as it contains all documents
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    # Handle different JSON structures
                    if isinstance(data, list):
                        # If it's a list of documents
                        docs_to_add = data[:limit] if limit else data
                        documents.extend(docs_to_add)
                        print(f"Loaded {len(docs_to_add)} documents from {file_path}")
                    elif isinstance(data, dict) and "documents" in data:
                        # If it's a dict with a "documents" key
                        docs_to_add = data["documents"][:limit] if limit else data["documents"]
                        documents.extend(docs_to_add)
                        print(f"Loaded {len(docs_to_add)} documents from {file_path}")
                    else:
                        # If it's a single document
                        documents.append(data)
                        print(f"Loaded 1 document from {file_path}")
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
        
        # Apply limit to the final list if needed
        if limit and len(documents) > limit:
            documents = documents[:limit]
            
        return documents

    def truncate_text(self, text: str) -> str:
        """Truncate text to avoid API limits."""
        if len(text) > self.max_text_length:
            return text[:self.max_text_length] + "... [TRUNCATED]"
        return text

    def extract_json_from_response(self, response_text: str) -> Dict[str, Any]:
        """Extract JSON from text response even if there's surrounding text."""
        # Try to find JSON pattern in the response
        json_pattern = r'(\{.*\})'
        json_matches = re.findall(json_pattern, response_text, re.DOTALL)
        
        if json_matches:
            for json_str in json_matches:
                try:
                    # Try to parse the JSON string
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    continue
        
        # If no valid JSON found, create a default structure
        print("Could not find valid JSON in response. Creating default structure.")
        return {"entities": [], "relationships": []}

    def create_knowledge_graph(self, document: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Generate a knowledge graph for a document with retry mechanism."""
        title = document.get('title', 'Untitled')
        metadata = document.get('metadata', {})
        body_text = document.get('body_text', '')
        
        # Create document summary
        doc_summary = f"Document Title: {title}\n\n"
        doc_summary += "Metadata:\n"
        for key, value in metadata.items():
            doc_summary += f"- {key}: {value}\n"
        
        doc_summary += "\nContent:\n"
        doc_summary += self.truncate_text(body_text)
        
        # Prepare prompt for structured output
        prompt = f"""
        Analyze the following CIA document and create a knowledge graph in JSON format. 
        Extract entities (people, organizations, locations, events, concepts) and their relationships.
        
        For each entity:
        - Give it a unique ID (preferably short and descriptive)
        - Identify its type (person, organization, location, event, concept)
        - Record any attributes mentioned (like roles, dates, descriptors)
        
        For each relationship:
        - Identify the source entity ID
        - Identify the target entity ID
        - Describe the relationship type (e.g., "works_for", "located_in", "participated_in")
        
        IMPORTANT: Respond ONLY with a valid JSON object. The JSON must have exactly this structure:
        {{
          "entities": [
            {{
              "id": "unique_identifier",
              "name": "entity_name",
              "type": "person|organization|location|event|concept",
              "attributes": {{"key1": "value1", "key2": "value2"}}
            }}
          ],
          "relationships": [
            {{
              "source": "source_entity_id",
              "target": "target_entity_id",
              "type": "relationship_type",
              "attributes": {{"key1": "value1", "key2": "value2"}}
            }}
          ]
        }}
        
        CIA Document to analyze:
        {doc_summary}
        """
        
        print(f"\nProcessing document {index+1}: {title}")
        
        # Implement retry mechanism
        for attempt in range(self.max_retries):
            try:
                response = call_llm(
                    self.model_name,
                    [{"role": "user", "content": prompt}],
                    response_format={"type": "json_schema", "json_schema": {"name": "knowledge_graph", "schema": {"type": "object"}}},
                    task="sam_gov.crest_kg",
                    trace_id=f"sam_gov.crest_kg/document_{index + 1}/attempt_{attempt + 1}",
                    max_budget=0,
                )

                # Try to parse response as JSON
                try:
                    kg_data = json.loads(response.content)
                    print(f"Successfully created knowledge graph with {len(kg_data.get('entities', []))} entities and {len(kg_data.get('relationships', []))} relationships")
                    return kg_data
                except json.JSONDecodeError:
                    # If JSON parsing fails, try to extract JSON from text
                    kg_data = self.extract_json_from_response(response.content)
                    print(f"Extracted knowledge graph with {len(kg_data.get('entities', []))} entities and {len(kg_data.get('relationships', []))} relationships")
                    return kg_data
                    
            except Exception as e:
                print(f"Attempt {attempt+1}/{self.max_retries} failed: {e}")
                if attempt < self.max_retries - 1:
                    print(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    print(f"All attempts failed. Creating empty knowledge graph.")
                    return {"entities": [], "relationships": []}
        
        return {"entities": [], "relationships": []}

    def merge_knowledge_graphs(self, knowledge_graphs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge multiple knowledge graphs with entity deduplication."""
        merged_kg = {"entities": [], "relationships": []}
        entity_ids = set()
        entity_id_map = {}  # Map original IDs to new IDs
        
        # Process entities first
        for kg_index, kg in enumerate(knowledge_graphs):
            for entity in kg.get("entities", []):
                # Skip entities without required fields
                if not entity.get("id") or not entity.get("name"):
                    continue
                
                original_id = entity.get("id")
                entity_name = entity.get("name")
                
                # Check for duplicate entities by name (case insensitive)
                existing_entities = [e for e in merged_kg["entities"] 
                                    if e.get("name", "").lower() == entity_name.lower()]
                
                if existing_entities:
                    # Map this entity's ID to the existing entity's ID
                    entity_id_map[f"{kg_index}:{original_id}"] = existing_entities[0]["id"]
                else:
                    # Create a new unique ID if needed
                    if original_id in entity_ids:
                        new_id = f"{original_id}_{len(entity_ids)}"
                    else:
                        new_id = original_id
                    
                    entity_ids.add(new_id)
                    entity_id_map[f"{kg_index}:{original_id}"] = new_id
                    
                    # Update the entity with the new ID
                    entity["id"] = new_id
                    merged_kg["entities"].append(entity)
        
        # Process relationships
        for kg_index, kg in enumerate(knowledge_graphs):
            for rel in kg.get("relationships", []):
                source_id = rel.get("source")
                target_id = rel.get("target")
                
                # Skip relationships without source or target
                if not source_id or not target_id:
                    continue
                
                # Map to new entity IDs
                new_source_id = entity_id_map.get(f"{kg_index}:{source_id}", source_id)
                new_target_id = entity_id_map.get(f"{kg_index}:{target_id}", target_id)
                
                # Update relationship with new IDs
                rel["source"] = new_source_id
                rel["target"] = new_target_id
                
                merged_kg["relationships"].append(rel)
        
        return merged_kg

    def visualize_knowledge_graph(self, kg_data: Dict[str, Any], output_file: str = "kg_visualization.png"):
        """Create a visualization of the knowledge graph using NetworkX."""
        try:
            G = nx.DiGraph()
            
            # Add nodes (entities)
            for entity in kg_data.get("entities", []):
                entity_id = entity.get("id", "unknown")
                entity_name = entity.get("name", entity_id)
                entity_type = entity.get("type", "unknown")
                
                # Add node with attributes
                G.add_node(entity_id, name=entity_name, type=entity_type)
            
            # Add edges (relationships)
            for rel in kg_data.get("relationships", []):
                source = rel.get("source")
                target = rel.get("target")
                rel_type = rel.get("type", "related_to")
                
                # Skip relationships with missing source or target
                if not source or not target:
                    continue
                
                # Add edge with attributes
                G.add_edge(source, target, type=rel_type)
            
            # Set up the visualization
            plt.figure(figsize=(20, 16))
            
            # Create node colors based on entity type
            node_colors = []
            node_types = set()
            for node in G.nodes:
                node_type = G.nodes[node].get("type", "unknown")
                node_types.add(node_type)
            
            # Define a color map for entity types
            color_map = {
                "person": "lightblue",
                "organization": "lightgreen",
                "location": "lightyellow",
                "event": "lightcoral",
                "concept": "lavender",
                "unknown": "lightgray"
            }
            
            # Set node colors based on type
            for node in G.nodes:
                node_type = G.nodes[node].get("type", "unknown")
                node_colors.append(color_map.get(node_type, "lightgray"))
            
            # Use spring layout for positioning
            pos = nx.spring_layout(G, k=0.15, iterations=50)
            
            # Draw the graph
            nx.draw_networkx_nodes(G, pos, node_size=700, node_color=node_colors, alpha=0.8)
            nx.draw_networkx_edges(G, pos, width=1.0, alpha=0.7, arrowsize=20)
            
            # Add labels
            labels = {node: G.nodes[node].get("name", node) for node in G.nodes}
            nx.draw_networkx_labels(G, pos, labels, font_size=10)
            
            # Add edge labels
            edge_labels = {(source, target): G.edges[source, target].get("type", "") 
                          for source, target in G.edges}
            nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8)
            
            # Create a legend for entity types
            legend_elements = [plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=color_map.get(t, "lightgray"), 
                                        markersize=10, label=t) for t in node_types]
            plt.legend(handles=legend_elements, loc='upper right')
            
            plt.title(f"Knowledge Graph Visualization ({len(G.nodes)} entities, {len(G.edges)} relationships)")
            plt.axis('off')
            
            # Save the visualization
            full_path = os.path.join(self.output_dir, output_file)
            plt.savefig(full_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"Visualization saved to {full_path}")
            return True
        
        except Exception as e:
            print(f"Error creating visualization: {e}")
            return False

    def process_documents(self, num_documents: Optional[int] = 5, visualize: bool = True):
        """Process multiple documents and create a knowledge graph."""
        print(f"Starting knowledge graph creation for {num_documents or 'all'} CIA documents")
        
        # Load documents
        documents = self.load_documents(limit=num_documents)
        if not documents:
            print("No documents found. Exiting.")
            return
        
        print(f"Processing {len(documents)} documents")
        
        # Create knowledge graphs
        knowledge_graphs = []
        for i, doc in enumerate(documents):
            # Process document
            kg = self.create_knowledge_graph(doc, i)
            knowledge_graphs.append(kg)
            
            # Save individual knowledge graph
            output_file = os.path.join(self.output_dir, f"cia_kg_document_{i+1}.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(kg, f, indent=2)
            print(f"Saved individual knowledge graph to {output_file}")
            
            # Visualize individual knowledge graph
            if visualize:
                self.visualize_knowledge_graph(kg, f"cia_kg_document_{i+1}.png")
            
            # Add a delay to avoid API rate limits
            if i < len(documents) - 1:
                time.sleep(2)
        
        # Merge all knowledge graphs
        if knowledge_graphs:
            merged_kg = self.merge_knowledge_graphs(knowledge_graphs)
            
            # Save merged knowledge graph
            output_file = os.path.join(self.output_dir, f"cia_kg_merged_{len(knowledge_graphs)}_documents.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(merged_kg, f, indent=2)
            print(f"\nSaved merged knowledge graph to {output_file}")
            print(f"Final knowledge graph contains {len(merged_kg['entities'])} entities and {len(merged_kg['relationships'])} relationships")
            
            # Visualize merged knowledge graph
            if visualize:
                self.visualize_knowledge_graph(merged_kg, f"cia_kg_merged_{len(knowledge_graphs)}_documents.png")
        
        return knowledge_graphs

def main():
    # Change these settings as needed
    NUM_DOCUMENTS = 5  # Number of documents to process (None for all)
    VISUALIZE = True   # Set to False to skip visualization
    
    # Need to install additional packages for visualization
    if VISUALIZE:
        try:
            import networkx
            import matplotlib
        except ImportError:
            print("To enable visualization, install required packages:")
            print("pip install networkx matplotlib")
            VISUALIZE = False
    
    # Create and run the knowledge graph creator
    kg_creator = KnowledgeGraphCreator()
    kg_creator.process_documents(num_documents=NUM_DOCUMENTS, visualize=VISUALIZE)

if __name__ == "__main__":
    main()
