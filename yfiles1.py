import json
import os
import random
import math
import webbrowser
from typing import Dict, Any
from pathlib import Path

# Install yfiles_jupyter_graphs if needed
try:
    from yfiles_jupyter_graphs import GraphWidget
except ImportError:
    print("Installing yfiles_jupyter_graphs...")
    import subprocess
    subprocess.check_call(["pip", "install", "yfiles_jupyter_graphs"])
    from yfiles_jupyter_graphs import GraphWidget

# Load the knowledge graph
def load_knowledge_graph(filepath):
    """Load the knowledge graph from a JSON file"""
    print(f"Loading knowledge graph from {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        kg_data = json.load(f)
    return kg_data

# Create a color map for entity types
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

# Convert knowledge graph to yFiles format
def convert_kg_to_yfiles_format(kg_data):
    """Convert the knowledge graph data to the format expected by yFiles widget"""
    # Prepare nodes
    nodes = []
    for entity in kg_data.get("entities", []):
        entity_id = entity.get("id", "unknown")
        entity_name = entity.get("name", entity_id)
        entity_type = entity.get("type", "unknown")
        
        # Add node
        nodes.append({
            "id": entity_id,
            "properties": {
                "label": entity_name,
                "type": entity_type,
                **entity.get("attributes", {})
            }
        })
    
    # Prepare edges
    edges = []
    for i, rel in enumerate(kg_data.get("relationships", [])):
        source = rel.get("source")
        target = rel.get("target")
        rel_type = rel.get("type", "related_to")
        
        # Skip relationships with missing source or target
        if not source or not target:
            continue
        
        # Add edge
        edges.append({
            "id": f"rel_{i}",
            "start": source,
            "end": target,
            "properties": {
                "label": rel_type,
                **rel.get("attributes", {})
            }
        })
    
    return nodes, edges

# Create mapping functions
def node_color_mapping(node: Dict):
    """Map node colors based on entity type"""
    entity_type = node.get("properties", {}).get("type", "unknown")
    return get_entity_color(entity_type)

def node_label_mapping(node: Dict):
    """Map node labels from the properties"""
    return node.get("properties", {}).get("label", str(node.get("id", "")))

def edge_label_mapping(edge: Dict):
    """Map edge labels from the properties"""
    return edge.get("properties", {}).get("label", "")

def node_type_mapping(node: Dict):
    """Map node types from the properties"""
    return node.get("properties", {}).get("type", "unknown")

def node_size_mapping(node: Dict):
    """Adjust node sizes based on entity type"""
    entity_type = node.get("properties", {}).get("type", "unknown").lower()
    if entity_type == "person":
        return (60, 60)
    elif entity_type == "organization":
        return (80, 80)
    elif entity_type == "concept":
        return (100, 60)
    else:
        return (70, 50)

# Export visualization to HTML
def export_graph_to_html(widget, output_file="cia_knowledge_graph.html"):
    """Export the widget to HTML"""
    from IPython.display import HTML
    
    # Create a basic HTML template
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>CIA Knowledge Graph Visualization</title>
        <style>
            body { margin: 0; font-family: Arial, sans-serif; }
            #graph-container { 
                width: 100%; 
                height: 100vh; 
                border: 1px solid #ccc; 
            }
            .header {
                background-color: #333;
                color: white;
                padding: 10px;
                text-align: center;
            }
            .footer {
                position: fixed;
                bottom: 0;
                width: 100%;
                background-color: #333;
                color: white;
                text-align: center;
                padding: 5px;
                font-size: 12px;
            }
            .legend {
                position: absolute;
                top: 10px;
                right: 10px;
                background: rgba(255, 255, 255, 0.8);
                border: 1px solid #ccc;
                padding: 10px;
                border-radius: 5px;
            }
            .legend-item {
                margin: 5px 0;
            }
            .color-box {
                display: inline-block;
                width: 20px;
                height: 20px;
                margin-right: 5px;
                vertical-align: middle;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h2>CIA Knowledge Graph Visualization</h2>
        </div>
        
        <div id="graph-container">
            <!-- Graph will be rendered here -->
        </div>
        
        <div class="legend">
            <h3>Entity Types</h3>
            <div class="legend-item"><span class="color-box" style="background-color: #66c2a5;"></span>Person</div>
            <div class="legend-item"><span class="color-box" style="background-color: #fc8d62;"></span>Organization</div>
            <div class="legend-item"><span class="color-box" style="background-color: #8da0cb;"></span>Location</div>
            <div class="legend-item"><span class="color-box" style="background-color: #e78ac3;"></span>Event</div>
            <div class="legend-item"><span class="color-box" style="background-color: #a6d854;"></span>Concept</div>
            <div class="legend-item"><span class="color-box" style="background-color: #cccccc;"></span>Other</div>
        </div>
        
        <div class="footer">
            CIA Documents Knowledge Graph - Created with yFiles for Jupyter
        </div>
        
        <script>
            // Replace this with yFiles visualization code
            document.getElementById('graph-container').innerHTML = 'This is a static HTML export. The interactive visualization requires JavaScript libraries that cannot be included.';
        </script>
    </body>
    </html>
    """
    
    # Write HTML to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    print(f"Exported static HTML to {output_file}")
    return output_file

# Alternative visualization using NetworkX with HTML export
def visualize_with_networkx(kg_data, output_file="cia_knowledge_graph_networkx.html"):
    """Create a NetworkX visualization and export to HTML"""
    import networkx as nx
    import matplotlib.pyplot as plt
    from networkx.drawing.nx_agraph import graphviz_layout
    
    try:
        # Try to use PyGraphviz for better layout
        import pygraphviz
        use_graphviz = True
    except ImportError:
        use_graphviz = False
        print("PyGraphviz not available. Using spring layout instead.")
    
    # Create graph
    G = nx.DiGraph()
    
    # Add nodes
    for entity in kg_data.get("entities", []):
        entity_id = entity.get("id", "unknown")
        entity_name = entity.get("name", entity_id)
        entity_type = entity.get("type", "unknown")
        
        # Add node with attributes
        G.add_node(entity_id, name=entity_name, entity_type=entity_type, 
                   color=get_entity_color(entity_type), **entity.get("attributes", {}))
    
    # Add edges
    for rel in kg_data.get("relationships", []):
        source = rel.get("source")
        target = rel.get("target")
        rel_type = rel.get("type", "related_to")
        
        # Skip relationships with missing source or target
        if not source or not target:
            continue
        
        # Skip relationships where source or target node doesn't exist
        if source not in G.nodes or target not in G.nodes:
            continue
        
        # Add edge with attributes
        G.add_edge(source, target, relation_type=rel_type, **rel.get("attributes", {}))
    
    print(f"NetworkX graph has {len(G.nodes)} nodes and {len(G.edges)} edges")
    
    # Calculate node colors based on type
    node_colors = [G.nodes[node].get("color", "#cccccc") for node in G.nodes]
    
    # Calculate node sizes based on centrality
    try:
        centrality = nx.betweenness_centrality(G)
        node_sizes = [300 * (centrality[node] + 0.1) for node in G.nodes]
    except:
        node_sizes = [300 for _ in G.nodes]
    
    # Set up the visualization
    plt.figure(figsize=(20, 16))
    
    # Use an appropriate layout
    if use_graphviz:
        try:
            pos = graphviz_layout(G, prog="dot")
        except:
            pos = nx.spring_layout(G, k=0.15, iterations=50, seed=42)
    else:
        pos = nx.spring_layout(G, k=0.15, iterations=50, seed=42)
    
    # Draw nodes
    nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color=node_colors, alpha=0.8)
    
    # Draw edges
    nx.draw_networkx_edges(G, pos, width=1.0, alpha=0.7, arrowsize=15)
    
    # Add labels (limit to important nodes)
    if len(G.nodes) > 50:
        # For large graphs, only label the most important nodes
        centrality_threshold = sorted(centrality.values(), reverse=True)[min(50, len(centrality)-1)]
        labels = {node: G.nodes[node].get("name", node) for node in G.nodes 
                  if centrality[node] >= centrality_threshold}
    else:
        # For small graphs, label all nodes
        labels = {node: G.nodes[node].get("name", node) for node in G.nodes}
    
    nx.draw_networkx_labels(G, pos, labels, font_size=10, font_weight='bold')
    
    # Create a legend for entity types
    unique_types = set(G.nodes[node].get("entity_type", "unknown").lower() for node in G.nodes)
    unique_colors = [get_entity_color(t) for t in unique_types]
    
    legend_elements = [plt.Line2D([0], [0], marker='o', color='w', 
                                markerfacecolor=get_entity_color(t), 
                                markersize=10, label=t.capitalize()) 
                      for t in sorted(unique_types)]
    plt.legend(handles=legend_elements, loc='upper right', title="Entity Types")
    
    # Set title and turn off axis
    plt.title("CIA Documents Knowledge Graph", fontsize=16)
    plt.axis('off')
    
    # Save as PNG and HTML
    plt.savefig(output_file.replace('.html', '.png'), dpi=300, bbox_inches='tight')
    
    # Create HTML file
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>CIA Knowledge Graph Visualization</title>
        <style>
            body {{ margin: 0; font-family: Arial, sans-serif; text-align: center; }}
            .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
            img {{ max-width: 100%; border: 1px solid #ddd; }}
            .header {{ background-color: #333; color: white; padding: 10px; }}
            .footer {{ margin-top: 20px; padding: 10px; background-color: #f5f5f5; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>CIA Documents Knowledge Graph</h1>
            <p>{len(G.nodes)} entities and {len(G.edges)} relationships</p>
        </div>
        <div class="container">
            <img src="{output_file.replace('.html', '.png')}" alt="Knowledge Graph Visualization">
            <div class="footer">
                <p>Generated from CIA document analysis</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Saved visualization to {output_file} and {output_file.replace('.html', '.png')}")
    return output_file

# Main function to visualize the knowledge graph
def main():
    filepath = "C:\\Users\\Brian\\Downloads\\crest_kg\\cia_kg_merged_5_documents.json"
    
    # Load the knowledge graph
    kg_data = load_knowledge_graph(filepath)
    
    # Check if yFiles can be properly initialized
    try:
        # Try to create a yFiles widget
        nodes, edges = convert_kg_to_yfiles_format(kg_data)
        w = GraphWidget()
        w.nodes = nodes
        w.edges = edges
        w.directed = True
        
        # Set custom mappings
        w.set_node_color_mapping(node_color_mapping)
        w.set_node_label_mapping(node_label_mapping)
        w.set_edge_label_mapping(edge_label_mapping)
        w.set_node_type_mapping(node_type_mapping)
        w.set_node_size_mapping(node_size_mapping)
        
        # Set the widget height
        w.layout.height = '800px'
        
        # Export to HTML
        html_file = export_graph_to_html(w)
        print(f"Since you're running this as a script, an HTML template has been created. For full interactive visualization, please run this in a Jupyter notebook.")
        
    except Exception as e:
        print(f"Error with yFiles visualization: {e}")
        print("Falling back to NetworkX visualization...")
    
    # Create NetworkX visualization (as a fallback)
    networkx_html = visualize_with_networkx(kg_data)
    
    # Open the visualization in the default browser
    output_path = Path(networkx_html).resolve()
    webbrowser.open(f'file://{output_path}')
    
    print("\nVisualization complete!")
    print("Note: For a full interactive visualization with yFiles, please run this in a Jupyter notebook.")
    print("For instructions on setting up a Jupyter environment, visit: https://jupyter.org/install")

if __name__ == "__main__":
    main()