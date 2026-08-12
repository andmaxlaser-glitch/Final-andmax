import ezdxf
import math

def calcular_precio_pro(perimetro_mm, ancho_mm, alto_mm, material, espesor, cantidad):
    precios = {
        "MDF": {1: 600, 2: 700, 3: 800, 5: 900, 8: 1000, 10: 1200},
        "Acrilico": {1: 800, 2: 900, 3: 1000, 4: 1100, 5: 1200, 6: 1400, 8: 1600, 10: 1800},
        "Acero al carbono": {1: 8500, 2: 9350, 3: 10285, 4: 11313, 5: 12444, 6: 13689, 8: 15058, 10: 16564, 12: 18220},
        "Acero inoxidable": {1: 8500, 2: 9350, 3: 10285, 4: 11313, 5: 12444, 6: 13689, 8: 15058, 10: 16564, 12: 18220},
        "Aluminio": {1: 8500, 2: 9350, 3: 10285, 4: 11313, 5: 12444, 6: 13689, 8: 15058, 10: 16564, 12: 18220}
    }
    
    try:
        esp_int = int(espesor)
        tarifa_base = precios.get(material, {}).get(esp_int, 0)
        
        metros_corte = perimetro_mm / 1000
        if metros_corte < 0.5:
            metros_corte = 0.5  
            
        costo_corte = metros_corte * tarifa_base
        area_m2 = (ancho_mm / 1000) * (alto_mm / 1000)
        costo_material = area_m2 * (tarifa_base * 0.4) 
        
        # Precio por una unidad
        precio_unitario = costo_corte + costo_material
        precio_minimo = 2000 if "Acero" in material or material == "Aluminio" else 800
        
        if precio_unitario < precio_minimo:
            precio_unitario = precio_minimo
            
        # Precio total multiplicando por la cantidad de piezas
        precio_total = precio_unitario * cantidad
        return round(precio_total, 2)
    except:
        return 0.0

def analizar_dxf(ruta_archivo, material="MDF", espesor=1, cantidad=1):
    try:
        doc = ezdxf.readfile(ruta_archivo)
        msp = doc.modelspace()
        
        perimetro_total = 0.0
        min_x, min_y = float('inf'), float('inf')
        max_x, max_y = float('-inf'), float('-inf')

        def actualizar_limites(x, y):
            nonlocal min_x, min_y, max_x, max_y
            if x < min_x: min_x = x
            if y < min_y: min_y = y
            if x > max_x: max_x = x
            if y > max_y: max_y = y

        geometrias = {
            "lineas": [],
            "circulos": [],
            "arcos": [],
            "polilineas": []
        }

        circulos = list(msp.query('CIRCLE'))
        for c in circulos:
            perimetro_total += 2 * math.pi * c.dxf.radius
            cx, cy, r = c.dxf.center.x, c.dxf.center.y, c.dxf.radius
            geometrias["circulos"].append({"cx": cx, "cy": cy, "r": r})
            actualizar_limites(cx - r, cy - r)
            actualizar_limites(cx + r, cy + r)
            
        lineas = list(msp.query('LINE'))
        for l in lineas:
            p1, p2 = l.dxf.start, l.dxf.end
            perimetro_total += math.sqrt((p2.x - p1.x)**2 + (p2.y - p1.y)**2)
            geometrias["lineas"].append({"x1": p1.x, "y1": p1.y, "x2": p2.x, "y2": p2.y})
            actualizar_limites(p1.x, p1.y)
            actualizar_limites(p2.x, p2.y)
            
        arcos = list(msp.query('ARC'))
        for a in arcos:
            angulo = abs(a.dxf.end_angle - a.dxf.start_angle)
            perimetro_total += 2 * math.pi * a.dxf.radius * (angulo / 360.0)
            geometrias["arcos"].append({
                "cx": a.dxf.center.x, "cy": a.dxf.center.y, "r": a.dxf.radius,
                "start": math.radians(a.dxf.start_angle), "end": math.radians(a.dxf.end_angle)
            })
            actualizar_limites(a.dxf.center.x - a.dxf.radius, a.dxf.center.y - a.dxf.radius)
            actualizar_limites(a.dxf.center.x + a.dxf.radius, a.dxf.center.y + a.dxf.radius)

        polilineas = list(msp.query('LWPOLYLINE'))
        for pl in polilineas:
            perimetro_total += pl.length
            pts = [(p[0], p[1]) for p in pl.get_points()]
            geometrias["polilineas"].append(pts)
            for p in pts:
                actualizar_limites(p[0], p[1])

        ancho_mm = max_x - min_x if max_x > min_x else 100
        alto_mm = max_y - min_y if max_y > min_y else 100

        perimetro_redondeado = round(perimetro_total, 2)
        precio_calculado = calcular_precio_pro(perimetro_redondeado, ancho_mm, alto_mm, material, espesor, cantidad)

        return {
            "estado": "exito",
            "conteo_elementos": {
                "lineas": len(lineas),
                "circulos": len(circulos),
                "arcos": len(arcos),
                "polilineas": len(polilineas)
            },
            "perimetro_total_mm": perimetro_redondeado,
            "dimensiones": f"{round(ancho_mm, 1)} x {round(alto_mm, 1)} mm",
            "material": material,
            "espesor": espesor,
            "cantidad": cantidad,
            "precio_total": precio_calculado,
            "bounds": {"min_x": min_x, "min_y": min_y, "max_x": max_x, "max_y": max_y, "width": ancho_mm, "height": alto_mm},
            "geometrias": geometrias
        }
    except Exception as e:
        return {"estado": "error", "mensaje": f"No pude leer el archivo: {str(e)}"}
