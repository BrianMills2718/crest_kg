import json
import os
import webbrowser
from pathlib import Path
import subprocess
import sys

# Install pyvis if not already installed
try:
    from pyvis.network import Network
except ImportError:
    print("Installing pyvis...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyvis"])
    from pyvis.network import Network

# Function to find the most recent knowledge graph file
def find_latest_kg_file():
    """Find the most recent knowledge graph file"""
    import glob
    
    # Look for knowledge graph files
    kg_files = glob.glob("cia_ufo_output/ufo_*kg_*.json")
    if not kg_files:
        print("No knowledge graph files found!")
        return None
    
    # Sort by modification time (most recent first)
    kg_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return kg_files[0]

# Load the knowledge graph
def load_knowledge_graph(filepath=None):
    """Load the knowledge graph from a JSON file"""
    if not filepath:
        filepath = find_latest_kg_file()
        if not filepath:
            return None
    
    print(f"Loading knowledge graph from {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        kg_data = json.load(f)
    
    print(f"Loaded knowledge graph with {len(kg_data.get('entities', []))} entities and {len(kg_data.get('relationships', []))} relationships")
    return kg_data

# Get entity color based on type
def get_entity_color(entity_type):
    """Return a color based on entity type"""
    color_map = {
        "document": "#1f78b4",    # Blue
        "person": "#33a02c",      # Green
        "location": "#e31a1c",    # Red
        "time": "#ff7f00",        # Orange
        "organization": "#6a3d9a", # Purple
        "concept": "#fdbf6f",     # Light orange
        "collection": "#a6cee3",  # Light blue
        "file": "#cab2d6",        # Light purple
        "unknown": "#cccccc"      # Gray
    }
    return color_map.get(entity_type.lower(), "#cccccc")

def visualize_with_pyvis(kg_data=None, output_file="ufo_knowledge_graph_interactive.html"):
    """Create an interactive visualization using Pyvis"""
    # Load knowledge graph if not provided
    if not kg_data:
        kg_data = load_knowledge_graph()
        if not kg_data:
            print("No knowledge graph data available.")
            return None
    
    # Create network
    net = Network(height="900px", width="100%", directed=True, notebook=False)
    
    # Configure physics for better layout
    net.barnes_hut(spring_length=200, spring_strength=0.01, damping=0.09, central_gravity=0.5)
    
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
        title = f"<b>{entity_name}</b><br>Type: {entity_type}<br>ID: {entity_id}"
        
        # Add attributes to title if available
        if "attributes" in entity:
            for key, value in entity.get("attributes", {}).items():
                if value:  # Only add non-empty attributes
                    title += f"<br>{key}: {value}"
        
        # Adjust node size and shape based on entity type
        size = 20  # Default size
        shape = "dot"  # Default shape
        
        if entity_type == "document":
            size = 30
            shape = "square"
        elif entity_type == "person":
            size = 25
            shape = "diamond"
        elif entity_type == "organization":
            size = 25
            shape = "triangle"
        elif entity_type == "concept":
            size = 25
            shape = "star"
        elif entity_type == "location":
            size = 20
            shape = "triangle"
        elif entity_type == "time":
            size = 15
            shape = "dot"
        
        # Add node to network
        net.add_node(entity_id, label=entity_name, title=title, color=color, size=size, shape=shape)
    
    # Add edges
    for rel in kg_data.get("relationships", []):
        source = rel.get("source")
        target = rel.get("target")
        rel_type = rel.get("type", "related_to")
        
        # Skip relationships with missing source or target
        if not source or not target:
            continue
        
        # Skip if nodes don't exist (could happen if there was filtering)
        if source not in [node['id'] for node in net.nodes] or target not in [node['id'] for node in net.nodes]:
            continue
        
        # Create tooltip
        title = f"<b>Relationship:</b> {rel_type}"
        
        # Add attributes to title if available
        if "attributes" in rel:
            for key, value in rel.get("attributes", {}).items():
                if value:  # Only add non-empty attributes
                    title += f"<br>{key}: {value}"
        
        # Determine edge color based on relationship type
        edge_color = "#999999"  # Default gray
        if "discusses" in rel_type.lower() or "mentions" in rel_type.lower():
            edge_color = "#ff9900"  # Orange for mentions/discussions
        elif "part_of" in rel_type.lower() or "has_file" in rel_type.lower():
            edge_color = "#0077cc"  # Blue for organizational relationships
        elif "location" in rel_type.lower():
            edge_color = "#33cc33"  # Green for location
        
        # Add edge to network
        net.add_edge(source, target, label=rel_type, title=title, color=edge_color, arrows="to")
    
    # Add custom buttons and controls to the HTML
    net.set_options("""
    {
      "nodes": {
        "font": {
          "size": 14,
          "face": "Tahoma"
        }
      },
      "edges": {
        "font": {
          "size": 12,
          "face": "Tahoma"
        },
        "smooth": {
          "enabled": true,
          "type": "dynamic"
        },
        "arrows": {
          "to": {
            "enabled": true,
            "scaleFactor": 0.5
          }
        },
        "length": 200
      },
      "physics": {
        "stabilization": {
          "iterations": 1000
        },
        "barnesHut": {
          "gravitationalConstant": -80000,
          "centralGravity": 0.3,
          "springLength": 200,
          "springConstant": 0.05,
          "damping": 0.09
        }
      },
      "interaction": {
        "navigationButtons": true,
        "keyboard": true,
        "tooltipDelay": 300,
        "hideEdgesOnDrag": true
      }
    }
    """)
    
    # Print statistics
    print(f"Interactive graph has {len(net.nodes)} nodes and {len(net.edges)} edges")
    print("Entity types:")
    for entity_type, count in sorted(entity_type_counts.items()):
        print(f"  - {entity_type}: {count} entities")
    
    # Add custom HTML with a legend
    html_before = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>CIA UFO Documents Knowledge Graph</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
            }
            .header {
                background-color: #333;
                color: white;
                padding: 10px 20px;
                text-align: center;
            }
            .container {
                display: flex;
                height: calc(100vh - 100px);
            }
            #mynetwork {
                flex-grow: 1;
                border: 1px solid #ddd;
            }
            .legend {
                width: 220px;
                padding: 10px;
                background-color: #f8f8f8;
                border-left: 1px solid #ddd;
                overflow-y: auto;
            }
            .legend-item {
                margin: 8px 0;
                display: flex;
                align-items: center;
            }
            .color-box {
                width: 20px;
                height: 20px;
                margin-right: 10px;
                border-radius: 3px;
            }
            .controls {
                padding: 10px;
                background-color: #f0f0f0;
                border-bottom: 1px solid #ddd;
            }
            button {
                padding: 5px 10px;
                margin-right: 5px;
                cursor: pointer;
            }
            .footer {
                padding: 10px;
                text-align: center;
                font-size: 12px;
                color: #666;
                background-color: #f5f5f5;
                border-top: 1px solid #ddd;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>CIA UFO Documents Knowledge Graph</h1>
            <p>Interactive visualization of UFO: Fact or Fiction? collection</p>
        </div>
        <div class="controls">
            <button onclick="network.stabilize(100)">Stabilize</button>
            <button onclick="network.fit()">Fit to Screen</button>
            <button onclick="togglePhysics()">Toggle Physics</button>
            <span style="margin-left: 20px;">
                Node Filter: 
                <select id="nodeTypeFilter" onchange="filterNodesByType()">
                    <option value="all">Show All</option>
                    <option value="document">Documents Only</option>
                    <option value="person">Persons Only</option>
                    <option value="organization">Organizations Only</option>
                    <option value="concept">Concepts Only</option>
                    <option value="location">Locations Only</option>
                </select>
            </span>
        </div>
        <div class="container">
    """
    
    html_after = """
            <div class="legend">
                <h3>Entity Types</h3>
                <div class="legend-item">
                    <div class="color-box" style="background-color: #1f78b4;"></div>
                    <div>Document</div>
                </div>
                <div class="legend-item">
                    <div class="color-box" style="background-color: #33a02c;"></div>
                    <div>Person</div>
                </div>
                <div class="legend-item">
                    <div class="color-box" style="background-color: #e31a1c;"></div>
                    <div>Location</div>
                </div>
                <div class="legend-item">
                    <div class="color-box" style="background-color: #ff7f00;"></div>
                    <div>Time</div>
                </div>
                <div class="legend-item">
                    <div class="color-box" style="background-color: #6a3d9a;"></div>
                    <div>Organization</div>
                </div>
                <div class="legend-item">
                    <div class="color-box" style="background-color: #fdbf6f;"></div>
                    <div>Concept</div>
                </div>
                
                <h3>Relationship Types</h3>
                <div class="legend-item">
                    <div class="color-box" style="background-color: #ff9900;"></div>
                    <div>Mentions/Discusses</div>
                </div>
                <div class="legend-item">
                    <div class="color-box" style="background-color: #0077cc;"></div>
                    <div>Organizational</div>
                </div>
                <div class="legend-item">
                    <div class="color-box" style="background-color: #33cc33;"></div>
                    <div>Location-based</div>
                </div>
                <div class="legend-item">
                    <div class="color-box" style="background-color: #999999;"></div>
                    <div>Other</div>
                </div>
                
                <h3>Statistics</h3>
                <div>Entities: {num_nodes}</div>
                <div>Relationships: {num_edges}</div>
            </div>
        </div>
        <div class="footer">
            Created from CIA UFO FOIA documents - Knowledge Graph Visualization
        </div>
        
        <script>
            // Store the original dataset
            let allNodes = new vis.DataSet(network.body.data.nodes.get());
            let allEdges = new vis.DataSet(network.body.data.edges.get());
            
            // Function to toggle physics
            function togglePhysics() {{
                network.physics.options.enabled = !network.physics.options.enabled;
                network.setOptions({{ physics: {{ enabled: network.physics.options.enabled }} }});
            }}
            
            // Function to filter nodes by type
            function filterNodesByType() {{
                let selectedType = document.getElementById('nodeTypeFilter').value;
                
                if (selectedType === 'all') {{
                    // Restore all nodes and edges
                    network.body.data.nodes.clear();
                    network.body.data.edges.clear();
                    network.body.data.nodes.add(allNodes.get());
                    network.body.data.edges.add(allEdges.get());
                    return;
                }}
                
                // Get nodes of selected type
                let filteredNodes = allNodes.get().filter(node => {{
                    return node.title && node.title.toLowerCase().includes('type: ' + selectedType);
                }});
                
                // Get their IDs
                let filteredNodeIds = filteredNodes.map(node => node.id);
                
                // Get edges connected to these nodes
                let filteredEdges = allEdges.get().filter(edge => {{
                    return filteredNodeIds.includes(edge.from) && filteredNodeIds.includes(edge.to);
                }});
                
                // Update the visualization
                network.body.data.nodes.clear();
                network.body.data.edges.clear();
                network.body.data.nodes.add(filteredNodes);
                network.body.data.edges.add(filteredEdges);
            }}
        </script>
    </body>
    </html>
    """.format(num_nodes=len(net.nodes), num_edges=len(net.edges))
    
    # Save the visualization with custom HTML
    net.html = html_before + net.html + html_after
    net.save_graph(output_file)
    print(f"Interactive visualization saved to {output_file}")
    return output_file

def main():
    # Create visualization
    html_file = visualize_with_pyvis()
    
    # Open the visualization in the default browser
    if html_file:
        output_path = Path(html_file).resolve()
        webbrowser.open(f'file://{output_path}')
        print("\nVisualization opened in your web browser")
    
    print("\nProcess completed!")

if __name__ == "__main__":
    main()