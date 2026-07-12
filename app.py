from flask import Flask, request, jsonify, render_template, send_from_directory, session, redirect, url_for, make_response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from functools import wraps
import io
import csv # Added for Excel exporting

# Initialize the monolithic app configuration
app = Flask(__name__, static_folder='static', template_folder='templates')

# CRITICAL: Secret key needed for secure login sessions
app.secret_key = 'sb_publishable_r6Zzf1dImJ_eSi0Rjf-Uiw_Goj-xPWt'

# ==========================================
# 1. LIVE SUPABASE DATABASE CONFIGURATION
# ==========================================
# Migrated from Neon to your personal Supabase instance with credentials applied
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres.zxzoxyfkceckhrdhoqqo:nexauto2026@aws-1-ap-south-1.pooler.supabase.com:6543/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Admission(db.Model):
    __tablename__ = 'students' # Re-mapped to standard students naming context
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    course = db.Column(db.String(100), nullable=False)
    education = db.Column(db.String(100))
    batch_number = db.Column(db.Integer, nullable=False) # New trackable column for grouping
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

# ==========================================
# 2. BACKEND API ENDPOINT (Automatic Batching)
# ==========================================
@app.route('/api/apply', methods=['POST'])
def apply():
    try:
        data = request.json
        
        # Guard Check: Avoid duplicate email submissions
        existing = Admission.query.filter_by(email=data['Email']).first()
        if existing:
            return jsonify({"success": False, "message": "This email has already been registered."}), 400

        # LOGIC: Query current maximum batch index
        highest_batch = db.session.query(db.func.max(Admission.batch_number)).scalar()
        
        if highest_batch is None:
            assigned_batch = 1
        else:
            # Count how many students currently exist in that active batch
            current_batch_count = Admission.query.filter_by(batch_number=highest_batch).count()
            
            # If the current capacity hits or exceeds 10, roll over to the next numerical batch
            if current_batch_count >= 10:
                assigned_batch = highest_batch + 1
            else:
                assigned_batch = highest_batch

        new_student = Admission(
            name=data['Name'],
            phone=data['Phone'],
            email=data['Email'],
            course=data['Course'],
            education=data.get('Education', ''),
            batch_number=assigned_batch
        )
        db.session.add(new_student)
        db.session.commit()
        return jsonify({"success": True, "message": f"Application saved successfully to Batch {assigned_batch}!"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

# ==========================================
# 3. HTML LOGIN SYSTEM & SECURITY GATE
# ==========================================
def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == 'nexauto2026':
            session['logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            error = 'Invalid credentials. Please try again.'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

# ==========================================
# 4. ADMIN DASHBOARD & CRUD MANAGEMENT
# ==========================================
@app.route('/admin')
@requires_auth
def admin_dashboard():
    # Fetch all students sorted chronologically
    students = Admission.query.order_by(Admission.timestamp.desc()).all()
    
    # Calculate global structural metrics for dashboard UI injection
    total_count = Admission.query.count()
    
    # Aggregate student distribution matching respective batches
    batch_raw_data = db.session.query(
        Admission.batch_number, 
        db.func.count(Admission.id)
    ).group_by(Admission.batch_number).order_by(Admission.batch_number).all()
    
    batch_summary = [{"number": b[0], "count": b[1]} for b in batch_raw_data]

    # Package context together for your updated dashboard template rendering
    response = make_response(render_template(
        'admin.html', 
        students=students, 
        total_students=total_count, 
        batches=batch_summary
    ))
    
    # Anti-caching enforcement protocols
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# Action Route: Data Management Removal Protocol (CRUD)
@app.route('/admin/delete/<int:student_id>', methods=['POST'])
@requires_auth
def delete_student(student_id):
    try:
        target_student = Admission.query.get_or_404(student_id)
        db.session.delete(target_student)
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

# Action Route: Dynamic PDF Report Engine Generation
@app.route('/admin/download_pdf/<int:student_id>')
@requires_auth
def download_pdf(student_id):
    target_student = Admission.query.get_or_404(student_id)
    
    # Import ReportLab layout canvas components locally
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    
    # Build styled document layout structures
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(100, 750, "NexAuto Institute - Student Document Profile")
    pdf.setLineWidth(1)
    pdf.line(100, 735, 512, 735)
    
    pdf.setFont("Helvetica", 12)
    pdf.drawString(100, 690, f"System Admission ID: {target_student.id}")
    pdf.drawString(100, 660, f"Full Legal Name: {target_student.name}")
    pdf.drawString(100, 630, f"Contact Number: {target_student.phone}")
    pdf.drawString(100, 600, f"Verified Email Address: {target_student.email}")
    pdf.drawString(100, 570, f"Enrolled Course Focus: {target_student.course}")
    pdf.drawString(100, 540, f"Educational Background: {target_student.education or 'Not Specified'}")
    pdf.drawString(100, 510, f"Assigned Cohort Grouping: Batch {target_student.batch_number}")
    pdf.drawString(100, 480, f"Timestamp Matrix: {target_student.timestamp.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    
    pdf.showPage()
    pdf.save()
    
    buffer.seek(0)
    pdf_output = buffer.getvalue()
    buffer.close()
    
    # Build and deploy download payload header structures to trigger local browser downloads
    response = make_response(pdf_output)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=Student_Profile_{target_student.id}.pdf'
    return response

# Action Route: Export Specific Batch to Excel (CSV format)
@app.route('/admin/download_batch/<int:batch_num>')
@requires_auth
def download_batch(batch_num):
    # Fetch all students that belong to the requested batch
    students_in_batch = Admission.query.filter_by(batch_number=batch_num).all()
    
    # Create an in-memory string buffer to hold the CSV data
    si = io.StringIO()
    writer = csv.writer(si)
    
    # Write the header row for the Excel file
    writer.writerow(['ID', 'Full Name', 'Phone', 'Email', 'Course', 'Education', 'Registration Date'])
    
    # Loop through the students and write their data into the rows
    for student in students_in_batch:
        writer.writerow([
            student.id, 
            student.name, 
            student.phone, 
            student.email, 
            student.course, 
            student.education, 
            student.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    # Package the output and force the browser to download it as a file
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = f"attachment; filename=NexAuto_Batch_{batch_num}_Students.csv"
    output.headers["Content-type"] = "text/csv"
    return output

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
    # Make sure you have executed 'pip install reportlab' in your execution environment terminal
    app.run(debug=True, port=5000)