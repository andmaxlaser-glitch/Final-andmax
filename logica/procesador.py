import ezdxf
import math

def calcular_precio(perimetro_mm, material, espesor):
    # Tabla de precios por METRO de corte según material y espesor
    precios = {
        "MDF": {1: 600, 2: 700, 3: 800, 5: 900, 8: 1000, 10: 1200},
        "Acrilico": {1: 800, 2: 900, 3: 1000, 4: 1100, 5: 1200, 6: 1400, 8: 1600, 10: 1800},
        "Acero al carbono": {1: 8500, 2: 9350, 3: 10285, 4: 11313, 5: 12444, 6: 13689, 8: 15058, 10: 16564, 12: 18220},
        "Acero inoxidable": {1: 8500, 2: 9350, 3: 10285, 4: 11313, 5: 12444, 6: 13689, 8: 15058, 10: 16564, 12: 18220},
        "Aluminio": {1: 8500, 2: 9350, 3: 10285, 4: 11313, 5: 12444, 6: 13689, 8: 15058, 10: 16564, 12: 18220}
    }
    
    try:
        esp_int = int(espesor)
        costo_por_metro = precios.get(material, {}).get(esp_int, 0)
        
        # Convertimos los milímetros del perímetro a metros
        perimetro_metros = perimetro_mm / 1000
        
        # Precio final = Metros de corte * Precio por metro de la lista
        return round(perimetro_metros * costo_por_metro, 2)
    except:
        return 0.0

def analizar_dxf(ruta_archivo, material="MDF", espesor=1):
    try:
        doc = ezdxf.readfile(ruta_archivo)
        msp = doc.modelspace()
        
        perimetro_total = 0.0
        
        circulos = list(msp.query('CIRCLE'))
        for c in circulos:
            perimetro_total += 2 * math.pi * c.dxf.radius
            
        lineas = list(msp.query('LINE'))
        for l in lineas:
            p1, p2 = l.dxf.start, l.dxf.end
            perimetro_total += math.sqrt((p2.x - p1.x)**2 + (p2.y - p1.y)**2)
            
        arcos = list(msp.query('ARC'))
        for a in arcos:
            angulo = abs(a.dxf.end_angle - a.dxf.start_angle)
            perimetro_total += 2 * math.pi * a.dxf.radius * (angulo / 360.0)

        polilineas = list(msp.query('LWPOLYLINE'))
        for pl in polilineas:
            perimetro_total += pl.length

        perimetro_redondeado = round(perimetro_total, 2)
        precio_calculado = calcular_precio(perimetro_redondeado, material, espesor)

        return {
            "estado": "exito",
            "conteo_elementos": {
                "lineas": len(lineas),
                "circulos": len(circulos),
                "arcos": len(arcos),
                "polilineas": len(polilineas)
            },
            "perimetro_total_mm": perimetro_redondeado,
            "material": material,
            "espesor": espesor,
            "precio_total": precio_calculado
        }
    except Exception as e:
        return {"estado": "error", "mensaje": f"No pude leer el archivo: {str(e)}"}
