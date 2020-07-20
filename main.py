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
BUILDINGS_MODULE_API_LOCS_GET = os.getenv('BUILDINGS_MODULE_API_LOCS_GET', '/api/buildings/locations/')
BUILDINGS_URL = f"http://{BUILDINGS_MODULE_HOST}:{BUILDINGS_MODULE_PORT}"

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
    location_id: ID of the work made in location module

    """

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    m2_gen_id = db.Column(db.Integer)
    location_id = db.Column(db.Integer)

    # TODO
    # location_id
    # layout_id
    # time_est_id
    # cost_est_id

    def to_dict(self):
        """
        Convert to dictionary
        """
        dict = {
            'id': self.id,
            'name': self.name,
            'm2_gen_id': self.m2_gen_id,
            'user_id': self.user_id,
            'location_id': self.location_id
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


def get_location_by_id(location_id, token):
    headers = {'Authorization': token}
    api_url = BUILDINGS_URL + BUILDINGS_MODULE_API_LOCS_GET + str(location_id)
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
          - location_id
          properties:
            name:
              type: string
              description: Project name
            m2_gen_id:
              type: integer
              description: Saved data ID for the current user generated by M2 module
            location_id:
              type: integer
              description: Saved data ID for the current user generated by location module
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
        if not request.json or request.json.keys() != {'name','m2_gen_id','location_id'}:
            abort(400)
        request.json['user_id'] = request.environ['user_id']
        projects = Project.query.filter_by(user_id=request.json['user_id'], name=request.json['name'])
        if projects.count() > 0:
            return "This Project already exists.", 409

        project = Project()
        project.name = request.json['name']
        project.user_id = request.json['user_id']
        project.m2_gen_id = request.json['m2_gen_id'] if 'm2_gen_id' in request.json else None
        project.location_id = request.json['location_id'] if 'location_id' in request.json else None

        db.session.add(project)
        db.session.commit()

        return project.serialize(), 201

    except Exception as exp:
        app.logger.error(f"Error in database: mesg ->{exp}")
        abort(jsonify({'message': exp}), 500)


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
                - location_id
              properties:
                name:
                  type: string
                  description: Project name
                m2_gen_id:
                  type: integer
                  description: Saved data ID for the current user generated by M2 module
                location_id:
                  type: integer
                  description: Saved data ID for the current user generated by location module
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
        project.name = request.json['name']
        project.m2_gen_id = request.json['m2_gen_id']
        project.location_id = request.json['location_id']

        db.session.commit()

        project_updated = Project.query.filter_by(id=project_id).first()

        return project_updated.serialize(), 200
    except Exception as exp:
        app.logger.error(f"Error in database: mesg ->{exp}")
        return exp, 500


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
      if project.location_id is not None:
        location = get_location_by_id(project.location_id, token)
        if location is not None:
          return jsonify(location), 200
        return "The location associated with this project was not found", 404
      return "This project does not have a location associated", 404  
    return "Project doesn't exist", 404
  except SQLAlchemyError as e:
    abort(f'Error getting data: {e}', 500)
  except Exception as exp:
    msg = f"Error: mesg ->{exp}"
    app.logger.error(msg)
    return msg, 500

if __name__ == '__main__':
    app.run()
    app.debug = True
