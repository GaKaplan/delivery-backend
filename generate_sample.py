from reportlab.pdfgen import canvas

def create_sample_pdf(filename):
    c = canvas.Canvas(filename)
    c.drawString(100, 800, "Lista de Reparto - Enero 2026")
    
    addresses = [
        "Juan Perez - Av. Corrientes 1234, Buenos Aires, Argentina",
        "Maria Garcia - Av. Rivadavia 5000, Buenos Aires, Argentina",
        "Carlos Lopez - Calle Florida 500, Buenos Aires, Argentina",
        "Ana Martinez - Av. Santa Fe 3000, Buenos Aires, Argentina",
        "Pedro Sanchez - Av. Belgrano 1000, Buenos Aires, Argentina"
    ]
    
    y = 750
    for addr in addresses:
        c.drawString(100, y, addr)
        y -= 20
        
    c.save()
    print(f"Created {filename}")

if __name__ == "__main__":
    create_sample_pdf("sample_delivery.pdf")
