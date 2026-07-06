import streamlit as st
import re
from rapidfuzz import fuzz

# ==========================================
# BUILT-IN DNC LIST
# ==========================================
DNC_RAW = [
    "North America Procurement Council",
    "Campito Plumbing & Heating",
    "Analytical And Combustion Systems",
    "Thiel LLC",
    "Geosyntec Consultants",
    "ForeFront Power",
    "Sustainable Energi",
    "sandbox",
    "C & H Agency",
    "Indexing Solutions",
    "MGI",
    "New York State Office of General Services",
    "Builders Exchange of Rochester",
    "Builders Exchange of the Southern Tier",
    "Gexpro",
    "Upstate Companies 1, LLC",
    "Progressive Piling and Engineering",
    "Eastern Contractors Association",
    "Architectural Resources",
    "Blackridge Research & Consulting",
    "Johnson Controls Security Solutions",
    "Builders Exchange",
    "NYSDOT",
    "Camelot Print & Copy Centers",
    "CIS",
    "ConstructConnect",
    "Csi estimation",
    "Dodge Data and Analytics",
    "uvhmiwhv",
    "True Bid Data Inc.",
    "CrownTV",
    "www.gizmosf.com",
    "Coastal Specified Products",
    "DF Interactive LLC",
    "Teflon Software Consulting",
    "CPC Estimating House",
    "AVANT GUARDS MFG Security Screens",
    "Extech Building Material, Inc",
    "SOPREMA",
    "Crestview Group",
    "Stark Tech",
    "Total Bid Data Corp",
    "System Partners",
    "QTO Solutions",
    "Green Meadows",
    "Dynamic Estimation Inc",
    "Quantum Ridge Ventures",
    "CARE FREE IMPROVEMENTS",
    "Quantify360 Enterprises",
    "Traditional Air Conditioning",
    "Reed Construction Data",
    "Fred Weber",
    "Dodge Reports",
    "BCA Architects & Engineers",
    "Syracuse Builders Exchange",
    "NYS Office of Mental Health",
    "Advertising4u",
    "System Partners",
    "PWXPress",
    "Rees Scientific",
    "Kitchens To Go by Mobile Modular",
    "BRITO CLEANING AND MAINTANANCE",
    "American Jail Products, LLC",
    "Dwyer Architectural",
    "Construction Exchange Of Buffalo",
    "QTO Expert LLC",
    "The Rose Report",
    "Engro Estimating"
]

# ==========================================
# NORMALIZE COMPANY NAMES
# ==========================================
def normalize_name(text):
    if not text:
        return ""
    text = text.upper()
    # Strip ALL punctuation first so "A.B.C." == "ABC" and "O'Brien" == "OBRIEN"
    text = re.sub(r"[^A-Z0-9\s]", "", text)
    # Remove common company suffix words
    remove_words = ["LLC", "INC", "CORP", "CORPORATION", "LTD", "LIMITED", "CO", "COMPANY", "GROUP"]
    for word in remove_words:
        text = re.sub(r"\b" + re.escape(word) + r"\b", "", text)
    # Collapse spaces
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ==========================================
# PARSE OGS LINE: name [TAB address] [TAB phone]
# Handles 1, 2, or 3 columns — missing cols = ""
# ==========================================
def parse_ogs_line(line):
    parts = [p.strip() for p in line.strip().split('\t')]
    name  = parts[0] if len(parts) > 0 else ""
    # Phone is last column if 3 cols, or 2nd col if only 2 cols
    if len(parts) >= 3:
        phone = parts[2]
    elif len(parts) == 2:
        # Could be name+address or name+phone — treat as phone
        phone = parts[1]
    else:
        phone = ""
    return name, phone


# ==========================================
# PARSE EXCEL LINE: name [TAB phone]
# Handles 1 or 2 columns
# ==========================================
def parse_excel_line(line):
    parts = [p.strip() for p in line.strip().split('\t')]
    name = parts[0] if len(parts) > 0 else ""
    return name


# ==========================================
# FUZZY MATCH
# ==========================================
def is_similar(name, database, threshold=85):
    for existing in database:
        if fuzz.token_sort_ratio(name, existing) >= threshold:
            return True
    return False


# ==========================================
# PAGE CONFIG
# ==========================================
st.set_page_config(page_title="Company Comparison Tool", layout="wide")

st.title("📋 Company Comparison Tool")
st.write("Finds companies in OGS/DASNY that are **missing** from your Excel list (and not on DNC).")

# ==========================================
# INPUTS  —  Excel = 2 cols | OGS = 3 cols
# ==========================================
left, right = st.columns([2, 3])

with left:
    st.subheader("Excel Companies")
    st.caption("2 columns → **Company Name** | **Phone**")
    excel_raw = st.text_area(
        "Paste from Excel (name + phone)",
        height=380,
        placeholder="ACME Corp\t(212) 555-0100\nBeta LLC\t(718) 555-0200"
    )

with right:
    st.subheader("OGS / DASNY / SCA Companies")
    st.caption("3 columns → **Company Name** | **Address** | **Phone**")
    ogs_raw = st.text_area(
        "Paste from OGS (name + address + phone)",
        height=380,
        placeholder="ALFA STAR CONSTRUCTION\t18007 Jamaica Ave, Jamaica NY\t(718) 219-6900"
    )

# ==========================================
# RUN
# ==========================================
if st.button("🔍 RUN COMPARISON", use_container_width=True):

    if not excel_raw.strip() or not ogs_raw.strip():
        st.warning("Please paste data into both boxes.")
    else:

        # Build Excel name set (for matching only)
        excel_db = set()
        for line in excel_raw.splitlines():
            if not line.strip():
                continue
            name = parse_excel_line(line)
            cleaned = normalize_name(name)
            if cleaned:
                excel_db.add(cleaned)

        # Build DNC set
        dnc_db = set()
        for dnc in DNC_RAW:
            cleaned = normalize_name(dnc)
            if cleaned:
                dnc_db.add(cleaned)

        # Process OGS — find companies missing from Excel (and not DNC)
        results = []   # list of (name, phone)
        seen   = set()

        for line in ogs_raw.splitlines():
            if not line.strip():
                continue

            name, phone = parse_ogs_line(line)
            if not name:
                continue

            norm = normalize_name(name)

            if is_similar(norm, dnc_db, threshold=90):
                continue   # on DNC — skip

            if is_similar(norm, excel_db, threshold=85):
                continue   # already in Excel — skip

            if norm in seen:
                continue   # duplicate in OGS — skip

            results.append((name, phone))
            seen.add(norm)

        # ==========================================
        # OUTPUT
        # ==========================================
        st.divider()

        if results:
            st.success(f"✅ {len(results)} new companies found — missing from Excel.")

            # Preview table
            st.table([{"Company Name": n, "Phone": p} for n, p in results])

            # Tab-separated for Google Sheets
            lines = ["Company Name\tPhone"] + [f"{n}\t{p}" for n, p in results]
            output_text = "\n".join(lines)

            st.subheader("📋 Copy → Paste into Google Sheets")
            st.caption("Select all text below → Copy → Paste into cell A1 in Google Sheets")
            st.text_area("Google Sheets output", value=output_text, height=300)

        else:
            st.error("No new companies found.")