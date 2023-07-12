import os
import ast
# from urllib import request
from apiflask.validators import Length,Range
from apiflask import APIFlask, Schema, PaginationSchema,abort
from apiflask.fields import Integer, String, Boolean, Date, List, Nested
from flask_sqlalchemy import SQLAlchemy
from flask import request

from dotenv import load_dotenv

# set openapi.info.title and openapi.info.version
app = APIFlask(__name__,
               title='LLM Extension', 
               version='1.0',
               spec_path='/openapi.json', 
               docs_path='/docs')

# load .env if present
load_dotenv()

# # the secret API key, plus we need a username in that record
# API_TOKEN="{{'{0}':'appuser'}}".format(os.getenv('API_TOKEN'))
# #convert to dict:
# tokens=ast.literal_eval(API_TOKEN)

# database URI
DB2_URI=os.getenv('DB2_URI')
# optional table arguments, e.g., to set another table schema
ENV_TABLE_ARGS=os.getenv('TABLE_ARGS')
TABLE_ARGS=None
if ENV_TABLE_ARGS:
    TABLE_ARGS=ast.literal_eval(ENV_TABLE_ARGS)


app.config['SERVERS'] = [
    {
        'description': 'Code Engine deployment',
        'url': 'https://{appname}.{projectid}.{region}.codeengine.appdomain.cloud',
        'variables':
        {
            "appname":
            {
                "default": "myapp",
                "description": "application name"
            },
            "projectid":
            {
                "default": "projectid",
                "description": "the Code Engine project ID"
            },
            "region":
            {
                "default": "us-south",
                "description": "the deployment region, e.g., us-south"
            }
        }
    },
    {
        'description': 'local test',
        'url': 'http://127.0.0.1:{port}',
        'variables':
        {
            'port':
            {
                'default': "5000",
                'description': 'local port to use'
            }
        }
    }
]

# configure SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI']=DB2_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Initialize SQLAlchemy for our database
db = SQLAlchemy(app)

# sample records to be inserted after table recreation
sample_events=[
    {
        "first_name":"Drue",
        "last_name": "Vanhorn",
        "phone":"5558675309",
        "security_word":"arrow",
        "card_status": "APPROVED",
        "pin": "5657",
        "withdrawal_limit": "500"
    },
    {
        "first_name":"Dylan",
        "last_name": "Zucker",
        "phone":"5551234567",
        "security_word":"hammer",
        "card_status": "IN PROCESS",
        "pin": "9999",
        "withdrawal_limit": "600"
    },

]


# Schema for table "EVENTS"
# Set default schema to "EVENTS"
class EventModel(db.Model):
    __tablename__ = 'EVENTS'
    __table_args__ = TABLE_ARGS
    qid = db.Column('QID',db.Integer, primary_key=True)
    llmQuery = db.Column('LLMQUERY',db.String(2000))
    response = db.Column('RESPONSE',db.String(2000))


# the Python output for Events
class EventOutSchema(Schema):
    qid = Integer()
    llmQuery = String()
    response = String()


# the Python input for Events
class EventInSchema(Schema):
    llmQuery = String(required=True, validate=Length(0, 2000))
    response = String(required=True, validate=Length(0, 2000))

# use with pagination
class EventQuerySchema(Schema):
    page = Integer(load_default=1)
    per_page = Integer(load_default=20, validate=Range(max=30))

class EventsOutSchema(Schema):
    events = List(Nested(EventOutSchema))
    pagination = Nested(PaginationSchema)


# (re-)create the event table with sample records
@app.post('/database/recreate')
@app.input({'confirmation': Boolean(load_default=False)}, location='query')
#@app.output({}, 201)
def create_database(query):
    """Recreate the database schema
    Recreate the database schema and insert sample data.
    Request must be confirmed by passing query parameter.
    """
    if query['confirmation'] is True:
        db.drop_all()
        db.create_all()
        for e in sample_events:
            event = EventModel(**e)
            db.session.add(event)
        db.session.commit()
    else:
        abort(400, message='confirmation is missing',
            detail={"error":"check the API for how to confirm"})
        return {"message": "error: confirmation is missing"}
    return {"message":"database recreated"}


@app.input(EventQuerySchema, 'query')
@app.output(EventsOutSchema)
@app.get('/query')
def ai_response(query):
    """It will return o/p after each 30 sec if it is not fully processed.
    ```
    """
    
    return query

# default "homepage", also needed for health check by Code Engine
@app.get('/')
def print_default():
    """ Greeting
    health check
    """
    # returning a dict equals to use jsonify()
    return {'message': 'This is the Watson LLM Custom-Extension API server'}

# @app.spec_processor
@app.post('/query')
@app.input(EventInSchema, location='json')
@app.output(EventOutSchema, 201)
def input_query(data):
    """Insert a new event record
    Insert a new event record with the given attributes. Its new EID is returned.
    """
    event = EventModel(**data)
    # db.session.add(event)
    # db.session.commit()
    return event



@app.post("/upload-file")
def upload_file():
    file = request.files["file"]
    if file:
        file_path = f"uploads/{file.filename}"
        file.save(file_path)
        return {"filename": file.filename, "path": file_path}
    else:
        return {"message": "No file provided."}, 400




# Start the actual app
# Get the PORT from environment or use the default
port = os.getenv('PORT', '5000')
if __name__ == "__main__":
    app.run(host='0.0.0.0',port=int(port))