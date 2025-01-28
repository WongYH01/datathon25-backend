from flask import Flask, request, jsonify

app = Flask(__name__)

# takes in an array of files and runs all the logic to get the json output and store in MongoDB{pdf_name, date&time, json result, status(running, completed, failed)}, create db entry THEN update the same entry with the json
@app.route('/upload')
def upload():
    # iterate thru list of files
        # function to pre-process the file to text
        # function to run the ai
        # while its waiting for the ai function
            # function to create entry into MongoDB
        # After done another function to add the json inside
    return None

# Returns the number of pages with /10 and ceiling it
@app.route('/page')
def page():

    return None

# Takes in page number and run the logic {if 1 is first 10, 2 is next 10}, returns that 10 of uid, date and name
@app.route('/list')
def lister():

    return None

# Takes in the uid and returns the json of single entry
@app.route('/get')
def get():

    return None



if __name__ == '__main__':
    app.run(port=5000, debug=True)  #debug=True: enable one-hot reloading