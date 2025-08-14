
import streamlit as st
from datetime import datetime
from typing import Dict, Any

st.set_page_config(page_title="BMS Requirements Form", page_icon="🔋", layout="wide")

# ---------- Helpers ----------
def init_state():
    defaults = {
        "step": 1,
        "data": {},
        "chem_cell_nominal_map": {"NMC": 3.6, "NCA": 3.6, "LFP": 3.2, "LTO": 2.4, "Other": 3.6},
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

def download_json_button(data: Dict[str, Any]):
    fname = f"BMS_Requirements_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    st.download_button("⬇️ Download JSON", data=json.dumps(data, indent=2), file_name=fname, mime="application/json")

def header():
    cols = st.columns([1, 5, 1])
    with cols[1]:
        st.markdown("### 🔋 Battery Management System — Requirements Intake")
        st.caption("Two-step, easy form: **Basics** → **Advanced Features**")
    st.divider()

init_state()
header()

# ---------- Sidebar ----------
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

# ---------- Step 1: Basics ----------
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

# ---------- Step 2: Advanced ----------
if st.session_state.step == 2:
    st.subheader("Step 2 — Advanced Features")
    st.caption("Fine-tune algorithms, protections, controls, and serviceability.")

    # Layout in sections
    st.markdown("##### Algorithms & Balancing")
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

    st.markdown("##### Power & HV Controls")
    h1, h2 = st.columns(2)
    with h1:
        set_kv("precharge", st.checkbox("Precharge control", value=bool(kv("precharge", True))))
        set_kv("contactors", st.multiselect("Contactors", ["Main + / Main -", "Charger", "Heater/AC", "Others"], default=kv("contactors", ["Main + / Main -"])))
        set_kv("imd_required", st.checkbox("Isolation Monitoring (IMD)", value=bool(kv("imd_required", True))))
    with h2:
        set_kv("thermal_mgmt", st.multiselect("Thermal management", ["Fan PWM", "Coolant pump", "PTC heater", "Chiller control"], default=kv("thermal_mgmt", ["Fan PWM"])))
        set_kv("redundancy", st.selectbox("Redundancy / Diagnostics depth", ["Basic", "Enhanced", "Safety-critical"], index=(["Basic","Enhanced","Safety-critical"].index(kv("redundancy")) if kv("redundancy") in ["Basic","Enhanced","Safety-critical"] else 1)))
        set_kv("diag_features", st.multiselect("Diagnostics", ["DTCs (ISO 14229)", "Freeze frames", "Self-test", "Blackbox after fault"], default=kv("diag_features", ["DTCs (ISO 14229)"])))

    st.markdown("##### Program & Scale")
    s1, s2 = st.columns(2)
    with s1:
        set_kv("target_hardware", st.selectbox("Preferred IC / AFE (optional)", ["Not specified", "TI BQ76952", "NXP MC33772/33771", "ADI LTC6811/6813", "Other"], index=(["Not specified","TI BQ76952","NXP MC33772/33771","ADI LTC6811/6813","Other"].index(kv("target_hardware")) if kv("target_hardware") in ["Not specified","TI BQ76952","NXP MC33772/33771","ADI LTC6811/6813","Other"] else 0)))
        set_kv("proto_timeline", st.selectbox("Prototype timeline", ["< 2 months", "2–4 months", "4–6 months", "> 6 months"], index=(["< 2 months","2–4 months","4–6 months","> 6 months"].index(kv("proto_timeline")) if kv("proto_timeline") in ["< 2 months","2–4 months","4–6 months","> 6 months"] else 1)))
    with s2:
        set_kv("annual_volume", st.selectbox("Estimated annual volume", ["<100", "100–1k", "1k–10k", "10k–100k", ">100k"], index=(["<100","100–1k","1k–10k","10k–100k",">100k"].index(kv("annual_volume")) if kv("annual_volume") in ["<100","100–1k","1k–10k","10k–100k",">100k"] else 2)))
        set_kv("budget_band", st.selectbox("Budget band (controller+integration)", ["Undisclosed", "₹ <10L", "₹ 10–50L", "₹ 50L–2Cr", "₹ >2Cr"], index=(["Undisclosed","₹ <10L","₹ 10–50L","₹ 50L–2Cr","₹ >2Cr"].index(kv("budget_band")) if kv("budget_band") in ["Undisclosed","₹ <10L","₹ 10–50L","₹ 50L–2Cr","₹ >2Cr"] else 0)))

    # Navigation
    cleft, cmid, cright = st.columns([1,2,1])
    with cleft:
        st.button("⬅️ Back", use_container_width=True, on_click=prev_step)
    with cright:
        st.button("✅ Finish & Show Summary", type="primary", use_container_width=True)

    st.divider()
    st.markdown("#### Summary")
    st.caption("Review and download your inputs as JSON.")
    st.json(st.session_state["data"])
    download_json_button(st.session_state["data"])

    st.markdown("---")
    st.caption("Tip: Use the sidebar to upload a previous JSON and continue editing.")

# ---------- Footer ----------
st.markdown("")
st.caption("Made with ❤️ for fast BMS scoping.")

