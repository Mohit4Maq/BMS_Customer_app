
import streamlit as st
import json, datetime
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="BMS Requirements Form", page_icon="🔋", layout="wide")

# ===================== Google Sheets Storage =====================
def get_gs_client():
    """Build a gspread client from a Service Account JSON stored in st.secrets."""
    # Expect st.secrets to contain:
    #   GCP_SERVICE_ACCOUNT (stringified JSON)
    #   SHEET_ID (the Google Sheets ID)
    required = ["GCP_SERVICE_ACCOUNT", "SHEET_ID"]
    for r in required:
        if r not in st.secrets:
            st.warning(f"Missing secret: {r}. Add it in Streamlit Cloud → Settings → Secrets.")
            return None, None
    svc_json = st.secrets["GCP_SERVICE_ACCOUNT"]
    try:
        info = json.loads(svc_json)
    except Exception as e:
        st.error(f"GCP_SERVICE_ACCOUNT is not valid JSON: {e}")
        return None, None
    creds = Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    client = gspread.authorize(creds)
    return client, st.secrets["SHEET_ID"]

def append_to_sheet(payload: dict):
    """Append a new row with timestamp, contact info, and JSON payload to Google Sheets."""
    client, sheet_id = get_gs_client()
    if not client:
        return False, "No Google Sheets client"
    try:
        sh = client.open_by_key(sheet_id)
        ws = sh.sheet1  # use first worksheet
        ts = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        row = [
            ts,
            payload.get("project_name",""),
            payload.get("company",""),
            payload.get("contact_email",""),
            json.dumps(payload, ensure_ascii=False),
        ]
        ws.append_row(row, value_input_option="USER_ENTERED")
        return True, None
    except Exception as e:
        return False, str(e)

def sheet_link():
    if "SHEET_ID" in st.secrets:
        sid = st.secrets["SHEET_ID"]
        return f"https://docs.google.com/spreadsheets/d/{sid}/edit"
    return None

# ===================== App State & Helpers =====================
def init_state():
    defaults = {
        "step": 1,
        "data": {},
        "chem_cell_nominal_map": {"NMC": 3.6, "NCA": 3.6, "LFP": 3.2, "LTO": 2.4, "Other": 3.6},
        "submitted": False,
        "saved": False,
        "save_error": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def next_step():
    st.session_state.step = min(2, st.session_state.step + 1)

def prev_step():
    st.session_state.step = max(1, st.session_state.step - 1)

def reset_form():
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    init_state()

def kv(k, default=None):
    return st.session_state["data"].get(k, default)

def set_kv(k, v):
    st.session_state["data"][k] = v

def calc_nominal_pack_voltage(series_cells, chem, cell_nominal_override):
    base = st.session_state["chem_cell_nominal_map"].get(chem, 3.6)
    cell_nominal = cell_nominal_override or base
    try:
        return round((series_cells or 0) * cell_nominal, 2)
    except Exception:
        return None

def required(ok: bool, label: str):
    if not ok:
        st.caption(f"❗Please fill **{label}**")
    return ok

def download_json_button(data):
    fname = f"BMS_Requirements_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    st.download_button("⬇️ Download JSON", data=json.dumps(data, indent=2), file_name=fname, mime="application/json")

def header():
    cols = st.columns([1, 5, 1])
    with cols[1]:
        st.markdown("### 🔋 Battery Management System — Requirements Intake")
        st.caption("Two-step, easy form: **Basics** → **Advanced Features**")
    st.divider()

# ===================== UI =====================
init_state()
header()

# Sidebar
with st.sidebar:
    st.markdown("## Progress")
    st.progress(50 if st.session_state.step == 1 else 100, text="Step 1/2" if st.session_state.step == 1 else "Step 2/2")
    st.markdown("### Quick Actions")
    if st.button("🔄 Reset"):
        reset_form()
        st.stop()
    st.markdown("---")
    st.markdown("### Load previous JSON")
    up = st.file_uploader("Upload requirements JSON", type=["json"], label_visibility="collapsed")
    if up is not None:
        try:
            st.session_state.data = json.load(up)
            st.success("Loaded previous responses.")
        except Exception as e:
            st.error(f"Could not load JSON: {e}")

# Step 1
if st.session_state.step == 1:
    st.subheader("Step 1 — Basics")
    st.caption("Tell us about the application and pack fundamentals.")
    c1, c2 = st.columns(2)

    with c1:
        set_kv("project_name", st.text_input("Project / Program Name *", kv("project_name", "")))
        set_kv("company", st.text_input("Company / Team *", kv("company", "")))
        set_kv("contact_email", st.text_input("Primary Contact Email *", kv("contact_email", "")))

        set_kv("application", st.selectbox(
            "Application Segment *",
            ["Passenger EV", "2W/3W", "Commercial EV", "Energy Storage (ESS)", "Industrial Vehicle", "Drone/UAV", "Other"],
            index=(["Passenger EV","2W/3W","Commercial EV","Energy Storage (ESS)","Industrial Vehicle","Drone/UAV","Other"].index(kv("application")) if kv("application") in ["Passenger EV","2W/3W","Commercial EV","Energy Storage (ESS)","Industrial Vehicle","Drone/UAV","Other"] else 0)
        ))

        set_kv("chemistry", st.selectbox(
            "Cell Chemistry *", ["NMC", "NCA", "LFP", "LTO", "Other"],
            index=(["NMC","NCA","LFP","LTO","Other"].index(kv("chemistry")) if kv("chemistry") in ["NMC","NCA","LFP","LTO","Other"] else 0)
        ))
        set_kv("cell_nominal_v", st.number_input("Cell nominal voltage (V) — optional override", min_value=0.0, max_value=10.0, value=float(kv("cell_nominal_v", 0.0)), step=0.01, help="Leave 0 to use typical chemistry value"))
    with c2:
        set_kv("series_cells", st.number_input("Cells in series (S) *", min_value=0, max_value=1000, value=int(kv("series_cells", 0))))
        set_kv("parallel_cells", st.number_input("Cells in parallel (P)", min_value=0, max_value=1000, value=int(kv("parallel_cells", 0))))
        set_kv("pack_capacity_ah", st.number_input("Target pack capacity (Ah) *", min_value=0.0, max_value=10000.0, value=float(kv("pack_capacity_ah", 0.0)), step=0.1))
        set_kv("max_cont_current_a", st.number_input("Max continuous current (A) *", min_value=0.0, max_value=10000.0, value=float(kv("max_cont_current_a", 0.0)), step=0.1))
        set_kv("max_peak_current_a", st.number_input("Max peak current (A)", min_value=0.0, max_value=10000.0, value=float(kv("max_peak_current_a", 0.0)), step=0.1))

    st.markdown("##### Environment & Compliance")
    e1, e2, e3 = st.columns(3)
    with e1:
        set_kv("min_temp_c", st.number_input("Min ambient (°C)", -60, 100, int(kv("min_temp_c", 0))))
        set_kv("max_temp_c", st.number_input("Max ambient (°C)", -60, 150, int(kv("max_temp_c", 40))))
    with e2:
        set_kv("ingress_protection", st.selectbox("Target IP rating", ["IP54", "IP65", "IP67", "IP69K", "Not sure"], index=(["IP54","IP65","IP67","IP69K","Not sure"].index(kv("ingress_protection")) if kv("ingress_protection") in ["IP54","IP65","IP67","IP69K","Not sure"] else 2)))
        set_kv("vibration_standard", st.selectbox("Vibration/Mechanical", ["IEC 60068", "ISO 16750", "OEM-specific", "Not sure"], index=(["IEC 60068","ISO 16750","OEM-specific","Not sure"].index(kv("vibration_standard")) if kv("vibration_standard") in ["IEC 60068","ISO 16750","OEM-specific","Not sure"] else 3)))
    with e3:
        set_kv("safety_standards", st.multiselect("Safety/Regulatory (choose all that apply)",
                        ["ISO 26262", "IEC 61508", "UL 2580", "AIS-156", "AIS-038 Rev 2", "UN 38.3", "Other"],
                        default=kv("safety_standards", [])))
        set_kv("asil_level", st.selectbox("Target ASIL", ["None/Not defined","QM","ASIL A","ASIL B","ASIL C","ASIL D"],
                                          index=(["None/Not defined","QM","ASIL A","ASIL B","ASIL C","ASIL D"].index(kv("asil_level")) if kv("asil_level") in ["None/Not defined","QM","ASIL A","ASIL B","ASIL C","ASIL D"] else 0)))

    st.markdown("##### Interfaces")
    set_kv("interfaces", st.multiselect("Communication Interfaces", ["CAN 2.0", "CAN FD", "LIN", "UART", "Ethernet", "BLE/WiFi for service"], default=kv("interfaces", ["CAN FD"])))
    set_kv("nominal_pack_voltage_v", calc_nominal_pack_voltage(kv("series_cells", 0), kv("chemistry", "NMC"), kv("cell_nominal_v", 0.0)))

    with st.expander("Calculated fields"):
        st.metric("Estimated nominal pack voltage (V)", kv("nominal_pack_voltage_v", 0.0))

    # Validation & Navigation
    req_ok = True
    req_ok &= required(bool(kv("project_name")), "Project / Program Name")
    req_ok &= required(bool(kv("company")), "Company / Team")
    req_ok &= required(bool(kv("contact_email")), "Primary Contact Email")
    req_ok &= required(int(kv("series_cells", 0)) > 0, "Cells in series (S)")
    req_ok &= required(float(kv("pack_capacity_ah", 0.0)) > 0.0, "Target pack capacity (Ah)")
    req_ok &= required(float(kv("max_cont_current_a", 0.0)) > 0.0, "Max continuous current (A)")

    left, mid, right = st.columns([1,2,1])
    with mid:
        st.button("➡️ Next: Advanced Features", type="primary", use_container_width=True, on_click=next_step, disabled=not req_ok)

# Step 2
if st.session_state.step == 2:
    st.subheader("Step 2 — Advanced Features")
    st.caption("Fine-tune algorithms, protections, controls, and serviceability.")

    a1, a2 = st.columns(2)
    with a1:
        set_kv("soc_method", st.selectbox("SoC Estimation", ["Coulomb Counting", "OCV + Model", "Kalman/UKF", "Neural/Fusion", "Not sure"], index=(["Coulomb Counting","OCV + Model","Kalman/UKF","Neural/Fusion","Not sure"].index(kv("soc_method")) if kv("soc_method") in ["Coulomb Counting","OCV + Model","Kalman/UKF","Neural/Fusion","Not sure"] else 1)))
        set_kv("soh_method", st.selectbox("SoH Estimation", ["Rint/Impedance", "Capacity Fade Tracking", "Data-driven", "Hybrid", "Not sure"], index=(["Rint/Impedance","Capacity Fade Tracking","Data-driven","Hybrid","Not sure"].index(kv("soh_method")) if kv("soh_method") in ["Rint/Impedance","Capacity Fade Tracking","Data-driven","Hybrid","Not sure"] else 2)))
        set_kv("balancing", st.selectbox("Cell Balancing", ["None","Passive (bleed)", "Active (inductive/capacitive)"], index=(["None","Passive (bleed)","Active (inductive/capacitive)"].index(kv("balancing")) if kv("balancing") in ["None","Passive (bleed)","Active (inductive/capacitive)"] else 1)))
        set_kv("balancing_power_w", st.number_input("Balancing power per cell (W)", 0.0, 20.0, float(kv("balancing_power_w", 0.5)), 0.1))
    with a2:
        set_kv("logging_rate_hz", st.number_input("Data logging rate (Hz)", 0.0, 1000.0, float(kv("logging_rate_hz", 1.0)), 0.1))
        set_kv("ota_updates", st.checkbox("OTA firmware updates", value=bool(kv("ota_updates", True))))
        set_kv("security", st.multiselect("Security", ["Secure Boot", "Signed Firmware", "Encrypted CAN", "Role-based auth"], default=kv("security", ["Secure Boot","Signed Firmware"])))

    st.markdown("##### Protections")
    p1, p2, p3 = st.columns(3)
    with p1:
        set_kv("ov_th_v", st.number_input("Over-voltage threshold (V/cell)", 2.0, 6.0, float(kv("ov_th_v", 4.25)), 0.01))
        set_kv("uv_th_v", st.number_input("Under-voltage threshold (V/cell)", 1.0, 4.0, float(kv("uv_th_v", 2.5)), 0.01))
    with p2:
        set_kv("ocd_a", st.number_input("Over-current discharge (A)", 0.0, 20000.0, float(kv("ocd_a", 400.0)), 1.0))
        set_kv("occ_a", st.number_input("Over-current charge (A)", 0.0, 20000.0, float(kv("occ_a", 200.0)), 1.0))
    with p3:
        set_kv("ot_c", st.number_input("Over-temperature (°C)", 20, 120, int(kv("ot_c", 80))))
        set_kv("ut_c", st.number_input("Under-temperature (°C)", -60, 40, int(kv("ut_c", -10))))

    # Submit & storage
    st.divider()
    st.markdown("#### Submit & Save")
    st.caption("Click submit to append your response to a Google Sheet and optionally download the JSON.")

    c1, c2, c3 = st.columns([1,1,1])
    with c1:
        st.button("⬅️ Back", use_container_width=True, on_click=prev_step)
    with c2:
        submit_clicked = st.button("💾 Submit & Save ", type="primary", use_container_width=True)
    with c3:
        download_json_button(st.session_state["data"])

    if submit_clicked:
        st.session_state["submitted"] = True
        ok, err = append_to_sheet(st.session_state["data"])
        st.session_state["saved"] = ok
        st.session_state["save_error"] = err
        if ok:
            link = sheet_link()
            st.success("✅ Saved to Google Sheets.")
            #if link:
                #st.markdown(f"Open your responses here: {link}")
        else:
            st.error(f"❌ Save failed: {err}")

    st.markdown("---")
    st.markdown("#### Live Preview of Submission JSON")
    st.json(st.session_state["data"])

# Footer
st.markdown("")
st.caption("Made with ❤️ for fast BMS scoping.")


