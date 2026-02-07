import unittest
import json
import os
from app import app, db, User
from eth_account import Account

class Web3AuthTestCase(unittest.TestCase):
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

    def test_nonce_generation(self):
        res = self.app.post('/api/nonce', data=json.dumps(dict(
            address='0x1234567890123456789012345678901234567890'
        )), content_type='application/json')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn('nonce', data)

    def test_ethereum_login(self):
        # Create a test account
        acc = Account.create()
        address = acc.address

        # Get nonce
        res = self.app.post('/api/nonce', data=json.dumps(dict(
            address=address
        )), content_type='application/json')
        nonce = json.loads(res.data)['nonce']

        # Sign message
        message = f"Sign this message to authenticate: {nonce}"
        from eth_account.messages import encode_defunct
        encoded_message = encode_defunct(text=message)
        signature = acc.sign_message(encoded_message).signature.hex()

        # Login
        res = self.app.post('/api/login/ethereum', data=json.dumps(dict(
            address=address,
            signature=signature,
            nonce=nonce
        )), content_type='application/json')

        self.assertEqual(res.status_code, 200)
        self.assertIn('token', json.loads(res.data))

    def test_ethereum_login_invalid_nonce(self):
        acc = Account.create()
        address = acc.address

        # Get nonce
        res = self.app.post('/api/nonce', data=json.dumps(dict(
            address=address
        )), content_type='application/json')
        nonce = json.loads(res.data)['nonce']

        # Sign message
        message = f"Sign this message to authenticate: {nonce}"
        from eth_account.messages import encode_defunct
        encoded_message = encode_defunct(text=message)
        signature = acc.sign_message(encoded_message).signature.hex()

        # Login with WRONG nonce
        res = self.app.post('/api/login/ethereum', data=json.dumps(dict(
            address=address,
            signature=signature,
            nonce='wrong_nonce'
        )), content_type='application/json')

        self.assertEqual(res.status_code, 401)
        self.assertIn('Invalid nonce', json.loads(res.data)['message'])

    def test_ethereum_login_user_creation(self):
        acc = Account.create()
        address = acc.address
        res = self.app.post('/api/nonce', data=json.dumps(dict(address=address)), content_type='application/json')
        nonce = json.loads(res.data)['nonce']
        from eth_account.messages import encode_defunct
        encoded_message = encode_defunct(text=f"Sign this message to authenticate: {nonce}")
        signature = acc.sign_message(encoded_message).signature.hex()

        self.app.post('/api/login/ethereum', data=json.dumps(dict(
            address=address,
            signature=signature,
            nonce=nonce
        )), content_type='application/json')

        # Verify user created
        with app.app_context():
            user = User.query.filter_by(eth_address=address).first()
            self.assertIsNotNone(user)
            self.assertEqual(user.eth_address, address)

if __name__ == '__main__':
    unittest.main()
