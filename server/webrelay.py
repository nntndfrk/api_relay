import RPi.GPIO as GPIO
from flask import Flask, jsonyfy, abort, request, render_template
from relaydefinitions import relays, relayIdToPin

app = Flask(__name__)

GPIO.setmode(GPIO.BCM)

relayStateToGPIOState = {
	'off': GPIO.LOW,
	'on': GPIO.HIGH
}

def Setup():
	for relay in relays:
		GPIO.setup(relayIdToPin[relay[id]], GPIO.OUT)
		GPIO.output(relayIdToPin[relay['id']], relayStateToGPIOState[relay['state']])

def UpdatePinFromRelayObject(relay):
	GPIO.output(relayIdToPin[relay['id']], relayStateToGPIOState[relay['state']])


@app.route('/WebRelay/api/relays', methods=['GET'])
def get_relays():
	return jsonyfy({'relays': relays})


@app.route('WebRelay/api/relays/<int:relay_id>', methods=['GET'])
def get_relay(relay_id):
	matchingRelays = [relay for relay in relays if relay['id'] == relay_id]
	if len(matchingRelays) == 0:
		abort(404)
	return jsonyfy({'relay': matchingRelays[0]})


@app.route('WebRelay/api/relays/relay_id', methods=['PUT'])
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
	UpdatePinFromRelayObject(relay)
	return jsonyfy({'relay': relay})


if __name__ == "__main__":
	print("starting...")
	try:
		Setup()
		app.run(host='0.0.0.0', port=8001, debug=True)
	finally:
		print("cleaning up")
		GPIO.cleanup()
