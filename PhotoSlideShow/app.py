from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, abort, jsonify, send_file, Response
import bcrypt
import mysql.connector
import os
import shutil
import base64
import jwt
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from flask_jwt_extended import verify_jwt_in_request
from PIL import Image
import io
import numpy as np
import tempfile
from io import BytesIO
from flask import after_this_request
from psycopg2.extras import DictCursor
from urllib.parse import urlparse
import psycopg2
import urllib.request
import psycopg2.errors

VIDEO_DIRECTORY = "/home/home/Desktop"

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'default_secret_key')

url = urlparse("postgresql://varun:Gte0P03BF2I_Fs9XUj5f-g@field-troll-9043.8nk.gcp-asia-southeast1.cockroachlabs.cloud:26257/group_35?sslmode=verify-full")


# db = mysql.connector.connect(
#     host="localhost",
#     user="Varun",
#     password="Varun@123",
#     database="users(change name)"
# )
# cursor = db.cursor()

db_params = {
    'dbname': url.path[1:],
    'user': url.username,
    'password': url.password,
    'host': url.hostname,
    'port': url.port
}
db = psycopg2.connect(**db_params)
cursor = db.cursor()


# cursor.execute("CREATE TABLE IF NOT EXISTS users (id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(255), email VARCHAR(255) UNIQUE NOT NULL, password VARCHAR(255))")

# cursor.execute(
#     """CREATE TABLE IF NOT EXISTS images (
#         id INT AUTO_INCREMENT PRIMARY KEY,
#         user_id INT,
#         filename VARCHAR(255),
#         file_format VARCHAR(50),
#         dimensions VARCHAR(50),
#         color_mode VARCHAR(50),
#         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#         image_data LONGBLOB NOT NULL
#     )"""
# )


def get_db_connection():
    # return mysql.connector.connect(
    #     host="localhost",
    #     user="Varun",
    #     password="Varun@123",
    #     database="users"
    # )
    return psycopg2.connect(**db_params)

def generate_jwt_token(email):
    payload = {'email': email}
    secret_key = '@#23$%^'  
    token = jwt.encode(payload, secret_key, algorithm='HS256')
    return token


def verify_jwt_token(token):
    secret_key = '@#23$%^'  
    try:
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None 
    except jwt.InvalidTokenError:
        return None  
   
       
def retrieve_background_music(background_music_id):
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT blob_data FROM AudioFiles WHERE musicid = %s", (background_music_id,))
            result = cursor.fetchone()
            if result:
                return result[0]
            else:
                return None
    except Exception as e:
        app.logger.error(f"Error retrieving background music path: {str(e)}")
        return None
    finally:
        if connection:
            connection.close()
    
   
@app.route('/redirect-home')
def redirect_home():
    verify_jwt_in_request()
    return redirect(url_for('home'))

@app.route('/success.html')
def success():
    return render_template('success.html')

@app.route('/home.html')
def home():
    return render_template('home.html')

def find_user_details(user_id):
    cursor.execute("SELECT * FROM users WHERE username = %s", (user_id,))
    user_data = cursor.fetchone()
    if user_data:
        return {'username': user_data[1], 'email': user_data[2], 'password': user_data[3]}
    return None

def hash_password(password):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

@app.route('/')
def welcome():
    return render_template('welcome.html')

@app.route('/signup.html', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirmpassword = request.form['confirm-password']
        if password==confirmpassword:
            hashed_password = hash_password(password)
            
            try:
                cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                            (username, email, hashed_password))
                db.commit()
                user_id = cursor.lastrowid  
                token = generate_jwt_token(email)
                session['user_id'] = user_id  
                return redirect(url_for('success', token=token))
            except psycopg2.errors.UniqueViolation as e:
                flash("User with this email already exists!")
        else:
            flash("Password doesn't match with Confirm-Password")        
    return render_template('signup.html')

@app.route('/successlogin')
def successlogin():
    token = request.args.get('token')
    if token:
        payload = verify_jwt_token(token)
        if payload:
            email = payload['email']
            user_data = find_user_details(email)
            return render_template('home.html', data=user_data)
        else:
            flash("Invalid or expired token", "error")
    else:
        flash("Token not provided", "error")
    return render_template('login.html')

# import pymysql.cursors

# conn = pymysql.connect(
#     host='localhost',
#     user='Varun',
#     password='Varun@123',
#     database='users',
#     cursorclass=pymysql.cursors.DictCursor
# )

@app.route('/admin')
def admin():
    # Fetch user data from database
    db=get_db_connection()
    with db.cursor() as cursor:
        cursor.execute('SELECT id, username, email, password FROM users')
        users = cursor.fetchall()
    
    # Render admin template with user data
    return render_template('admin.html', users=users)

@app.route('/login.html', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if email=='admin@email.com' and  password=='admin@123':
            return redirect(url_for('admin'))
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user_data = cursor.fetchone()

        if user_data:
            stored_password = user_data[3]
            if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                user_id = user_data[0]
                user_name = user_data[1]  
                token = generate_jwt_token(email)
                session['user_id'] = user_id
                session['user_name']  = user_name
                return redirect(url_for('successlogin', token=token))
            else:
                flash("Invalid email or password. Please try again!", 'error')
        else:
            flash("Invalid email or password. Please try again!", 'error')

    return render_template('login.html')

@app.route("/upload.html" , methods=['GET','POST'])
def start():
    return render_template('upload.html')

@app.route('/images', methods=['GET'])
def get_images():
    user_id = session.get('user_id')
    cursor.execute("SELECT filename, image_data FROM images WHERE user_id = %s", (user_id,))
    images = cursor.fetchall()
    images_data = []
    for image in images:
        filename, image_data = image
        encoded_image = base64.b64encode(image_data).decode('utf-8')
        images_data.append({'filename': filename, 'image_data': encoded_image})
    return {'images': images_data}

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    cursor.execute("SELECT image_data FROM images WHERE filename = %s", (filename,))
    image_data = cursor.fetchone()
    if image_data:
        return send_from_directory('uploads', filename, mimetype='image/*') 
    else:
        return abort(404)

@app.route('/upload', methods=['POST'])
def uploads():
    try:
        files = request.files.getlist('file-input')
        userid = session.get('user_id')
        print(userid)
        for file in files:
            print(file.mimetype)
            if not file.mimetype.startswith('image/'):
                flash("Only image files are allowed.", 'error')
                return render_template("upload.html")

            filename = file.filename
            image_data = file.read()

            image = Image.open(file)
            file_format = image.format
            dimensions = f"{image.width}x{image.height}"
            color_mode = image.mode

            cursor.execute("""
                INSERT INTO images
                (user_id, filename, image_data, file_format, dimensions, color_mode)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (userid, filename, image_data, file_format, dimensions, color_mode))
        db.commit()
    except Exception as e:
        db.rollback()
    return render_template("upload.html")


@app.route('/retrieve_audio_tracks', methods=['GET'])
def retrieve_audio_tracks():
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT musicid, file_name FROM AudioFiles")
            audio_tracks = cursor.fetchall()
            return jsonify(audio_tracks), 200

    except Exception as e:
        app.logger.error(f"Error during audio track retrieval: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred during audio track retrieval'}), 500

    finally:
        if connection:
            connection.close()


@app.route('/retrieve_audio_track/<int:audio_id>', methods=['GET'])
def retrieve_audio_track(audio_id):
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT blob_data FROM AudioFiles WHERE musicid = %s", (audio_id,))
            audio_data = cursor.fetchone()

            if audio_data:
                audio_data = audio_data[0]
                return send_file(io.BytesIO(audio_data), mimetype='audio/mpeg')
            else:
                return "Audio track not found", 404

    except Exception as e:
        app.logger.error(f"Error during audio track retrieval: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred during audio track retrieval'}), 500

    finally:
        if connection:
            connection.close()
            
@app.route('/playaudio/<int:song_id>')
def playaudio(song_id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT blob_data FROM AudioFiles WHERE musicid = %s", (song_id,))
        blob_data = cursor.fetchone()

        if blob_data:
            blob_data = blob_data[0]

            return send_file(io.BytesIO(blob_data), mimetype='audio/mpeg')
        else:
            return "Song not found", 404 

    except Exception as e:
        return f"An error occurred: {str(e)}", 500  

    finally:
        if 'connection' in locals() and connection.open:
            cursor.close()
            connection.close()            


from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip, concatenate_audioclips
from moviepy.editor import *


@app.route('/create_video', methods=['POST'])
def create_video():
    data = request.json
    selected_images = data.get('images')
    selectedDurations = data.get('durations')
    background_music_id = data.get('backgroundMusicId')
    transition_effect_name = data.get('transitionEffect', 'fadein')
    transition_duration = float(data.get('transitionDuration', 1.0))
    videoquality = data.get('videoquality','144p')
    
    
    if(videoquality == "144p"):
        width = 256
        height = 144
    if(videoquality == "240p"):
       width = 426
       height = 240
    if(videoquality == "360p"):
       width = 640
       height = 360
    if(videoquality == "480p"):
       width = 854
       height = 480
    if(videoquality == "720p"):
       width = 1280
       height = 720
    if(videoquality == "960p"):
       width = 1280
       height = 960
    if(videoquality == "1080p"):
        width = 1920
        height = 1080                        
    
    transition = {
    'Fade In': 'fadein',
    'Fade Out': 'fadeout',
    'Fade': 'fade',
    'Slide In': 'slide_in',
    'Slide Out': 'slide_out',
    }
    
    transition_effects = {
        'fadein': lambda clip: clip.fadein(transition_duration),
        'fadeout': lambda clip: clip.fadeout(transition_duration),
        'fade': lambda clip: clip.fadein(transition_duration).fadeout(transition_duration),
        'slide_in': lambda clip: clip.slide_in(transition_duration, direction='left'), 
        'slide_out': lambda clip: clip.slide_out(transition_duration, direction='right')
    }
        
    clips = []
    total_image_duration = 0
    total_transition_duration = 0

    for i, image_base64 in enumerate(selected_images):
        image_data = base64.b64decode(image_base64)
        image = Image.open(BytesIO(image_data))
        resized_image = image.resize((width, height))
        image_array = np.asarray(resized_image)
        image_clip = ImageClip(image_array).set_duration(selectedDurations[i])

        if i > 0:
            if transition_effect_name in transition:
                transition_effect = transition_effects[transition[transition_effect_name]]
                transition_clip = transition_effect(image_clip).set_duration(transition_duration)
                clips.append(transition_clip)
                total_transition_duration += transition_duration  
            else:
                transition_clip = image_clip.crossfadein(transition_duration)
                clips.append(transition_clip)
                total_transition_duration += transition_duration

        clips.append(image_clip)
        total_image_duration += selectedDurations[i]
        
    print(total_transition_duration)   
    total_video_duration = total_image_duration + total_transition_duration

    final_clip = concatenate_videoclips(clips)

    background_music_data = retrieve_background_music(background_music_id)

    with tempfile.NamedTemporaryFile(delete=False) as temp_audio_file:
        temp_audio_file.write(background_music_data)
        temp_audio_file_path = temp_audio_file.name

    background_music_clip = AudioFileClip(temp_audio_file_path)

    loop_count = int(total_video_duration // background_music_clip.duration) + 1
    looped_music_clips = [background_music_clip] * loop_count
    looped_music_clip = concatenate_audioclips(looped_music_clips)
    looped_music_clip = looped_music_clip.subclip(0, total_video_duration)


    final_clip = final_clip.set_duration(total_video_duration)
    final_clip = final_clip.set_audio(looped_music_clip)
    
    pwd = os.getcwd()
    output_folder_name = 'output'
    output_folder = os.path.join(pwd, output_folder_name)

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    video_filename = 'output.mp4'
    video_path = os.path.join(output_folder, video_filename)

    final_clip.write_videofile(video_path, codec='libx264', fps=24)

    os.remove(temp_audio_file_path)

    return url_for('get_video', filename=video_filename)
   
@app.route('/get_video/<filename>')
def get_video(filename):
    pwd = os.getcwd()
    output_folder_name = 'output'
    output_folder = os.path.join(pwd, output_folder_name)


    video_path = os.path.join(output_folder, filename)

    if os.path.exists(video_path):
        response = send_file(video_path)
        return response
    else:
        return "Video file not found", 404

@app.route('/logout')
def logout():
    session.clear()  
    return redirect(url_for('welcome')) 

@app.route("/x.html" , methods=['GET','POST'])
def st():
    return render_template('x.html')

if __name__ == '__main__':
    app.run(debug=True,port=3000)