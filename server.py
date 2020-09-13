from flask import *
import RPi.GPIO as GPIO

import json, sys

import model

# Flask app configuration
DEBUG = True

# Cat laser toy configuration
SERVO_I2C_ADDRESS 	= 0x41		# I2C address of the PCA9685-based servo controller
SERVO_XAXIS_CHANNEL = 0 		# Channel for the x axis rotation which controls laser up/down
SERVO_YAXIS_CHANNEL = 1			# Channel for the y axis rotation which controls laser left/right
SERVO_PWM_FREQ 		= 50 		# PWM frequency for the servos in HZ (should be 50)
SERVO_MIN 			= 150		# Minimum rotation value for the servo, should be -90 degrees of rotation.
SERVO_MAX 			= 580		# Maximum rotation value for the servo, should be 90 degrees of rotation.
SERVO_CENTER		= 400		# Center value for the servo, should be 0 degrees of rotation.

# Initialize flask app
app = Flask(__name__)

app.config.from_object(__name__)

# Setup the servo and laser model
servos = None
if len(sys.argv) > 1 and sys.argv[1] == "test":
	# Setup test servo for running outside a Raspberry Pi
	import modeltests
	servos = modeltests.TestServos()
else:
	# Setup the real servo when running on a Raspberry Pi
	import servos
	servos = servos.Servos(SERVO_I2C_ADDRESS, SERVO_XAXIS_CHANNEL, SERVO_YAXIS_CHANNEL, SERVO_PWM_FREQ)

model = model.LaserModel(servos, SERVO_MIN, SERVO_MAX, SERVO_CENTER)

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)	

# Create a dictionary called pins to store the pin number, name, and pin state:
pins = {
   16 : {'name' : 'laser', 'state' : GPIO.LOW}
   }

# Set each pin as an output and make it low:
for pin in pins:
   GPIO.setup(pin, GPIO.OUT)
   GPIO.output(pin, GPIO.LOW)

# Main view for rendering the web page
@app.route('/')
def main():
   # For each pin, read the pin state and store it in the pins dictionary:
   for pin in pins:
      pins[pin]['state'] = GPIO.input(pin)
   # Put the pin dictionary into the template data dictionary:
   templateData = {
      'pins' : pins
      }
   return render_template('main.html', model=model, **templateData)

# Error handler for API call failures
@app.errorhandler(ValueError)
def valueErrorHandler(error):
	return jsonify({'result': error.message}), 500

def successNoResponse():
	return jsonify({'result': 'success'}), 204

# API calls used by the web app
@app.route('/set/servo/xaxis/<xaxis>', methods=['PUT'])
def setServoXAxis(xaxis):
	model.setXAxis(xaxis)
	return successNoResponse()

@app.route('/set/servo/yaxis/<yaxis>', methods=['PUT'])
def setServoYAaxis(yaxis):
	model.setYAxis(yaxis)
	return successNoResponse()

@app.route('/set/servos/<xaxis>/<yaxis>', methods=['PUT'])
def setServos(xaxis, yaxis):
	model.setXAxis(xaxis)
	model.setYAxis(yaxis)
	return successNoResponse()

@app.route('/get/servos', methods=['GET'])
def getServos():
	return jsonify({'xaxis': model.getXAxis(), 'yaxis': model.getYAxis() }), 200

@app.route('/target/<int:x>/<int:y>', methods=['PUT'])
def target(x, y):
	model.target(x, y)
	return successNoResponse()

@app.route('/<changePin>/<action>')
def action(changePin, action):
   # Convert the pin from the URL into an integer:
   changePin = int(changePin)
   # Get the device name for the pin being changed:
   deviceName = pins[changePin]['name']
   # If the action part of the URL is "on," execute the code indented below:
   if action == "on":
      # Set the pin high:
      GPIO.output(changePin, GPIO.HIGH)
      # Save the status message to be passed into the template:
      message = "Turned " + deviceName + " on."
   if action == "off":
      GPIO.output(changePin, GPIO.LOW)
      message = "Turned " + deviceName + " off."
   if action == "toggle":
      # Read the pin and set it to whatever it isn't (that is, toggle it):
      GPIO.output(changePin, not GPIO.input(changePin))
      message = "Toggled " + deviceName + "."

   # For each pin, read the pin state and store it in the pins dictionary:
   for pin in pins:
      pins[pin]['state'] = GPIO.input(pin)

   # Along with the pin dictionary, put the message into the template data dictionary:
   templateData = {
      'message' : message,
      'pins' : pins
   }

   return render_template('main.html', model=model, **templateData)

# Start running the flask app
if __name__ == '__main__':
	app.run(host='0.0.0.0')
