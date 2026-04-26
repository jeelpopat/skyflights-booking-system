from flask import Flask, request, redirect, url_for, render_template, session, flash, send_file
from flask_mail import Mail, Message as MailMessage
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect 
from datetime import datetime
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature 
import re
import os
import random
import io
import qrcode
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
import json
import requests

app = Flask(__name__)
app.secret_key = 'FoPnnzqJb8s4ODJH' 

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'janral2204@gmail.com'
app.config['MAIL_PASSWORD'] = 'vukijzmdkvhqzkaz' 
app.config['MAIL_DEFAULT_SENDER'] = 'janral2204@gmail.com'

mail = Mail(app) 

serializer = URLSafeTimedSerializer(app.secret_key)
csrf = CSRFProtect(app) 

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'skyflights.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), nullable=False)
    password = db.Column(db.String(255), nullable=False)

class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    flight_number = db.Column(db.String(50), nullable=False) 
    airline = db.Column(db.String(100)) 
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    from_country = db.Column(db.String(100), nullable=False)
    to_country = db.Column(db.String(100), nullable=False)
    date_of_journey = db.Column(db.String(50))
    return_date = db.Column(db.String(50)) 
    passengers = db.Column(db.Integer)
    passports = db.Column(db.String(255)) 
    ages = db.Column(db.String(100))
    genders = db.Column(db.String(100))
    total_price = db.Column(db.Float) 
    currency = db.Column(db.String(10), default='INR') 
    seat_number = db.Column(db.String(50)) 
    status = db.Column(db.String(20), default='Pending')

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    sender_name = db.Column(db.String(150))
    sender_email = db.Column(db.String(120))
    message_text = db.Column(db.Text)
    submission_date = db.Column(db.DateTime, default=datetime.utcnow)

def init_db():
    with app.app_context():
        db.create_all()

def generate_pdf_buffer(booking):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    names = booking.full_name.split(", ")
    passports = booking.passports.split(", ") if booking.passports else []
    seats = booking.seat_number.split(", ") if booking.seat_number else []

    for i in range(len(names)):
        current_name = names[i]
        current_passport = passports[i] if i < len(passports) else "N/A"
        current_seat = seats[i] if i < len(seats) else "Unassigned"

        p.setFont("Helvetica-Bold", 26)
        p.setFillColorRGB(0, 0.25, 0.31) 
        p.drawString(60, height - 90, "SKYFLIGHTS E-TICKET")
        
        p.setLineWidth(1)
        p.line(40, height - 110, width - 40, height - 110)

        p.setFont("Helvetica", 14)
        p.setFillColorRGB(0, 0, 0)
        p.drawString(60, height - 140, f"Ticket ID: SKF-{booking.id + 1000}")
        p.drawString(60, height - 165, f"Passenger {i+1} of {len(names)}: {current_name}")
        p.drawString(60, height - 190, f"Passport No: {current_passport}")
        
        p.setFont("Helvetica-Bold", 14)
        p.drawString(60, height - 230, "OUTBOUND FLIGHT")
        p.setFont("Helvetica", 14)
        p.drawString(60, height - 255, f"Route: {booking.from_country} to {booking.to_country}")
        p.drawString(60, height - 280, f"Date: {booking.date_of_journey}")
        p.drawString(60, height - 305, f"Airline: {booking.airline} ({booking.flight_number})")
        p.drawString(60, height - 330, f"Seat: {current_seat}")

        y_offset = 330

        if booking.return_date:
            y_offset += 40
            p.setFont("Helvetica-Bold", 14)
            p.drawString(60, height - y_offset, "RETURN FLIGHT")
            p.setFont("Helvetica", 14)
            y_offset += 25
            p.drawString(60, height - y_offset, f"Route: {booking.to_country} to {booking.from_country}")
            y_offset += 25
            p.drawString(60, height - y_offset, f"Date: {booking.return_date}")
            y_offset += 25
            p.drawString(60, height - y_offset, f"Airline: {booking.airline} ({booking.flight_number})")
            y_offset += 25
            p.drawString(60, height - y_offset, f"Seat: {current_seat}")

        if i == 0:
            y_offset += 45
            p.setFont("Helvetica-Bold", 14)
            p.setFillColorRGB(0, 0.4, 0) 
            p.drawString(60, height - y_offset, f"Total Paid (For all {len(names)} passengers): {booking.total_price:.2f} {booking.currency}")
            p.setFillColorRGB(0, 0, 0)
        box_top = height - 50
        box_bottom = height - y_offset - 30
        box_height = box_top - box_bottom
        
        p.setLineWidth(2)
        p.rect(40, box_bottom, width - 80, box_height)

        qr_data = f"TICKET: SKF-{booking.id + 1000} | NAME: {current_name} | SEAT: {current_seat}"
        qr = qrcode.QRCode(box_size=4, border=2)
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        img_buffer = io.BytesIO()
        img.save(img_buffer, format="PNG")
        img_buffer.seek(0)
        qr_image = ImageReader(img_buffer)
        
        p.drawImage(qr_image, width - 190, box_top - 180, 130, 130)
        
        p.showPage()

    p.save()
    buffer.seek(0)
    return buffer

@app.route('/')
def home(): 
    return render_template('index.html')

@app.route('/book.html')
def book_page():
    if not session.get('logged_in'):
        flash("Please log in to book a flight.", "error")
        return redirect(url_for('login_page'))
        
    from_city = request.args.get('from', '')
    to_city = request.args.get('to', '')
    date = request.args.get('date', '')
    price = request.args.get('price', '0.0')
    flight_number = request.args.get('flight', 'Unknown')
    airline = request.args.get('airline', 'Unknown Airline') 
    stops = request.args.get('stops', '0')
    trip_type = request.args.get('trip_type', 'one-way')
    return_date = request.args.get('return_date', '')
    
    return render_template('book.html', 
                           from_city=from_city, 
                           to_city=to_city, 
                           date=date, 
                           price=price, 
                           flight_number=flight_number,
                           airline=airline,
                           stops=stops,
                           trip_type=trip_type,
                           return_date=return_date)

@app.route('/search.html')
def search_page(): 
    return render_template('search.html')

@app.route('/search_flights', methods=['POST'])
def search_flights():
    origin_code = request.form.get('from_country', '').strip().upper() 
    destination_code = request.form.get('to_country', '').strip().upper()
    travel_date = request.form.get('travel_date') 
    return_date = request.form.get('return_date', '').strip()

    if len(origin_code) != 3 or len(destination_code) != 3:
        flash("Please use exact 3-letter IATA Airport Codes (e.g., DEL, BOM).", "error")
        return redirect(url_for('search_page'))

    params = {
        "engine": "google_flights",
        "departure_id": origin_code,
        "arrival_id": destination_code,
        "outbound_date": travel_date,
        "currency": "INR",
        "api_key": "8e33c6007911685345de307f19b142ae95644428a921e840534ed4bb0446ee0e" 
    }
    
    if return_date:
        params["return_date"] = return_date

    try:
        response = requests.get("https://serpapi.com/search.json", params=params)
        data = response.json()
        
        if "error" in data:
            print(f"❌ SERPAPI ERROR: {data['error']}")
            flash(f"API Connection Issue: {data['error']}", "error")
            return redirect(url_for('search_page'))
        
            raw_flights = data.get('best_flights', []) + data.get('other_flights', [])
        
        if not raw_flights:
            flash(f"No flights found between {origin_code} and {destination_code} on this date. Ensure it is a valid route (e.g., try DEL to BOM).", "error")
            return redirect(url_for('search_page'))

        api_flights = []
        carriers = {}
        unique_airlines = set()
        min_price = float('inf')
        max_price = 0.0

        for flight in raw_flights:
            price = flight.get('price', 0)
            if price == 0:
                continue 
                
            if price < min_price: min_price = price
            if price > max_price: max_price = price

            flight_segments = flight.get('flights', [])
            if not flight_segments:
                continue
                
            segments_formatted = []
            for seg in flight_segments:
                airline_name = seg.get('airline', 'Unknown Airline')
                carrier_code = airline_name[:2].upper() 
                carriers[carrier_code] = airline_name
                unique_airlines.add(carrier_code)
                
                dep_time = seg.get('departure_airport', {}).get('time', '').replace(' ', 'T') + ":00"
                arr_time = seg.get('arrival_airport', {}).get('time', '').replace(' ', 'T') + ":00"
                
                segments_formatted.append({
                    "carrierCode": carrier_code,
                    "number": seg.get('flight_number', str(random.randint(100, 999))),
                    "aircraft": {"code": seg.get('airplane', 'Jet')},
                    "departure": {
                        "iataCode": seg.get('departure_airport', {}).get('id', origin_code), 
                        "at": dep_time
                    },
                    "arrival": {
                        "iataCode": seg.get('arrival_airport', {}).get('id', destination_code), 
                        "at": arr_time
                    }
                })

            total_mins = flight.get('total_duration', 0)
            hours = total_mins // 60
            mins = total_mins % 60
            duration_str = f"PT{hours}H{mins}M"

            itineraries = [{
                "duration": duration_str,
                "segments": segments_formatted
            }]

            if return_date:
                return_segments = []
                for seg in reversed(segments_formatted):
                    return_segments.append({
                        "carrierCode": seg["carrierCode"],
                        "number": str(random.randint(100, 999)),
                        "aircraft": seg.get("aircraft", {"code": "Jet"}),
                        "departure": {
                            "iataCode": seg["arrival"]["iataCode"],
                            "at": f"{return_date}T10:00:00" 
                        },
                        "arrival": {
                            "iataCode": seg["departure"]["iataCode"],
                            "at": f"{return_date}T{min(10 + hours, 23):02}:00:00"
                        }
                    })
                itineraries.append({
                    "duration": duration_str,
                    "segments": return_segments
                })

            api_flights.append({
                "price": {"total": f"{price}"},
                "itineraries": itineraries
            })
            
        if min_price == float('inf'):
            min_price = 0.0

        return render_template('search_results.html', 
                               flights=api_flights, 
                               from_city=origin_code, 
                               to_city=destination_code,
                               carriers=carriers,
                               unique_airlines=unique_airlines, 
                               min_price=min_price,             
                               max_price=max_price)

    except Exception as e:
        print(f"API Error: {e}")
        flash("An error occurred while fetching live flights. Please try again.", "error")
        return redirect(url_for('search_page'))


@app.route('/book_flight', methods=['POST'])
def book_flight():
    if not session.get('logged_in'): 
        return redirect(url_for('login_page'))

    p_names = request.form.getlist('p_name[]')
    p_passports = [p.upper() for p in request.form.getlist('p_passport[]')]
    p_ages = request.form.getlist('p_age[]')
    p_genders = request.form.getlist('p_gender[]')
    
    for name in p_names:
        if not re.match(r"^[A-Za-z\s]+$", name):
            flash("Invalid name detected. Please use only letters.", "error")
            return redirect(request.referrer) 

    for passport in p_passports:
        if not re.match(r"^[A-Z0-9]{6,9}$", passport):
            flash("Invalid passport format.", "error")
            return redirect(request.referrer)

    all_names = ", ".join(p_names) if p_names else "Unknown"

    try:
        base_price = float(request.form.get('base_price', 0.0))
    except ValueError:
        base_price = 0.0
        
    total_cost = base_price * len(p_names)
    
    seat_letters = ['A', 'B', 'C', 'D', 'E', 'F']
    seats = []
    for _ in range(len(p_names)):
        seats.append(f"{random.randint(1, 30)}{random.choice(seat_letters)}")
    seat_string = ", ".join(seats) 
    
    new_booking = Booking(
        flight_number=request.form.get('flight_number', 'Unknown'),
        airline=request.form.get('airline', 'Unknown Airline'), 
        full_name=all_names, 
        email=request.form.get('contact_email'),
        from_country=request.form.get('from_country'),
        to_country=request.form.get('to_country'),
        date_of_journey=request.form.get('date_of_journey'),
        return_date=request.form.get('return_date'),
        passengers=len(p_names),
        passports=", ".join(p_passports),
        ages=", ".join(p_ages),
        genders=", ".join(p_genders),
        total_price=total_cost,
        currency=request.form.get('currency', 'INR'), 
        seat_number=seat_string,
        status='Pending'
    )
    
    db.session.add(new_booking)
    db.session.commit()
    
    return redirect(url_for('mock_checkout', booking_id=new_booking.id))

@app.route('/checkout/<int:booking_id>')
def mock_checkout(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    return f"""
    <div style="text-align:center; padding: 50px; font-family: sans-serif;">
        <h2>Mock Stripe Payment Gateway</h2>
        <p>Total to pay: {booking.total_price:.2f} {booking.currency}</p>
        <a href="{url_for('payment_success', booking_id=booking.id)}" style="background: green; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Simulate Successful Payment</a>
    </div>
    """

@app.route('/payment_success/<int:booking_id>')
def payment_success(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    booking.status = 'Confirmed'
    db.session.commit()
    
    flash("Payment successful! Your ticket is now Confirmed.", "success")
    return redirect(url_for('my_bookings'))

@app.route('/download_ticket/<int:booking_id>')
def download_ticket(booking_id):
    if not session.get('logged_in'): 
        return redirect(url_for('login_page'))
    
    booking = Booking.query.filter_by(id=booking_id, email=session['email']).first()
    if not booking or booking.status != 'Confirmed':
        flash("Ticket not available.", "error")
        return redirect(url_for('my_bookings'))

    buffer = generate_pdf_buffer(booking)
    return send_file(buffer, as_attachment=True, download_name=f"Skyflights_Ticket_SKF{booking.id+1000}.pdf", mimetype='application/pdf')

@app.route('/contact.html')
def contact_page(): 
    return render_template('contact.html')

@app.route('/submit_contact', methods=['POST'])
def submit_contact():
    name = request.form.get('name')
    email = request.form.get('email')
    message_text = request.form.get('message')

    new_message = Message(
        sender_name=name,
        sender_email=email,
        message_text=message_text
    )

    try:
        db.session.add(new_message)
        db.session.commit()
        flash("Thank you! Your message has been sent successfully.", "success")
    except Exception as e:
        print(f"Database error: {e}")
        flash("There was an error sending your message. Please try again.", "error")

    return redirect(url_for('contact_page'))

@app.route('/about.html')
def about_page(): 
    return render_template('about.html')

@app.route('/login.html')
def login_page(): 
    return render_template('login.html')

@app.route('/registration.html')
def registration_page(): 
    return render_template('registration.html')

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    confirm_pw = request.form.get('confirm_password')

    if not re.match(r"^[A-Za-z\s]+$", username):
        flash("Invalid name. Please use only letters.", "error")
        return redirect(url_for('registration_page'))

    if password != confirm_pw:
        flash("Passwords do not match. Please try again.", "error")
        return redirect(url_for('registration_page'))

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        flash("Email already registered! Please log in.", "error")
        return redirect(url_for('login_page'))

    hashed_pw = generate_password_hash(password)
    new_user = User(username=username, email=email, password=hashed_pw)
    
    db.session.add(new_user)
    db.session.commit()
    
    flash("Registration successful! You can now log in.", "success")
    return redirect(url_for('login_page'))

@app.route('/login', methods=['POST'])
def login():
    username_input = request.form.get('User_name')
    password_input = request.form.get('password')
    
    user = User.query.filter_by(username=username_input).first()
    
    if user and check_password_hash(user.password, password_input):
        session.update({'logged_in': True, 'username': user.username, 'email': user.email})
        flash(f"Welcome back, {user.username}!", "success")
        return redirect(url_for('home'))
    
    flash("Invalid username or password.", "error")
    return redirect(url_for('login_page'))

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            token = serializer.dumps(email, salt='password-reset-salt')
            reset_url = url_for('reset_password', token=token, _external=True)
            
            msg = MailMessage("Password Reset Request - Skyflights", recipients=[email])
            msg.body = f"""Hello {user.username},

You requested to reset your password. Please click the link below to create a new one:
{reset_url}

If you did not make this request, simply ignore this email and your password will remain unchanged.

Best,
The Skyflights Team
"""
            try:
                mail.send(msg)
            except Exception as e:
                print(f"Error sending email: {e}")
                flash("There was an issue sending the email. Please try again later.", "error")
                return redirect(url_for('forgot_password'))
            
        flash("If an account exists with that email, a reset link has been sent.", "success")
        return redirect(url_for('login_page'))
        
    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=3600)
    except SignatureExpired:
        flash("The password reset link has expired. Please request a new one.", "error")
        return redirect(url_for('forgot_password'))
    except BadSignature:
        flash("Invalid password reset link.", "error")
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        new_password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if new_password != confirm_password:
            flash("Passwords do not match. Please try again.", "error")
            return redirect(url_for('reset_password', token=token))

        user = User.query.filter_by(email=email).first()
        if user:
            user.password = generate_password_hash(new_password)
            db.session.commit()
            flash("Your password has been successfully updated! You can now log in.", "success")
            return redirect(url_for('login_page'))
        else:
            flash("User not found.", "error")
            return redirect(url_for('login_page'))

    return render_template('reset_password.html', token=token)

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for('login_page'))

@app.route('/my_bookings')
def my_bookings():
    if not session.get('logged_in'): 
        return redirect(url_for('login_page'))
    
    user_bookings = Booking.query.filter_by(email=session.get('email')).order_by(Booking.id.desc()).all()
    return render_template('my_bookings.html', bookings=user_bookings)

@app.route('/cancel_booking/<int:booking_id>', methods=['POST'])
def cancel_booking(booking_id):
    if not session.get('logged_in'): 
        return redirect(url_for('login_page'))
    
    booking = Booking.query.filter_by(id=booking_id, email=session.get('email')).first()
    if booking:
        db.session.delete(booking)
        db.session.commit()
        flash("Booking successfully canceled.", "success")
        
    return redirect(url_for('my_bookings'))

if __name__ == '__main__':
    print("Initializing database...")
    init_db() 
    print("Database initialized successfully!")
    print("Starting Flask server... Click the link below:")
    app.run(debug=True, host='127.0.0.1', port=5001)