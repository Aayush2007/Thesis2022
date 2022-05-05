from flask import Flask, render_template, Response, jsonify, request, redirect, url_for
import cv2
import os
import json
import numpy as np
from model import actions, mp_holistic, mediapipe_detection, draw_styled_landmarks, extract_keypoints, prepareModel
from statistics import mode
import random
import time
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
scheduler = BackgroundScheduler()
camera = cv2.VideoCapture(cv2.CAP_V4L2)
question_ids = []

f = open('v2_mscoco_val2014_annotations_yesno.json', )
val_anno = json.load(f)
f.close()

f = open('v2_OpenEnded_mscoco_val2014_questions_yesno.json', )
val_questions = json.load(f)
f.close()

with open("sentiment_data", "r") as fp:
    sentiment_data = json.load(fp)

question = ''
img_path = ''
ans = ''
tweet = ''
showTweet = False
num_tasks_shown = 0
showButton = True
taskFinish = False
prolific_id = ''
session_id = ''
sub_task_time = 10
total_num_tasks = 5

no_sequences = 60  # stores number of videos for each action.
sequence_length = 50  # stores number of frames per video
start_folder = 1

label_map = {label: num for num, label in enumerate(actions)}


def getAnswer(ques_id):
    for img in val_anno:
        if img['question_id'] == ques_id:
            return img['multiple_choice_answer']
    return '-1'


def getImgQuesAns(ques_id):
    BASE_PATH = os.path.join('static', 'val2014_yesno')
    for q in val_questions:
        if q['question_id'] == ques_id:
            ques = q['question']
            answer = getAnswer(q['question_id'])
            return ques, os.path.join(BASE_PATH, 'COCO_val2014_' + str(q['image_id']).zfill(12) + '.jpg'), answer

    return 'Not found', '', '-1'


def getItemsToShow():
    global showTweet
    global question
    global img_path
    global ans
    global tweet
    global num_tasks_shown
    global taskFinish

    print(num_tasks_shown)

    prob = np.random.binomial(5, 0.5)
    if prob < 3:
        showTweet = False
        # '/static/val2014_yesno/COCO_val2014_000000393282.jpg' # "Do you see a body of water in the picture?"
        # to random picture with question, image,answer
        question, img_path, ans = getImgQuesAns(random.choice(question_ids))
    else:
        showTweet = True
        # "The audio booth is ready to blow the roof off the Comcast Center tomorrow! Are you? #MDMadness"
        tweet = random.choice(sentiment_data)['text']

    num_tasks_shown += 1
    if num_tasks_shown == total_num_tasks:
        print('Task End.')
        scheduler.remove_job('getItemsJob')
        taskFinish = True


def generate_frames():
    global camera

    sequence = []
    sentence = []
    predictions = []
    threshold = 0.90
    model = prepareModel()

    with mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5) as holistic:
        while True:
            success, frame = camera.read()

            if not success:
                break
            else:

                image, results = mediapipe_detection(frame, holistic)
                draw_styled_landmarks(image, results)

                keypoints, lh, rh = extract_keypoints(results)
                sequence.append(keypoints)
                sequence = sequence[-50:]

                if len(sequence) == 50 and (sum(lh) != 0 or sum(rh) != 0):
                    res = model.predict(np.expand_dims(sequence, axis=0))[0]
                    print(actions[np.argmax(res)])
                    print("Accuracy:", res[np.argmax(res)])
                    predictions.append(np.argmax(res))

                    if mode(predictions[-3:]) == np.argmax(res):
                        if res[np.argmax(res)] > threshold:
                            print("Accuracy:", res[np.argmax(res)])
                            sequence = []
                            if len(sentence) > 0:
                                if actions[np.argmax(res)] != sentence[-1]:
                                    sentence.append(actions[np.argmax(res)])
                            else:
                                sentence.append(actions[np.argmax(res)])

                    if len(sentence) > 5:
                        sentence = sentence[-5:]

                ret, buffer = cv2.imencode('.jpg', image)
                frame = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/_task-stuff', methods=['GET'])
def stuff():
    return jsonify(showTweet=showTweet, tweet=tweet, img_path=img_path, question=question, taskFinish=taskFinish)


@app.route('/home', methods=['GET', 'POST'])
def home():
    global showButton
    global prolific_id
    global session_id

    prolific_id = request.args.get("PROLIFIC_PID")
    session_id = request.args.get("SESSION_ID")

    if request.method == 'POST':
        # getItemsToShow()
        if scheduler.state == 2:
            scheduler.resume()
        else:
            scheduler.start()
        showButton = False

    return render_template('index.html', img_path=img_path, tweet=tweet, question=question, showTweet=showTweet,
                           showButton=showButton)


@app.route('/')
def index():
    global showButton
    global num_tasks_shown
    global showTweet
    global question
    global img_path
    global ans
    global tweet
    global taskFinish

    print('[DEBUG] call cv2.VideoCapture(0) from PID', os.getpid())
    showButton = True
    if scheduler.state != 0:
        num_tasks_shown = 0
        showTweet = False
        question = ''
        img_path = ''
        ans = ''
        tweet = ''
        taskFinish = False
        scheduler.pause()
        if scheduler.get_job(job_id='getItemsJob') is None:
            scheduler.add_job(func=getItemsToShow, trigger="interval", seconds=sub_task_time, id='getItemsJob')

    return redirect(url_for('home'))


@app.route('/video')
def video():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':

    for val in val_questions:
        question_ids.append(val['question_id'])

    scheduler.add_job(func=getItemsToShow, trigger="interval", seconds=sub_task_time, id='getItemsJob')

    app.run(debug=False, host='0.0.0.0', port=8080)

    # from waitress import serve

    # serve(app, host="0.0.0.0", port=8080)
