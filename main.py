from flask import Flask, request, jsonify
import mongodb_actions as mgd
import parsing_to_openai as oai

import math
import json

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

        return jsonify({"message": "Processing completed"}), 200

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


if __name__ == '__main__':
    app.run(port=5000, debug=True)  #debug=True: enable one-hot reloading