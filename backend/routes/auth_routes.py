from flask import Blueprint, render_template, request, redirect, url_for, session
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint('auth', __name__)

# Database configuration
db_config = {
    'user': 'root',
    'password': '2002',
    'host': 'localhost',
    'database': 'task_management',
    'auth_plugin': 'mysql_native_password'
}

# Registration Route
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        role = request.form.get('role')
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            if role == 'admin':
                cursor.execute(
                    "INSERT INTO admins (name, email, password) VALUES (%s, %s, %s)",
                    (name, email, hashed_password)
                )
            elif role == 'user':
                cursor.execute(
                    "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
                    (name, email, hashed_password)
                )
            conn.commit()
            cursor.close()
            conn.close()
            return redirect(url_for('auth.login'))
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            return "Error occurred while inserting data into the database."

    return render_template('register.html')

# Login Route
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form.get('role')
        email = request.form.get('email')
        password = request.form.get('password')

        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor(dictionary=True)
            if role == 'admin':
                cursor.execute("SELECT * FROM admins WHERE email = %s", (email,))
            elif role == 'user':
                cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()

            if user and check_password_hash(user['password'], password):
                session['email'] = email
                session['role'] = role
                if role == 'admin':
                    return redirect(url_for('auth.admin_dashboard'))
                elif role == 'user':
                    return redirect(url_for('auth.user_dashboard'))
            else:
                error_message = "Invalid email or password. Please try again."
                return render_template('login.html', error=error_message)

        except mysql.connector.Error as err:
            print(f"Error: {err}")
            error_message = "An error occurred. Please try again later."
            return render_template('login.html', error=error_message)

    return render_template('login.html')

# Admin Dashboard
@auth_bp.route('/admin/dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))
    
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM projects WHERE project_type = 'project'")
        projects = cursor.fetchall()
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return "An error occurred. Please try again later."

    return render_template('admin_dashboard.html', projects=projects, users=users)

# Create Project
@auth_bp.route('/admin/create_project', methods=['GET', 'POST'])
def create_project():
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')

        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO projects (name, description, project_type) VALUES (%s, %s, 'project')",
                (name, description)
            )
            conn.commit()
            cursor.close()
            conn.close()
            return redirect(url_for('auth.admin_dashboard'))
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            return "An error occurred while creating the project."

    return render_template('create_project.html')

# Assign Task
@auth_bp.route('/admin/assign_task', methods=['GET', 'POST'])
def assign_task():
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        task_id = request.form['task_id']
        user_id = request.form['user_id']

        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE projects SET user_id = %s WHERE id = %s AND project_type = %s',
                (user_id, task_id, 'task')
            )
            conn.commit()
            cursor.close()
            conn.close()
            return redirect(url_for('auth.assign_task'))
        except mysql.connector.Error as err:
            print(f"Error while assigning task: {err}")
            return "An error occurred while assigning the task."

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            'SELECT id, name FROM projects WHERE project_type = %s AND user_id IS NULL',
            ('task',)
        )
        tasks = cursor.fetchall()
        
        cursor.execute('SELECT id, name FROM users')
        users = cursor.fetchall()
        
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        print(f"Error while fetching tasks and users: {err}")
        return "An error occurred while fetching tasks and users."

    return render_template('assign_task.html', tasks=tasks, users=users)

# User Dashboard
@auth_bp.route('/user/dashboard')
def user_dashboard():
    if session.get('role') != 'user':
        return redirect(url_for('auth.login'))

    email = session.get('email')
    
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        user_id = cursor.fetchone()['id']
        cursor.execute("SELECT * FROM projects WHERE user_id = %s AND project_type = 'task'", (user_id,))
        tasks = cursor.fetchall()
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return "An error occurred. Please try again later."

    return render_template('user_dashboard.html', tasks=tasks)

# Update Task Status
@auth_bp.route('/user/update_task/<int:task_id>', methods=['POST'])
def update_task(task_id):
    if session.get('role') != 'user':
        return redirect(url_for('auth.login'))

    new_status = request.form.get('status')
    
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE projects SET status = %s WHERE id = %s AND user_id = (SELECT id FROM users WHERE email = %s) AND project_type = 'task'",
            (new_status, task_id, session['email'])
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        return redirect(url_for('auth.user_dashboard'))

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return "An error occurred while updating the task."
