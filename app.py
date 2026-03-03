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
    c.line(w/2 - 0.3*cm, h/2, w/2 + 0.3*cm, h/2)
    c.line(w/2, h/2 - 0.3*cm, w/2, h/2 + 0.3*cm)
    # Σημάδια στις πλευρές
    offset = 0.3 * cm
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
        label_height = h/2

        # --- price zone (0 → 6.5 cm from top) --------------------------------
        # determine centers of specified zones
        center_x = x_start + 5.25 * cm
        # integer zone center: from 1cm to 6cm -> midpoint 3.5cm from top
        int_baseline = quad_top - 3.5 * cm
        # decimal zone center: from 1.8cm to 6cm -> midpoint 3.9cm from top
        dec_baseline = quad_top - 3.9 * cm

        price = data['prices'][i]
        if "," in price:
            int_part, frac = price.split(",", 1)
            dec_part = "," + frac
        else:
            int_part = price
            dec_part = ""

        # measure widths for centering
        int_width = c.stringWidth(int_part, "Helvetica-Bold", data['int_size'])
        dec_width = 0
        if dec_part:
            dec_size = data['int_size'] * 0.85
            dec_width = c.stringWidth(dec_part, "Helvetica-Bold", dec_size)
        total_width = int_width + dec_width
        start_left = center_x - total_width / 2

        # draw integer part stretched vertically covering 1–6cm zone
        c.saveState()
        c.scale(1, 1.5)
        c.setFont("Helvetica-Bold", data['int_size'])
        c.drawString(start_left, int_baseline / 1.5, int_part)
        c.restoreState()

        # draw decimal part stretched vertically covering 1.8–6cm zone
        y_euro = dec_baseline  # use decimal baseline for euro alignment as well
        if dec_part:
            c.saveState()
            c.scale(1, 1.2)
            c.setFont("Helvetica-Bold", dec_size)
            c.drawString(start_left + int_width + 1, dec_baseline / 1.2, dec_part)
            c.restoreState()

        # euro symbol after decimals, unscaled
        spacing = 2  # points of padding
        euro_x = center_x + total_width/2 + spacing
        euro_font_size = 30
        c.setFont("Helvetica-Bold", euro_font_size)
        c.drawString(euro_x, y_euro, "€")

        # --- description zone (6.8 → 11 cm from top) -------------------------
        zone_top = quad_top - 6.8 * cm
        zone_bottom = quad_top - 11 * cm
        zone_height = zone_top - zone_bottom
        p = Paragraph(data['descs'][i], style)
        p.wrap(9 * cm, zone_height)
        # center vertically inside the zone
        desc_bottom = zone_bottom + (zone_height - p.height) / 2
        p.drawOn(c, x_start + (10.5 * cm - 9 * cm) / 2, desc_bottom)

        # --- logo zone (11.2 cm from top to bottom) ---------------------------
        if data['logo']:
            logo_img = ImageReader(data['logo'])
            logo_w, logo_h = 8.4 * cm, 3.84 * cm
            logo_x = x_start + (10.5 * cm - logo_w) / 2
            # position so that the top of the image is 11.2cm below quad_top
            logo_top = quad_top - 11.2 * cm
            logo_y = logo_top - logo_h
            c.drawImage(logo_img, logo_x, logo_y, width=logo_w, height=logo_h, preserveAspectRatio=True)

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
        # show preview below the button
        try:
            import base64
            pdf.seek(0)
            b64 = base64.b64encode(pdf.read()).decode('utf-8')
            pdf_display = f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="400px"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)
        except Exception:
            pass
        st.download_button("Κατέβασμα PDF", pdf, "Tags.pdf", "application/pdf")
