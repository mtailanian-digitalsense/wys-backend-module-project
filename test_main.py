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
        f = open('oauth-private.key', 'r')
        self.key = f.read()
        f.close()
        self.app = app.test_client()
        
        db.create_all()
        db.session.add(
                Project(id=1,
                        name='Project1',
                        user_id=1,
                        m2_gen_id=1,
                        location_gen_id=1,
                        layout_gen_id=1))
        db.session.add(
                Project(id=2, 
                        name='Project2', 
                        user_id=1,
                        m2_gen_id=2, 
                        location_gen_id=2,
                        layout_gen_id=2))
        db.session.add(
                Project(id=3,
                        name='Project3',
                        user_id=1,
                        m2_gen_id=3,
                        location_gen_id=3,
                        layout_gen_id=3))
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    @staticmethod
    def build_token(key, user_id=1):
        payload = {
            "aud": "1",
            "jti": "450ca670aff83b220d8fd58d9584365614fceaf210c8db2cf4754864318b5a398cf625071993680d",
            "iat": 1592309117,
            "nbf": 1592309117,
            "exp": 1624225038,
            "sub": "23",
            "user_id": user_id,
            "scopes": [],
            "uid": 23
        }
        return ('Bearer ' + jwt.encode(payload, key, algorithm='RS256').decode('utf-8')).encode('utf-8')

    def test_create_project(self):
        with app.test_client() as client:

            client.environ_base['HTTP_AUTHORIZATION'] = self.build_token(self.key)
            sent = {'name' : 'ProjectTest', 'm2_gen_id': 4, 'location_gen_id': 4, 'layout_gen_id': 4}
            rv = client.post('/api/projects', data = json.dumps(sent), content_type='application/json')

            self.assertEqual(rv.status_code, 201)

    def test_get_project_by_id(self):
        with app.test_client() as client:
            client.environ_base['HTTP_AUTHORIZATION'] = self.build_token(self.key)
            rv = client.get('/api/projects/1')
            assert b'{"id":1,"layout_gen_id":1,"location_gen_id":1,"m2_gen_id":1,"name":"Project1","time_gen_id":null,"user_id":1}\n' in rv.data
   
    def test_update_project(self):
        with app.test_client() as client:
            client.environ_base['HTTP_AUTHORIZATION'] = self.build_token(self.key)
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
            client.environ_base['HTTP_AUTHORIZATION'] = self.build_token(self.key)
            rv = client.delete('/api/projects/2')
            self.assertEqual(rv.status_code, 200)
    
    def test_get_projects_by_user(self):
        with app.test_client() as client:
            uid = 1
            client.environ_base['HTTP_AUTHORIZATION'] = self.build_token(self.key, user_id=uid)
            rv = client.get('/api/projects')
            datas = json.loads(rv.data)
            assert len(datas) == 3

if __name__ == '__main__':
    unittest.main()