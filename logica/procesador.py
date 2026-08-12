import ezdxf
import math

def analizar_dxf(ruta_archivo):
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

        return {
            "estado": "exito",
            "conteo_elementos": {
                "lineas": len(lineas),
                "circulos": len(circulos),
                "arcos": len(arcos),
                "polilineas": len(polilineas)
            },
            "perimetro_total_mm": round(perimetro_total, 2)
        }
    except Exception as e:
        return {"estado": "error", "mensaje": f"No pude leer el archivo: {str(e)}"}
