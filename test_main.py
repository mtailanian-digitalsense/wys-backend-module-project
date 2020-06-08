import unittest
import os
import json
from main import Project, app, db


class ProjectTest(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + \
            os.path.join('.', 'test.db')
        self.app = app.test_client()
        db.create_all()
        db.session.add(Project(id=1, name='Project1', user_id=1,
                               m2_gen_id=1, location_id=1))
        db.session.add(Project(id=2, name='Project2', user_id=1,
                               m2_gen_id=2, location_id=2))
        db.session.add(
            Project(
                id=3,
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
            sent = {'name' : 'ProjectTest', 'm2_gen_id': 4, 'user_id': 2, 'location_id': 4}
            rv = client.post('/api/projects', data = json.dumps(sent), content_type='application/json')

            self.assertEqual(rv.status_code, 201)

    def test_get_by_id(self):
        with app.test_client() as client:
            rv = client.get('/api/projects/1')
            assert b'{"id":1,"location_id":1,"m2_gen_id":1,"name":"Project1","user_id":"1"}\n' in rv.data

            rv = client.get('/api/projects/100')
            assert rv.status_code == 404
    
    def test_get_by_user(self):
        with app.test_client() as client:
            rv = client.get('/api/user/1/projects')
            datas = json.loads(rv.data)
            assert len(datas) == 3
            rv = client.get('/api/user/100/projects')
            assert rv.status_code == 404

if __name__ == '__main__':
    unittest.main()
