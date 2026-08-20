import json
import os
import networkx as nx
import matplotlib.pyplot as plt
from typing import Dict, Any

def visualize_knowledge_graph(json_file_path: str, output_file: str = "kg_visualization.png", 
                             figsize=(20, 16), node_size=700, layout_scale=0.15):
    """
    Create a visualization of a knowledge graph from a JSON file.
    
    Args:
        json_file_path: Path to the JSON file containing the knowledge graph
        output_file: Path where the visualization image will be saved
        figsize: Size of the figure (width, height) in inches
        node_size: Size of the nodes in the visualization
        layout_scale: Scale factor for the spring layout (smaller values spread nodes farther)
    """
    print(f"Loading knowledge graph from {json_file_path}...")
    
    try:
        # Load the knowledge graph from the JSON file
        with open(json_file_path, 'r', encoding='utf-8') as f:
            kg_data = json.load(f)
        
        # Create a directed graph
        G = nx.DiGraph()
        
        # Add nodes (entities)
        print("Adding entities as nodes...")
        for entity in kg_data.get("entities", []):
            entity_id = entity.get("id", "unknown")
            entity_name = entity.get("name", entity_id)
            entity_type = entity.get("type", "unknown")
            
            # Handle attributes, avoiding "type" conflict
            attributes = entity.get("attributes", {})
            if "type" in attributes:
                # Rename the attribute to avoid conflict
                attributes["attr_type"] = attributes.pop("type")
            
            # Add node with attributes
            G.add_node(entity_id, name=entity_name, entity_type=entity_type, **attributes)
        
        # Add edges (relationships)
        print("Adding relationships as edges...")
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
            
            # Handle attributes, avoiding "type" conflict
            attributes = rel.get("attributes", {})
            if "type" in attributes:
                attributes["attr_type"] = attributes.pop("type")
            
            # Add edge with attributes
            G.add_edge(source, target, relation_type=rel_type, **attributes)
        
        print(f"Knowledge graph has {len(G.nodes)} nodes and {len(G.edges)} edges")
        
        # Set up the visualization
        plt.figure(figsize=figsize)
        
        # Define a color map for entity types
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
        
        # Get all unique node types
        node_types = set()
        for node in G.nodes:
            node_type = G.nodes[node].get("entity_type", "unknown").lower()
            node_types.add(node_type)
        
        # Set node colors based on type
        node_colors = []
        for node in G.nodes:
            node_type = G.nodes[node].get("entity_type", "unknown").lower()
            node_colors.append(color_map.get(node_type, "#cccccc"))
        
        # Use spring layout for positioning
        print("Calculating node positions...")
        pos = nx.spring_layout(G, k=layout_scale, iterations=50, seed=42)
        
        # Draw the graph
        print("Drawing the graph...")
        nx.draw_networkx_nodes(G, pos, node_size=node_size, node_color=node_colors, alpha=0.8)
        nx.draw_networkx_edges(G, pos, width=1.0, alpha=0.7, arrowsize=15)
        
        # Add labels
        labels = {node: G.nodes[node].get("name", node) for node in G.nodes}
        nx.draw_networkx_labels(G, pos, labels, font_size=10, font_weight='bold')
        
        # Add edge labels (but filter to avoid overcrowding)
        # Only show edge labels for a random subset if there are many edges
        edge_label_threshold = 50
        edge_labels = {}
        
        if len(G.edges) <= edge_label_threshold:
            # Show all edge labels if below threshold
            edge_labels = {(source, target): G.edges[source, target].get("relation_type", "") 
                          for source, target in G.edges}
        else:
            # Show labels for a subset of edges
            import random
            edges_to_label = random.sample(list(G.edges), edge_label_threshold)
            edge_labels = {(source, target): G.edges[source, target].get("relation_type", "") 
                          for source, target in edges_to_label}
            
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8)
        
        # Create a legend for entity types
        legend_elements = [plt.Line2D([0], [0], marker='o', color='w', 
                                    markerfacecolor=color_map.get(t, "#cccccc"), 
                                    markersize=10, label=t.capitalize()) 
                          for t in sorted(node_types)]
        plt.legend(handles=legend_elements, loc='upper right', title="Entity Types")
        
        # Set title and turn off axis
        plt.title(f"CIA Documents Knowledge Graph\n({len(G.nodes)} entities, {len(G.edges)} relationships)", 
                 fontsize=16, fontweight='bold')
        plt.axis('off')
        
        # Save the visualization
        print(f"Saving visualization to {output_file}...")
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        
        # Also save as PDF if possible
        try:
            pdf_output = output_file.replace('.png', '.pdf')
            plt.savefig(pdf_output, bbox_inches='tight')
            print(f"Also saved as PDF: {pdf_output}")
        except Exception as pdf_error:
            print(f"Could not save as PDF: {pdf_error}")
            
        plt.close()
        
        print(f"Visualization successfully saved to {output_file}")
        
        # Return graph statistics
        return {
            "num_entities": len(G.nodes),
            "num_relationships": len(G.edges),
            "entity_types": sorted(list(node_types)),
            "most_connected_entities": sorted([(G.nodes[node].get("name", node), G.degree(node)) 
                                             for node in G.nodes], 
                                            key=lambda x: x[1], reverse=True)[:10]
        }
    
    except Exception as e:
        print(f"Error creating visualization: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    # File paths
    input_file = "C:\\Users\\Brian\\Downloads\\crest_kg\\cia_kg_merged_5_documents.json"
    output_file = "cia_knowledge_graph_visualization.png"
    
    # Create visualization
    stats = visualize_knowledge_graph(input_file, output_file)
    
    if stats:
        print("\nKnowledge Graph Statistics:")
        print(f"Number of entities: {stats['num_entities']}")
        print(f"Number of relationships: {stats['num_relationships']}")
        print(f"Entity types: {', '.join(stats['entity_types'])}")
        
        print("\nMost connected entities:")
        for entity, connections in stats['most_connected_entities']:
            print(f"  - {entity}: {connections} connections")

if __name__ == "__main__":
    main()