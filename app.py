from flask import Flask, render_template, request, redirect, url_for, session, flash
import psycopg2
import psycopg2.extras
from flask_bcrypt import Bcrypt
import cloudinary
import cloudinary.uploader
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Configure Cloudinary
cloudinary.config(
    cloud_name='dqodwa97j',
    api_key='735942196894695',
    api_secret='*********************************'
)

# PostgreSQL DB Connection
def get_db_connection():
    return psycopg2.connect(
        host="gondola.proxy.rlwy.net",
        database="railway",
        user="postgres",
        password="cyGJPsjtAKghabRPsqcXaBGYQGTLXMse",
        port="18846",
        cursor_factory=psycopg2.extras.DictCursor
    )

@app.route('/')
def home():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT news_posts.*, users.username FROM news_posts JOIN users ON news_posts.user_id = users.id ORDER BY timestamp DESC")
    posts = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_pw = Bcrypt().generate_password_hash(password).decode('utf-8')

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                    (username, email, hashed_pw))
        conn.commit()
        cur.close()
        conn.close()

        flash('Registration successful!', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user and Bcrypt().check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = user.get('is_admin', False)
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/post', methods=['GET', 'POST'])
def post_news():
    if 'user_id' not in session:
        flash('Login required to post news.', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        source_link = request.form['source_link']
        image = request.files['image']
        video = request.files['video']
        user_id = session['user_id']

        image_path = None
        video_path = None

        if image and image.filename:
            img_upload = cloudinary.uploader.upload(image, folder="news_images")
            image_path = img_upload['secure_url']

        if video and video.filename:
            vid_upload = cloudinary.uploader.upload_large(video, folder="news_videos", resource_type="video")
            video_path = vid_upload['secure_url']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""INSERT INTO news_posts (user_id, title, description, source_link, image_path, video_path)
                        VALUES (%s, %s, %s, %s, %s, %s)""",
                    (user_id, title, description, source_link, image_path, video_path))
        conn.commit()
        cur.close()
        conn.close()

        flash('News posted successfully and pending verification.', 'success')
        return redirect(url_for('home'))

    return render_template('post_news.html')

if __name__ == '__main__':
    app.run(debug=True)
