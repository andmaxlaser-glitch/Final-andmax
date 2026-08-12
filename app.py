import os
from flask import Flask, render_template, request, jsonify
from logica.procesador import analizar_dxf

app = Flask(__name__)
UPLOAD_FOLDER = 'pruebas'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analizar', methods=['POST'])
def analizar():
    if 'archivo_dxf' not in request.files:
        return jsonify({"estado": "error", "mensaje": "No se subió ningún archivo"})

    archivo = request.files['archivo_dxf']
    if archivo.filename == '':
        return jsonify({"estado": "error", "mensaje": "Nombre de archivo vacío"})

    if archivo:
        ruta_archivo = os.path.join(app.config['UPLOAD_FOLDER'], archivo.filename)
        archivo.save(ruta_archivo)
        resultado = analizar_dxf(ruta_archivo)
        return jsonify(resultado)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
@app.route('/analizar', methods=['POST'])
def analizar():
    # ... (código anterior de archivo)
    material = request.form.get('material')
    espesor = request.form.get('espesor')
    
    # ... (guardar archivo)
    resultado = analizar_dxf(ruta_archivo)
    
    # Calcular precio
    precio_total = calcular_precio(resultado['perimetro_total_mm'], material, espesor)
    resultado['precio_total'] = precio_total
    return jsonify(resultado)
