import RPi.GPIO as GPIO
import os
import time
import threading
import multiprocessing
from flask import Flask, jsonify, abort, request, render_template, make_response
from relaydefinitions import relays, relayIdToPin

from flask_sqlalchemy import SQLAlchemy
from werkzeug.contrib.fixers import ProxyFix
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['DEBUG'] = True
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = \
    'sqlite:///'+ os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)

#========  Auth  ========
from flask_httpauth import HTTPBasicAuth
auth = HTTPBasicAuth()

cur_proc_list = []

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    

    def __repr__(self):
        return '<User %r>' % self.username
#========  end Auth  ========


#======== GPIO  ========
GPIO.setmode(GPIO.BCM)

relayStateToGPIOState = {
    'off': GPIO.LOW,
    'on': GPIO.HIGH
}


def Setup():
    GPIO.setwarnings(False)
    for relay in relays:
        GPIO.setup(relayIdToPin[relay['id']], GPIO.OUT)
        GPIO.output(relayIdToPin[relay['id']], relayStateToGPIOState[relay['state']])

def UpdatePinFromRelayObject(relay):
    GPIO.output(relayIdToPin[relay['id']], relayStateToGPIOState[relay['state']])

def get_new_state(relay):
    if relay['state'] == 'off':
        newState = 'on'
    else:
        newState = 'off'
    relay['state'] = newState
    return relay

def TimerPinFromRelayObject(relay):
    relay = get_new_state(relay)
    UpdatePinFromRelayObject(relay)
    time.sleep(relay['timer'])
    relay = get_new_state(relay)
    UpdatePinFromRelayObject(relay)



#======== end GPIO  ========


#======== NeoPixel RGB-LED  ========
from neopixel import *
from ledconf import *

strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
strip.begin()

def wheel(pos):
    """Generate rainbow colors across 0-255 positions."""
    if pos < 85:
        return Color(pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return Color(255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return Color(0, pos * 3, 255 - pos * 3)

def colorWipe(strip, color, wait_ms=50):
    """Wipe color across display a pixel at a time."""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
        strip.show()
        time.sleep(wait_ms/1000.0)


def theaterChase(strip, color, wait_ms=50, iterations=10):
    """Movie theater light style chaser animation."""
    for j in range(iterations):
        for q in range(3):
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i+q, color)
            strip.show()
            time.sleep(wait_ms/1000.0)
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i+q, 0)




def rainbow(strip, wait_ms=20, iterations=1):
    """Draw rainbow that fades across all pixels at once."""
    for j in range(256*iterations):
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, wheel((i+j) & 255))
        strip.show()
        time.sleep(wait_ms/1000.0)


def rainbowCycle(strip, wait_ms=20, iterations=5):
    """Draw rainbow that uniformly distributes itself across all pixels."""
    for j in range(256*iterations):
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, wheel(((i * 256 / strip.numPixels()) + j) & 255))
        strip.show()
        time.sleep(wait_ms/1000.0)


def theaterChaseRainbow(strip, wait_ms=50):
    """Rainbow movie theater light style chaser animation."""
    for j in range(256):
        for q in range(3):
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i+q, wheel((i+j) % 255))
            strip.show()
            time.sleep(wait_ms/1000.0)
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i+q, 0)

#======== end NeoPixel  ========

#========  API  ========


@app.before_first_request
def io_init():
    """GPIO init"""
    GPIO.setmode(GPIO.BCM)
    Setup()

    
@auth.verify_password
def ver_password(username, password):
    user = User.query.filter_by(username=username).first()
    if not user:
        return False
    return user.verify_password(password)


@auth.error_handler
def unauthorized():
    return make_response(jsonify({'error': 'Unauthorized access'}), 401)


@app.route('/api/v1.0/relays', methods=['GET'])
@auth.login_required
def get_relays():
    return jsonify({'relays': relays})


@app.route('/api/v1.0/relays/<int:relay_id>', methods=['GET'])
@auth.login_required 
def get_relay(relay_id):
    matchingRelays = [relay for relay in relays if relay['id'] == relay_id]
    if len(matchingRelays) == 0:
        abort(404)
    return jsonify({'relay': matchingRelays[0]})


@app.route('/api/v1.0/relays/<int:relay_id>', methods=['PUT'])
@auth.login_required 
def update_relay(relay_id):
    matchingRelays = [relay for relay in relays if relay['id'] == relay_id]

    if len(matchingRelays) == 0:
        abort(404)
    if not request.json:
        abort(400)
    if not 'state' in request.json:
        abort(400)

    relay = matchingRelays[0]
    relay['state'] = request.json.get('state')
    u = threading.Thread(target=UpdatePinFromRelayObject, args=(relay,))
    u.daemon = True
    u.start()
    return jsonify({'relay': relay})


@app.route('/api/v1.0/relays_t/<int:relay_id>', methods=['PUT'])
@auth.login_required 
def update_relay_t(relay_id):
    matchingRelays = [relay for relay in relays if relay['id'] == relay_id]

    if len(matchingRelays) == 0:
        abort(404)
    if not request.json:
        abort(400)
    if not 'timer' in request.json:
        abort(400)

    relay = matchingRelays[0]
    relay['timer'] = float(request.json.get('timer'))
    t = threading.Thread(target=TimerPinFromRelayObject, args=(relay,))
    t.daemon = True
    t.start()
    return jsonify({'relay': relay})


@app.route('/api/v1.0/led/colorWipe', methods=['PUT'])
@auth.login_required 
def apicolorWipe():
    if not request.json:
        abort(400)
    if not 'color' in request.json:
        abort(400)
    if not 'wait_ms' in request.json:
        wait_ms = 50
    else:
        wait_ms = int(request.json.get('wait_ms'))
    lcolor = request.json.get('color').split()
    color = Color(int(lcolor[0]), int(lcolor[1]), int(lcolor[2]))
    if len(cur_proc_list)>0:
        cur_proc = cur_proc_list.pop()
        cur_proc.terminate()
    try:
        proc = multiprocessing.Process(target=colorWipe, args=(strip, color, wait_ms,))
        cur_proc_list.append(proc)
        proc.start()
        return jsonify({'colorWipe': 'OK'})
    except:
        abort(501)


@app.route('/api/v1.0/led/rainbow', methods=['PUT'])
@auth.login_required 
def apirainbow():
    if not request.json:
        abort(400)
    if not 'wait_ms' in request.json:
        wait_ms = 20
    else:
        wait_ms = int(request.json.get('wait_ms'))
    if not 'iterations' in request.json:
        iterations = 1
    else:
        iterations = int(request.json.get('iterations'))
    if len(cur_proc_list)>0:
        cur_proc = cur_proc_list.pop()
        cur_proc.terminate()  
    try:
        proc = multiprocessing.Process(target=rainbow, args=(strip, wait_ms, iterations,))
        cur_proc_list.append(proc)
        proc.start()
        return jsonify({'rainbow': 'OK'})
    except:
        abort(501)


@app.route('/api/v1.0/led/theaterChase', methods=['PUT'])
@auth.login_required 
def apitheaterChase():
    if not request.json:
        abort(400)
    if not 'color' in request.json:
        abort(400)
    if not 'wait_ms' in request.json:
        wait_ms = 50
    else:
        wait_ms = int(request.json.get('wait_ms'))
    if not 'iterations' in request.json:
        iterations = 10
    else:
        iterations = int(request.json.get('iterations'))
    lcolor = request.json.get('color').split()
    color = Color(int(lcolor[0]), int(lcolor[1]), int(lcolor[2]))
    if len(cur_proc_list)>0:
        cur_proc = cur_proc_list.pop()
        cur_proc.terminate()
    try:
        proc = multiprocessing.Process(target=theaterChase, args=(strip, color, wait_ms, iterations,))
        cur_proc_list.append(proc)
        proc.start()
        return jsonify({'theaterChase': 'OK'})
    except:
        abort(501)


@app.route('/api/v1.0/led/rainbowCycle', methods=['PUT'])
@auth.login_required 
def apirainbowCycle():
    if not request.json:
        abort(400)
    if not 'wait_ms' in request.json:
        wait_ms = 20
    else:
        wait_ms = int(request.json.get('wait_ms'))
    if not 'iterations' in request.json:
        iterations = 5
    else:
        iterations = int(request.json.get('iterations'))
    if len(cur_proc_list)>0:
        cur_proc = cur_proc_list.pop()
        cur_proc.terminate()
    try:
        proc = multiprocessing.Process(target=rainbowCycle, args=(strip, wait_ms, iterations,))
        cur_proc_list.append(proc)
        proc.start()
        return jsonify({'rainbowCycle': 'OK'})
    except:
        abort(501)


@app.route('/api/v1.0/led/theaterChaseRainbow', methods=['PUT'])
@auth.login_required 
def apitheaterChaseRainbow():
    if not request.json:
        abort(400)
    if not 'wait_ms' in request.json:
        wait_ms = 50
    else:
        wait_ms = int(request.json.get('wait_ms'))
    if len(cur_proc_list)>0:
        cur_proc = cur_proc_list.pop()
        cur_proc.terminate()
    try:
        proc = multiprocessing.Process(target=theaterChaseRainbow, args=(strip, wait_ms,))
        cur_proc_list.append(proc)
        proc.start()
        return jsonify({'theaterChaseRainbow': 'OK'})
    except:
        abort(501)


@app.route('/', methods=['GET'])
@auth.login_required 
def index():
    return render_template('index.html')

#========  end API  ========

app.wsgi_app = ProxyFix(app.wsgi_app)

#========  run standalone dev-server to dedug  ========
if __name__ == "__main__":
    print("starting...")
    try:
        Setup()
        app.run(host='0.0.0.0', port=8000, debug=False)
    finally:
        print("cleaning up")
        GPIO.cleanup()