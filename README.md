This is an example of a simple web API implemented using
[Flask](http://flask.pocoo.org/) and
[Flask-RESTful](http://flask-restful.readthedocs.org/en/latest/).

**To run it:**
1. Install required dependencies:
   ```
   $ pip install -r requirements.txt
   ``` 

2. Run the helpdesk server:
   ```
   $ python server.py
   ```
   
__**class/rel Documentation:**__

*attribute values describing application flow*

- collection: Describes a collection of requests.

- request: May appear within collection. Describes an individual request.

- username: May appear within request. Identifier of patron submitting request.

- id: May appear within request. A request’s unique ID

- title: May appear within request. Requested item’s title.

- oclc: May appear within request. Requested item’s OCLC number.

- date: May appear within request. Date when request was submitted.

- item-home: May appear within request. Location of item requested.

- pickup: May appear within request. Indicates pickup location for requested item.

- status: May appear within request. Indicates the current stage of the request’s processing.

- callnumber: May appear within request. Item’s call number.

- eta: May appear within request. Indicates the estimated time of arrival for a request. The time at which the item will be available for pickup at the requested pickup location.

- create-update: Class of forms used to create and update requests.

- create: May appear within create-update. Appears when the form submitted creates a new request.

- update: May appear within create-update. Appears when the form submitted updates a request.

- search: Indicates a templated query form that filters requests based on text submitted in search form.

*rel values:*

- collection: Points to the collection of requests.

- item: Links to an individual request.

- service-locations: Links to a collection of locations with information that may be useful for updating a request.
   
