import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader  # Αυτό επιλύει το σφάλμα της εικόνας
from io import BytesIO

# Ρυθμίσεις σελίδας
st.set_page_config(page_title="Εκτυπωτής Ετικετών", layout="wide")

st.title("🏷️ Εκτυπωτής Ετικετών (Web Version)")

# --- Συναρτήσεις Σχεδίασης ---
def draw_crop_marks(c, w, h):
    length = 0.8 * cm
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(0.5)
    # Σταυρός στο κέντρο
    c.line(w/2 - 0.8*cm, h/2, w/2 + 0.8*cm, h/2)
    c.line(w/2, h/2 - 0.8*cm, w/2, h/2 + 0.8*cm)
    # Σημάδια στις πλευρές
    offset = 0.5 * cm
    c.line(w/2, h - offset, w/2, h - offset - length)
    c.line(w/2, offset, w/2, offset + length)
    c.line(offset, h/2, offset + length, h/2)
    c.line(w - offset, h/2, w - offset - length, h/2)

def generate_pdf(data):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4
    quads = [(0, h/2), (w/2, h/2), (0, 0), (w/2, 0)]
    
    style = ParagraphStyle(name='C', fontSize=data['desc_size'], leading=data['desc_size']+4, alignment=1)

    for i in range(4):
        x_start, y_start = quads[i]
        quad_top = y_start + (h/2)
        
        # Λογότυπο με χρήση ImageReader για αποφυγή σφαλμάτων διαδρομής
        if data['logo']:
            logo_img = ImageReader(data['logo'])
            logo_w, logo_h = 8.4 * cm, 3.84 * cm
            logo_x = x_start + (10.5*cm - logo_w) / 2
            c.drawImage(logo_img, logo_x, y_start + 0.5*cm, width=logo_w, height=logo_h, preserveAspectRatio=True)

        # Τιμή με Stretch (Scale)
        c.saveState()
        c.scale(1, 1.5) 
        c.setFont("Helvetica-Bold", data['int_size'])
        y_pos = (quad_top - 6*cm) / 1.5 # Προσαρμογή ύψους λόγω scale
        c.drawCentredString(x_start + 5.25*cm, y_pos, data['prices'][i])
        c.restoreState()
        
        # Περιγραφή
        p = Paragraph(data['descs'][i], style)
        p.wrap(9*cm, 4*cm)
        p.drawOn(c, x_start + (10.5*cm - 9*cm)/2, quad_top - 7*cm)

    draw_crop_marks(c, w, h)
    c.save()
    buffer.seek(0)
    return buffer



# --- GUI ---
st.sidebar.header("Ρυθμίσεις")
int_size = st.sidebar.slider("Μέγεθος Τιμής", 50, 150, 120)
desc_size = st.sidebar.slider("Μέγεθος Περιγραφής", 10, 50, 30)

logo_file = st.file_uploader("Ανέβασμα Λογοτύπου", type=['png', 'jpg', 'jpeg'])

descs = []
prices = []
cols = st.columns(2)
for i in range(4):
    with cols[i % 2]:
        descs.append(st.text_area(f"Περιγραφή {i+1}", height=60))
        prices.append(st.text_input(f"Τιμή {i+1}", "0,00"))

if st.button("ΔΗΜΙΟΥΡΓΙΑ PDF"):
    data = {'descs': descs, 'prices': prices, 'logo': logo_file, 'int_size': int_size, 'desc_size': desc_size}
    pdf = generate_pdf(data)
    st.download_button("Κατέβασμα PDF", pdf, "Tags.pdf", "application/pdf")