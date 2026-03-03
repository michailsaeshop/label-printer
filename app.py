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
        # draw the price with vertical stretch
        c.saveState()
        c.scale(1, 1.5) 
        c.setFont("Helvetica-Bold", data['int_size'])
        y_pos = (quad_top - 6*cm) / 1.5  # Προσαρμογή ύψους λόγω scale
        c.drawCentredString(x_start + 5.25*cm, y_pos, data['prices'][i])
        c.restoreState()

        # after unscaling, draw euro symbol without stretch
        price = data['prices'][i]
        # compute text width using the same font size as the price
        text_width = c.stringWidth(price, "Helvetica-Bold", data['int_size'])
        center_x = x_start + 5.25*cm
        euro_font_size = 30
        # final y coordinate unscaled
        y_euro = quad_top - 6*cm
        # position euro sign just to the right of the price text
        spacing = 2  # points of padding
        euro_x = center_x + text_width/2 + spacing
        c.setFont("Helvetica-Bold", euro_font_size)
        c.drawString(euro_x, y_euro, "€")
        
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
# styled sliders with bold, larger labels
st.sidebar.markdown("<span style='font-size:18px; font-weight:bold;'>Μέγεθος Τιμής</span>", unsafe_allow_html=True)
int_size = st.sidebar.slider("", 50, 150, 120)

st.sidebar.markdown("<span style='font-size:18px; font-weight:bold;'>Μέγεθος Περιγραφής</span>", unsafe_allow_html=True)
desc_size = st.sidebar.slider("", 10, 50, 30)

# styled title for logo uploader matching other headings
st.markdown("<span style='font-size:20px; font-weight:bold;'>Ανέβασμα Λογοτύπου</span>", unsafe_allow_html=True)
# remove default label so widget appears directly under title
logo_file = st.file_uploader("", type=["png", "jpg", "jpeg"])

# tighten spacing between labels and their inputs via small CSS hack
st.markdown("""
    <style>
    /* reduce bottom margin on widget rows to bring inputs closer to titles */
    div[data-baseweb="file-uploader"],
    div.stTextInput, div.stTextArea {
        margin-top: 0.2rem !important;
        margin-bottom: 0.2rem !important;
    }
    </style>
""", unsafe_allow_html=True)

# main inputs for four labels
descs = []
prices = []
cols = st.columns(2)
for i in range(4):
    with cols[i % 2]:
        # custom styled labels for inputs
        st.markdown(f"<span style='font-size:20px; font-weight:bold;'>Περιγραφή {i+1}</span>", unsafe_allow_html=True)
        # provide unique keys to avoid duplicate element IDs
        descs.append(st.text_area("", height=60, key=f"desc_{i}"))
        st.markdown(f"<span style='font-size:20px; font-weight:bold;'>Τιμή {i+1}</span>", unsafe_allow_html=True)
        prices.append(st.text_input("", "0,00", key=f"price_{i}"))

# generate/download PDF when requested
if st.button("ΔΗΜΙΟΥΡΓΙΑ PDF"):
    data = {
        'descs': descs,
        'prices': prices,
        'logo': logo_file,
        'int_size': int_size,
        'desc_size': desc_size,
    }
    pdf = generate_pdf(data)
    st.download_button("Κατέβασμα PDF", pdf, "Tags.pdf", "application/pdf")
