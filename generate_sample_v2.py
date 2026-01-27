from reportlab.pdfgen import canvas

def create_sample_pdf(filename):
    c = canvas.Canvas(filename)
    c.drawString(100, 800, "Hoja de Ruta 7024")
    c.drawString(100, 780, "Desde 20/01/2026 hasta 21/01/2026")
    
    # Headers simulating the user's PDF
    c.drawString(50, 750, "Cód.Cli.   Cliente o Dirección                  Cant. Bultos   Horario")
    
    # Data in "Code 0 Address" format
    data = [
        "7145   0 AV GAONA 2759               14    10:00 A 23:00",
        "5046   0 AV SAN MARTIN 7170          25    9 a 14",
        "6057   0 CARLOS ANTONIO LOPEZ 3585   38    10:00 a 14:00",
        "1467   0 CARLOS CALVO 4251           9     10 a 14",
        "6700   0 CHARRUA 3172                10    -",
        "453    0 CORDOBA 4001                30    9:00 A 14:00",
        "608    0 GASCON 285                  8     9 A 14 30"
    ]
    
    y = 730
    for line in data:
        c.drawString(50, y, line)
        y -= 20
        
    c.save()
    print(f"Created {filename}")

if __name__ == "__main__":
    create_sample_pdf("sample_delivery_v2.pdf")
