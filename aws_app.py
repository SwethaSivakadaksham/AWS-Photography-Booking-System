from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime
import hashlib
import os
import boto3
import uuid

from werkzeug.utils import secure_filename
from botocore.exceptions import ClientError

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# AWS Configuration
REGION = 'us-east-1'

dynamodb = boto3.resource('dynamodb', region_name=REGION)
s3 = boto3.client('s3', region_name=REGION)
# SNS client removed — notifications will use local logging/prints

# DynamoDB Tables (Create these tables in DynamoDB manually)
users_table = dynamodb.Table('Users')
photographers_table = dynamodb.Table('Photographers')
bookings_table = dynamodb.Table('Bookings')
admin_users_table = dynamodb.Table('AdminUsers')
photographer_users_table = dynamodb.Table('PhotographerUsers')

# SNS removed: using local print/logging for notifications

# S3 Configuration
S3_BUCKET = 'your-photography-bucket'
S3_REGION = 'us-east-1'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def send_notification(subject, message):
    print(f"Notification: {subject} - {message}")

def upload_to_s3(file, folder):
    if not file or file.filename == '':
        return None
    
    if not allowed_file(file.filename):
        return None
    
    try:
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        key = f"{folder}/{timestamp}_{filename}"
        
        s3.upload_fileobj(
            file,
            S3_BUCKET,
            key,
            ExtraArgs={'ContentType': file.content_type}
        )
        
        return f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{key}"
    except ClientError as e:
        print(f"Error uploading to S3: {e}")
        return None

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Local in-memory fallback data (from app.py) — used when DynamoDB/Tables aren't available
users_db = {}

photographers_db = {
    1: {
        'name': 'John Smith',
        'specialization': 'Wedding Photography',
        'rate': 10000,
        'contact': 'john@photographer.com',
        'bio': 'Experienced wedding photographer with passion for capturing emotional moments',
        'image': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&h=400&fit=crop',
        'experience': 12,
        'location': 'Mumbai',
        'skills': ['Wedding Ceremonies', 'Reception Events', 'Prenup Shoots', 'Same-Day Edits'],
        'availability': ['Monday', 'Friday', 'Saturday', 'Sunday']
    },
    2: {
        'name': 'Sarah Johnson',
        'specialization': 'Portrait Photography',
        'rate': 8000,
        'contact': 'sarah@photographer.com',
        'bio': 'Professional portrait photographer specializing in headshots and personal branding',
        'image': 'https://images.unsplash.com/photo-1602233158242-3ba0ac4d2167?q=80&w=736&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',
        'experience': 8,
        'location': 'Bangalore',
        'skills': ['Headshots', 'Personal Branding', 'Studio Portraits', 'Natural Light'],
        'availability': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    },
    3: {
        'name': 'Mike Davis',
        'specialization': 'Event Photography',
        'rate': 15000,
        'contact': 'mike@photographer.com',
        'bio': 'Dynamic event photographer capturing energy and moments at corporate and private events',
        'image': 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=400&h=400&fit=crop',
        'experience': 10,
        'location': 'Delhi',
        'skills': ['Corporate Events', 'Product Launches', 'Conferences', 'Live Coverage'],
        'availability': ['Thursday', 'Friday', 'Saturday', 'Sunday']
    },
    4: {
        'name': 'Emily Rodriguez',
        'specialization': 'Family Photography',
        'rate': 9000,
        'contact': 'emily@photographer.com',
        'bio': 'Specializing in capturing beautiful family moments and creating lasting memories',
        'image': 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=400&h=400&fit=crop',
        'experience': 9,
        'location': 'Pune',
        'skills': ['Family Portraits', 'Maternity', 'Newborn', 'Children Photography'],
        'availability': ['Monday', 'Tuesday', 'Wednesday', 'Saturday', 'Sunday']
    },
    5: {
        'name': 'David Chen',
        'specialization': 'Corporate Photography',
        'rate': 14000,
        'contact': 'david@photographer.com',
        'bio': 'Expert in corporate events, executive headshots, and business photography',
        'image': 'https://images.unsplash.com/photo-1615109398623-88346a601842?q=80&w=1974&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',
        'experience': 11,
        'location': 'Hyderabad',
        'skills': ['Executive Headshots', 'Corporate Events', 'Office Shoots', 'Annual Reports'],
        'availability': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    },
    6: {
        'name': 'Jessica Williams',
        'specialization': 'Fashion Photography',
        'rate': 20000,
        'contact': 'jessica@photographer.com',
        'bio': 'Professional fashion photographer with experience in editorial and commercial work',
        'image': 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=400&h=400&fit=crop',
        'experience': 13,
        'location': 'Mumbai',
        'skills': ['Fashion Shoots', 'Editorial', 'Lookbooks', 'Product Photography'],
        'availability': ['Wednesday', 'Thursday', 'Friday', 'Saturday']
    },
    7: {
        'name': 'Robert Thompson',
        'specialization': 'Real Estate Photography',
        'rate': 10000,
        'contact': 'robert@photographer.com',
        'bio': 'Specializing in property photography, drone shots, and virtual tours',
        'image': 'https://plus.unsplash.com/premium_photo-1689977927774-401b12d137d6?q=80&w=1170&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',
        'experience': 7,
        'location': 'Gurgaon',
        'skills': ['Property Shoots', 'Aerial Photography', 'Virtual Tours', '3D Visualization'],
        'availability': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    },
    8: {
        'name': 'Amanda Foster',
        'specialization': 'Nature & Landscape Photography',
        'rate': 9000,
        'contact': 'amanda@photographer.com',
        'bio': 'Capturing stunning landscapes and wildlife in their natural habitat',
        'image': 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?q=80&w=688&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',
        'experience': 6,
        'location': 'Shimla',
        'skills': ['Landscape', 'Wildlife', 'Adventure Photography', 'Travel Photography'],
        'availability': ['Thursday', 'Friday', 'Saturday', 'Sunday']
    },
    9: {
        'name': 'Chris Martinez',
        'specialization': 'Sports Photography',
        'rate': 13000,
        'contact': 'chris@photographer.com',
        'bio': 'Dynamic sports photographer covering all types of athletic events',
        'image': 'https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=400&h=400&fit=crop',
        'experience': 9,
        'location': 'Bangalore',
        'skills': ['Sports Events', 'Action Photography', 'Coaching Sessions', 'Tournaments'],
        'availability': ['Saturday', 'Sunday']
    },
    10: {
        'name': 'Lauren Mitchell',
        'specialization': 'Baby & Newborn Photography',
        'rate': 11000,
        'contact': 'lauren@photographer.com',
        'bio': 'Gentle and creative approach to capturing precious baby moments',
        'image': 'https://plus.unsplash.com/premium_photo-1670282393309-70fd7f8eb1ef?q=80&w=687&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',
        'experience': 8,
        'location': 'Chennai',
        'skills': ['Newborn', 'Baby Portraits', 'Milestone Sessions', 'Maternity'],
        'availability': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Saturday']
    }
}

bookings_db = {}

next_user_id = 1
next_booking_id = 1

def get_next_user_id():
    global next_user_id
    user_id = next_user_id
    next_user_id += 1
    return user_id

def get_next_booking_id():
    global next_booking_id
    booking_id = next_booking_id
    next_booking_id += 1
    return booking_id

admin_users = {
    'admin': {
        'password': hash_password('admin123'),
        'user_type': 'admin'
    }
}

photographer_users = {
    'john_smith': {
        'password': hash_password('john123'),
        'photographer_id': 1,
        'user_type': 'photographer'
    },
    'sarah_johnson': {
        'password': hash_password('sarah123'),
        'photographer_id': 2,
        'user_type': 'photographer'
    }
}

def user_exists(username):
    try:
        response = users_table.get_item(Key={'username': username})
        if 'Item' in response:
            return True
    except ClientError as e:
        print(f"Error checking user (DynamoDB): {e}")

    # Fallback to local in-memory users
    return any(u.get('username') == username for u in users_db.values())

def email_exists(email):
    try:
        # DynamoDB scan
        response = users_table.scan(FilterExpression='email = :email', ExpressionAttributeValues={':email': email})
        return len(response.get('Items', [])) > 0
    except ClientError as e:
        print(f"Error checking email (DynamoDB): {e}")

    # Fallback to local users
    return any(u.get('email') == email for u in users_db.values())

def authenticate_user(username, password):
    try:
        response = users_table.get_item(Key={'username': username})
        if 'Item' in response:
            user = response['Item']
            if user['password'] == hash_password(password):
                return username
        return None
    except ClientError as e:
        print(f"Error authenticating user (DynamoDB): {e}")
    # Fallback to local users
    for u in users_db.values():
        if u.get('username') == username and u.get('password') == hash_password(password):
            return username
    return None
    # Fallback to local users
    for u in users_db.values():
        if u.get('username') == username and u.get('password') == hash_password(password):
            return username
    return None

def get_user_by_username(username):
    try:
        response = users_table.get_item(Key={'username': username})
        return response.get('Item')
    except ClientError as e:
        print(f"Error getting user (DynamoDB): {e}")
    # Fallback to local users
    for u in users_db.values():
        if u.get('username') == username:
            return u
    return None
    # Fallback to local users
    for u in users_db.values():
        if u.get('username') == username:
            return u
    return None

def get_photographer_by_id(photographer_id):
    try:
        response = photographers_table.get_item(Key={'id': photographer_id})
        return response.get('Item')
    except ClientError as e:
        print(f"Error getting photographer (DynamoDB): {e}")
    # Fallback to local photographers
    # Try direct key (string), then int conversion
    if photographer_id in photographers_db:
        return photographers_db[photographer_id]
    try:
        pid = int(photographer_id)
        return photographers_db.get(pid)
    except Exception:
        return None
    # Fallback to local photographers
    # Try direct key (string), then int conversion
    if photographer_id in photographers_db:
        return photographers_db[photographer_id]
    try:
        pid = int(photographer_id)
        return photographers_db.get(pid)
    except Exception:
        return None

def get_user_bookings(username):
    try:
        response = bookings_table.scan(
            FilterExpression='username = :username',
            ExpressionAttributeValues={':username': username}
        )
        bookings = response.get('Items', [])
        
        for booking in bookings:
            photographer = get_photographer_by_id(booking['photographer_id'])
            booking['photographer_name'] = photographer['name'] if photographer else 'Unknown'
        
        return bookings
    except ClientError as e:
        print(f"Error getting user bookings (DynamoDB): {e}")
    # Fallback to local bookings (local stores user by user_id or username)
    result = []
    for bid, booking in bookings_db.items():
        if booking.get('username') == username or booking.get('user_id') == username:
            b = booking.copy()
            b['booking_id'] = bid
            photographer = get_photographer_by_id(b.get('photographer_id'))
            b['photographer_name'] = photographer['name'] if photographer else 'Unknown'
            result.append(b)
    return result
    # Fallback to local bookings (local stores user by user_id or username)
    result = []
    for bid, booking in bookings_db.items():
        if booking.get('username') == username or booking.get('user_id') == username:
            b = booking.copy()
            b['booking_id'] = bid
            photographer = get_photographer_by_id(b.get('photographer_id'))
            b['photographer_name'] = photographer['name'] if photographer else 'Unknown'
            result.append(b)
    return result

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not username or not email or not password or not confirm_password:
            return render_template('register.html', error='All fields are required')

        if user_exists(username):
            return render_template('register.html', error='Username already exists')

        if email_exists(email):
            return render_template('register.html', error='Email already registered')

        if password != confirm_password:
            return render_template('register.html', error='Passwords do not match')

        if len(password) < 6:
            return render_template('register.html', error='Password must be at least 6 characters')

        try:
            users_table.put_item(Item={
                'username': username,
                'email': email,
                'password': hash_password(password),
                'user_type': 'customer',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            
            send_notification("New Customer Registration", f"User {username} has registered.")
            return redirect(url_for('login'))
        except ClientError as e:
            print(f"Error registering user (DynamoDB): {e}")
            # Fallback: store user in local in-memory DB
            user_id = get_next_user_id()
            users_db[user_id] = {
                'username': username,
                'email': email,
                'password': hash_password(password),
                'user_type': 'customer',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            send_notification("New Customer Registration (local)", f"User {username} has registered (local fallback).")
            return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login')
def login():
    return render_template('login_select.html')

@app.route('/login/customer', methods=['GET', 'POST'])
def login_customer():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            return render_template('login_customer.html', error='Username and password required')

        user = authenticate_user(username, password)
        if user is None:
            return render_template('login_customer.html', error='Invalid username or password')

        user_data = get_user_by_username(username)
        if user_data['user_type'] != 'customer':
            return render_template('login_customer.html', error='Please use the appropriate login portal for your account type')

        session['username'] = username
        session['user_type'] = 'customer'
        
        send_notification("Customer Login", f"User {username} has logged in.")
        return redirect(url_for('photographers'))

    return render_template('login_customer.html')

@app.route('/login/photographer', methods=['GET', 'POST'])
def login_photographer():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            return render_template('login_photographer.html', error='Username and password required')

        try:
            response = photographer_users_table.get_item(Key={'username': username})
            if 'Item' in response:
                photographer_info = response['Item']
            else:
                # Not found in DynamoDB, fallback to local
                photographer_info = photographer_users.get(username)

            if not photographer_info or photographer_info.get('password') != hash_password(password):
                return render_template('login_photographer.html', error='Invalid username or password')

            photographer = get_photographer_by_id(photographer_info['photographer_id'])
            session['username'] = username
            session['photographer_id'] = photographer_info['photographer_id']
            session['photographer_name'] = photographer['name'] if photographer else username
            session['user_type'] = 'photographer'

            send_notification("Photographer Login", f"Photographer {username} has logged in.")
            return redirect(url_for('photographer_dashboard'))
        except ClientError as e:
            print(f"Error during login (DynamoDB): {e}")
            # Fallback to local photographer_users
            photographer_info = photographer_users.get(username)
            if not photographer_info or photographer_info.get('password') != hash_password(password):
                return render_template('login_photographer.html', error='Invalid username or password')

            photographer = get_photographer_by_id(photographer_info['photographer_id'])
            session['username'] = username
            session['photographer_id'] = photographer_info['photographer_id']
            session['photographer_name'] = photographer['name'] if photographer else username
            session['user_type'] = 'photographer'

            send_notification("Photographer Login (local)", f"Photographer {username} has logged in (local fallback).")
            return redirect(url_for('photographer_dashboard'))

    return render_template('login_photographer.html')

@app.route('/login/admin', methods=['GET', 'POST'])
def login_admin():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            return render_template('login_admin.html', error='Username and password required')

        try:
            response = admin_users_table.get_item(Key={'username': username})
            if 'Item' in response:
                admin_info = response['Item']
            else:
                admin_info = admin_users.get(username)

            if not admin_info or admin_info.get('password') != hash_password(password):
                return render_template('login_admin.html', error='Invalid username or password')

            session['username'] = username
            session['user_type'] = 'admin'

            send_notification("Admin Login", f"Admin {username} has logged in.")
            return redirect(url_for('admin_dashboard'))
        except ClientError as e:
            print(f"Error during admin login (DynamoDB): {e}")
            # Fallback to local admin_users
            admin_info = admin_users.get(username)
            if not admin_info or admin_info.get('password') != hash_password(password):
                return render_template('login_admin.html', error='Invalid username or password')

            session['username'] = username
            session['user_type'] = 'admin'

            send_notification("Admin Login (local)", f"Admin {username} has logged in (local fallback).")
            return redirect(url_for('admin_dashboard'))

    return render_template('login_admin.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/photographers')
def photographers():
    if 'username' not in session or session.get('user_type') != 'customer':
        return redirect(url_for('login'))

    try:
        response = photographers_table.scan()
        photographers_list = response.get('Items', [])
        return render_template('photographers.html', photographers=photographers_list)
    except ClientError as e:
        print(f"Error getting photographers (DynamoDB): {e}")
    # Fallback to local photographers
    photographers_list = []
    for pid, p in photographers_db.items():
        p_copy = p.copy()
        p_copy['id'] = pid
        photographers_list.append(p_copy)
    return render_template('photographers.html', photographers=photographers_list)

@app.route('/book/<photographer_id>', methods=['GET', 'POST'])
def book(photographer_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    try:
        photographer = get_photographer_by_id(photographer_id)
        if not photographer:
            return redirect(url_for('photographers'))

        if request.method == 'POST':
            booking_date = request.form.get('booking_date', '').strip()
            booking_time = request.form.get('booking_time', '').strip()
            location = request.form.get('location', '').strip()
            notes = request.form.get('notes', '').strip()

            if not booking_date or not booking_time or not location:
                return render_template('book.html', photographer=photographer, 
                                     photographer_id=photographer_id, 
                                     error='Date, time, and location are required')

            booking_date_obj = datetime.strptime(booking_date, '%Y-%m-%d')
            day_name = booking_date_obj.strftime('%A')
            
            if day_name not in photographer.get('availability', []):
                available_days = ', '.join(photographer.get('availability', []))
                return render_template('book.html', photographer=photographer, 
                                     photographer_id=photographer_id, 
                                     error=f'Photographer is not available on {day_name}. Available days: {available_days}')

            booking_id = str(uuid.uuid4())
            try:
                bookings_table.put_item(Item={
                    'booking_id': booking_id,
                    'username': session['username'],
                    'photographer_id': photographer_id,
                    'date': booking_date,
                    'time': booking_time,
                    'location': location,
                    'notes': notes,
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'status': 'Pending'
                })
            except ClientError as e:
                print(f"Error creating booking (DynamoDB): {e}")
                # Fallback: store booking locally
                bookings_db[booking_id] = {
                    'username': session.get('username'),
                    'photographer_id': photographer_id,
                    'date': booking_date,
                    'time': booking_time,
                    'location': location,
                    'notes': notes,
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'status': 'Pending'
                }

            send_notification("New Booking", f"Booking {booking_id} created for photographer {photographer['name']}")
            return redirect(url_for('dashboard'))

        return render_template('book.html', photographer=photographer, photographer_id=photographer_id)
    except ClientError as e:
        print(f"Error during booking: {e}")
        return render_template('book.html', photographer={}, photographer_id=photographer_id, error='Booking failed. Please try again.')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    try:
        bookings = get_user_bookings(session['username'])
        return render_template('dashboard.html', bookings=bookings)
    except ClientError as e:
        print(f"Error getting dashboard: {e}")
        return render_template('dashboard.html', bookings=[], error='Failed to load dashboard')

@app.route('/photographer-dashboard')
def photographer_dashboard():
    if 'username' not in session or session.get('user_type') != 'photographer':
        return redirect(url_for('login'))

    try:
        response = bookings_table.scan()
        all_bookings = response.get('Items', [])
        return render_template('photographer_dashboard.html', bookings=all_bookings)
    except ClientError as e:
        print(f"Error getting photographer dashboard (DynamoDB): {e}")
    # Fallback to local bookings_db
    all_bookings = []
    for bid, booking in bookings_db.items():
        b = booking.copy()
        b['booking_id'] = bid
        all_bookings.append(b)
    return render_template('photographer_dashboard.html', bookings=all_bookings)

@app.route('/admin-dashboard')
def admin_dashboard():
    if 'username' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('login_admin'))

    try:
        users_response = users_table.scan()
        photographers_response = photographers_table.scan()
        bookings_response = bookings_table.scan()

        users = users_response.get('Items', [])
        photographers = photographers_response.get('Items', [])
        bookings = bookings_response.get('Items', [])

        total_users = len(users)
        customer_users = sum(1 for u in users if u.get('user_type') == 'customer')
        total_photographers = len(photographers)
        total_bookings = len(bookings)

        stats = {
            'total_users': total_users,
            'customer_users': customer_users,
            'total_photographers': total_photographers,
            'total_bookings': total_bookings
        }

        return render_template('admin_dashboard.html', stats=stats)
    except ClientError as e:
        print(f"Error getting admin dashboard (DynamoDB): {e}")
    # Fallback to local in-memory stats
    users = list(users_db.values())
    photographers = list(photographers_db.values())
    bookings = list(bookings_db.values())

    total_users = len(users)
    customer_users = sum(1 for u in users if u.get('user_type') == 'customer')
    total_photographers = len(photographers)
    total_bookings = len(bookings)

    stats = {
        'total_users': total_users,
        'customer_users': customer_users,
        'total_photographers': total_photographers,
        'total_bookings': total_bookings
    }

    return render_template('admin_dashboard.html', stats=stats)

@app.route('/admin/photographers')
def admin_photographers():
    if 'username' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('login_admin'))

    try:
        response = photographers_table.scan()
        photographers_list = response.get('Items', [])
        return render_template('admin_photographers.html', photographers=photographers_list)
    except ClientError as e:
        print(f"Error getting photographers (DynamoDB): {e}")
    # Fallback to local photographers
    photographers_list = []
    for pid, p in photographers_db.items():
        p_copy = p.copy()
        p_copy['id'] = pid
        photographers_list.append(p_copy)
    return render_template('admin_photographers.html', photographers=photographers_list)

@app.route('/admin/photographer/add', methods=['GET', 'POST'])
def admin_add_photographer():
    if 'username' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('login_admin'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        specialization = request.form.get('specialization', '').strip()
        rate = request.form.get('rate', '').strip()
        contact = request.form.get('contact', '').strip()
        bio = request.form.get('bio', '').strip()
        experience = request.form.get('experience', '').strip()
        location = request.form.get('location', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        skills = request.form.get('skills', '').strip()
        availability = request.form.getlist('availability')
        image_file = request.files.get('image')

        if not all([name, specialization, rate, contact, bio, experience, location, username, password]):
            return render_template('admin_add_photographer.html', error='All fields except image are required')

        # Check if photographer username already exists (DynamoDB first, then local)
        try:
            response = photographer_users_table.get_item(Key={'username': username})
            if 'Item' in response:
                return render_template('admin_add_photographer.html', error='Username already exists')
        except ClientError as e:
            print(f"Error checking photographer username (DynamoDB): {e}")
            if username in photographer_users:
                return render_template('admin_add_photographer.html', error='Username already exists')

        try:
            rate = int(rate)
            experience = int(experience)
        except ValueError:
            return render_template('admin_add_photographer.html', error='Rate and experience must be numbers')

        if len(password) < 6:
            return render_template('admin_add_photographer.html', error='Password must be at least 6 characters')

        try:
            photographer_id = str(uuid.uuid4())
            image_url = None

            # Upload image to S3 if provided
            if image_file and image_file.filename:
                image_url = upload_to_s3(image_file, 'photographers')
                if not image_url:
                    return render_template('admin_add_photographer.html', error='Failed to upload image')

            # Add photographer to DynamoDB
            photographers_table.put_item(Item={
                'id': photographer_id,
                'name': name,
                'specialization': specialization,
                'rate': rate,
                'contact': contact,
                'bio': bio,
                'image': image_url or 'https://via.placeholder.com/400x400?text=' + name.replace(' ', '+'),
                'experience': experience,
                'location': location,
                'skills': [s.strip() for s in skills.split(',')] if skills else [],
                'availability': availability if availability else ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
            })

            # Add photographer user credentials to DynamoDB
            photographer_users_table.put_item(Item={
                'username': username,
                'password': hash_password(password),
                'photographer_id': photographer_id,
                'user_type': 'photographer'
            })

            send_notification("New Photographer Added", f"Photographer {name} has been added to the system.")
            return redirect(url_for('admin_photographers'))
        except ClientError as e:
            print(f"Error adding photographer to DynamoDB: {e}")
            # Fallback: add locally
            next_photo_id = max(photographers_db.keys()) + 1 if photographers_db else 1
            photographers_db[next_photo_id] = {
                'name': name,
                'specialization': specialization,
                'rate': rate,
                'contact': contact,
                'bio': bio,
                'image': image_file.filename if image_file and image_file.filename else 'https://via.placeholder.com/400x400?text=' + name.replace(' ', '+'),
                'experience': experience,
                'location': location,
                'skills': [s.strip() for s in skills.split(',')] if skills else [],
                'availability': availability if availability else ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
            }
            photographer_users[username] = {
                'password': hash_password(password),
                'photographer_id': next_photo_id,
                'user_type': 'photographer'
            }
            send_notification("New Photographer Added (local)", f"Photographer {name} has been added locally.")
            return redirect(url_for('admin_photographers'))

    return render_template('admin_add_photographer.html')

@app.route('/admin/photographer/<photographer_id>/delete', methods=['POST'])
def admin_delete_photographer(photographer_id):
    if 'username' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('login_admin'))

    try:
        photographers_table.delete_item(Key={'id': photographer_id})
        send_notification("Photographer Deleted", f"Photographer {photographer_id} has been removed.")
        return redirect(url_for('admin_photographers'))
    except ClientError as e:
        print(f"Error deleting photographer (DynamoDB): {e}")
        # Fallback: attempt to delete from local photographers_db
        try:
            pid = int(photographer_id)
            if pid in photographers_db:
                del photographers_db[pid]
        except Exception:
            # if not int or not present, ignore
            pass
        send_notification("Photographer Deleted (local)", f"Photographer {photographer_id} removed locally.")
        return redirect(url_for('admin_photographers'))

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
