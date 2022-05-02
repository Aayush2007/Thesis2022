import cv2
from flask import Blueprint, render_template, Response

views = Blueprint(__name__, "views")
camera = cv2.VideoCapture(0)


@views.route('/')
def index():
    return render_template("index.html")


def gen():
    while True:
        success, image = camera.read()

        if not success:
            break

        ret, jpeg = cv2.imencode('.jpg', image)
        frame = jpeg.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')


@views.route('/video')
def video():
    #global video
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')
