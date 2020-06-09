"""
This module run a microservice called Project service. This module
manage all logic for wys projects

"""

from flask import Flask, jsonify, abort, request
from flask_sqlalchemy import SQLAlchemy
from flask_swagger import swagger
from flask_swagger_ui import get_swaggerui_blueprint

import os

# Loading Config Parameters
DB_USER = os.getenv('DB_USER', 'wys')
DB_PASS = os.getenv('DB_PASSWORD', 'rac3e/07')
DB_IP = os.getenv('DB_IP_ADDRESS', '10.2.19.195')
DB_PORT = os.getenv('DB_PORT', '3307')
DB_SCHEMA = os.getenv('DB_SCHEMA', 'wys')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql://{DB_USER}:{DB_PASS}@{DB_IP}:{DB_PORT}/{DB_SCHEMA}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


if __name__ == '__main__':
    app.run()
    app.debug=True


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
    name = db.Column(db.String(120))
    user_id = db.Column(db.String(120))
    m2_gen_id = db.Column(db.Integer)
    location_id = db.Column(db.Integer)
    # TODO
    # location_id
    # layout_id
    # time_est_id
    # cost_est_id

    def serialize(self):
        """
        Serialize to json
        """
        dict = {
            'id': self.id,
            'name': self.name,
            'm2_gen_id': self.m2_gen_id,
            'user_id': self.user_id,
            'location_id': self.location_id
        }
        return jsonify(dict)

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

db.create_all()

# Swagger Config

SWAGGER_URL = '/api/docs/'
API_URL = '/api/spec'
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={  # Swagger UI config overrides
        'app_name': "WYS Api. Project Service"
    }
)

app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)


@app.route("/api/spec", methods=['GET'])
def spec():
    return jsonify(swagger(app))

@app.route('/api/projects', methods=['POST'])
def create_project():
    """
        Create a new project
        ---
        consumes:
        - "application/json"
        - "application/xml"
        produces:
        - "application/xml"
        - "application/json"
        parameters:
        - in: "body"
          name: "body"
          description: "Project object that needs to be added to the store"
          required: true
        responses:
          201:
            description: Project Object
          405:
            description: "Invalid input"
    """

    try:
        if not request.json or (not 'name' and not 'm2_gen_id' and not 'user_id' and not 'location_id') in request.json:
            abort(400)

        project = Project()
        project.name = request.json['name']
        project.m2_gen_id = request.json['m2_gen_id']
        project.user_id = request.json['user_id']
        project.location_id = request.json['location_id']

        db.session.add(project)
        db.session.commit()
        
        return project.serialize(), 201

    except Exception as exp:
        app.logger.error(f"Error in database: mesg ->{exp}")
        return exp, 500

@app.route('/api/projects/<project_id>', methods = ['GET', 'PUT', 'DELETE'])
def get_project_by_id(project_id):
    """
        Get Project By ID
        ---
        parameters:
          - in: path
            name: project_id
            type: integer
            description: Project ID
        responses:
          200:
            description: Project Object
          404:
            description: Project Not Found 
    """
    try:
        project = Project.query.filter_by(id=project_id).first()
        app.logger.warning(project)
        if(project is not None):
            if request.method == 'GET':
                return project.serialize(), 200
            if request.method == 'PUT':
                project.name = request.json['name']
                project.m2_gen_id = request.json['m2_gen_id']
                project.user_id = request.json['user_id']
                project.location_id = request.json['location_id']

                db.session.commit()

                project_updated = Project.query.filter_by(id=project_id).first()
                
                return project_updated.serialize(), 200
                
            if request.method == 'DELETE':
                db.session.delete(project)
                db.session.commit()

                return jsonify({'result': 'Project deleted'}), 200

        return '{}', 204

    except Exception as exp:
        app.logger.error(f"Error in database: mesg ->{exp}")
        return exp, 500


@app.route("/api/user/<user_id>/projects")
def get_projects_by_user(user_id):
    """
        Get Projects By User ID
        ---
        parameters:
          - in: path
            name: user_id
            type: integer
            description: User ID
        responses:
          200:
            description: Projects of the user
          404:
            description: User not found
    """
    try:
        projects = Project.query.filter_by(user_id=user_id)

        if(projects.count() > 0):
            dicts = [project.to_dict() for project in projects]
            return jsonify(dicts)

        return '{}', 204

    except Exception as exp:
        app.logger.error(f"Error in database: mesg ->{exp}")
        return exp, 500
