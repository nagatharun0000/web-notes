from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'secret123'  # Used to manage session securely
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

# Model for users
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

# Model for notes
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

# Redirect from homepage to login
@app.route('/')
def home():
    return redirect('/login')

# Signup page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        uname = request.form['username']
        pwd = request.form['password']
        if User.query.filter_by(username=uname).first():
            return "Username already exists!"
        hashed_pwd = generate_password_hash(pwd)
        new_user = User(username=uname, password=hashed_pwd)
        db.session.add(new_user)
        db.session.commit()
        return redirect('/login')
    return render_template('register.html')

# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uname = request.form['username']
        pwd = request.form['password']
        user = User.query.filter_by(username=uname).first()
        if user and check_password_hash(user.password, pwd):
            session['user_id'] = user.id
            return redirect('/notes')
        else:
            return "Invalid credentials!"
    return render_template('login.html')

# Notes page
@app.route('/notes', methods=['GET', 'POST'])
def notes():
    if 'user_id' not in session:
        return redirect('/login')
    user_id = session['user_id']
    if request.method == 'POST':
        content = request.form['note']
        new_note = Note(content=content, user_id=user_id)
        db.session.add(new_note)
        db.session.commit()
    notes = Note.query.filter_by(user_id=user_id).all()
    return render_template('notes.html', notes=notes)

@app.route('/delete_note/<int:note_id>', methods=['POST'])
def delete_note(note_id):
    if 'user_id' not in session:
        return redirect('/login')

    note = Note.query.get(note_id)
    if note and note.user_id == session['user_id']:
        db.session.delete(note)
        db.session.commit()
    return redirect('/notes')

# Logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect('/login')

@app.route('/edit_note/<int:note_id>', methods=['GET', 'POST'])
def edit_note(note_id):
    if 'user_id' not in session:
        return redirect('/login')

    note = Note.query.get(note_id)
    if note.user_id != session['user_id']:
        return "Unauthorized", 403

    if request.method == 'POST':
        new_content = request.form['updated_note']
        note.content = new_content
        db.session.commit()
        return redirect('/notes')

    return render_template('edit_note.html', note=note)

# Run the app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
