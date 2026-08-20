import json
import os
import webbrowser
from pathlib import Path

# Install required packages if needed
try:
    from pyvis.network import Network
except ImportError:
    print("Installing pyvis...")
    import subprocess
    subprocess.check_call(["pip", "install", "pyvis"])
    from pyvis.network import Network

def load_knowledge_graph(filepath):
    """Load the knowledge graph from a JSON file"""
    print(f"Loading knowledge graph from {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        kg_data = json.load(f)
    return kg_data

def get_entity_color(entity_type):
    """Return a color based on entity type"""
    color_map = {
        "person": "#66c2a5",       # Teal
        "organization": "#fc8d62", # Orange
        "location": "#8da0cb",     # Blue
        "event": "#e78ac3",        # Pink
        "concept": "#a6d854",      # Green
        "country": "#ffd92f",      # Yellow
        "time": "#e5c494",         # Tan
        "unknown": "#cccccc"       # Gray
    }
    return color_map.get(entity_type.lower(), "#15AFAC")  # Default color if type not found

def visualize_with_pyvis(kg_data, output_file="cia_knowledge_graph_interactive.html"):
    """Create an interactive visualization using Pyvis"""
    # Create network
    net = Network(height="800px", width="100%", directed=True, notebook=False)
    net.toggle_physics(True)
    net.set_options("""
    {
      "physics": {
        "forceAtlas2Based": {
          "gravitationalConstant": -50,
          "centralGravity": 0.01,
          "springLength": 100,
          "springConstant": 0.08
        },
        "maxVelocity": 50,
        "solver": "forceAtlas2Based",
        "timestep": 0.35,
        "stabilization": {
          "enabled": true,
          "iterations": 1000
        }
      },
      "edges": {
        "color": {
          "inherit": true
        },
        "smooth": {
          "enabled": true,
          "type": "dynamic"
        }
      },
      "interaction": {
        "tooltipDelay": 200,
        "hideEdgesOnDrag": true,
        "multiselect": true
      }
    }
    """)
    
    # Add nodes
    entity_type_counts = {}
    for entity in kg_data.get("entities", []):
        entity_id = entity.get("id", "unknown")
        entity_name = entity.get("name", entity_id)
        entity_type = entity.get("type", "unknown").lower()
        
        # Count entity types
        entity_type_counts[entity_type] = entity_type_counts.get(entity_type, 0) + 1
        
        # Set visualization properties
        color = get_entity_color(entity_type)
        title = f"Type: {entity_type}<br>ID: {entity_id}"
        
        # Add attributes to title if available
        if "attributes" in entity:
            for key, value in entity.get("attributes", {}).items():
                title += f"<br>{key}: {value}"
        
        # Adjust node size based on entity type
        size = 20  # Default size
        if entity_type == "person":
            size = 25
        elif entity_type == "organization":
            size = 30
        elif entity_type == "concept":
            size = 35
        
        # Add node to network
        net.add_node(entity_id, label=entity_name, title=title, color=color, size=size)
    
    # Add edges
    for rel in kg_data.get("relationships", []):
        source = rel.get("source")
        target = rel.get("target")
        rel_type = rel.get("type", "related_to")
        
        # Skip relationships with missing source or target
        if not source or not target:
            continue
        
        # Create tooltip
        title = f"Relationship: {rel_type}"
        
        # Add attributes to title if available
        if "attributes" in rel:
            for key, value in rel.get("attributes", {}).items():
                title += f"<br>{key}: {value}"
        
        # Add edge to network
        net.add_edge(source, target, label=rel_type, title=title)
    
    # Print statistics
    print(f"Interactive graph has {len(net.nodes)} nodes and {len(net.edges)} edges")
    print("Entity types:")
    for entity_type, count in sorted(entity_type_counts.items()):
        print(f"  - {entity_type}: {count} entities")
    
    # Save the visualization
    net.save_graph(output_file)
    print(f"Interactive visualization saved to {output_file}")
    return output_file

def main():
    filepath = "C:\\Users\\Brian\\Downloads\\crest_kg\\cia_kg_merged_5_documents.json"
    
    # Load the knowledge graph
    kg_data = load_knowledge_graph(filepath)
    
    # Create interactive visualization
    html_file = visualize_with_pyvis(kg_data)
    
    # Open the visualization in the default browser
    output_path = Path(html_file).resolve()
    webbrowser.open(f'file://{output_path}')
    
    print("\nVisualization complete! The interactive graph has been opened in your web browser.")

if __name__ == "__main__":
    main()