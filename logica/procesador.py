import ezdxf
import math
import io
import traceback
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.svg import SVGBackend

def calcular_precio_pro(perimetro_mm, ancho_mm, alto_mm, material, espesor):
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
        
        precio_total = costo_corte + costo_material
        precio_minimo = 2000 if "Acero" in material or material == "Aluminio" else 800
        
        if precio_total < precio_minimo:
            precio_total = precio_minimo
            
        return round(precio_total, 2)
    except:
        return 0.0

def generar_svg(ruta_archivo):
    try:
        doc = ezdxf.readfile(ruta_archivo)
        msp = doc.modelspace()
        
        out = io.StringIO()
        backend = SVGBackend(out)
        ctx = RenderContext(doc)
        Frontend(ctx, backend).draw_layout(msp, finalize=True)
        
        return out.getvalue()
    except Exception as e:
        # Imprime el error exacto en los logs de Render para depurar
        print(f"Error generando SVG: {traceback.format_exc()}")
        return ""

def analizar_dxf(ruta_archivo, material="MDF", espesor=1):
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

        circulos = list(msp.query('CIRCLE'))
        for c in circulos:
            perimetro_total += 2 * math.pi * c.dxf.radius
            actualizar_limites(c.dxf.center.x - c.dxf.radius, c.dxf.center.y - c.dxf.radius)
            actualizar_limites(c.dxf.center.x + c.dxf.radius, c.dxf.center.y + c.dxf.radius)
            
        lineas = list(msp.query('LINE'))
        for l in lineas:
            p1, p2 = l.dxf.start, l.dxf.end
            perimetro_total += math.sqrt((p2.x - p1.x)**2 + (p2.y - p1.y)**2)
            actualizar_limites(p1.x, p1.y)
            actualizar_limites(p2.x, p2.y)
            
        arcos = list(msp.query('ARC'))
        for a in arcos:
            angulo = abs(a.dxf.end_angle - a.dxf.start_angle)
            perimetro_total += 2 * math.pi * a.dxf.radius * (angulo / 360.0)
            actualizar_limites(a.dxf.center.x - a.dxf.radius, a.dxf.center.y - a.dxf.radius)
            actualizar_limites(a.dxf.center.x + a.dxf.radius, a.dxf.center.y + a.dxf.radius)

        polilineas = list(msp.query('LWPOLYLINE'))
        for pl in polilineas:
            perimetro_total += pl.length
            for p in pl.get_points():
                actualizar_limites(p[0], p[1])

        ancho_mm = max_x - min_x if max_x > min_x else 100
        alto_mm = max_y - min_y if max_y > min_y else 100

        perimetro_redondeado = round(perimetro_total, 2)
        precio_calculado = calcular_precio_pro(perimetro_redondeado, ancho_mm, alto_mm, material, espesor)
        svg_code = generar_svg(ruta_archivo)

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
            "precio_total": precio_calculado,
            "svg_data": svg_code
        }
    except Exception as e:
        return {"estado": "error", "mensaje": f"No pude leer el archivo: {str(e)}"}
