import unittest
import os
import json
import jwt
from main import Project, app, db


class ProjectTest(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + \
        os.path.join('.', 'test.db')
        self.app = app.test_client()
        
        db.create_all()
        db.session.add(
                Project(id=1, 
                        name='Project1', 
                        user_id=1,
                        m2_gen_id=1, 
                        location_id=1))
        db.session.add(
                Project(id=2, 
                        name='Project2', 
                        user_id=1,
                        m2_gen_id=2, 
                        location_id=2))
        db.session.add(
                Project(id=3,
                        name='Project3',
                        user_id=1,
                        m2_gen_id=3,
                        location_id=3))
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_create_project(self):
        with app.test_client() as client:
            client.environ_base['HTTP_AUTHORIZATION'] = jwt.encode({'some': 'payload'}, app.config['SECRET_KEY'], algorithm='HS256')
            sent = {'name' : 'ProjectTest', 'm2_gen_id': 4, 'user_id': 2, 'location_id': 4}
            rv = client.post('/api/projects', data = json.dumps(sent), content_type='application/json')

            self.assertEqual(rv.status_code, 201)

    def test_get_project_by_id(self):
        with app.test_client() as client:
            client.environ_base['HTTP_AUTHORIZATION'] = jwt.encode({'some': 'payload'}, app.config['SECRET_KEY'], algorithm='HS256')
            rv = client.get('/api/projects/1')
            assert b'{"id":1,"location_id":1,"m2_gen_id":1,"name":"Project1","user_id":1}\n' in rv.data
   
    def test_update_project(self):
        with app.test_client() as client:
            client.environ_base['HTTP_AUTHORIZATION'] = jwt.encode({'some': 'payload'}, app.config['SECRET_KEY'], algorithm='HS256')
            rv = client.get('/api/projects/1')
            project = json.loads(rv.get_data(as_text=True))
            project['name'] = "UpdateName"

            rvu = client.put('/api/projects/1', data = json.dumps(project), content_type='application/json')

            updated_project = json.loads(rvu.get_data(as_text=True))
            if rvu.status_code == 200:
                self.assertEqual("UpdateName", updated_project['name'])
            
            self.assertEqual(rvu.status_code, 200)

    def test_delete_project(self):
        with app.test_client() as client:
            client.environ_base['HTTP_AUTHORIZATION'] = jwt.encode({'some': 'payload'}, app.config['SECRET_KEY'], algorithm='HS256')
            rv = client.delete('/api/projects/2')
            self.assertEqual(rv.status_code, 200)
    
    def test_get_projects_by_user(self):
        with app.test_client() as client:
            client.environ_base['HTTP_AUTHORIZATION'] = jwt.encode({'some': 'payload'}, app.config['SECRET_KEY'], algorithm='HS256')
            rv = client.get('/api/user/1/projects')
            datas = json.loads(rv.data)
            assert len(datas) == 3
    
if __name__ == '__main__':
    unittest.main()