from flask import Flask, request, jsonify, render_template
import mongodb_actions as mgd
import parsing_to_openai as oai
import networkx as nx
from pyvis.network import Network
import math
import json
import os

app = Flask(__name__)

# takes in an array of files and runs all the logic to get the json output and store in MongoDB{pdf_name, date&time, json result, status(running, completed, failed)}, create db entry THEN update the same entry with the json
@app.route('/upload', methods=['POST'])
def upload():
    # iterate thru list of files
        # function to pre-process then run the ai
        # while its waiting for the ai function
            # function to create entry into MongoDB
        # After done another function to add the json inside
    try:
        if 'file[]' not in request.files:
            return jsonify({"error": "No files provided"}), 400
        
        file_list = request.files.getlist("file[]")
        doc_ids = []
        
        # REPLACE WITH QUEUE HERE
        for file in file_list:
            file_name = file.filename

            doc_id = mgd.createDocument(file_name)

            if doc_id:
                doc_ids.append(doc_id)
                relationships = oai.call_openai(file)

                if relationships:
                    mgd.updateDocument(relationships,doc_id,"Confirmed")
                else:
                    mgd.updateDocument("",doc_id,"Cancelled")
        # END OF REPLACEMENT

        return jsonify({"message": "Processing completed", "document_ids": doc_ids}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Returns the number of pages with /10 and ceiling it
@app.route('/page', methods=['GET'])
def page():
    num_docs = mgd.getNumberOfDocuments()
    result = 0
    if (num_docs!=False):
        result = math.ceil(num_docs/10)
    format_result = {
        "pages":result
    }
    return jsonify(format_result)

# Takes in page number and run the logic {if 1 is first 10, 2 is next 10}, returns that 10 of uid, date and name
@app.route('/list')
def lister():
    data = request.get_json()
    pageNum = data["pageNum"]

    try:
        result_list = mgd.get_documents_with_page(pageNum)
        return result_list

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Takes in the uid and returns the json of single entry
@app.route('/get', methods=['GET'])
def get():
    try:
        data = request.get_json()
        document_id = data["document_id"]
        result = mgd.getJsonWithId(document_id)

        if result:
            return result

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/visualize', methods=['GET'])
def visualize():
    try:
        # Get the request data
        data = request.get_json()
        print("Received data:", data)  # Debugging: print received data
        
        document_id = data.get("document_id")
        if not document_id:
            return jsonify({"error": "document_id is required"}), 400

        # Fetch the document from MongoDB (returns the array of dictionaries directly)
        document = mgd.getJsonWithId(document_id)
      
        if not document:
            return jsonify({"error": "Document not found"}), 404

        # Directly use the returned 'entity_relationships' list (array of dictionaries)
        entity_relationships = document

        if not isinstance(entity_relationships, list):
            return jsonify({"error": "Expected 'entity_relationship' to be a list"}), 400

        # Initialize NetworkX graph and node counts
        G = nx.Graph()
        node_counts = {}

        # Iterate through each item in the entity_relationships array
        for item in entity_relationships:
            if isinstance(item, dict):  # Ensure the item is a dictionary
                # Extract the relevant fields
                entity1 = item.get("entity1")
                relationship = item.get("relationship")
                entity2 = item.get("entity2")

                # Check if the necessary keys are present
                if entity1 and relationship and entity2:
                    G.add_edge(entity1, entity2, label=relationship)
                    node_counts[entity1] = node_counts.get(entity1, 0) + 1
                    node_counts[entity2] = node_counts.get(entity2, 0) + 1
                else:
                    # Handle missing keys
                    print(f"Missing expected keys in item: {item}")
            else:
                # Handle unexpected item type
                print(f"Unexpected item type in entity_relationships: {type(item)} - Item: {item}")

        # Convert the NetworkX graph to PyVis Network
        pyvis_graph = Network(notebook=False, height="750px", width="100%", bgcolor="#222222", font_color="white")

        # Add nodes with color based on frequency and show frequency on hover
        for node in G.nodes():
            frequency = node_counts.get(node, 1)
            color_intensity = max(0, 255 - (frequency * 20))
            color = f"rgb({color_intensity}, {color_intensity}, {color_intensity})"
            
            # Modify the tooltip to show the frequency count
            pyvis_graph.add_node(node, 
                                 label=node, 
                                 title=f"{node} appeared {frequency} times",  # Show frequency on hover
                                 size=20 + len(list(G.neighbors(node))), 
                                 color=color)

        # Add edges to the graph
        for edge in G.edges(data=True):
            pyvis_graph.add_edge(edge[0], edge[1], title=edge[2]['label'])

        # Set options for PyVis graph without the events part
        pyvis_graph.set_options(json.dumps({
            "physics": {
                "enabled": True,
                "repulsion": {
                    "nodeDistance": 200,
                    "springLength": 100
                }
            },
            "interaction": {
                "hover": True,
                "tooltipDelay": 200,
                "hideEdgesOnDrag": False
            }
        }))

        # Generate HTML with PyVis (ensure the container is there)
        output_file = "templates/entity_relationship_graph.html"
        pyvis_graph.write_html(output_file)  # Write out the pyvis graph HTML

        # Return the template (Ensure the file exists)
        try:
            return render_template("entity_relationship_graph.html")
        except Exception as e:
            print(f"Error rendering template: {str(e)}")  # Log error for debugging
            return jsonify({"error": "Failed to render template"}), 500

    except Exception as e:
        print(f"Error occurred: {str(e)}")  # Log the error for debugging
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(port=5000, debug=True)  #debug=True: enable one-hot reloading