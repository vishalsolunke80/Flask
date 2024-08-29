from flask import Flask, render_template, request, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_mail import Mail
import json

local_server = True
with open('config.json', 'r') as c:
    params = json.load(c)["params"]

app = Flask(__name__)
app.secret_key = 'super-secret-key'  # Add a secret key for session management

# Configure the mail server settings
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=params['gmail_user'],
    MAIL_PASSWORD=params['gmail_password']
)
mail = Mail(app)

# Configure the database URI
if local_server:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Model definition for the Contacts table
class Contacts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(99), nullable=False)
    email = db.Column(db.String(99), nullable=False)
    phone = db.Column(db.String(99), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(99), nullable=False)
    content = db.Column(db.String(99), nullable=False)
    slug = db.Column(db.String(22), nullable=False)
    image = db.Column(db.String(22), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)  # Corrected default value to datetime.utcnow

@app.route('/home')
@app.route('/')
def index():
    posts = Posts.query.filter_by().all()[0:params['no_of_posts']]
    return render_template('index.html', params=params, posts=posts)

@app.route('/about')
def about():
    return render_template('about.html', params=params)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session and session['user'] == params['admin_user']:
        posts=Posts.query.all()
        return render_template('dashboard.html', params=params,posts=posts)

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == params['admin_user'] and password == params['admin_password']:
            # Set session variable
            session['user'] = username
            posts=Posts.query.all()
            return render_template('dashboard.html', params=params,posts=posts)

    return render_template('login.html', params=params)

@app.route('/edit/<string:sno>', methods=['GET', 'POST'])
def edit(sno):
    if 'user' in session and session['user'] == params['admin_user']:
        if request.method=='POST':
            title=request.form.get('title')
            content=request.form.get('content')
            slug=request.form.get('slub')
            image=request.form.get('image')
        if sno==0:
            post=Posts(title=title,content=content,slug=slug,image=image)
            db.session.add(post)
            db.session.commit()
    return render_template('edit.html',params=params,sno=sno)


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')

        # Creating a new contact entry
        entry = Contacts(name=name, email=email, phone=phone, message=message)
        db.session.add(entry)
        db.session.commit()

        # Send an email notification
        mail.send_message(
            'New message from ' + name,
            sender=params['gmail_user'],
            recipients=[params['gmail_user']],
            body=message + '\n' + phone
        )

        # Render contact page with success message
        return render_template('contact.html', params=params)

    return render_template('contact.html', params=params)

@app.route('/post/<string:post_slug>', methods=['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html', params=params, post=post)

if __name__ == '__main__':
    app.run(debug=True)
