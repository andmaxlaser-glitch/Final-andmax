import os
import gc
import mercadopago
import resend
from flask import Flask, render_template, request, jsonify
from logica.procesador import analizar_dxf

app = Flask(__name__)
UPLOAD_FOLDER = 'pruebas'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configuración de Mercado Pago
MP_ACCESS_TOKEN = os.environ.get('MP_ACCESS_TOKEN', 'TU_ACCESS_TOKEN_DE_MERCADO_PAGO')
sdk = mercadopago.SDK(MP_ACCESS_TOKEN)

# Configuración de Resend API
resend.api_key = os.environ.get('RESEND_API_KEY', 're_tu_api_key_aqui')

# Definimos directamente tu correo de destino para evitar errores de variables faltantes
CORREO_DESTINO = os.environ.get('CORREO_DESTINO', 'andmaxlaser@gmail.com')

ordenes_pendientes = {}

@app.route('/')
def index():
    status = request.args.get('status')
    preference_id = request.args.get('preference_id')
    
    if status == 'approved' and preference_id and preference_id in ordenes_pendientes:
        datos_compra = ordenes_pendientes.pop(preference_id)
        
        # Envío directo del correo al volver del pago aprobado
        enviar_correo_nuevo_pedido(app, datos_compra)
        
        return render_template('index.html', pago_exitoso=True)
        
    return render_template('index.html', pago_exitoso=False)

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
        resultado['nombre_archivo_fisico'] = archivo.filename
        gc.collect()
        
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
        
        if "response" in preference_response and "id" in preference_response["response"]:
            preference = preference_response["response"]
            pref_id = preference["id"]
            ordenes_pendientes[pref_id] = datos_carrito
            return jsonify({"id": pref_id, "init_point": preference["init_point"]})
        else:
            error_msg = preference_response.get("response", "Respuesta desconocida de MP")
            return jsonify({"error": str(error_msg)}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def enviar_correo_nuevo_pedido(app_context, carrito):
    with app_context.app_context():
        try:
            cuerpo_html = "<h3>Has recibido un nuevo pedido abonado a través de la web:</h3><ul>"
            for item in carrito:
                cuerpo_html += f"""
                    <li>
                        <b>Archivo:</b> {item.get('nombre_archivo')}<br>
                        <b>Material:</b> {item.get('material')} - <b>Espesor:</b> {item.get('espesor')} mm<br>
                        <b>Cantidad:</b> {item.get('cantidad')} u.<br>
                        <b>Dimensiones:</b> {item.get('dimensiones')} | <b>Subtotal:</b> ${item.get('precio_total'):,.2f}
                    </li><br>
                """
            cuerpo_html += "</ul><p>Los planos originales se encuentran adjuntos en este correo.</p>"

            # Preparar archivos adjuntos para Resend
            adjuntos = []
            for item in carrito:
                nombre_fisico = item.get('nombre_archivo_fisico')
                if nombre_fisico:
                    ruta_completa = os.path.join(app.config['UPLOAD_FOLDER'], nombre_fisico)
                    if os.path.exists(ruta_completa):
                        with open(ruta_completa, 'rb') as f:
                            contenido_bytes = f.read()
                            import base64
                            contenido_base64 = base64.b64encode(contenido_bytes).decode('utf-8')
                            adjuntos.append({
                                "filename": item.get('nombre_archivo', 'pieza.dxf'),
                                "content": contenido_base64
                            })

            params = {
                "from": "onboarding@resend.dev",
                "to": [CORREO_DESTINO],
                "subject": "¡Nuevo pedido de corte láser pagado! 🚀",
                "html": cuerpo_html,
                "attachments": adjuntos
            }

            email = resend.Emails.send(params)
            print(f"¡Correo enviado con éxito mediante Resend! ID: {email}")
            gc.collect()
        except Exception as e:
            print(f"Error detallado al enviar el correo con Resend: {e}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
