from flask_sqlalchemy import SQLAlchemy# type: ignore
from sqlalchemy.exc import IntegrityError# type: ignore
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file# type: ignore
from flask_mail import Mail, Message# type: ignore
import random
import string
from flask import Flask, jsonify# type: ignore
from werkzeug.utils import secure_filename # type: ignore
import os
import plotly.express as px# type: ignore
import numpy as np# type: ignore
# from tensorflow.keras.preprocessing import image# type: ignore
# import tensorflow as tf# type: ignore
from sklearn.tree import DecisionTreeClassifier# type: ignore
from sklearn.model_selection import train_test_split# type: ignore
import numpy as np,pandas as pd# type: ignore
import os
import csv
from dotenv import load_dotenv# type: ignore
import pdfkit# type: ignore
# from reportlab.pdfgen import c# type: ignoreanvas
from io import BytesIO# type: ignore
from flask.helpers import send_file# type: ignore
from reportlab.lib.pagesizes import letter# type: ignore
from reportlab.lib import colors# type: ignore
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle# type: ignore
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, Spacer# type: ignore
from io import BytesIO
import google.generativeai as genai# type: ignore
from markdown import markdown# type: ignore
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import random

app = Flask(__name__)
port = int(os.environ.get("PORT", 5000))
mail = Mail(app)
load_dotenv()

app.secret_key = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS') == 'True'
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS') == 'True'
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')
mail = Mail(app)
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), nullable=False)
    password = db.Column(db.String(120), nullable=False)
  
    type_of_doctor = db.Column(db.String(50))

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    blood_group = db.Column(db.String(10), nullable=False)
    time_slot = db.Column(db.String(50), nullable=False)
    phone_number = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    type_of_doctor = db.Column(db.String(50))
    status = db.Column(db.String(20), default='Pending')
    prescription_file = db.Column(db.String(255))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('appointments', lazy=True))

def create_tables():
    with app.app_context():
        db.create_all()

def generate_random_string(length=10):
    letters_and_digits = string.ascii_letters + string.digits
    return ''.join(random.choice(letters_and_digits) for i in range(length))

def send_mail(subject, recipient, body):
    msg = Message(subject, recipients=[recipient])
    msg.body = body
    mail.send(msg)
    

# Set the path to the directory containing text files
text_files_dir = os.path.join(os.path.dirname(__file__), 'static/prescriptions')

# Set the path to the directory where PDFs will be saved
pdf_output_dir = os.path.join(os.path.dirname(__file__), 'static/pdfs')

# Function to convert text file to PDF
def convert_to_pdf(file_path, output_path):
    with open(file_path, 'r') as file:
        content = file.read()

    pdfkit.from_string(content, output_path, {'title': 'PDF Conversion', 'footer-center': '[page]/[topage]'})
    
# ============================================================ model ============================================================ 


data = pd.read_csv(os.path.join("static","Data", "Training.csv"))
df = pd.DataFrame(data)
cols = df.columns
cols = cols[:-1]
x = df[cols]
y = df['prognosis']
x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.33, random_state=42)

dt = DecisionTreeClassifier()
clf_dt=dt.fit(x_train,y_train)

indices = [i for i in range(132)]
symptoms = df.columns.values[:-1]

dictionary = dict(zip(symptoms,indices))

def predict(symptom):
    user_input_symptoms = symptom
    user_input_label = [0 for i in range(132)]
    for i in user_input_symptoms:
        idx = dictionary[i]
        user_input_label[idx] = 1

    user_input_label = np.array(user_input_label)
    user_input_label = user_input_label.reshape((-1, 1)).transpose()

    predicted_disease = dt.predict(user_input_label)[0]
    confidence_score = np.max(dt.predict_proba(user_input_label)) * 100  # Assuming decision tree has predict_proba method

    return predicted_disease, confidence_score

with open('static/Data/Testing.csv', newline='') as f:
        reader = csv.reader(f)
        symptoms = next(reader)
        symptoms = symptoms[:len(symptoms)-1]
        
# ============================================================ routes ============================================================ 

@app.route('/', methods=['GET', 'POST'])
def index():
    username = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        username = user.username
        email = user.email
        type_of_doctor = user.type_of_doctor
        if user.type_of_doctor:
            appointments = Appointment.query.filter_by(type_of_doctor=user.type_of_doctor).all()
            return render_template('doctor-dashboard.html', username=username, email=email, type_of_doctor=type_of_doctor, appointments=appointments)
            
        
        else:
            user_appointments = user.appointments
            return render_template('patient-dashboard.html', username=username, user_appointments=user_appointments)
            
    return render_template('index.html')


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    username = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        username = user.username
        Email = user.email 
        user_appointments = user.appointments
        return render_template('patient-profile.html', username=username,Email=Email, user_appointments=user_appointments)
    return render_template('index')

@app.route('/patient-register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        try:
            user = User(username=username, email=email, password=password)
            db.session.add(user)
            db.session.commit()
            session['user_id'] = user.id
            return redirect(url_for('index'))
        except IntegrityError:
            db.session.rollback()
            flash('Username already exists. Please choose a different username.', 'error')

    return render_template('patient-register.html')

@app.route('/doctor-register', methods=['GET', 'POST'])
def doctor_register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        type_of_doctor = request.form['type_of_doctor']
        user = User(username=username,email=email, password=password, type_of_doctor=type_of_doctor)
        db.session.add(user)
        db.session.commit()
        session['user_id'] = user.id
        return redirect(url_for('index'))
    return render_template('doctor-register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user_id'] = user.id
            return redirect(url_for('index'))
        else:
            flash('Wrong username or password. Please try again.', 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

@app.route('/book-appointment', methods=['GET', 'POST'])
def book_appointment():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    username = None
    
    user = User.query.get(session['user_id'])
    username = user.username
    
    # Fetch distinct types of doctors from the database
    doctor_types = db.session.query(User.type_of_doctor).distinct().all()
    doctor_types = [doctor[0] for doctor in doctor_types]

    if request.method == 'POST':
        name = request.form['name']
        age = int(request.form['age'])
        blood_group = request.form['blood_group']
        time_slot = request.form['time_slot']
        phone_number = request.form['phone_number']
        email = request.form['email']
        type_of_doctor = request.form['type_of_doctor']

        appointment = Appointment(
            name=name,
            age=age,
            blood_group=blood_group,
            time_slot=time_slot,
            phone_number=phone_number,
            email=email,
            type_of_doctor=type_of_doctor,
            user=user
        )

        db.session.add(appointment)
        db.session.commit()

        # Notify the doctor via email
        doctor_email = User.query.filter_by(type_of_doctor=type_of_doctor).first().email
        subject = 'New Appointment Request'
        body = f'Hello Doctor,\n\nYou have a new appointment request. Please log in to the system to approve or reject it.'
        send_mail(subject, doctor_email, body)

        return redirect(url_for('index'))

    return render_template('book-appointment.html',doctor_types=doctor_types,username=username)

@app.route('/approve-appointment/<int:appointment_id>')
def approve_appointment(appointment_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    doctor = User.query.get(session['user_id'])
    appointment = Appointment.query.get(appointment_id)

    if appointment.type_of_doctor != doctor.type_of_doctor:
        return redirect(url_for('index'))

    appointment.status = 'Approved'
    db.session.commit()

    # Notify the patient via email
    subject = 'Appointment Approved'
    body = f'Hello {appointment.name},\n\nYour appointment has been approved. Please log in to the system to view the details.'
    send_mail(subject, appointment.email, body)

    return redirect(url_for('index'))

@app.route('/policy')
def policy():
    return render_template('privacy-policy.html')

@app.route('/Transforming_Healthcare')
def Transforming_Healthcare():
    username = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        username = user.username
        return render_template('blog_Transforming Healthcare.html',username=username)
    return render_template('index.html')

@app.route('/Holistic_Health')
def Holistic_Health():
    username = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        username = user.username
        return render_template('blog_Holistic Health.html',username=username)
    return render_template('index.html')

@app.route('/Nourishing_Body')
def Nourishing_Body():
    username = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        username = user.username
        return render_template('blog_Nourishing_Body.html',username=username)
    return render_template('index.html')

@app.route('/Importance_of_Games')
def Importance_of_Games():
    username = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        username = user.username
        return render_template('blog_Importance_of_Games.html',username=username)
    return render_template('index.html')

genai.configure(api_key='AIzaSyDynN2eNlpri7vfQW2f2TmFJkzXtEpcNt4')

model = genai.GenerativeModel('gemini-pro')
chat_model = model.start_chat(history=[])   # chat based on history

img_model = genai.GenerativeModel('gemini-pro-vision')

@app.route('/conference')
def conference():
    return render_template('conference.html')

@app.route('/mail-service')
def mail_service():
    return render_template('mail_service.html')

@app.route("/chat", methods=['GET', 'POST'])
def chat():
    if request.method == 'POST':
        query = request.json['query']
        if (len(query.strip()) == 0):
            return jsonify("Please enter something!")
        try:
            gemini_response = chat_model.send_message(
                query).text   # Send message based on the chat history
        except:
            return jsonify("Something went wrong!")
        print(gemini_response)
        return gemini_response
    else:
        return render_template("chats.html")
 

@app.route("/chat1", methods=['POST'])
def chat1():
    query = request.json['query']
    if (len(query.strip()) == 0):
        return jsonify({"error": "Please enter something!"})
    try:
        gemini_response = chat_model.send_message(query).text
        # Create a JSON response
        json_response = {"response": gemini_response}

        return json_response
    except Exception as e:
        return ({"error": str(e)})
 
# Image to text  



@app.route("/image_chat", methods=['POST', 'GET'])
def image_chat():
    if request.method == 'POST':
        img = request.files['image']   # Loads the file
        q = request.form['query']   # Loads the query

        image = Image.open(img)   # Read the image in PIL format
        try:
            response = img_model.generate_content(
                [q, image])   # Generate content for the image
        except:
            return jsonify("Something went wrong!")
        return jsonify(markdown(response.text))
    else:
        return render_template("image_upload.html")

@app.route('/schedule-meeting/<int:appointment_id>', methods=['POST'])
def schedule_meeting(appointment_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    doctor = User.query.get(session['user_id'])
    appointment = Appointment.query.get(appointment_id)

    if appointment.type_of_doctor != doctor.type_of_doctor:
        return redirect(url_for('index'))

    # Generate a unique meeting room ID
    room_id = str(random.randint(1000, 9999))

    # Construct the meeting link
    meeting_link = f"{request.url_root}videocall?roomID={room_id}&username={appointment.name}"

    #Send the meeting link to patient's email
    send_meeting_email(appointment.email, appointment.name, meeting_link)

    return redirect(url_for('videocall') + f"?roomID={room_id}&username={doctor.username}")

def send_meeting_email(patient_email, patient_name, meeting_link):
    sender_email = os.getenv('MAIL_USERNAME')
    sender_password = os.getenv('MAIL_PASSWORD')
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = patient_email
    msg['Subject'] = "Your Health-Genie Appointment Link"
    
    body = f"Dear {patient_name},\n\nYour doctor has scheduled an online appointment. Please join using the link below:\n\n{meeting_link}\n\nRegards,\nHealth-Genie Team"
    msg.attach(MIMEText(body, 'plain'))
    
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, patient_email, msg.as_string())

@app.route('/videocall')
def videocall():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    # Retrieve username and room ID for meeting
    user = User.query.get(session['user_id'])
    username = user.username
    roomID = request.args.get('roomID')
    
    return render_template('videocall.html', username=username, roomID=roomID)

@app.route('/doctor-patients')
def doctor_patients():
    username = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        username = user.username

        doctor = User.query.get(session['user_id'])

        if not doctor.type_of_doctor:
            return redirect(url_for('index'))

        # Fetch appointments assigned to the doctor
        appointments = Appointment.query.filter_by(type_of_doctor=doctor.type_of_doctor).all()
        file_list = os.listdir(text_files_dir)

        return render_template('doctor-patients.html', doctor=doctor, appointments=appointments,username=username,file_list=file_list)
    return render_template('index.html')

@app.route('/prescribe-medicine/<int:appointment_id>', methods=['GET', 'POST'])
def prescribe_medicine(appointment_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    doctor = User.query.get(session['user_id'])
    appointment = Appointment.query.get(appointment_id)

    if appointment.type_of_doctor != doctor.type_of_doctor:
        return redirect(url_for('index'))
    
    #load medicines from JSON file
    with open("medicine.json") as f:
        available_medicines = json.load(f)

    if request.method == 'POST':
        selected_medicines = request.form.getlist('medicines[]')

        # Create a PDF document using ReportLab
        buffer = BytesIO()
        pdf = SimpleDocTemplate(buffer, pagesize=letter)

        # Define styles for the header and footer
        styles = getSampleStyleSheet()
        header_style = ParagraphStyle(
            'Header1',
            parent=styles['Heading1'],
            fontName='monospace',
            fontSize=18,
            spaceAfter=12,
            textColor=colors.green,
        )

        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.gray,
        )

        # Create content for the PDF
        content = []

        # Add Jansevak header with green color
        # jansevak_header = Paragraph("<font color='green' size='24'><b>Jansevak: We Care for Your Health</b></font>", header_style)
        # content.append(jansevak_header)

        # Add space after Jansevak header
        content.append(Spacer(1, 12))

        # Add patient details
        patient_details = (
            f"<b>Patient Details:</b><br/>"
            f"Name: {appointment.name}<br/>"
            f"Age: {appointment.age}<br/>"
            f"Blood Group: {appointment.blood_group}<br/>"
            f"Phone Number: {appointment.phone_number}<br/>"
            f"Email ID: {appointment.email}"
        )
        content.append(Paragraph(patient_details, styles['Normal']))

        # Add space after patient details
        content.append(Spacer(1, 12))

        # Add prescribed medicines
        prescribed_meds = "<b>Prescribed Medicines:</b><br/>"
        for medicine in selected_medicines:
            prescribed_meds += f"- {medicine}<br/>"
        content.append(Paragraph(prescribed_meds, styles['Normal']))

        # Add space after prescribed medicines
        content.append(Spacer(1, 12))

        # Add doctor details and footer
        doctor_details = (
            f"<b>Prescribed by Dr. {doctor.username} ({doctor.type_of_doctor})</b><br/>"
            "Thank you for choosing Health-Genie! We wish you good health."
        )
        content.append(Paragraph(doctor_details, styles['Normal']))

        # Add space after doctor details
        content.append(Spacer(1, 12))

        # Build the PDF
        pdf.build(content)

        # Save the PDF to the file
        pdf_filename = f"prescription_{appointment_id}.pdf"
        pdf_filepath = os.path.join("static", "prescriptions", pdf_filename)
        buffer.seek(0)
        with open(pdf_filepath, 'wb') as pdf_file:
            pdf_file.write(buffer.read())

        buffer.close()

        # Update appointment status to 'Prescribed'
        appointment.status = 'Prescribed'
        appointment.prescription_file = pdf_filepath
        db.session.commit()

        #Send the prescription PDF to the patient's email
        sender_email = os.getenv("MAIL_USERNAME")
        sender_password = os.getenv("MAIL_PASSWORD")
        smtp_server = os.getenv("MAIL_SERVER")
        smtp_port = int(os.getenv("MAIL_PORT"))

        #Create email message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = appointment.email
        msg['Subject'] = "Your Prescription from Health-Genie"
        body = "Please find your prescription attached.\n\nBest wishes for your recovery!\nHealth-Genie Team"

        msg.attach(MIMEText(body, 'plain'))

        #Attach the PDF file
        with open(pdf_filepath, 'rb') as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachemt; filename = {pdf_filename}')
        msg.attach(part)

        #Send the email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)

        return redirect(url_for('doctor_patients'))

    return render_template('prescribe-medicine.html', appointment=appointment, available_medicines=available_medicines)
    
@app.route('/view-prescription/<int:appointment_id>')
def view_prescription(appointment_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    doctor = User.query.get(session['user_id'])
    appointment = Appointment.query.get(appointment_id)

    if appointment.type_of_doctor != doctor.type_of_doctor or appointment.status != 'Prescribed':
        return redirect(url_for('index'))

    prescription_filepath = appointment.prescription_file

    return send_file(prescription_filepath, as_attachment=True)

@app.route('/view-prescription-patient/<int:appointment_id>')
def view_prescription_patient(appointment_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    appointment = Appointment.query.get(appointment_id)

    if not user or not appointment or appointment.user_id != user.id or appointment.status != 'Prescribed':
        return redirect(url_for('profile'))  # Change this line to redirect to the patient's profile instead of index

    # Read prescription text from the file
    prescription_filepath = appointment.prescription_file
    

    return send_file(prescription_filepath, as_attachment=True)

# ============================================================ scans ============================================================ 
    
@app.route('/braintumor', methods=['GET', 'POST'])
def braintumor():
    username = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        username = user.username
        return render_template('brain-tumor.html',username=username)
    else:
        return render_template('index.html')
    

@app.route('/disease_predict', methods=['GET', 'POST'])
def disease_predict():
    username = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        username = user.username
        chart_data={}
        if request.method == 'POST':
            selected_symptoms = []
            if(request.form['Symptom1']!="") and (request.form['Symptom1'] not in selected_symptoms):
                selected_symptoms.append(request.form['Symptom1'])
            if(request.form['Symptom2']!="") and (request.form['Symptom2'] not in selected_symptoms):
                selected_symptoms.append(request.form['Symptom2'])
            if(request.form['Symptom3']!="") and (request.form['Symptom3'] not in selected_symptoms):
                selected_symptoms.append(request.form['Symptom3'])
            if(request.form['Symptom4']!="") and (request.form['Symptom4'] not in selected_symptoms):
                selected_symptoms.append(request.form['Symptom4'])
            disease, confidence_score = predict(selected_symptoms)
            
            chart_data = {
            'disease': disease,
            'confidence_score': confidence_score
            }
            return render_template('disease_predict.html',symptoms=symptoms,disease=disease, chart_data=chart_data,confidence_score=confidence_score,username=username)
            
        return render_template('disease_predict.html',symptoms=symptoms,username=username,chart_data=chart_data)
    else:
        return render_template('index.html')

@app.route('/lung')
def lung():
    username = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        username = user.username
        return render_template('lung.html',username=username)
    else:
        return render_template('index.html')

@app.route('/cataract')
def cataract():
    username = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        username = user.username
        return render_template('cataract.html',username=username)
    return render_template('index.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port, debug=True)  # Ensure it listens on all interfaces
    create_tables()