from flask import Flask, render_template, Response, jsonify, request, redirect, url_for, make_response
import os
import json
import numpy as np
import random
from datetime import datetime
import google.cloud.logging
import logging
from google.cloud import storage
import string


# datetime format '%Y-%m-%d %H:%M:%S.%f'
client = storage.Client(project="seventh-port-334508")
bucket = client.bucket("seventh-port-334508.appspot.com")

log_client = google.cloud.logging.Client(project="seventh-port-334508", )
log_client.setup_logging()

app = Flask(__name__)

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

# survey_link = 'https://docs.google.com/forms/d/e/1FAIpQLSeZtch5xA8JUKQioa-EQoQIccS_zsc1Yw1RM_YPkwpFN4dN-Q/viewform' \
#               '?usp=pp_url&entry.1722510161='

index_html = 'index2.html'

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

prolific_id = None
session_id = None
response_obj_tasks = []
timeKeep = 0

showTask1 = False
taskTyping = False


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


def getItemsToShow(numTask, ppid):
    global showTweet, question, img_path, ans, tweet, num_tasks_shown, taskFinish, tweet_label
    global timeKeep, bucket, prolific_id, session_id

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

    num_tasks_shown += 1
    print('Task Number: ', numTask, 'of total: ', total_num_tasks, 'for ppid: ', ppid)
    if int(numTask) == total_num_tasks:
        print('Task End.')
        taskFinish = True


@app.route('/_task-stuff', methods=['GET'])
def stuff():
    if not showTask1 and not showButton:
        getItemsToShow(request.cookies.get('task_count'), request.cookies.get('ppid'))

    return jsonify(showTweet=showTweet, tweet=tweet, img_path=img_path, question=question,
                   taskFinish=request.cookies.get('task_finish') == "true",
                   sentence=[], timeKeep=timeKeep, showButton=showButton, taskTyping=taskTyping, ans=ans,
                   tweet_label=tweet_label)


@app.route('/getTask2Response', methods=['POST'])
def getTask2Response():

    result = json.loads(request.form.get('response'))

    blob = bucket.blob('task2/' + str(result['prolific_pid']) + '_'
                       + str(result['session_id']) + '.txt')
    blob.upload_from_string(str(result))

    return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}


@app.route('/home', methods=['GET', 'POST'])
def home():
    global showButton, num_tasks_shown

    resp = make_response(
        render_template(index_html, img_path=img_path, tweet=tweet, question=question, showTweet=showTweet,
                        showButton=showButton, sentence=[], sub_task_time=sub_task_time,
                        total_num_tasks=total_num_tasks, showTask1=showTask1, taskTyping=taskTyping))
    if request.method == 'POST':
        showButton = False
        return render_template(index_html, img_path=img_path, tweet=tweet, question=question, showTweet=showTweet,
                               showButton=showButton, sentence=[], sub_task_time=sub_task_time,
                               total_num_tasks=total_num_tasks, showTask1=showTask1, taskTyping=taskTyping)

    if request.args.get('ppid') is not None and request.args.get('sid') is not None:
        resp.set_cookie('ppid', request.args.get('ppid'))
        resp.set_cookie('sid', request.args.get('sid'))

    return resp


@app.route('/')
def index():
    global showButton, num_tasks_shown, showTweet, question, img_path, ans, tweet, taskFinish, tweet_label
    global response_obj_tasks, prolific_id, session_id  # , timeKeep

    num_tasks_shown = 0
    showTweet = False
    question = ''
    img_path = ''
    ans = ''
    tweet = ''
    tweet_label = ''
    taskFinish = False
    prolific_id = None
    session_id = None
    response_obj_tasks = []

    showButton = True
    print("REquest args: " + str(request.args.get("PROLIFIC_PID")) + ' , ' + str(request.args.get("SESSION_ID")))
    app.logger.debug("REquest args: " + str(request.args.get("PROLIFIC_PID")) + ' , '
                     + str(request.args.get("SESSION_ID")))

    prolific_id = ''.join(random.sample(string.ascii_lowercase, 5)) if request.args.get("PROLIFIC_PID") is None \
        else request.args.get("PROLIFIC_PID")
    session_id = ''.join(random.sample(string.digits, 5)) if request.args.get("SESSION_ID") is None \
        else request.args.get("SESSION_ID")

    return redirect(url_for('home', ppid=prolific_id, sid=session_id))
