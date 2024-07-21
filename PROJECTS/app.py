from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL database configuration
db_config = {
    'user': 'root',
    'password': 'root',
    'host': 'localhost',
    'database': 'student'
}

def create_table():
    """Creates the tasks table if it doesn't exist."""
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS tasks (
                task_id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                description TEXT NOT NULL,
                due_date DATE NOT NULL,
                completed BOOLEAN DEFAULT FALSE
            )''')

    conn.commit()
    conn.close()

def execute_query(query, values=None):
    """Executes a MySQL query."""
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    if values:
        cursor.execute(query, values)
    else:
        cursor.execute(query)

    conn.commit()
    conn.close()

def fetch_tasks():
    """Fetches tasks from the database."""
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    cursor.execute("SELECT task_id, title, description, due_date, completed FROM tasks")
    tasks = cursor.fetchall()

    conn.close()
    return tasks

def fetch_task_by_id(task_id):
    """Fetches a task by its ID."""
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    cursor.execute("SELECT title, description, due_date FROM tasks WHERE task_id = %s", (task_id,))
    task = cursor.fetchone()

    conn.close()
    return task

@app.route('/')
def index():
    create_table()
    tasks = fetch_tasks()
    return render_template('index.html', tasks=tasks)

@app.route('/create_task', methods=['POST'])
def create_task():
    title = request.form['title']
    description = request.form['description']
    due_date = request.form['due_date']

    if not title or not description or not due_date:
        flash('Please fill in all fields.', 'error')
        return redirect(url_for('index'))

    query = "INSERT INTO tasks (title, description, due_date, completed) VALUES (%s, %s, %s, %s)"
    values = (title, description, due_date, False)
    execute_query(query, values)

    flash('Task created successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/fetch_tasks', methods=['POST'])
def fetch_tasks_by_date():
    due_date = request.form['due_date']

    if not due_date:
        flash('Please enter a due date.', 'error')
        return redirect(url_for('index'))

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    cursor.execute("SELECT task_id, title, description, due_date, completed FROM tasks WHERE due_date = %s", (due_date,))
    tasks = cursor.fetchall()

    conn.close()

    if not tasks:
        flash(f'No tasks found for due date {due_date}.', 'info')

    return render_template('index.html', tasks=tasks)

@app.route('/update_task/<int:task_id>', methods=['POST'])
def update_task(task_id):
    title = request.form['title']
    description = request.form['description']
    due_date = request.form['due_date']

    if not title or not description or not due_date:
        flash('Please fill in all fields.', 'error')
        return redirect(url_for('index'))

    query = "UPDATE tasks SET title = %s, description = %s, due_date = %s WHERE task_id = %s"
    values = (title, description, due_date, task_id)
    execute_query(query, values)

    flash('Task updated successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/delete_task/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    query = "DELETE FROM tasks WHERE task_id = %s"
    execute_query(query, (task_id,))
    flash('Task deleted successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/edit_task/<int:task_id>', methods=['GET'])
def edit_task(task_id):
    task = fetch_task_by_id(task_id)
    return render_template('edit_task.html', task=task, task_id=task_id)


if __name__ == '__main__':
    app.run(debug=True)
