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
        titulo = f"Corte Láser: {item.get('nombre_archivo', 'Pieza')} ({item.get('material')} {item.get('espesor')}mm)"
        cantidad = int(item.get('cantidad', 1))
        precio_unitario = float(item.get('precio_total', 0)) / cantidad
        
        items_mp.append({
            "title": titulo,
            "quantity": cantidad,
            "currency_id": "ARS",
            "unit_price": round(precio_unitario, 2)
        })

    # Obtenemos la URL actual de tu sitio automáticamente para el retorno de pago
    base_url = request.host_url.rstrip('/')

    preference_data = {
        "items": items_mp,
        "back_urls": {
            "success": f"{base_url}/",
            "failure": f"{base_url}/",
            "pending": f"{base_url}/"
        },
        "auto_return": "approved",
    }

    try:
        preference_response = sdk.preference().create(preference_data)
        
        # Imprimimos la respuesta completa en la consola de Render por si hay dudas
        print("Respuesta de Mercado Pago:", preference_response)
        
        if "response" in preference_response and "id" in preference_response["response"]:
            preference = preference_response["response"]
            return jsonify({"id": preference["id"], "init_point": preference["init_point"]})
        else:
            # Si Mercado Pago devolvió un error de validación, lo capturamos
            error_msg = preference_response.get("response", "Respuesta desconocida de MP")
            return jsonify({"error": str(error_msg)}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500
