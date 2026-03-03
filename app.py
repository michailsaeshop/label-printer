import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader  # Αυτό επιλύει το σφάλμα της εικόνας
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO

# register Arial Bold font (assumes font file available in system)
# common filename 'arialbd.ttf'; fall back silently if missing
FONT_NAME = 'Helvetica-Bold'  # default
try:
    pdfmetrics.registerFont(TTFont('Arial-Bold', 'arialbd.ttf'))
    FONT_NAME = 'Arial-Bold'
except Exception:
    try:
        pdfmetrics.registerFont(TTFont('Arial-Bold', 'Arial Bold.ttf'))
        FONT_NAME = 'Arial-Bold'
    except Exception:
        # registration failed; keep default FONT_NAME
        pass

# Ρυθμίσεις σελίδας
# you can specify a page_icon (emoji or path to image) for the app
st.set_page_config(page_title="Εκτυπωτής Ετικετών", page_icon="🏷️", layout="wide")

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

        # parse price into integer and decimal parts (comma included)
        price = data['prices'][i]
        if "," in price:
            int_part, frac = price.split(",", 1)
            dec_part = "," + frac
        else:
            int_part = price
            dec_part = ""

        # areas relative to the top/left of the label (no print margins)
        # integer area: 0.8–6.8cm vertical, 0.6–4.7cm horizontal
        int_top_offset = 0.8 * cm
        int_bottom_offset = 6.8 * cm
        int_left_offset = 0.6 * cm
        int_right_offset = 4.7 * cm
        int_height_area = int_bottom_offset - int_top_offset   # 6.0cm
        int_area_right_x = x_start + int_right_offset
        baseline_y = quad_top - int_bottom_offset               # bottom of int area

        # compute vertical scale to fill the area
        v_scale_int = int_height_area / data['int_size']

        # decimal area: 1.5–6.8cm vertical, 4.9–9.1cm horizontal
        dec_top_offset = 1.5 * cm
        dec_bottom_offset = 6.8 * cm
        dec_left_offset = 4.9 * cm
        dec_right_offset = 9.1 * cm
        dec_height_area = dec_bottom_offset - dec_top_offset   # 5.3cm
        dec_area_right_x = x_start + dec_right_offset
        dec_area_left_x = x_start + dec_left_offset
        # note bottom of decimal area is same as integer

        v_scale_dec = dec_height_area / data['int_size']

        # compute widths of each part (unscaled)
        int_width = c.stringWidth(int_part, FONT_NAME, data['int_size'])
        dec_width = c.stringWidth(dec_part, FONT_NAME, data['int_size']) if dec_part else 0

        # compute horizontal scale to fit widths into their areas
        int_area_left_x = x_start + int_left_offset
        int_area_width = int_right_offset - int_left_offset
        h_scale_int = 1.0
        if int_width > 0 and int_width > int_area_width:
            h_scale_int = int_area_width / int_width

        dec_area_width = dec_right_offset - dec_left_offset
        h_scale_dec = 1.0
        if dec_width > 0 and dec_width > dec_area_width:
            h_scale_dec = dec_area_width / dec_width

        # draw integer part right-aligned, bottom-aligned with both scales
        scaled_int_width = int_width * h_scale_int
        start_x_int = int_area_right_x - scaled_int_width
        c.saveState()
        c.scale(h_scale_int, v_scale_int)
        c.setFont(FONT_NAME, data['int_size'])
        c.drawString(start_x_int / h_scale_int, baseline_y / v_scale_int, int_part)
        c.restoreState()

        # draw decimal part if exists
        if dec_part:
            scaled_dec_width = dec_width * h_scale_dec
            start_x_dec = dec_area_right_x - scaled_dec_width
            c.saveState()
            c.scale(h_scale_dec, v_scale_dec)
            c.setFont(FONT_NAME, data['int_size'])
            c.drawString(start_x_dec / h_scale_dec, baseline_y / v_scale_dec, dec_part)
            c.restoreState()

        # euro symbol area: 9.3–10.1cm horizontal, font size fixed at 30
        euro_right_offset = 10.1 * cm
        euro_area_right_x = x_start + euro_right_offset
        euro_font = 30
        euro_width = c.stringWidth("€", FONT_NAME, euro_font)
        euro_x = euro_area_right_x - euro_width
        c.saveState()
        c.setFont(FONT_NAME, euro_font)
        c.drawString(euro_x, baseline_y, "€")
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
# add CSS for framing each label's inputs
st.markdown("""
    <style>
    .label-box {
        border: 1px solid #ccc;
        padding: 0.75rem;
        margin-bottom: 1rem;
        border-radius: 4px;
        background-color: #f9f9f9;
    }
    </style>
""", unsafe_allow_html=True)
descs = []
prices = []
cols = st.columns(2)
for i in range(4):
    with cols[i % 2]:
        # wrap this label's controls in a box
        st.markdown("<div class='label-box'>", unsafe_allow_html=True)
        # input titles
        st.markdown(f"<span style='font-size:20px; font-weight:bold;'>Περιγραφή {i+1}</span>", unsafe_allow_html=True)
        # provide unique keys and capture values
        desc_val = st.text_area("", height=60, key=f"desc_{i}")
        st.markdown(f"<span style='font-size:20px; font-weight:bold;'>Τιμή {i+1}</span>", unsafe_allow_html=True)
        price_val = st.text_input("", "0,00", key=f"price_{i}")

        # append values for later PDF generation
        descs.append(desc_val)
        prices.append(price_val)
        st.markdown("</div>", unsafe_allow_html=True)

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
