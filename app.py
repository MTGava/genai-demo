from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import base64
import io
import os
from PIL import Image
import google.generativeai as genai
import edge_tts
from base64 import b64encode

app = Flask(__name__)
CORS(app) # Habilitar CORS para todas as rotas da sua aplicação

genai.configure(api_key=os.environ.get('GOOGLE_API_KEY'))
model = genai.GenerativeModel(model_name="gemini-1.5-flash")
VOICE = "pt-BR-AntonioNeural"
OUTPUT_FILE = "audio.mp3"

@app.route('/hello-world')
def hello_world():
    return 'Hello, World!'

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/describe', methods=['POST'])
def describe_image():

    # Verifica se a requisição contém dados
    if 'image' not in request.json:
        return jsonify({'error': 'No image data sent in request body'}), 400
    
    if 'context' not in request.json or request.json['context'] == '':
        context = 'Descreva com detalhes em Portgues Brasil'
    else:
        context = request.json['context']

    try:
        # Decodifica a base64 para obter os bytes da imagem
        image_data = base64.b64decode(request.json['image'])
        
        # Converte os bytes em um objeto de imagem
        image = Image.open(io.BytesIO(image_data))

        response = model.generate_content([context, image])
        response.resolve()

        communicate = edge_tts.Communicate(text=response.text, voice=VOICE, rate="+30%")
        communicate.save(OUTPUT_FILE)

        with open(OUTPUT_FILE, "wb") as file:
            for chunk in communicate.stream_sync():
                if chunk["type"] == "audio":
                    file.write(chunk["data"])

        # Leia o arquivo MP3 como binário
        with open('audio.mp3', 'rb') as f:
            audio_data = f.read()

        # Converta o binário em base64
        mp3_base64 = b64encode(audio_data).decode('utf-8')

        # Retorna a descrição da imagem como JSON
        return jsonify({'description': mp3_base64}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400
