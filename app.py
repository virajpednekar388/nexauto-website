from flask import Flask, request, jsonify, render_template, send_from_directory, session, redirect, url_for, make_response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from functools import wraps

# Initialize the monolithic app configuration
app = Flask(__name__, static_folder='static', template_folder='templates')

# CRITICAL: Secret key needed for secure login sessions
app.secret_key = 'nexauto_secure_session_key_2026'

# ==========================================
# 1. CLOUD NEON DATABASE CONFIGURATION
# ==========================================
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://neondb_owner:npg_eVjG6R2dPZcX@ep-round-darkness-ao63yvbv.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Admission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    course = db.Column(db.String(100), nullable=False)
    education = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

# ==========================================
# 2. BACKEND API ENDPOINT (Form Submissions)
# ==========================================
@app.route('/api/apply', methods=['POST'])
def apply():
    try:
        data = request.json
        new_student = Admission(
            name=data['Name'],
            phone=data['Phone'],
            email=data['Email'],
            course=data['Course'],
            education=data.get('Education', '')
        )
        db.session.add(new_student)
        db.session.commit()
        return jsonify({"success": True, "message": "Application saved successfully!"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

# ==========================================
# 3. HTML LOGIN SYSTEM & SECURITY GATE
# ==========================================
def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # If the admin is not logged in, send them to the beautiful HTML login page
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        # Check credentials
        if request.form['username'] == 'admin' and request.form['password'] == 'nexauto2026':
            session['logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            error = 'Invalid credentials. Please try again.'
    
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    # Updated: Now redirects immediately back to the login page
    return redirect(url_for('login'))

# ==========================================
# 4. ADMIN DASHBOARD ROUTE
# ==========================================
@app.route('/admin')
@requires_auth
def admin_dashboard():
    students = Admission.query.order_by(Admission.timestamp.desc()).all()
    
    # Package the HTML into a response object
    response = make_response(render_template('admin.html', students=students))
    
    # Tell the browser NEVER to cache this page to prevent "Back" button snooping
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response

# ==========================================
# 5. FRONTEND ROUTING (Serving the SPA)
# ==========================================
@app.route('/pages/<filename>')
def serve_pages(filename):
    return send_from_directory('templates/pages', filename)

@app.route('/')
@app.route('/<path:path>')
def serve_spa(path=None):
    if path and path.startswith('api/'):
        return {"error": "API route not found"}, 404
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)