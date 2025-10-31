import os
from flask import Flask, request, jsonify, make_response, render_template, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from passlib.hash import sha256_crypt
from fpdf import FPDF
import jwt
from functools import wraps
from datetime import datetime, timedelta

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False, default='staff')

    def set_password(self, password):
        self.password_hash = sha256_crypt.hash(password)

    def check_password(self, password):
        return sha256_crypt.verify(password, self.password_hash)

    def __repr__(self):
        return f'<User {self.username}>'

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('transactions', lazy=True))
    flagged_transaction = db.relationship('FlaggedTransaction', backref='transaction', uselist=False)


class FlaggedTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'), nullable=False)
    reason = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending') # pending, resolved

class TimeLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('timelogs', lazy=True))
    clock_in = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    clock_out = db.Column(db.DateTime)

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'staff')

    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'Username already exists'}), 400

    new_user = User(username=username, role=role)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User created successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400

    user = User.query.filter_by(username=username).first()

    if user is None or not user.check_password(password):
        return jsonify({'message': 'Invalid username or password'}), 401

    token = jwt.encode({
        'user_id': user.id,
        'role': user.role,
        'exp': datetime.utcnow() + timedelta(minutes=30)
    }, app.config['SECRET_KEY'])

    return jsonify({'token': token})

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
        except:
            return jsonify({'message': 'Token is invalid!'}), 401

        return f(current_user, *args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        if current_user.role != 'admin':
            return jsonify({'message': 'Cannot perform that function!'}), 403
        return f(current_user, *args, **kwargs)
    return decorated

@app.route('/transaction', methods=['POST'])
@token_required
def add_transaction(current_user):
    data = request.get_json()
    amount = data.get('amount')
    location = data.get('location')

    if not all([amount, location]):
        return jsonify({'message': 'Missing required fields'}), 400

    new_transaction = Transaction(amount=amount, location=location, user_id=current_user.id)
    db.session.add(new_transaction)
    db.session.commit()

    check_transaction(new_transaction)

    return jsonify({'message': 'Transaction added successfully'}), 201

def check_transaction(transaction):
    """
    Analyzes a transaction and flags it if it meets suspicious criteria.
    """
    # Rule 1: Amount exceeds a certain threshold
    if transaction.amount > 10000:
        flag_transaction(transaction, "High transaction amount")
        return

    # Rule 2: High frequency of transactions from a single user
    # (e.g., more than 5 transactions in the last hour)
    from datetime import datetime, timedelta
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    recent_transactions = Transaction.query.filter(
        Transaction.user_id == transaction.user_id,
        Transaction.timestamp >= one_hour_ago
    ).count()

    if recent_transactions > 5:
        flag_transaction(transaction, "High frequency of transactions")
        return

    # Rule 3: Transactions from a suspicious location
    suspicious_locations = ["known_fraud_location_1", "known_fraud_location_2"]
    if transaction.location in suspicious_locations:
        flag_transaction(transaction, "Transaction from a suspicious location")
        return

def flag_transaction(transaction, reason):
    """
    Flags a transaction as suspicious and sends an alert.
    """
    # Check if the transaction is already flagged
    if transaction.flagged_transaction:
        return

    flagged_transaction = FlaggedTransaction(
        transaction_id=transaction.id,
        reason=reason
    )
    db.session.add(flagged_transaction)
    db.session.commit()

    send_admin_alert(transaction, reason)

def send_admin_alert(transaction, reason):
    """
    Sends an email alert to the admin about a flagged transaction.
    (Placeholder for now)
    """
    print(f"ALERT: Transaction {transaction.id} flagged for '{reason}'")

@app.route('/admin/flagged-transactions', methods=['GET'])
@token_required
@admin_required
def get_flagged_transactions(current_user):
    flagged = FlaggedTransaction.query.all()
    output = []
    for f in flagged:
        output.append({
            'id': f.id,
            'transaction_id': f.transaction_id,
            'reason': f.reason,
            'status': f.status,
            'timestamp': f.transaction.timestamp
        })
    return jsonify(output)

@app.route('/admin/flagged-transactions/<int:id>', methods=['PUT'])
@token_required
@admin_required
def update_flagged_transaction(current_user, id):
    data = request.get_json()
    new_status = data.get('status')

    if not new_status or new_status not in ['pending', 'resolved']:
        return jsonify({'message': 'Invalid status'}), 400

    flagged = FlaggedTransaction.query.get(id)
    if not flagged:
        return jsonify({'message': 'Flagged transaction not found'}), 404

    flagged.status = new_status
    db.session.commit()
    return jsonify({'message': 'Status updated successfully'})

@app.route('/admin/users', methods=['GET'])
@token_required
@admin_required
def get_users(current_user):
    users = User.query.all()
    output = []
    for user in users:
        output.append({
            'id': user.id,
            'username': user.username,
            'role': user.role
        })
    return jsonify(output)

@app.route('/admin/users/<int:id>', methods=['PUT'])
@token_required
@admin_required
def update_user(current_user, id):
    data = request.get_json()
    new_role = data.get('role')

    if not new_role or new_role not in ['admin', 'staff']:
        return jsonify({'message': 'Invalid role'}), 400

    user = User.query.get(id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    user.role = new_role
    db.session.commit()
    return jsonify({'message': 'User role updated successfully'})

@app.route('/admin/payroll', methods=['GET'])
@token_required
@admin_required
def get_payroll(current_user):
    from datetime import datetime, timedelta
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    time_logs = TimeLog.query.filter(
        TimeLog.clock_out != None,
        TimeLog.clock_in >= thirty_days_ago
    ).all()

    payroll_data = {}
    hourly_rate = 20 # Fixed hourly rate for all staff

    for log in time_logs:
        if log.user_id not in payroll_data:
            payroll_data[log.user_id] = {
                'username': log.user.username,
                'total_hours': 0,
                'total_pay': 0
            }

        duration = log.clock_out - log.clock_in
        hours_worked = duration.total_seconds() / 3600
        pay = hours_worked * hourly_rate

        payroll_data[log.user_id]['total_hours'] += hours_worked
        payroll_data[log.user_id]['total_pay'] += pay

    return jsonify(list(payroll_data.values()))

@app.route('/admin/payroll/pdf', methods=['GET'])
@token_required
@admin_required
def get_payroll_pdf(current_user):
    from datetime import datetime, timedelta
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    time_logs = TimeLog.query.filter(
        TimeLog.clock_out != None,
        TimeLog.clock_in >= thirty_days_ago
    ).all()

    payroll_data = {}
    hourly_rate = 20 # Fixed hourly rate for all staff

    for log in time_logs:
        if log.user_id not in payroll_data:
            payroll_data[log.user_id] = {
                'username': log.user.username,
                'total_hours': 0,
                'total_pay': 0
            }

        duration = log.clock_out - log.clock_in
        hours_worked = duration.total_seconds() / 3600
        pay = hours_worked * hourly_rate

        payroll_data[log.user_id]['total_hours'] += hours_worked
        payroll_data[log.user_id]['total_pay'] += pay

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Payroll Report", ln=1, align="C")

    pdf.cell(50, 10, txt="Username", border=1)
    pdf.cell(50, 10, txt="Total Hours", border=1)
    pdf.cell(50, 10, txt="Total Pay", border=1)
    pdf.ln()

    for user_id, data in payroll_data.items():
        pdf.cell(50, 10, txt=data['username'], border=1)
        pdf.cell(50, 10, txt=str(round(data['total_hours'], 2)), border=1)
        pdf.cell(50, 10, txt=str(round(data['total_pay'], 2)), border=1)
        pdf.ln()

    response = make_response(pdf.output(dest='S').encode('latin-1'))
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=payroll_report.pdf'

    return response

@app.route('/api/transaction', methods=['POST'])
@token_required
def api_add_transaction(current_user):
    data = request.get_json()
    amount = data.get('amount')
    location = data.get('location')

    # For the API, we'll associate transactions with a dedicated 'api_user'
    # In a real app, you might have different API users for different sources
    api_user = User.query.filter_by(username='api_user').first()
    if not api_user:
        api_user = User(username='api_user', role='api')
        api_user.set_password('api_password') # Not used for login, just for consistency
        db.session.add(api_user)
        db.session.commit()

    if not all([amount, location]):
        return jsonify({'message': 'Missing required fields'}), 400

    new_transaction = Transaction(amount=amount, location=location, user_id=api_user.id)
    db.session.add(new_transaction)
    db.session.commit()

    check_transaction(new_transaction)

    return jsonify({'message': 'Transaction added successfully'}), 201

@app.route('/admin/analytics', methods=['GET'])
@token_required
@admin_required
def get_analytics(current_user):

    total_transactions = Transaction.query.count()
    total_flagged = FlaggedTransaction.query.count()

    # Example: Transactions per location
    location_counts = db.session.query(
        Transaction.location, db.func.count(Transaction.location)
    ).group_by(Transaction.location).all()

    locations = {loc: count for loc, count in location_counts}

    return jsonify({
        'total_transactions': total_transactions,
        'total_flagged': total_flagged,
        'transactions_by_location': locations
    })

@app.route('/clock-in', methods=['POST'])
@token_required
def clock_in(current_user):
    # Check if there's an open time log
    open_time_log = TimeLog.query.filter_by(user_id=current_user.id, clock_out=None).first()
    if open_time_log:
        return jsonify({'message': 'User is already clocked in'}), 400

    new_time_log = TimeLog(user_id=current_user.id)
    db.session.add(new_time_log)
    db.session.commit()

    return jsonify({'message': 'Clocked in successfully'}), 201

@app.route('/clock-out', methods=['POST'])
@token_required
def clock_out(current_user):
    time_log = TimeLog.query.filter_by(user_id=current_user.id, clock_out=None).first()

    if not time_log:
        return jsonify({'message': 'User is not clocked in'}), 400

    time_log.clock_out = db.func.current_timestamp()
    db.session.commit()

    return jsonify({'message': 'Clocked out successfully'}), 200

# Frontend Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/staff')
def staff_page():
    return render_template('staff.html')

@app.route('/admin')
def admin_page():
    return render_template('admin.html')

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    app.run(debug=True)
