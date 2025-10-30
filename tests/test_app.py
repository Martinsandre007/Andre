import unittest
import json
from app import app, db, User

class AuthTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SECRET_KEY'] = 'test_secret'
        self.app = app.test_client()
        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def _get_token(self, username='testuser', password='testpassword'):
        self.app.post('/register', data=json.dumps(dict(
            username=username,
            password=password
        )), content_type='application/json')

        res = self.app.post('/login', data=json.dumps(dict(
            username=username,
            password=password
        )), content_type='application/json')

        return json.loads(res.data)['token']

    def test_register(self):
        res = self.app.post('/register', data=json.dumps(dict(
            username='testuser',
            password='testpassword'
        )), content_type='application/json')
        self.assertEqual(res.status_code, 201)

    def test_login(self):
        # First, register a user
        self.app.post('/register', data=json.dumps(dict(
            username='testuser',
            password='testpassword'
        )), content_type='application/json')

        # Now, log in
        res = self.app.post('/login', data=json.dumps(dict(
            username='testuser',
            password='testpassword'
        )), content_type='application/json')
        self.assertEqual(res.status_code, 200)

    def test_add_transaction(self):
        token = self._get_token()
        res = self.app.post('/transaction', headers={
            'x-access-token': token
        }, data=json.dumps(dict(
            amount=100.0,
            location='test location'
        )), content_type='application/json')
        self.assertEqual(res.status_code, 201)

if __name__ == '__main__':
    unittest.main()
