from __future__ import division, print_function
# coding=utf-8
import os
from black import err
import numpy as np

# Keras
from keras.models import load_model
from keras.preprocessing import image

# Flask utils
from flask import Flask, jsonify, send_from_directory, request
from werkzeug.utils import secure_filename
from flask_cors import CORS

# Api key authentication module
from modules import authenticateKey

# Define a flask app
# app = Flask(__name__, static_folder='front-end/build', static_url_path='')
app = Flask(__name__)
# CORS(app)

# Model saved with Keras model.save()
MALARIA_MODEL_PATH = 'models/Malaria/malaria_pred_cnn.h5'
PNEUMONIA_MODEL_PATH = 'models/Pneumonia/pneumonia_pred_cnn.h5'

# Load your trained model
malaria_model = load_model(MALARIA_MODEL_PATH)
pneumonia_model = load_model(PNEUMONIA_MODEL_PATH)
# model._make_predict_function()          # Necessary to make everything ready to run on the GPU ahead of time
print('Model loaded. Start serving...')


def predictDisease(img_path, model):
    image_to_predict = image.load_img(img_path, target_size=(130, 130, 3))
    image_to_predict = image.img_to_array(image_to_predict)
    image_to_predict = np.expand_dims(image_to_predict, axis=0)
    preds = model.predict(image_to_predict)
    return preds


@app.route("/", defaults={'path': ''})
def serve(path):
    return send_from_directory(app.static_folder, 'index.html')


@app.errorhandler(404)
def not_found(e):
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/predict', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # Get the file from post request
        f = request.files['file']

        # Get disease type to diagnose
        disease_type = request.args.get("disease")
        print("DISEASE: "+disease_type)

        # Get user email from request
        user_email = request.args.get("user-email")

        # Get Api key from request
        api_key = request.args.get("api-key")
        api_key_validity = authenticateKey.checkApiKeyValidity(
            user_email, api_key)

        if user_email == "" or api_key == "":
            return jsonify({'results': "X000"})

        if not api_key_validity:
            return jsonify({'results': "X001"})

        print("Received file from client...", f)
        # Save the file to ./uploads
        basepath = os.path.dirname(__file__)
        file_path = os.path.join(
            basepath, 'uploads', secure_filename(f.filename))
        f.save(file_path)

        if (disease_type == '1'):
            print("Malaria")
            preds = predictDisease(file_path, malaria_model)
        elif (disease_type == '2'):
            print("Pneumonia")
            preds = predictDisease(file_path, pneumonia_model)
        elif (disease_type == '3'):
            print("Covid19")

        # Remove file from server after predictions
        os.remove(file_path)

        try:
            labels = np.array(preds)
        except UnboundLocalError as error:
            print(error)
            return jsonify({'results': "Error!"})

        labels[labels >= 0.9] = 1
        labels[labels <= 0.02] = 0

        print(labels)
        final = np.array(labels)        

        if final[0][0] == 0:
            pred_result = "Infected"
        elif final[0][0] == 1:
            pred_result = "Normal"

        response = jsonify({'results': pred_result})
    return response


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
# if __name__ == '__main__':  
#     app.run(host='0.0.0.0', port=80)
    # uncomment this section to serve the app locally with gevent at:  http://localhost:5000
    # Serve the app with gevent
    # http_server = WSGIServer(('', 5000), app)
    # http_server.serve_forever()
