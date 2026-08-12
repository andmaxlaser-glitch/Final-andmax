def calcular_precio(perimetro, material, espesor):
    precios = {
        "MDF": {1: 600, 2: 700, 3: 800, 5: 900, 8: 1000, 10: 1200},
        "Acrilico": {1: 800, 2: 900, 3: 1000, 4: 1100, 5: 1200, 6: 1400, 8: 1600, 10: 1800},
        "Acero al carbono": {1: 8500, 2: 9350, 3: 10285, 4: 11313, 5: 12444, 6: 13689, 8: 15058, 10: 16564, 12: 18220},
        "Acero inoxidable": {1: 8500, 2: 9350, 3: 10285, 4: 11313, 5: 12444, 6: 13689, 8: 15058, 10: 16564, 12: 18220},
        "Aluminio": {1: 8500, 2: 9350, 3: 10285, 4: 11313, 5: 12444, 6: 13689, 8: 15058, 10: 16564, 12: 18220}
    }
    
    # Obtener costo unitario según material y espesor
    costo_unitario = precios.get(material, {}).get(int(espesor), 0)
    return round(perimetro * costo_unitario, 2)
        }
    except Exception as e:
        return {"estado": "error", "mensaje": f"No pude leer el archivo: {str(e)}"}
