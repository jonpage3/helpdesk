# First we import parts of the frameworks we're using:
#
# Flask <http://flask.pocoo.org> is a simple framework for building web
# applications in Python. It handles basic things like parsing incoming
# HTTP requests and generating responses.
#
# Flask-RESTful <https://flask-restful.readthedocs.io/> is an add-on to Flask
# that makes it easier to build web applications that adhere to the REST
# architectural style.

from flask import (Flask, Response, request, render_template, make_response,
                   redirect)
from flask_restful import Api, Resource, reqparse, abort

# Next we import some standard Python libraries and functions:
#
# json <https://docs.python.org/3/library/json.html> for loading a JSON file
# from disk (our "database") into memory.
#
# datetime <https://docs.python.org/3/library/datetime.html> to help us
# generate timestamps for help tickets.
#
# wraps <https://docs.python.org/3/library/functools.html#functools.wraps>
# is just a convenience function that will help us implement authentication.

import json
import datetime
from functools import wraps

# These are the constant values for library locations
PICKUP_LOCATIONS = ('Davis Library','Undergraduate Library','Science Library Annex',
                    'Art Library','Law Library','SILS Library')

#loads the data from request_data.jsonld file
with open('request_data.jsonld') as request_data:
    request_data = json.load(request_data)

# The next three functions implement simple authentication.

# Check that username and password are OK; DON'T DO THIS FOR REAL
def check_auth(username, password):
    return username == 'admin' and password == 'secret'

# Issue an authentication challenge
def authenticate():
    return Response(
        'Please authenticate yourself', 401,
        {'WWW-Authenticate': 'Basic realm="helpdesk"'})

# Decorator for methods that require authentication
def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


# The following are three  helper functions used in our resource classes.

# helps generate an ID for a new request
# based on number of most recent request
def generate_maxid(requests):
    IDs =[]
    for x in requests:
        IDs.append(int(requests[x]['id']))
    return max(IDs)

#function to help generate ETAs for a request
#Works on simple logic that if a pickup location
#is different than the item location, it will take
#day longer to process the request. Also assumes it takes
#one day to change request status.
def generate_etas(request):

    def eta(num):
        return f"{(datetime.datetime.now() + datetime.timedelta(days=num)):%m-%d-%Y}"

    other_etas = {}

    if request['pickup'] == request['location']:
        if request['status'] == 'Awaiting Circulation Processing':
            request['eta'] = eta(2)
            other_etas['eta'] = eta(3)
        elif request['status'] == 'Awaiting Stacks Searching':
            request['eta'] = eta(1)
            other_etas['eta'] = eta(2)
        else:
            request['eta'] = 'Request Finished'
    else:
        if request['status'] == 'Awaiting Circulation Processing':
            request['eta'] = eta(3)
            other_etas['eta'] = eta(3)
            #specify difference in changing pickup location
            #to book location
            other_etas['home'] = eta(2)
        elif request['status'] == 'Awaiting Stacks Searching':
            request['eta'] = eta(2)
            other_etas['eta'] = eta(2)
            other_etas['home'] = eta(1)
        elif request['status'] == 'In Transit':
            request['eta'] = eta(1)
            other_etas['eta'] = eta(1)

        else:
            request['eta'] = 'Request Finished'

    return other_etas

#Filter requests
def filter_request(query=''):
    def matches_query(item):
        (request_id,request) = item
        text = request['title'] + request['pickup'] + request['status']
        return query.lower() in text

    #filtered_requests = filter(matches_query,request_data['requests'].items())

    return filter(matches_query,request_data['requests'].items())

def sort_etas(sort_by=''):
    pass

# Helper function new_request_parser. Raises an error if the string x
# is empty (has zero length).
def nonempty_string(x):
    s = str(x)
    if len(x) == 0:
        raise ValueError('string is empty')
    return s

# Specify the data necessary to create a new request
#"title", 'item location', "pickup location" and "oclc" are required values
new_request_parser = reqparse.RequestParser()
for arg in ['username','title', 'location','pickup','oclc']:
    new_request_parser.add_argument(
        arg, type=nonempty_string, required=True,
    help="'{}' is a required value".format(arg))

#Specify the data necessary to update an existing request
#only the pickup and notes can be updated
update_request_parser = reqparse.RequestParser()
update_request_parser.add_argument(
    'pickup', type=str, default='')
update_request_parser.add_argument(
    'notes', type=str, default='')

# Specify the parameters for filtering requests.
# See `filter requests` above.
query_parser = reqparse.RequestParser()
query_parser.add_argument(
    'query', type=str, default='')


#parser for sorting etas
#THIS IS NOT USED IN THE CURRENT CODE
sort_parser = reqparse.RequestParser()
sort_parser.add_argument(
    'sort_by', type=str, choices=('pickup','eta'), default='')


# Then we define a couple of helper functions for inserting data into HTML
# templates (found in the templates/ directory). See
# <http://flask.pocoo.org/docs/latest/quickstart/#rendering-templates>.

def render_request_as_html(request):
    return render_template(
        'request.html', request=request,pickups=PICKUP_LOCATIONS)

def render_eta_list_as_html(request,other_etas):
    return render_template(
        'eta.html',request=request,pickups=PICKUP_LOCATIONS,other_etas = other_etas)

def render_request_list_as_html(requests):
    return render_template('Requests.html',requests=requests,pickups=PICKUP_LOCATIONS)

# Now we can start defining our resource classes. We define six classes:
# Request, RequestAsJSON, RequestList, RequestListAsJSON, ETA, ETAasJSON.
# All of them accept GET requests. Request also accepts PATCH requests,
# and RequestList also accepts POST requests.

# Define the request resource
class Request(Resource):

    # If a request with id does not exist,
    # respond with a 404, otherwise respond with an HTML representation
    def get(self, request_id):
        generate_etas(request_data['requests'][request_id])
        return make_response(render_request_as_html(request_data['requests'][request_id]),200)

    def patch(self,request_id):
        request = request_data['requests'][request_id]
        update = update_request_parser.parse_args()
        request['pickup'] = update['pickup']
        if len(update['notes'].strip()) > 0:
            request.setdefault('notes',[]).append(update['notes'])
        return make_response(render_request_as_html(request),200)

#define the requestasjson resource
class RequestAsJSON(Resource):

    def get(self, request_id):
        request = request_data['requests'][request_id]
        request['@context'] = request_data['@context']
        return request

#Define the eta resource
class ETA(Resource):

    def get(self,request_id):
        other_etas = generate_etas(request_data['requests'][request_id])
        return make_response(render_eta_list_as_html(request_data['requests'][request_id],other_etas),200)

#Define the eta resource as JSON
class ETAasJSON(Resource):

    def get(self,request_id):
        other_etas = generate_etas(request_data['requests'][request_id])
        request_data['@context'] = request_data['@context']
        return other_etas

# defines our request list resource
class RequestList(Resource):
    #responds with an HTML representation of the requests
    def get(self):
        query = query_parser.parse_args()
        return make_response(render_request_list_as_html(filter_request(**query)),
                                 '200')

    def post(self):
        request = new_request_parser.parse_args()
        request_id = str(generate_maxid(request_data['requests']) + 1)
        request['@id'] = 'request/' + request_id
        request['time'] = f"{datetime.datetime.now():%m-%d-%Y %H:%M}"
        request['status'] = 'Awaiting Circulation Processing'
        request['id'] = request_id
        request_data['requests'][request_id] = request
        return make_response(render_request_list_as_html(filter_request()),201)

class RequestListasJson(Resource):
    def get(self):
        return request_data

# After defining our resource classes, we define how URLs are assigned to
# resources by mapping resource classes to URL patterns.
app = Flask(__name__)
api = Api(app)
api.add_resource(RequestList,'/requests')
api.add_resource(RequestListasJson,'/requests.json')
api.add_resource(Request,'/request/<string:request_id>')
api.add_resource(RequestAsJSON,'/request/<string:request_id>.json')
api.add_resource(ETA,'/request/eta/<string:request_id>')
api.add_resource(ETAasJSON,'/request/eta/<string:request_id>.json')


# There is no resource mapped to the root path (/), so if a request comes in
# for that, redirect to the RequestList resource.
@app.route('/')
def index():
    return redirect(api.url_for(RequestList), code=303)


# Finally we add some headers to all of our HTTP responses which will allow
# JavaScript loaded from other domains and running in the browser to load
# representations of our resources (for security reasons, this is disabled
# by default.

@app.after_request
def after_request(response):
    response.headers.add(
        'Access-Control-Allow-Origin', '*')
    response.headers.add(
        'Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add(
        'Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response


# Now we can start the server.

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5555,
        debug=True,
        use_debugger=False,
        use_reloader=False)
