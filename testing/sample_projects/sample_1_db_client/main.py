from mysql.main_db import create_database
from mysql.event_client import AmlEventClient
from flask import Flask, jsonify, request


db_handle = create_database(write_url="sqlite:///:memory:")
event_client = AmlEventClient(db_handle)


app = Flask(__name__)



# Return type 
@app.route('/api/v1/autodiagonosis/event_list/<int:job_id>', methods=['GET'])
def get_event_list(job_id):
    status = {"Status":200, "Message":"successfully Executed","Error":None}
    try:
        # List of events data
        events = event_client.query_events(query_dict={"job_id":job_id})
        # events = EVENTCLIENT.query_events(query_dict={"job_id":job_id})
        if not events:
            status["Message"] = "Job_ID not in database"
        result = [status] + events
        return jsonify(result)
    except Exception as e:
        status["Status"] = 404
        status["Message"] = "Siginificant system failure"
        status["Error"] = str(e)
        return jsonify([status])
    

if __name__ == '__main__':
    app.run('0.0.0.0', port=7981, debug=False,threaded=True)