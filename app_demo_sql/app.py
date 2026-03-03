import uuid
import psycopg2
import psycopg2.extras
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
import os
import csv
import re

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Setup Postgres connection (configure as needed)
conn = psycopg2.connect(dbname="emo_annotation", user="neela", password="senha123", host="localhost")

# Directory to store images
IMAGE_DIR = './static/images/'
DIRECTORIES = os.listdir(IMAGE_DIR)

def custom_sort_key(filename):
    # Extract the frame number using regex
    match = re.match(r'frame(\d+)', filename)
    if match:
        return (int(match.group(1).lstrip('0') or '0'), filename)
    return (float('inf'), filename)  

def get_img_from_dir(dirs):
    ipath = os.path.join(IMAGE_DIR, dirs)
    filelist = os.listdir(ipath)
    imagelist = sorted(filelist, key=custom_sort_key)
    return imagelist

def generate_user_token():
    return str(uuid.uuid4())
    
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        username = request.form['username']
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("SELECT user_id FROM users WHERE user_name = %s", (username,))
            user = cur.fetchone()
            if not user:
                token = generate_user_token()
                cur.execute(
                        "INSERT INTO users (user_name, user_token) VALUES (%s, %s) RETURNING user_id", 
                        (username, token)
                        )
                user_id = cur.fetchone()['user_id']
                conn.commit()
            else:
                user_id = user['user_id']
                cur.execute(
                        "UPDATE users SET last_seen = CURRENT_TIMESTAMP WHERE user_id = %s", (user_id,)
                        )
                conn.commit()
            
            # After inserting or with existing user, checking the records 
            cur.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
            print("User record:", cur.fetchone())

        except Exception as e:
            conn.rollback()  # ROLLBACK TRANSACTION in case of error
            print(f"Database error: {e}")
            flash("An error occurred. Please try again.")
            return render_template('home.html', error="Database error occurred.")
        finally:
            cur.close()
        
        return redirect(url_for('dirlinks', username=username))
    return render_template('home.html')

@app.route('/dirlinks/<username>', methods=['GET', 'POST'])
def dirlinks(username):
    # List directories in the static/images folder
    #directories = [d for d in os.listdir(IMAGE_DIR) if os.path.isdir(os.path.join(IMAGE_DIR, d))]
    
    if request.method == 'POST':
        directory_name = request.form['directory_name']
        return redirect(url_for('imagelinks', username=username, directory_name=directory_name))
    return render_template('dirlinks.html', username=username, directories=DIRECTORIES)


@app.route('/imagelinks', methods=['GET', 'POST'])
def imagelinks():
    if request.method == 'POST':
        username = request.form['username']
        directory_name = request.form['directory_name']
        image = request.form['image']
        return redirect(url_for('response', username=username, directory_name=directory_name, image=image))

     # If GET request, retrieve images
    username = request.args.get('username')
    directory_name = request.args.get('directory_name')  
    return render_template('imagelinks.html', username=username, directory_name=directory_name, imagelist=get_img_from_dir(directory_name))

@app.route('/response/<directory_name>/<image>', methods=['GET','POST'])
def response(directory_name, image):
    emotions = ["raiva", "desgosto", "medo", "felicidade", "tristeza", "surpresa", "neutro", "o mesmo de antes", "indeciso"]
    username = request.args.get('username')

    if request.method == 'POST':
        if 'emotion' in request.form:
            emotion = request.form.get('emotion')
            additional_info = request.form.get('additional_info')
            try:
                cur = conn.cursor()
                # Get user_id
                cur.execute(
                        "SELECT user_id FROM users WHERE user_name = %s", (username,)
                        )
                user_res = cur.fetchone()
                if not user_res:
                     return "User not found", 400
                user_id = user_res[0]
                
                # Get or insert image
                file_path = os.path.join(IMAGE_DIR, directory_name, image)
                cur.execute(
                        "SELECT image_id FROM images WHERE file_path = %s", (file_path,)
                        )
                image_res = cur.fetchone()
                if image_res:
                    image_id = image_res[0]
                else:
                    cur.execute(
                            "INSERT INTO images (file_path, filename) VALUES (%s, %s) RETURNING image_id", 
                            (file_path, image)
                            )
                    image_id = cur.fetchone()[0]
                # Insert annotation
                cur.execute(
                        "INSERT INTO annotations (image_id, user_id, emotion_label, remark) VALUES (%s, %s, %s, %s)",
                        (image_id, user_id, emotion, additional_info)
                        )
                conn.commit()
            
                # After inserting image, confirm the record
                cur.execute("SELECT * FROM images WHERE image_id = %s", (image_id,))
                print("Image record:", cur.fetchone())
                # After inserting annotation, confirm the record
                cur.execute("SELECT * FROM annotations WHERE annotation_id = (SELECT MAX(annotation_id) FROM annotations)")
                print("Last Annotation:", cur.fetchone())

            except Exception as e:
                conn.rollback()
                print(f"Database error in response(): {e}")
                flash("Database error occurred. Please try again.")
                return render_template('response.html', username=username, emotions=emotions, directory_name=directory_name, image=image)
            finally:
                cur.close()

            return redirect(url_for('choice', username=username, directory_name=directory_name, image=image, emotion=emotion, additional_info=additional_info))

    return render_template('response.html', username=username, emotions=emotions, directory_name=directory_name, image=image)

@app.route('/choice', methods=['GET', 'POST'])
def choice():
    username = request.args.get('username')
    directory_name = request.args.get('directory_name')
    image = request.args.get('image')
    emotion = request.args.get('emotion')
    additional_info = request.args.get('additional_info')

    if request.method == 'POST':
        username = request.form.get('username')
        directory_name = request.form.get('directory_name')
        image = request.form.get('image')
        emotion = request.form.get('emotion')
        additional_info = request.form.get('additional_info')
        print("before choice, username: ",username)
        if request.form['continue'] == 'Sim':
            #username = request.args.get('username')
            print("from yes choice, username: ",username)
            return redirect(url_for('dirlinks', username=username)) # Redirect to dirlinks page
        else:
            return redirect(url_for('home'))  # Redirect back to home page
    return render_template('choice.html', username=username, directory_name=directory_name, image=image, emotion=emotion, additional_info=additional_info)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4000, debug=True)
