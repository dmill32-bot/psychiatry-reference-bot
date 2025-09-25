import json
import streamlit as st

st.set_page_config(page_title="Psychiatry Reference Bot (Beta)", page_icon="🧠", layout="wide")

@st.cache_data
def load_cards():
    with open("diagnoses.json","r") as f:
        return json.load(f)

cards = load_cards()

st.title("🧠 Psychiatry Reference Bot (Beta)")
st.write("**Educational reference for clinicians. Not a substitute for clinical judgment. Do not paste PHI.**")

# Sidebar: quick select
names = [c["diagnosis"]["name"] for c in cards]
st.sidebar.header("Quick Select")
sel = st.sidebar.selectbox("Jump to a diagnosis:", ["—"] + names)

# Search
st.subheader("Ask a quick question")
q = st.text_input("Example: 'OCD first-line meds and dosing' or 'Bipolar depression second line options'")

def score(card, query):
    text = " ".join([
        card["diagnosis"]["name"],
        card["diagnosis"]["core_criteria_summary"],
        " ".join(card["diagnosis"].get("differential",[])),
        " ".join([x.get("name","") for x in card["diagnosis"].get("screeners",[])]),
        " ".join(card.get("psychotherapies",[])),
        " ".join(card.get("special_populations",[])),
        " ".join(card.get("references",[]))
    ])
    text += " "
    # add medications text
    meds = []
    for tier in ["first_line","second_line"]:
        if tier in card["medications"]:
            for cls in card["medications"][tier]:
                meds.append(cls.get("class",""))
                for a in cls.get("agents",[]):
                    meds.append(a.get("name",""))
                    meds.append(a.get("adult_dose_range",""))
    text += " ".join(meds)
    # naive scoring: count keyword hits
    hits = 0
    for token in query.lower().split():
        if token in text.lower():
            hits += 1
    # name bonus
    if any(tok in card["diagnosis"]["name"].lower() for tok in query.lower().split()):
        hits += 2
    return hits

def render_card(card):
    diag = card["diagnosis"]
    st.markdown(f"## {diag['name']}")
    cols = st.columns(2)
    with cols[0]:
        st.markdown("### Diagnosis")
        st.write(f"**Codes:** {diag['codes']}")
        st.write(f"**Core criteria:** {diag['core_criteria_summary']}")
        if diag.get("differential"):
            st.write("**Differential:** " + ", ".join(diag["differential"]))
        if diag.get("screeners"):
            st.write("**Screeners:** " + "; ".join([
                f"{s['name']} – {s.get('use','')} ({s.get('cutoffs','')})"
                for s in diag['screeners']
            ]))
        if diag.get("workup_considerations"):
            st.write("**Work-up considerations:** " + "; ".join(diag["workup_considerations"]))
    with cols[1]:
        st.markdown("### Medications")
        for tier in ["first_line","second_line"]:
            if tier in card["medications"]:
                st.write(f"**{tier.replace('_',' ').title()}:**")
                for cls in card["medications"][tier]:
                    st.write(f"- *{cls.get('class','')}*")
                    for a in cls.get("agents",[]):
                        bullet = f"  - {a.get('name','')}"
                        if a.get("adult_dose_range"):
                            bullet += f" — **Dose:** {a['adult_dose_range']}"
                        extra = []
                        if a.get("titration"): extra.append(f"Titration: {a['titration']}")
                        if a.get("key_contras"): extra.append(f"Contra: {', '.join(a['key_contras'])}")
                        if a.get("monitoring"): extra.append(f"Monitoring: {', '.join(a['monitoring'])}")
                        if a.get("black_box"): extra.append(f"Black box: {a['black_box']}")
                        if a.get("interactions"): extra.append(f"Interactions: {', '.join(a['interactions'])}")
                        if a.get("notes"): extra.append(f"Notes: {a['notes']}")
                        if extra:
                            bullet += "  \n     " + " | ".join(extra)
                        st.markdown(bullet)
    st.markdown("### Psychotherapies")
    st.write(", ".join(card.get("psychotherapies",[])) or "—")
    st.markdown("### Special Populations")
    st.write(", ".join(card.get("special_populations",[])) or "—")
    st.markdown("### References")
    st.write("; ".join(card.get("references",[])) or "—")
    st.caption(card.get("disclaimer",""))

    # Patient handout (plain text)
    handout = f"""{diag['name']} — Patient Handout (Draft)
What it is: {diag['core_criteria_summary']}
Common treatments:
- Therapy: {', '.join(card.get('psychotherapies',[])) or 'varies by person'}
- Medicines: """

    med_lines = []
    for tier in ["first_line","second_line"]:
        if tier in card["medications"]:
            for cls in card["medications"][tier]:
                for a in cls.get("agents",[]):
                    med_lines.append(a.get("name",""))

    if med_lines:
        handout += ", ".join(sorted(set(med_lines)))
    else:
        handout += "Discuss options with your clinician."

    handout += "\nNotes: Medicine choices depend on your health history and other medicines. Never change a dose without your prescriber."

    st.download_button(
        "⬇️ Download patient handout (txt)",
        data=handout,
        file_name=f"{diag['name'].replace(' ','_')}_handout.txt",
        mime="text/plain"
    )

# Render by selection or search
chosen_card = None
if sel != "—":
    chosen_card = next((c for c in cards if c["diagnosis"]["name"] == sel), None)
elif q:
    ranked = sorted(cards, key=lambda c: score(c, q), reverse=True)
    chosen_card = ranked[0] if ranked else None

if chosen_card:
    render_card(chosen_card)
else:
    st.info("Select a diagnosis from the sidebar or ask a question above.")

st.markdown("---")
st.caption("© Beta for clinical reference. Do not store or paste PHI here.")
