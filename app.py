from apiflask import APIFlask
from apiflask.fields import Integer, String
from apiflask.validators import Length, OneOf
from apiflask import APIFlask, Schema, HTTPTokenAuth, PaginationSchema, pagination_builder, abort
import os
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

# @app.spec_processor
@app.get('/query')
# @app.doc(tags=['Hello'])
def say_hello():
    """It will return o/p after each 30 sec if it is not fully processed.
    ```
    """
    return {'message': 'Thank you for qurying, you will be reciving output after each 30sec till all response doesnot get over.'}



# @app.spec_processor
@app.post('/query')
# @app.doc(tags=['Hello'])
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