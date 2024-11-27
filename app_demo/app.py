""" Web Application to render images and emotion labels """
import csv
import os
import re
from flask import Flask, flash, redirect, render_template, request, url_for

app = Flask(__name__)

# path to directories where images are stored
IMAGE_DIR = './static/images/'

DIRECTORIES = os.listdir(IMAGE_DIR)

def custom_sort_key(filename):
    """ sort frames alphanumerically using regex """
    match = re.match(r'frame(\d+)', filename)
    if match:
        return (int(match.group(1).lstrip('0') or '0'), filename)
    return (float('inf'), filename)

def get_img_from_dir(selected_dir):
    """ get sorted imagelist given directory name """
    ipath = os.path.join(IMAGE_DIR, selected_dir)
    filelist = os.listdir(ipath)
    imagelist = sorted(filelist, key = custom_sort_key)
    return imagelist

@app.route('/', methods=['GET', 'POST'])
def home():
    """ Page 1: web app home page """
    if request.method == 'POST':
        username = request.form['username']
        return redirect(url_for('dirlinks',username=username))
    return render_template('home.html')

@app.route('/dirlinks/<username>', methods=['GET', 'POST'])
def dirlinks(username):
    """ Page 2: displays list of directories """    
    if request.method == 'POST':
        directory_name = request.form['directory_name']
        return redirect(url_for('imagelinks', username=username, directory_name=directory_name))
    return render_template('dirlinks.html', username=username, directories=DIRECTORIES)

@app.route('/imagelinks', methods=['GET', 'POST'])
def imagelinks():
    """ Page 3: display list of images from chosen directory """
    if request.method == 'POST':
        username = request.form['username']
        directory_name = request.form['directory_name']
        image = request.form['image']
        return redirect(url_for('response', username=username, directory_name=directory_name, image=image))
    # when request is GET:
    username = request.args.get('username')
    directory_name = request.args.get('directory_name')
    return render_template('imagelinks.html', username=username, directory_name=directory_name, imagelist=get_img_from_dir(directory_name))

@app.route('/response/<directory_name>/<image>', methods=['GET','POST'])
def response(directory_name, image):
    """ Page 4: render image and note user response """
    emotions = ["raiva", "desgosto", "medo", "felicidade", "tristeza", "surpresa", "neutro", "o mesmo de antes", "indeciso"]
    username = request.args.get('username')
    if request.method == 'POST':
        # get user response
        if 'emotion' in request.form:
            emotion = request.form.get('emotion')
            additional_info = request.form.get('additional_info')
            # Save responses to CSV
            with open('data/user_responses.csv', 'a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([username, directory_name, image, emotion, additional_info])
            return redirect(url_for('choice', username=username, directory_name=directory_name, image=image, 
                                    emotion=emotion, additional_info=additional_info))
    return render_template('response.html', username=username, emotions=emotions, directory_name=directory_name, image=image)
 
@app.route('/choice', methods=['GET', 'POST'])
def choice():
    """ Page 5: display earlier response and ask whether wish to continue """
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
        if request.form['continue'] == 'Sim':
            return redirect(url_for('dirlinks', username=username))  # Redirect to dirlinks page
        else:
            return redirect(url_for('home')) # Redirect back to home page
    return render_template('choice.html', username=username, directory_name=directory_name, image=image, emotion=emotion, additional_info=additional_info)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
