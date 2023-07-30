import os
# from urllib import request
from flask_cors import CORS,cross_origin
from apiflask import APIFlask, Schema, PaginationSchema
from apiflask.validators import Length, Range
from apiflask.fields import Integer, String, List, Nested, File
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from qna import llm

# from v2 import process_load_document,fetch_responses_with_quest_id,process_request_thread
# set openapi.info.title and openapi.info.version
app = APIFlask(__name__,
               title='LLM Extension',
               version='1.0',
               spec_path='/openapi.json',
               docs_path='/docs')

# load .env if present
load_dotenv()
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

hostip = os.getenv("HOSTIP")
devport =  os.getenv("DEVPORT")
app.config['SERVERS'] = [
    {
        'description': 'LLM extension on IKS deployment',
        'url': 'https://{hostip}:{devport}',
        'variables':
            {
                "hostip":
                    {
                        "default": hostip,
                        "description": "host ip"
                    },
                "devport":
                    {
                        "default": devport,
                        "description": "host port"
                    }
            }
    },
    {
        'description': 'local test',
        'url': 'http://{host}:{port}',
        'variables':
            {
                 'host':
                    {
                        'default': "127.0.0.1",
                        'description': 'local host to use'
                    },
                'port':
                    {
                        'default': "5000",
                        'description': 'local port to use'
                    }
                    
            }
    }
]

# sample records to be inserted after table recreation
sample_events = [
    {
        "llmQuery": "Whati is kubernetes",
        "response": "kubernetes"
    },
    {
        "llmQuery": "what is pod",
        "response": "pod is smallest unit of kubernetes"
    },

]


# the Python output for Events
class EventOutSchema(Schema):
    qid = Integer()
    response = String()


# the Python input for Events
class EventInSchema(Schema):
    llmQuery = String(required=True, validate=Length(0, 2000))


# use with pagination
class EventQuerySchema(Schema):
    qid = Integer(load_default=1)
    page = Integer(load_default=1)
    per_page = Integer(load_default=20, validate=Range(max=30))


class EventsOutSchema(Schema):
    events = List(Nested(EventOutSchema))
    pagination = Nested(PaginationSchema)


class QueryOutSchema(Schema):
    code = String(required=True, validate=Length(0, 10))
    response = String(required=True, validate=Length(0, 2000))


# @app.input(EventQuerySchema,'query')
@app.output(QueryOutSchema)
@app.get('/query/qid/<int:qid>')
@cross_origin()
def ai_response(qid):
    """It will return o/p after each 30 sec if it is not fully processed.
    ```
    """
    print("it is ai reponse return after each call")
    res = llm.fetch_responses_with_quest_id(qid)
    if res is None:
        return {
            'code': '202',
            'response': 'Thank you for your patience,Fetching the response...',
        }
    return {
        'code': '200',
        'response': res,
    }


# default "homepage", also needed for health check by Code Engine
@app.get('/')
@cross_origin()
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
@cross_origin()
def input_query(data):
    """Insert a new event record
    Insert a new event record with the given attributes. Its new EID is returned.
    """
    print("Datat", data)
    llmquery = data.get("llmQuery")
    print("Query is:", llmquery)
    answer = llm.make_qna_chain(llmquery)
    print(answer)
    return {
        'output': answer,
    }


class FileUpload(Schema):
    file = File()


@app.post("/upload-file")
@app.input(FileUpload, location='files')
@cross_origin()
def upload_file(data):
    f = data['file']
    filename = secure_filename(f.filename)
    # file_path=f.save(os.path.join("/uploads", filename))
    file_path = f.save(filename)
    print(file_path)
    llm.process_load_document(os.path.abspath(filename))
    return {'message': f'file {filename} saved.'}


# Start the actual app
# Get the PORT from environment or use the default
port = os.getenv('PORT', '5000')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(port))