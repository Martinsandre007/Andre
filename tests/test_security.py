import unittest
import json
import os
from app import app, db, User

class SecurityTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SECRET_KEY'] = 'test_secret'
        os.environ['API_KEY'] = 'test_api_key'
        self.app = app.test_client()
        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_register_role_escalation(self):
        # Attempt to register as admin
        res = self.app.post('/register', data=json.dumps(dict(
            username='attacker',
            password='password',
            role='admin'
        )), content_type='application/json')
        self.assertEqual(res.status_code, 201)

        # Check the role in the database
        with app.app_context():
            user = User.query.filter_by(username='attacker').first()
            self.assertEqual(user.role, 'staff') # Should be staff, not admin

    def test_api_unauthenticated_access(self):
        res = self.app.post('/api/transaction', data=json.dumps(dict(
            amount=100.0,
            location='test'
        )), content_type='application/json')
        self.assertEqual(res.status_code, 401)
        self.assertIn('Invalid or missing API key', res.get_data(as_text=True))

    def test_api_authenticated_access(self):
        res = self.app.post('/api/transaction', headers={
            'x-api-key': 'test_api_key'
        }, data=json.dumps(dict(
            amount=100.0,
            location='test'
        )), content_type='application/json')
        self.assertEqual(res.status_code, 201)

if __name__ == '__main__':
    unittest.main()
