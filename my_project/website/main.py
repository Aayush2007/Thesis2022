from flask import Flask, render_template, Response
import cv2
import os
import json
import numpy as np
from model import actions, mp_holistic, mediapipe_detection, draw_styled_landmarks, extract_keypoints, prepareModel


app = Flask(__name__)
camera = cv2.VideoCapture(-1)
question_ids = []

f = open('v2_mscoco_val2014_annotations_yesno.json', )
val_anno = json.load(f)
f.close()

f = open('v2_OpenEnded_mscoco_val2014_questions_yesno.json', )
val_questions = json.load(f)
f.close()

with open("sentiment_data", "r") as fp:
    sentiment_data = json.load(fp)

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
    BASE_PATH = os.path.join('val2014_yesno')
    for q in val_questions:
        if q['question_id'] == ques_id:
            ques = q['question']
            ans = getAnswer(q['question_id'])
            return ques, os.path.join(BASE_PATH, 'COCO_val2014_' + str(q['image_id']).zfill(12) + '.jpg'), ans

    return 'Not found', '', '-1'





def generate_frames():
    global camera

    sequence = []
    sentence = []
    predictions = []
    threshold = 0.90
    model = prepareModel()

    with mp_holistic.Holistic(min_detection_confidence=0.7, min_tracking_confidence=0.7) as holistic:
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

                    if np.unique(predictions[-5:])[0] == np.argmax(res):
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


@app.route('/')
def index():
    print('[DEBUG] call cv2.VideoCapture(0) from PID', os.getpid())
    img_path = '/static/COCO_val2014_000000393282.jpg'
    question = "Do you see a body of water in the picture?"
    tweet = "The audio booth is ready to blow the roof off the Comcast Center tomorrow! Are you? #MDMadness"
    showTweet = False

    return render_template('index.html', img_path=img_path, tweet=tweet, question=question, showTweet=showTweet)


@app.route('/video')
def video():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':

    for val in val_questions:
        question_ids.append(val['question_id'])

    # getImgQuesAns(random.choice(question_ids)) ## to random picture with question, image,answer

    app.run(debug=False, host='localhost', port=8080)
