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
    # each label occupies one quarter of the A4 page
    label_w = w / 2
    label_h = h / 2
    # corners of the four label quadrants (lower-left origin coordinates)
    quads = [
        (0, label_h),
        (label_w, label_h),
        (0, 0),
        (label_w, 0)
    ]
    
    style = ParagraphStyle(name='C', fontSize=data['desc_size'], leading=data['desc_size']+4, alignment=1)

    for i in range(4):
        x_start, y_start = quads[i]
        quad_top = y_start + label_h

        # --- price zone -----------------------------------------------------
        # from 1cm down to 6.8cm from the label top, with 0.8cm side margins
        PRICE_ZONE_TOP_MARGIN = 1 * cm
        PRICE_ZONE_BOTTOM_MARGIN = 6.8 * cm
        price_zone_top = quad_top - PRICE_ZONE_TOP_MARGIN
        price_zone_bottom = quad_top - PRICE_ZONE_BOTTOM_MARGIN
        price_zone_height = price_zone_top - price_zone_bottom
        price_zone_x0 = x_start + 0.8 * cm
        price_zone_width = label_w - 1.6 * cm

        center_x = x_start + label_w / 2
        baseline_y = price_zone_bottom

        price = data['prices'][i]
        if "," in price:
            int_part, frac = price.split(",", 1)
            dec_part = "," + frac
        else:
            int_part = price
            dec_part = ""

        int_width = c.stringWidth(int_part, "Helvetica-Bold", data['int_size'])
        dec_width = c.stringWidth(dec_part, "Helvetica-Bold", data['int_size']) if dec_part else 0
        total_width = int_width + dec_width

        # horizontal scaling to fit available width
        h_scale = 1.0
        if total_width > price_zone_width:
            h_scale = price_zone_width / total_width
            total_width *= h_scale

        # vertical scaling
        int_target_height = price_zone_height
        dec_target_height = ((quad_top - 1.5 * cm) - price_zone_bottom)
        if dec_target_height > price_zone_height:
            dec_target_height = price_zone_height
        v_scale_int = int_target_height / data['int_size']
        v_scale_dec = dec_target_height / data['int_size']

        start_left = center_x - total_width / 2

        c.saveState()
        c.scale(h_scale, v_scale_int)
        c.setFont("Helvetica-Bold", data['int_size'])
        c.drawString(start_left / h_scale, baseline_y / v_scale_int, int_part)
        c.restoreState()

        if dec_part:
            c.saveState()
            c.scale(h_scale, v_scale_dec)
            c.setFont("Helvetica-Bold", data['int_size'])
            c.drawString((start_left + int_width) / h_scale, baseline_y / v_scale_dec, dec_part)
            c.restoreState()

        euro_x = start_left + total_width + 2
        euro_font = data['int_size']
        c.saveState()
        c.scale(h_scale, 1)
        c.setFont("Helvetica-Bold", euro_font)
        c.drawString(euro_x / h_scale, baseline_y, "€")
        c.restoreState()

        # --- description zone ------------------------------------------------
        DESC_ZONE_TOP_MARGIN = 7.3 * cm
        DESC_ZONE_BOTTOM_MARGIN = 10.8 * cm
        desc_zone_top = quad_top - DESC_ZONE_TOP_MARGIN
        desc_zone_bottom = quad_top - DESC_ZONE_BOTTOM_MARGIN
        desc_zone_height = desc_zone_top - desc_zone_bottom
        desc_zone_x0 = x_start + 0.8 * cm
        desc_zone_width = label_w - 1.6 * cm

        p = Paragraph(data['descs'][i], style)
        p.wrap(desc_zone_width, desc_zone_height)
        desc_x = desc_zone_x0
        desc_y = desc_zone_top - p.height
        p.drawOn(c, desc_x, desc_y)

        # --- logo zone -------------------------------------------------------
        LOGO_ZONE_BOTTOM_MARGIN = 0.5 * cm
        LOGO_ZONE_TOP_MARGIN = 4 * cm
        logo_zone_bottom = y_start + LOGO_ZONE_BOTTOM_MARGIN
        logo_zone_top = y_start + LOGO_ZONE_TOP_MARGIN
        logo_zone_height = logo_zone_top - logo_zone_bottom
        logo_zone_x0 = x_start + 1 * cm
        logo_zone_width = label_w - 2 * cm

        if data['logo']:
            logo_img = ImageReader(data['logo'])
            c.drawImage(
                logo_img,
                logo_zone_x0,
                logo_zone_bottom,
                width=logo_zone_width,
                height=logo_zone_height,
                preserveAspectRatio=True,
                anchor='c',
            )

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
