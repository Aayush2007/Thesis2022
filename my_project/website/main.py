from flask import Flask, render_template, Response, jsonify, request, redirect, url_for, make_response, session
import os
import json
import numpy as np
from model import actions, prepareModel
from statistics import mode
import random
from datetime import datetime
import google.cloud.logging
from google.cloud import storage
import string

client = storage.Client(project="seventh-port-334508")
bucket = client.bucket("seventh-port-334508.appspot.com")

log_client = google.cloud.logging.Client(project="seventh-port-334508", )
log_client.setup_logging()

app = Flask(__name__)
survey_link = 'https://docs.google.com/forms/d/e/1FAIpQLSeNoKy0JEkgAipSI3SS8R4TnzOLX0o6kRaDr0uop8EZlMS2MA' \
              '/viewform?usp=pp_url&entry.1722510161='
question_ids = []

f = open('v2_mscoco_val2014_annotations_yesno_refined.json', )
val_anno = json.load(f)
f.close()

f = open('v2_OpenEnded_mscoco_val2014_questions_yesno_refined.json', )
val_questions = json.load(f)
f.close()

for val in val_questions:
    question_ids.append(val['question_id'])

with open("sentiment_data", "r") as fp:
    sentiment_data = json.load(fp)

question = ''
img_path = ''
ans = ''
tweet = ''
tweet_label = -1
showTweet = False
num_tasks_shown = 0
showButton = True
taskFinish = False
sub_task_time = 15
total_num_tasks = 16  # 5  #
# sentence = []
response_obj = {}
timeKeep = 0
sequence = []
predictions = []
threshold = 0.85
model = prepareModel()
returnFrames = None
tryMode = False
try_tasks = 5  # 3  #

start_date = None
prolific_id = None
session_id = None
response_obj_tasks = []

task_limit = 0

showTask1 = True

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
    BASE_PATH = os.path.join('static', 'val2014_yesno_refined')
    for q in val_questions:
        if q['question_id'] == ques_id:
            ques = q['question']
            answer = getAnswer(q['question_id'])
            return ques, os.path.join(BASE_PATH, 'COCO_val2014_' + str(q['image_id']).zfill(12) + '.jpg'), answer

    return 'Not found', '', '-1'


def getItemsToShow(numTask='0', ppid='hello', try_Mode=False):
    global showTweet, question, img_path, ans, tweet, num_tasks_shown, taskFinish, tweet_label
    global timeKeep, response_obj, bucket, showButton, task_limit

    prob = np.random.binomial(5, 0.5)
    if prob < 3:
        showTweet = False
        # to random picture with question, image,answer
        question, img_path, ans = getImgQuesAns(random.choice(question_ids))
        tweet = ''
    else:
        showTweet = True
        tweet_data = random.choice(sentiment_data)
        tweet = tweet_data['text']
        tweet_label = tweet_data['label']
        question = ''
        img_path = ''
        ans = ''

    # sentence = []
    timeKeep = 1

    num_tasks_shown += 1

    print("Number of tasks shown:", int(numTask), "Total tasks: ", task_limit, "tryMode: ", try_Mode, 'for ppid: ', ppid)

    if int(numTask) >= task_limit:  # end the task if over or equal.
        taskFinish = True

        if try_Mode:
            showButton = True
            print('Try Task End.')
        else:
            print('Task End.')

    return {'image_name': img_path, 'question': question, 'tweet': tweet, 'label': ans if len(ans) != 0 else tweet_label}


def keepTimer():
    global timeKeep
    if timeKeep == sub_task_time:
        pass
    else:
        timeKeep += 1


def generate_frames(framesReceived, lh, rh, sentence):
    global sequence, threshold, model, predictions

    # keypoints, lh, rh = extract_keypoints(framesReceived)
    # sequence.append(keypoints[-126:])
    # sequence[-50:]
    if len(framesReceived) == 50 and (sum(lh) != 0 or sum(rh) != 0):
        res = model.predict(np.expand_dims(framesReceived, axis=0))[0]
        print(actions[np.argmax(res)])
        print("Accuracy:", res[np.argmax(res)])
        predictions.append(np.argmax(res))

        if mode(predictions[-5:]) == np.argmax(res):
            if res[np.argmax(res)] > threshold:
                print("Accuracy:", res[np.argmax(res)])
                # sequence = []
                # if len(sentence) > 0:
                #     if actions[np.argmax(res)] != sentence[-1]:
                #         sentence.append(actions[np.argmax(res)])
                # else:
                sentence.append(actions[np.argmax(res)])

        if len(sentence) > 5:
            sentence = sentence[-5:]

    return sentence

    # ret, buffer = cv2.imencode('.jpg', image)
    # frame = None  # buffer.tobytes()

    # yield b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n'


@app.route('/getTaskResponse', methods=['POST'])
def getTaskResponse():

    result = json.loads(request.form.get('response'))

    blob = bucket.blob('seventh-port-334508.appspot.com/' + str(result['prolific_pid']) + '_'
                       + str(result['session_id']) + '.txt')
    blob.upload_from_string(str(result))

    return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}


@app.route('/set_items', methods=['POST'])
def set_items():
    global task_limit
    items = {}
    if request.cookies.get('try_mode') == 'true':
        task_limit = int(request.cookies.get('task_limit'))
        # sentence = json.loads(request.cookies.get('sentence'))
        items = getItemsToShow(request.cookies.get('try_task_count'), request.cookies.get('ppid'), request.cookies.get('try_mode') == 'true')
    if request.cookies.get('start_mode') == 'true':
        task_limit = int(request.cookies.get('task_limit'))
        # sentence = json.loads(request.cookies.get('sentence'))
        items = getItemsToShow(request.cookies.get('task_count'), request.cookies.get('ppid'))

    return json.dumps({'success': True, 'items': items}), 200, {'ContentType': 'application/json'}


@app.route('/_task-stuff', methods=['GET'])
def stuff():
    return jsonify(showTweet=showTweet, taskFinish=request.cookies.get('task_finish') == "true",
                   showButton=showButton, tryMode=request.cookies.get('try_mode') == "true", showTask1=showTask1)


@app.route('/try_mode', methods=['POST'])
def try_mode():
    global tryMode, showButton, num_tasks_shown, timeKeep, task_limit

    print("In try_mode: ", request.method)
    resetTasks()

    if request.method == 'POST':
        tryMode = request.cookies.get('try_mode') == 'true'
        print("Try mode is: ", tryMode)

        showButton = False  # request.cookies.get('show_button') == 'true'
        print("Show button:", showButton)

    return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}  # redirect(url_for('home'))


@app.route('/home', methods=['GET', 'POST'])
def home():
    global showButton, response_obj, tryMode, taskFinish, timeKeep, num_tasks_shown, task_limit
    print("In home: ", request.method, showButton)

    taskFinish = False
    # complete_survey_link = survey_link + str(prolific_id)

    resp = make_response(
        render_template('index.html', showTweet=showTweet,
                        showButton=showButton,
                        sub_task_time=sub_task_time,
                        total_num_tasks=total_num_tasks, showTask1=showTask1,
                        tryMode=request.cookies.get('try_mode') == "true", try_tasks=try_tasks))

    if request.method == 'POST':
        tryMode = request.cookies.get('try_mode') == 'true'
        showButton = False
        resetTasks()

        resp1 = make_response(
            render_template('index.html', showTweet=showTweet,
                            showButton=showButton, sub_task_time=sub_task_time,
                            total_num_tasks=total_num_tasks, showTask1=showTask1,
                            tryMode=request.cookies.get('try_mode') == "true", try_tasks=try_tasks))
        resp1.set_cookie('start_mode', 'true')
        return resp1

    if request.args.get('ppid') is not None and request.args.get('sid') is not None:
        print("Here...")
        resp.set_cookie('ppid', request.args.get('ppid'))
        resp.set_cookie('sid', request.args.get('sid'))
        # resp.set_cookie('show_button', 'true')
        resp.delete_cookie('try_mode')
        resp.delete_cookie('start_mode')

    return resp


@app.route('/')
def index():
    global showButton, start_date, prolific_id, session_id, tryMode

    showButton = True
    tryMode = request.cookies.get('try_mode') == 'true'
    print("REquest args: " + str(request.args.get("PROLIFIC_PID")) + ' , ' + str(request.args.get("SESSION_ID")))

    start_date = str(datetime.now())
    prolific_id = ''.join(random.sample(string.ascii_lowercase, 5)) if request.args.get(
        "PROLIFIC_PID") is None else request.args.get("PROLIFIC_PID")
    session_id = ''.join(random.sample(string.digits, 5)) if request.args.get(
        "SESSION_ID") is None else request.args.get("SESSION_ID")

    return redirect(url_for('home', ppid=prolific_id, sid=session_id))


def resetTasks():
    global num_tasks_shown, showTweet, question, img_path, ans, tweet, tweet_label, taskFinish, timeKeep, sequence
    global predictions, tryMode, response_obj_tasks

    num_tasks_shown = 0
    showTweet = False
    question = ''
    img_path = ''
    ans = ''
    tweet = ''
    tweet_label = ''
    taskFinish = False
    timeKeep = 0
    sequence = []
    # sentence = []
    predictions = []
    response_obj_tasks = []
    tryMode = False


@app.route('/image', methods=['POST'])
def image():
    global showButton
    try:
        image_file = json.loads(request.form.get('image'))  # get the image
        lh = json.loads(request.form.get('lh'))
        rh = json.loads(request.form.get('rh'))

        if (request.cookies.get('try_mode') == 'true' or request.cookies.get('start_mode') == 'true') and \
                (len(image_file) == 50 and (sum(lh) != 0 or sum(rh) != 0)):
            res = generate_frames(framesReceived=image_file, lh=lh, rh=rh,
                                  sentence=json.loads(request.cookies.get('sentence')))
            return json.dumps({'success': True, 'result': res}), 200, {'ContentType': 'application/json'}

        return json.dumps({'success': False}), 200, {'ContentType': 'application/json'}

    except Exception as e:
        print('POST /image error: %e' % e)
        app.logger.debug("Error in POST /image")
        app.logger.debug(e)
        return e


if __name__ == '__main__':
    app.run(debug=False)
