from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector.pooling
from datetime import datetime
import os

app = Flask(__name__, template_folder="templates")
app.secret_key = os.urandom(24)  # Secure random secret key

# Database configuration with connection pooling
db_config = {
    'user': 'root',
    'password': 'root',
    'host': 'localhost',
    'database': 'student',
    'pool_name': 'task_pool',
    'pool_size': 5
}

# Create connection pool
cnxpool = mysql.connector.pooling.MySQLConnectionPool(**db_config)

def create_table():
    """Initialize database table."""
    conn = cnxpool.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''CREATE TABLE IF NOT EXISTS tasks (
                    task_id INT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    description TEXT NOT NULL,
                    due_date DATE NOT NULL,
                    completed BOOLEAN DEFAULT FALSE
                )''')
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def execute_query(query, values=None):
    """Execute database query with error handling."""
    conn = cnxpool.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, values or ())
        conn.commit()
        return cursor.rowcount
    except Exception as e:
        conn.rollback()
        app.logger.error(f"Database error: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def fetch_tasks(filter_date=None):
    """Retrieve tasks with optional date filter."""
    conn = cnxpool.get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        if filter_date:
            cursor.execute("SELECT * FROM tasks WHERE due_date = %s", (filter_date,))
        else:
            cursor.execute("SELECT * FROM tasks")
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

@app.route('/')
def list_tasks():
    """List all tasks."""
    try:
        tasks = fetch_tasks()
        return render_template('index.html', tasks=tasks)
    except Exception as e:
        app.logger.error(f"Error fetching tasks: {e}")
        flash('Error loading tasks', 'error')
        return render_template('index.html', tasks=[])

@app.route('/tasks', methods=['POST'])
def create_task():
    """Handle task creation."""
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    due_date = request.form.get('due_date', '').strip()

    if not all([title, description, due_date]):
        flash('All fields are required', 'error')
        return redirect(url_for('list_tasks'))

    try:
        due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid date format. Use YYYY-MM-DD.', 'error')
        return redirect(url_for('list_tasks'))

    try:
        execute_query(
            "INSERT INTO tasks (title, description, due_date) VALUES (%s, %s, %s)",
            (title, description, due_date)
        )
        flash('Task created successfully', 'success')
    except Exception as e:
        app.logger.error(f"Error creating task: {e}")
        flash('Error creating task', 'error')

    return redirect(url_for('list_tasks'))

@app.route('/tasks/<int:task_id>', methods=['GET', 'POST'])
def handle_task(task_id):
    """Combined edit/update operations."""
    if request.method == 'GET':
        return show_edit_form(task_id)
    return update_task(task_id)

def show_edit_form(task_id):
    """Display task edit form."""
    conn = cnxpool.get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM tasks WHERE task_id = %s", (task_id,))
        task = cursor.fetchone()
        if not task:
            flash('Task not found', 'error')
            return redirect(url_for('list_tasks'))
        return render_template('edit_task.html', task=task)
    except Exception as e:
        app.logger.error(f"Error fetching task {task_id}: {e}")
        flash('Error loading task', 'error')
        return redirect(url_for('list_tasks'))
    finally:
        cursor.close()
        conn.close()

def update_task(task_id):
    """Update existing task."""
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    due_date = request.form.get('due_date', '').strip()

    if not all([title, description, due_date]):
        flash('All fields are required', 'error')
        return redirect(url_for('handle_task', task_id=task_id))

    try:
        due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid date format. Use YYYY-MM-DD.', 'error')
        return redirect(url_for('handle_task', task_id=task_id))

    try:
        affected = execute_query(
            "UPDATE tasks SET title=%s, description=%s, due_date=%s WHERE task_id=%s",
            (title, description, due_date, task_id)
        )
        if affected == 0:
            flash('Task not found', 'error')
        else:
            flash('Task updated successfully', 'success')
    except Exception as e:
        app.logger.error(f"Error updating task {task_id}: {e}")
        flash('Error updating task', 'error')

    return redirect(url_for('list_tasks'))

@app.route('/tasks/<int:task_id>/delete', methods=['POST'])
def delete_task(task_id):
    """Handle task deletion."""
    try:
        affected = execute_query(
            "DELETE FROM tasks WHERE task_id = %s",
            (task_id,)
        )
        if affected == 0:
            flash('Task not found', 'error')
        else:
            flash('Task deleted successfully', 'success')
    except Exception as e:
        app.logger.error(f"Error deleting task {task_id}: {e}")
        flash('Error deleting task', 'error')
    return redirect(url_for('list_tasks'))

@app.route('/tasks/filter', methods=['GET'])
def filter_tasks():
    """Filter tasks by date."""
    date_str = request.args.get('date', '')
    if not date_str:
        return redirect(url_for('list_tasks'))

    try:
        filter_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        tasks = fetch_tasks(filter_date)
        return render_template('index.html', tasks=tasks)
    except ValueError:
        flash('Invalid date format. Use YYYY-MM-DD.', 'error')
        return redirect(url_for('list_tasks'))

if __name__ == "__main__":
    create_table()
    app.run(host='0.0.0.0', port=5000, debug=True)
