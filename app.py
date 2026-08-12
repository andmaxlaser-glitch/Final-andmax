import os
import mercadopago
from flask import Flask, render_template, request, jsonify
from logica.procesador import analizar_dxf

app = Flask(__name__)
UPLOAD_FOLDER = 'pruebas'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configura tu Access Token de Mercado Pago (Reemplaza con tu token de Producción o Test)
# Puedes usar una variable de entorno o ponerlo directamente como texto de prueba por ahora:
MP_ACCESS_TOKEN = os.environ.get('MP_ACCESS_TOKEN', 'TU_ACCESS_TOKEN_DE_MERCADO_PAGO')
sdk = mercadopago.SDK(MP_ACCESS_TOKEN)

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
    
    material = request.form.get('material', 'MDF')
    espesor = request.form.get('espesor', '1')
    
    try:
        cantidad = int(request.form.get('cantidad', 1))
        if cantidad < 1: cantidad = 1
    except:
        cantidad = 1
    
    if archivo:
        ruta_archivo = os.path.join(app.config['UPLOAD_FOLDER'], archivo.filename)
        archivo.save(ruta_archivo)
        
        resultado = analizar_dxf(ruta_archivo, material, espesor, cantidad)
        return jsonify(resultado)

@app.route('/crear_preferencia', methods=['POST'])
def crear_preferencia():
    datos_carrito = request.json
    items_mp = []
    
    if not datos_carrito or not isinstance(datos_carrito, list):
        return jsonify({"error": "Carrito vacío o inválido"}), 400

    for item in datos_carrito:
        # Construimos el ítem para Mercado Pago basado en lo que hay en el carrito
        titulo = f"Corte Láser: {item.get('nombre_archivo', 'Pieza')} ({item.get('material')} {item.get('espesor')}mm)"
        cantidad = int(item.get('cantidad', 1))
        precio_unitario = float(item.get('precio_total', 0)) / cantidad # MP pide precio por unidad
        
        items_mp.append({
            "title": titulo,
            "quantity": cantidad,
            "currency_id": "ARS",
            "unit_price": round(precio_unitario, 2)
        })

    preference_data = {
        "items": items_mp,
        "back_urls": {
            "success": "https://tusitio.onrender.com/",  # Reemplaza con tu URL real de Render
            "failure": "https://tusitio.onrender.com/",
            "pending": "https://tusitio.onrender.com/"
        },
        "auto_return": "approved",
    }

    try:
        preference_response = sdk.preference().create(preference_data)
        preference = preference_response["response"]
        return jsonify({"id": preference["id"], "init_point": preference["init_point"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
