"""
This module run a microservice called Project service. This module
manage all logic for wys projects

"""

import jwt
import os
import requests
import logging
import json
from sqlalchemy.exc import SQLAlchemyError
from flask import Flask, jsonify, abort, request
from flask_sqlalchemy import SQLAlchemy
from flask_swagger import swagger
from flask_swagger_ui import get_swaggerui_blueprint
from flask_cors import CORS
from functools import wraps

# Loading Config Parameters
DB_USER = os.getenv('DB_USER', 'wys')
DB_PASS = os.getenv('DB_PASSWORD', 'rac3e/07')
DB_IP = os.getenv('DB_IP_ADDRESS', '10.2.19.195')
DB_PORT = os.getenv('DB_PORT', '3307')
DB_SCHEMA = os.getenv('DB_SCHEMA', 'wys')

BUILDINGS_MODULE_HOST = os.getenv('BUILDINGS_MODULE_HOST', '127.0.0.1')
BUILDINGS_MODULE_PORT = os.getenv('BUILDINGS_MODULE_PORT', 5004)
BUILDINGS_MODULE_API = os.getenv('BUILDINGS_MODULE_API', '/api/buildings/')
BUILDINGS_MODULE_API_LOCS_GET = os.getenv('BUILDINGS_MODULE_API_LOCS_GET', '/api/buildings/locations/')
BUILDINGS_URL = f"http://{BUILDINGS_MODULE_HOST}:{BUILDINGS_MODULE_PORT}"

M2_MODULE_HOST = os.getenv('M2_MODULE_HOST', '127.0.0.1')
M2_MODULE_PORT = os.getenv('M2_MODULE_PORT', 5001)
M2_MODULE_API = os.getenv('M2_MODULE_API', '/api/m2/')

PRICES_MODULE_HOST = os.getenv('PRICES_MODULE_HOST', '127.0.0.1')
PRICES_MODULE_PORT = os.getenv('PRICES_MODULE_PORT', 5008)
PRICES_MODULE_API = os.getenv('PRICES_MODULE_API', '/api/prices/')

TIMES_MODULE_HOST = os.getenv('TIMES_MODULE_HOST', '127.0.0.1')
TIMES_MODULE_PORT = os.getenv('TIMES_MODULE_PORT', 5007)
TIMES_MODULE_API = os.getenv('TIMES_MODULE_API', '/api/times/')

LAYOUT_MODULE_HOST = os.getenv('LAYOUT_MODULE_HOST', '127.0.0.1')
LAYOUT_MODULE_PORT = os.getenv('LAYOUT_MODULE_PORT', 5006)
LAYOUT_MODULE_API = os.getenv('LAYOUT_MODULE_API', '/api/layouts/')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql://{DB_USER}:{DB_PASS}@{DB_IP}:{DB_PORT}/{DB_SCHEMA}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.logger.setLevel(logging.DEBUG)
CORS(app)

try:
    f = open('oauth-public.key', 'r')
    key: str = f.read()
    f.close()
    app.config['SECRET_KEY'] = key
except Exception as e:
    app.logger.error(f'Can\'t read public key f{e}')
    exit(-1)

db = SQLAlchemy(app)

class Project(db.Model):
    """
    Project.
    Represent a WYS Project structure for save in db.

    Attributes
    ----------
    id: Represent the unique id of a project
    name: Name of the project
    m2_id: Id of the work made in M2 module
    location_gen_id: ID of the work made in location module
    layout_gen_id: ID of the layout used
    time_gen_id: ID of the time project information
    price_gen_id: ID of the price generated by a project

    """

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    m2_gen_id = db.Column(db.Integer)
    location_gen_id = db.Column(db.Integer)
    layout_gen_id = db.Column(db.Integer)
    time_gen_id = db.Column(db.Integer,nullable=True)
    price_gen_id = db.Column(db.Integer,nullable=True)

    # TODO
    # location_id
    # layout_id
    # time_gen_id
    # price_gen_id

    def to_dict(self):
        """
        Convert to dictionary
        """
        dict = {
            'id': self.id,
            'name': self.name,
            'm2_gen_id': self.m2_gen_id,
            'user_id': self.user_id,
            'location_gen_id': self.location_gen_id,
            'layout_gen_id': self.layout_gen_id,
            'time_gen_id': self.time_gen_id,
            'price_gen_id': self.price_gen_id 
        }
        return dict

    def serialize(self):
        """
        Serialize to json
        """
        return jsonify(self.to_dict())

db.create_all()

# Swagger Config

SWAGGER_URL = '/api/projects/docs/'
API_URL = '/api/projects/spec'
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={  # Swagger UI config overrides
        'app_name': "WYS Api. Project Service"
    }
)

app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)


def get_location_by_id(location_gen_id, token):
    headers = {'Authorization': token}
    api_url = BUILDINGS_URL + BUILDINGS_MODULE_API_LOCS_GET + str(location_gen_id)
    rv = requests.get(api_url, headers=headers)
    if rv.status_code == 200:
      return json.loads(rv.text)
    elif rv.status_code == 500:
      raise Exception("Cannot connect to the buildings module")
    return None

def token_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):

        bearer_token = request.headers.get('Authorization', None)
        try:
            token = bearer_token.split(" ")[1]
        except Exception as ierr:
            app.logger.error(ierr)
            abort(jsonify({'message': 'a valid bearer token is missing'}), 500)
        
        if not token:
            app.logger.debug("token_required")
            return jsonify({'message': 'a valid token is missing'})

        app.logger.debug("Token: " + token)
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'],
                              algorithms=['RS256'], audience="1")
            user_id: int = data['user_id']
            request.environ['user_id'] = user_id
        except Exception as err:
            return jsonify({'message': 'token is invalid', 'error': err})
        except KeyError as kerr:
            return jsonify({'message': 'Can\'t find user_id in token', 'error': kerr})

        return f(*args, **kwargs)

    return decorator


@app.route("/api/projects/spec", methods=['GET'])
@token_required
def spec():
    swag = swagger(app)
    swag['info']['version'] = "1.0"
    swag['info']['title'] = "WYS Projects API Service"
    swag['tags'] = [{
        "name": "projects",
        "description": "Methods to configure projects"
    },{
        "name": "projects/location",
        "description": "Methods to configure project location"
    }]
    return jsonify(swag)


@app.route('/api/projects', methods=['POST'])
@token_required
def create_project():
    """
        Create a new project
        ---
        consumes:
        - "application/json"
        tags:
        - "projects"
        produces:
        - "application/xml"
        - "application/json"
        parameters:
        - in: "body"
          name: "body"
          required:
          - name
          - m2_gen_id
          - location_gen_id
          - times_gen_id
          - price_gen_id
          properties:
            name:
              type: string
              description: Project name
            m2_gen_id:
              type: integer
              description: Saved data ID for the current user generated by M2 module
            location_gen_id:
              type: integer
              description: Saved data ID for the current user generated by location module
            layout_gen_id:
              type: integer
              description: Saved data ID for the current user generated by layout module
            time_gen_id:
              type: integer
              description: Saved data ID for the current user generated by time module
            price_gen_id:
              type: integer
              description: Saved data ID for the current user generated by layout price
          description: "Project object that needs to be added to the store"

        responses:
          201:
            description: Project Object
          400:
            description: "Empty field"
          500:
            description: "Database error"
    """

    try:
      #if not request.json or request.json.keys() != {'name','m2_gen_id','location_gen_id', 'layout_gen_id','time_gen_id','price_gen_id'}:
        if 'name' not in request.json:
            abort(400)

        request.json['user_id'] = request.environ['user_id']
        projects = Project.query.filter_by(user_id=request.json['user_id'], name=request.json['name'])
        if projects.count() > 0:
            return "This Project already exists.", 409

        project = Project()
        project.name = request.json['name']
        project.user_id = request.json['user_id']
        project.m2_gen_id = request.json['m2_gen_id'] if 'm2_gen_id' in request.json else None
        project.location_gen_id = request.json['location_gen_id'] if 'location_gen_id' in request.json else None
        project.layout_gen_id = request.json['layout_gen_id'] if 'layout_gen_id' in request.json else None
        project.time_gen_id = request.json['time_gen_id'] if 'time_gen_id' in request.json else None

        db.session.add(project)
        db.session.commit()

        return project.serialize(), 201

    except Exception as exp:
        app.logger.error(f"Error in database: mesg ->{exp}")
        abort(jsonify({'message': exp}), 500)


@app.route('/api/projects/all', methods=['GET'])
@token_required
def get_projects():
    """
        Get all projects
        ---
        consumes:
        - "application/json"
        tags:
        - "projects"
        produces:
        - "application/xml"
        - "application/json"
       
        responses:
          200:
            description: "Success"
          400:
            description: "User without id"
          500:
            description: "Database error"
    """

    try:
        print(':C')
        token = request.headers.get('Authorization', None)
        print(token)
        user_id = 23 #request.environ['user_id']
        if user_id is None:
            abort(400)
        print(f"http://{PRICES_MODULE_HOST}:{PRICES_MODULE_PORT}" + PRICES_MODULE_API + 'data/' + str(1))
        print(user_id)
        projects = Project.query.all()
        print(projects)
        p=[]
        for project in projects:
          print('hello')
          proj_dict=project.to_dict()
          if project.layout_gen_id is not None:
            data = get_layout_gen(project.id,token)
            proj_dict['floor_id']=None
            if data is not None:
              if 'floor_id' in data:
                proj_dict['floor_id']=data['floor_id']
            p.append(proj_dict)
 
        if projects is not None:
            if request.method == 'GET':
                 return jsonify(p),200

        return '{}', 404

    except Exception as exp:
        app.logger.error(f"Error in database: mesg ->{exp}")
        return exp, 500



@app.route('/api/projects/<project_id>', methods=['GET'])
@token_required
def manage_project_by_id(project_id):
    """
        Get Project By ID
        ---
          consumes:
            - "application/json"

          tags:
            - "projects"
          parameters:
            - in: path
              name: project_id
              type: integer
              description: Project ID
          responses:
            200:
              description: Project Object or deleted message
            404:
              description: Project Not Found
            500:
              description: "Database error"
    """
    try:
        project = Project.query.filter_by(id=project_id).first()
        if project is not None:
            if request.method == 'GET':
                return project.serialize(), 200

        return '{}', 404

    except Exception as exp:
        app.logger.error(f"Error in database: mesg ->{exp}")
        return exp, 500


@app.route('/api/projects/<project_id>', methods=['PUT'])
@token_required
def update_project_by_id(project_id):
    """
        Update Project By ID
        ---
          consumes:
            - "application/json"
          tags:
            - "projects"
          parameters:
            - in: path
              name: project_id
              type: integer
              description: Project ID
            - in: "body"
              name: "body"
              required:
                - name
                - m2_gen_id
                - location_gen_id
                - layout_gen_id
                - time_gen_id
                - price_gen_id
              properties:
                name:
                  type: string
                  description: Project name
                m2_gen_id:
                  type: integer
                  description: Saved data ID for the current user generated by M2 module
                location_gen_id:
                  type: integer
                  description: Saved data ID for the current user generated by location module
                layout_gen_id:
                  type: integer
                  description: Saved data ID for the current user generated by layout module
                time_gen_id:
                  type: integer
                  description: Saved data ID for the current user generated by time module
                price_gen_id:
                  type: integer
                  description: Saved data ID for the current user generated by layout price
          responses:
            200:
              description: Project Object or deleted message
            500:
              description: "Database error"
    """

    try:
        project = Project.query.filter_by(id=project_id).first()
        if project is None:
            return '{}', 404
        project.name = request.json['name'] if 'name' in request.json else project.name
        project.m2_gen_id = request.json['m2_gen_id'] if 'm2_gen_id' in request.json else project.m2_gen_id
        project.location_gen_id = request.json['location_gen_id'] if 'location_gen_id' in request.json else project.location_gen_id
        project.layout_gen_id = request.json['layout_gen_id'] if 'layout_gen_id' in request.json else project.layout_gen_id
        project.time_gen_id = request.json['time_gen_id'] if 'time_gen_id' in request.json else project.time_gen_id
        project.price_gen_id = request.json['price_gen_id'] if 'price_gen_id' in request.json else project.price_gen_id

        db.session.commit()

        project_updated = Project.query.filter_by(id=project_id).first()

        return project_updated.serialize(), 200
    except Exception as exp:
        app.logger.error(f"Error in database: mesg ->{exp}")
        return exp, 500

@app.route('/api/projects/pais/<nombre_p>', methods=['GET'])
@token_required
def get_pais(nombre_p):
    """
        Get Project By ID
        ---
          consumes:
            - "application/json"

          tags:
            - "projects"
          parameters:
            - in: path
              name: nombre_p
              type: string
              description: Project ID
          responses:
            200:
              description: Fue encontrado
            404:
              description: Pais no existe
    """
    if nombre_p == '':
        return '{}', 404
    else:
        '''codigo para conectarse a otra api que devuelva el dinero'''
        return nombre_p,200

   

@app.route('/api/projects/<project_id>', methods=['DELETE'])
@token_required
def delete_project_by_id(project_id):
    """
        Delete Project By ID
        ---
          consumes:
            - "application/json"

          tags:
            - "projects"
          parameters:
            - in: path
              name: project_id
              type: integer
              description: Project ID
          responses:
            200:
              description: Project Object or deleted message
            404:
              description: Project Not Found
            500:
              description: "Database error"
    """
    try:
        project = Project.query.filter_by(id=project_id).first()
        if project is None:
            return '{}', 404
        db.session.delete(project)
        db.session.commit()

        return jsonify({'result': 'Project deleted'}), 200
    except Exception as excp:
        app.logger.error(f"Error in database: mesg ->{excp}")
        return excp, 500

def get_m2(m2_gen_id, token):
    headers = {'Authorization': token}
    api_url = f"http://{M2_MODULE_HOST}:{M2_MODULE_PORT}" + M2_MODULE_API + 'data/' + str(m2_gen_id)
    rv = requests.get(api_url, headers=headers)
    if rv.status_code == 200:
        return json.loads(rv.text)
    elif rv.status_code == 500:
      raise Exception("Cannot connect to the prices module")
    return None

def get_price(price_gen_id, token):
    headers = {'Authorization': token}
    api_url = f"http://{PRICES_MODULE_HOST}:{PRICES_MODULE_PORT}" + PRICES_MODULE_API + 'data/' + str(price_gen_id)
    print('api-url: ',api_url)
    rv = requests.get(api_url, headers=headers)
    if rv.status_code == 200:
        return json.loads(rv.text)
    elif rv.status_code == 500:
      raise Exception("Cannot connect to the prices module")
    return None

def get_location(location_gen_id, token):
    headers = {'Authorization': token}
    api_url = f"http://{BUILDINGS_MODULE_HOST}:{BUILDINGS_MODULE_PORT}" + BUILDINGS_MODULE_API + 'data/' + str(location_gen_id)
    rv = requests.get(api_url, headers=headers)
    if rv.status_code == 200:
        return json.loads(rv.text)
    elif rv.status_code == 500:
      raise Exception("Cannot connect to the buildings module")
    return None

def get_time(time_gen_id, token):
    headers = {'Authorization': token}
    api_url = f"http://{TIMES_MODULE_HOST}:{TIMES_MODULE_PORT}" + TIMES_MODULE_API + 'data/' + str(time_gen_id)
    rv = requests.get(api_url, headers=headers)
    if rv.status_code == 200:
        return json.loads(rv.text)
    elif rv.status_code == 500:
      raise Exception("Cannot connect to the times module")
    return None

def get_layout(layout_gen_id, token):
    headers = {'Authorization': token}
    api_url = f"http://{LAYOUT_MODULE_HOST}:{LAYOUT_MODULE_PORT}" + LAYOUT_MODULE_API + 'data/' + str(layout_gen_id)
    rv = requests.get(api_url, headers=headers)
    print('en prices',rv)
    if rv.status_code == 200:
        return json.loads(rv.text)
    elif rv.status_code == 500:
      raise Exception("Cannot connect to the layout module")
    return None

def get_layout_gen(project_id, token):
    headers = {'Authorization': token}
    api_url = f"http://{LAYOUT_MODULE_HOST}:{LAYOUT_MODULE_PORT}" + LAYOUT_MODULE_API + 'inf/'+ str(project_id)
    print('api-url: ',api_url)
    print('headers',headers)
    try:
      rv = requests.get(api_url, headers=headers)
      print('helllloooooowww')
      print(rv)
      print(rv.text)
      print(rv.status_code)
      if rv.status_code == 200:
          return json.loads(rv.text)
      elif rv.status_code == 500:
        raise Exception("Cannot connect to the layout module")
      return None

    except Exception as e:
      raise Exception(f"Exception: {e}")
    
    
@app.route("/api/projects/details/<project_id>", methods=['GET'])
@token_required
def get_projects_details_by_user(project_id):
    """
        Get Projects Details By User ID and a project id (or not)
        ---
        tags:
            - "projects"
        parameters:
            - in: path
              name: project_id
              required: true
              default: all
              description: Saved project ID
        responses:
          200:
            description: Projects of the user indicated in jwt token
          404:
            description: User not found
          500:
            description: "Database error"
    """
    try:
      token = request.headers.get('Authorization', None)
      user_id = 23#: int = request.environ['user_id']
      print('holita')
      if project_id.isdigit():
        print('soy digito')
        project = Project.query.filter(
                    Project.id == project_id) .filter(
                    Project.user_id == user_id) .first()
        if project is not None:
          p={'id': project.id,'name':project.name,'m2':'','location':'','layout':'','time':'','price':''}
          if project.m2_gen_id is not None:
            data = get_m2(project.m2_gen_id,token)
            p['m2'] = data['m2']
          if project.price_gen_id is not None:
            data = get_price(project.price_gen_id,token)
            p['price'] = data['price']
          if project.location_gen_id is not None:
            data = get_location(project.location_gen_id,token)
            p['location'] = data['location']
          if project.time_gen_id is not None:
            data = get_time(project.time_gen_id,token)
            p['time'] = data['time']
          if project.layout_gen_id is not None:
            print('eooo')
            data = get_layout(project.layout_gen_id,token)
            print(data)
            p['layout'] = data['layout']
          return jsonify(p),200
      else:
        print('soy todo')
        projects = Project.query.filter_by(user_id=user_id)
        projects_list = []
        if projects.count() > 0:
          dicts = [project.to_dict() for project in projects]
          for d in dicts:
            p={'id': d['id'],'name':d['name'],'m2':'','location':'','layout':'','time':'','price':''}
            if d['m2_gen_id'] is not None:
              data = get_m2(d['m2_gen_id'],token)
              p['m2'] = data['m2']
            if d['price_gen_id'] is not None:
              data = get_price(d['price_gen_id'],token)
              p['price'] = data['price']
            if d['location_gen_id'] is not None:
              data = get_location(d['location_gen_id'],token)
              p['location'] = data['location']
            if d['time_gen_id'] is not None:
              data = get_time(d['time_gen_id'],token)
              p['time'] = data['time']
            if d['layout_gen_id'] is not None:
              print('eoo2')
              data = get_layout(d['layout_gen_id'],token)
              p['layout'] = data['layout']
            projects_list.append(p)
          return jsonify(projects_list),200
      
      return jsonify({'status': "Project doesn't exists or doesn't belong to the user."}), 404

    except KeyError as kerr:
      app.logger.error(f"Can't find user_id in token {kerr}")
      abort(jsonify({'message': kerr}), 403)

    except Exception as exp:
      app.logger.error(f"Error in database: mesg ->{exp}")
      abort(jsonify({'message': exp}), 500)


@app.route("/api/projects", methods=['GET'])
@token_required
def get_projects_by_user():
    """
        Get Projects By User ID
        ---
        tags:
            - "projects"
        responses:
          200:
            description: Projects of the user indicated in jwt token
          404:
            description: User not found
          500:
            description: "Database error"
    """
    try:
        user_id: int = request.environ['user_id']
        projects = Project.query.filter_by(user_id=user_id)

        if projects.count() > 0:
            dicts = [project.to_dict() for project in projects]
            return jsonify(dicts)

        return '[]', 404

    except KeyError as kerr:
        app.logger.error(f"Can't find user_id in token {kerr}")
        abort(jsonify({'message': kerr}), 500)

    except Exception as exp:
        app.logger.error(f"Error in database: mesg ->{exp}")
        abort(jsonify({'message': exp}), 500)

@app.route("/api/projects/<project_id>/location", methods=['GET'])
@token_required
def get_location_by_project_id(project_id):
  """
      Get location of Project by ID.
      ---
      parameters:
        - in: path
          name: project_id
          type: integer
          description: Project ID
      tags:
        - "projects/location"
      responses:
        200:
          description: Location Object (building and floor data).
        404:
          description: Project Not Found or the Proyect doesn't have a location associated.
        500:
          description: Internal Server error or Database error
  """
  try:
    token = request.headers.get('Authorization', None)
    project = Project.query.get(project_id)
    if project is not None:
      if project.location_gen_id is not None:
        location = get_location_by_id(project.location_gen_id, token)
        if location is not None:
          return jsonify(location), 200
        return "The location associated with this project was not found", 404
      return "This project does not have a location associated", 404  
    return "This Project doesn't exist", 404
  except SQLAlchemyError as e:
    abort(f'Error getting data: {e}', 500)
  except Exception as exp:
    msg = f"Error: mesg ->{exp}"
    app.logger.error(msg)
    return msg, 500

if __name__ == '__main__':
    app.run(debug = True)