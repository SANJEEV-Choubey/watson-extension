from apiflask import APIFlask
from apiflask.fields import Integer, String
from apiflask.validators import Length, OneOf
from apiflask import APIFlask, Schema, HTTPTokenAuth, PaginationSchema, pagination_builder, abort
from apiflask.fields import Integer, String, Boolean, Date, List, Nested
import os
from apiflask.validators import Length, Range

# set openapi.info.title and openapi.info.version
app = APIFlask(__name__,
               title='LLM Extension', 
               version='1.0',
               spec_path='/openapi.json', 
               docs_path='/docs', 
            #    docs_oauth2_redirect_path='/docs/oauth2-redirect', 
               redoc_path='/redoc')
app.config['SPEC_FORMAT'] = 'json'


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


# the Python output for Events
class QueryOutSchema(Schema):
    eid = Integer()
    shortname = String()
    location = String()
    begindate = Date()
    enddate = Date()
    contact = String()

# the Python input for Events
class QueryInSchema(Schema):
    shortname = String(required=True, validate=Length(0, 20))
    location = String(required=True, validate=Length(0, 60))
    begindate = Date(required=True)
    enddate = Date(required=True)
    contact = String(required=True, validate=Length(0, 255))

# use with pagination
class QuerySchema(Schema):
    page = Integer(load_default=1)
    per_page = Integer(load_default=20, validate=Range(max=30))

class QueryOutPutSchema(Schema):
    events = List(Nested(QueryOutSchema))
    pagination = Nested(PaginationSchema)



response='Returning values for provided query'
@app.output(QueryOutSchema)
@app.get('/query')
def say_hello():
    """It will return o/p after each 30 sec if it is not fully processed.
    ```
    """
    
    return QueryOutSchema



# @app.spec_processor
@app.post('/query')
@app.input({'confirmation': String(load_default="")}, location='query')
def input_query(query):
    
    """
     User query will be processed 
    """
    # pagination = EventModel.query.paginate(
    # page=query['page'],
    # per_page=query['per_page']
    # )
    # return {
    #     'events': pagination.items,
    #     'pagination': pagination_builder(pagination)
    # }

    return {'message': 'Thank you for your query, watson custom extension will provodie you response.'}


@app.input({'confirmation': String(load_default="")}, location='path')
@app.post('/write')
def write_doc(path):
    '''
    Get the doc path , download and save it and then call om's function with downloaded path, and then clear the volume.
    '''
    return {'message': 'Document written successfully'}




# Start the actual app
# Get the PORT from environment or use the default
port = os.getenv('PORT', '5000')
if __name__ == "__main__":
    app.run(host='0.0.0.0',port=int(port))