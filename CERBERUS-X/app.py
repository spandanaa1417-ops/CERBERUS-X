
import streamlit as st
import re
import io
import csv
from itertools import combinations
from pypdf import PdfReader
from docx import Document

# ==========================================
# CERBERUS-X
# Multimodal Evidence & Conflict Analysis
# ==========================================

st.set_page_config(
    page_title="CERBERUS-X",
    page_icon="🛡️",
    layout="wide"
)

# ---------- SESSION STATE ----------

if "documents" not in st.session_state:
    st.session_state.documents = []

if "evidence" not in st.session_state:
    st.session_state.evidence = []

if "conflicts" not in st.session_state:
    st.session_state.conflicts = []

# ---------- DOCUMENT EXTRACTION ----------

def extract_document(file):

    filename = file.name.lower()
    data = file.getvalue()
    pages = []

    try:

        if filename.endswith(".pdf"):

            reader = PdfReader(io.BytesIO(data))

            if reader.is_encrypted:
                return [], "PDF is password protected."

            for number, page in enumerate(reader.pages, 1):

                text = page.extract_text() or ""

                if text.strip():
                    pages.append({
                        "source": file.name,
                        "page": number,
                        "text": text
                    })

            if not pages:
                return [], "PDF contains no selectable text. OCR is required."

        elif filename.endswith(".docx"):

            doc = Document(io.BytesIO(data))

            parts = []

            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    parts.append(paragraph.text)

            for table in doc.tables:
                for row in table.rows:
                    parts.append(
                        " | ".join(cell.text for cell in row.cells)
                    )

            text = "\n".join(parts)

            if text.strip():
                pages.append({
                    "source": file.name,
                    "page": 1,
                    "text": text
                })

        elif filename.endswith(".txt"):

            text = data.decode("utf-8", errors="ignore")

            if text.strip():
                pages.append({
                    "source": file.name,
                    "page": 1,
                    "text": text
                })

        else:
            return [], "Unsupported file format."

        return pages, None

    except Exception as error:
        return [], str(error)


# ---------- EVIDENCE EXTRACTION ----------

def extract_evidence(documents):

    evidence = []

    for document in documents:

        sentences = re.split(
            r'(?<=[.!?])\s+|\n+',
            document["text"]
        )

        for sentence in sentences:

            sentence = sentence.strip()

            if len(sentence) > 5:

                evidence.append({
                    "source": document["source"],
                    "page": document["page"],
                    "text": sentence
                })

    return evidence


# ---------- ENTITY IDENTIFICATION ----------

def get_entity(text):

    employee_id = re.search(
        r'employee\s*id\s*[:#-]?\s*([A-Z0-9-]+)',
        text,
        re.IGNORECASE
    )

    if employee_id:
        return employee_id.group(1).upper()

    employee_name = re.search(
        r'employee\s*name\s*[:#-]?\s*([A-Za-z ]+)',
        text,
        re.IGNORECASE
    )

    if employee_name:
        return employee_name.group(1).strip().lower()

    return None


# ---------- FACT EXTRACTION ----------

def extract_facts(documents):

    facts = []

    for document in documents:

        entity = get_entity(document["text"])

        for line in document["text"].splitlines():

            if ":" not in line:
                continue

            key, value = line.split(":", 1)

            key = re.sub(
                r'[^a-z0-9 ]',
                '',
                key.lower()
            ).strip()

            if not key or not value.strip():
                continue

            if key in [
                "employee id",
                "employee name"
            ]:
                continue

            numbers = re.findall(
                r'\d[\d,]*(?:\.\d+)?',
                value
            )

            if numbers:

                facts.append({
                    "entity": entity,
                    "key": key,
                    "value": value.strip(),
                    "numbers": numbers,
                    "source": document["source"],
                    "page": document["page"]
                })

    return facts


# ---------- CONFLICT DETECTION ----------

def detect_conflicts(facts):

    conflicts = []

    for first, second in combinations(facts, 2):

        if first["source"] == second["source"]:
            continue

        if not first["entity"] or not second["entity"]:
            continue

        if first["entity"] != second["entity"]:
            continue

        if first["key"] != second["key"]:
            continue

        if first["numbers"] != second["numbers"]:

            conflicts.append({
                "entity": first["entity"],
                "field": first["key"],
                "value_a": first["value"],
                "value_b": second["value"],
                "source_a": first["source"],
                "page_a": first["page"],
                "source_b": second["source"],
                "page_b": second["page"]
            })

    return conflicts


# ---------- QUESTION RETRIEVAL ----------

STOPWORDS = {
    "the", "and", "for", "with", "what",
    "where", "when", "who", "how", "is",
    "are", "was", "were", "from", "this",
    "that", "has", "have", "had", "does"
}


def keywords(text):

    words = re.findall(
        r'[a-zA-Z0-9]+',
        text.lower()
    )

    return set(words) - STOPWORDS


def answer_question(question, evidence):

    question_words = keywords(question)
    results = []

    for item in evidence:

        sentence_words = keywords(item["text"])

        common = question_words & sentence_words

        if common:

            score = len(common) / max(
                len(question_words), 1
            )

            results.append((score, item))

    results.sort(
        key=lambda item: item[0],
        reverse=True
    )

    return results[:5]


# ==========================================
# SIDEBAR
# ==========================================

st.sidebar.title("🛡️ CERBERUS-X")

section = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Upload Documents",
        "Evidence Explorer",
        "Conflict Detection",
        "Ask CERBERUS-X"
    ]
)

st.sidebar.markdown("---")
st.sidebar.caption("Multimodal Evidence Intelligence")
st.sidebar.caption("Offline Document Analysis")


# ==========================================
# MAIN HEADER
# ==========================================

st.title("🛡️ CERBERUS-X")

st.subheader(
    "Intelligent Evidence & Conflict Analysis"
)

st.write(
    "Upload documents, extract evidence, "
    "compare facts, identify contradictions "
    "and generate traceable answers."
)


# ==========================================
# DASHBOARD
# ==========================================

if section == "Dashboard":

    st.header("Dashboard")

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Documents",
        len(st.session_state.documents)
    )

    c2.metric(
        "Evidence Records",
        len(st.session_state.evidence)
    )

    c3.metric(
        "Potential Conflicts",
        len(st.session_state.conflicts)
    )

    st.markdown("---")

    st.subheader("Analysis Pipeline")

    st.write("01 — Document Upload")
    st.write("02 — Text Extraction")
    st.write("03 — Evidence Identification")
    st.write("04 — Entity Resolution")
    st.write("05 — Conflict Detection")
    st.write("06 — Traceable Evidence Retrieval")

    if st.session_state.documents:
        st.success("Documents successfully loaded.")

    else:
        st.info("Upload documents to begin analysis.")

    if st.button("Clear All Data"):

        st.session_state.documents = []
        st.session_state.evidence = []
        st.session_state.conflicts = []

        st.rerun()


# ==========================================
# UPLOAD DOCUMENTS
# ==========================================

elif section == "Upload Documents":

    st.header("Upload Documents")

    uploaded_files = st.file_uploader(
        "Select multiple documents",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True
    )

    if st.button(
        "Process Documents",
        type="primary"
    ):

        if not uploaded_files:

            st.warning("Please upload documents first.")

        else:

            all_documents = []
            errors = []

            progress = st.progress(0)

            for index, file in enumerate(uploaded_files):

                extracted, error = extract_document(file)

                if error:
                    errors.append(
                        f"{file.name}: {error}"
                    )

                else:
                    all_documents.extend(extracted)

                progress.progress(
                    (index + 1) / len(uploaded_files)
                )

            if all_documents:

                st.session_state.documents = all_documents

                st.session_state.evidence = (
                    extract_evidence(all_documents)
                )

                facts = extract_facts(all_documents)

                st.session_state.conflicts = (
                    detect_conflicts(facts)
                )

                st.success("Processing completed!")

                a, b, c = st.columns(3)

                a.metric(
                    "Documents",
                    len(uploaded_files) - len(errors)
                )

                b.metric(
                    "Evidence",
                    len(st.session_state.evidence)
                )

                c.metric(
                    "Potential Conflicts",
                    len(st.session_state.conflicts)
                )

            if errors:

                st.warning("Some files could not be processed.")

                for error in errors:
                    st.error(error)

            if not all_documents:
                st.error("No readable text was extracted.")


# ==========================================
# EVIDENCE EXPLORER
# ==========================================

elif section == "Evidence Explorer":

    st.header("Evidence Explorer")

    search = st.text_input("Search extracted evidence")

    evidence = st.session_state.evidence

    filtered = [
        item for item in evidence
        if search.lower() in item["text"].lower()
    ] if search else evidence

    st.write(f"Records found: {len(filtered)}")

    for index, item in enumerate(filtered, 1):

        with st.expander(
            f"Evidence {index} | {item['source']} | Page {item['page']}"
        ):

            st.write(item["text"])

            st.caption(
                f"Source: {item['source']} | "
                f"Page: {item['page']}"
            )

    if not evidence:
        st.info("Upload documents first.")


# ==========================================
# CONFLICT DETECTION
# ==========================================

elif section == "Conflict Detection":

    st.header("Conflict Detection")

    conflicts = st.session_state.conflicts

    if not conflicts:

        st.info(
            "No potential conflicts were detected "
            "by the current comparison rules. "
            "This does not prove that all documents agree."
        )

    else:

        st.warning(
            f"{len(conflicts)} potential conflicts detected."
        )

        for index, item in enumerate(conflicts, 1):

            st.subheader(f"Conflict #{index}")

            left, right = st.columns(2)

            with left:

                st.error("Evidence A")

                st.write(
                    f"Field: {item['field']}"
                )

                st.write(
                    f"Value: {item['value_a']}"
                )

                st.caption(
                    f"{item['source_a']} | Page {item['page_a']}"
                )

            with right:

                st.info("Evidence B")

                st.write(
                    f"Field: {item['field']}"
                )

                st.write(
                    f"Value: {item['value_b']}"
                )

                st.caption(
                    f"{item['source_b']} | Page {item['page_b']}"
                )

            st.warning(
                "Potential contradiction. "
                "Human verification is required."
            )

            st.markdown("---")


# ==========================================
# ASK CERBERUS-X
# ==========================================

elif section == "Ask CERBERUS-X":

    st.header("Ask CERBERUS-X")

    question = st.text_input(
        "Ask a question about your documents",
        placeholder="Example: What is Rahul Sharma's salary?"
    )

    if st.button("Analyze Evidence", type="primary"):

        if not st.session_state.evidence:

            st.warning("Upload documents first.")

        elif not question.strip():

            st.warning("Enter a question.")

        else:

            results = answer_question(
                question,
                st.session_state.evidence
            )

            if results:

                st.subheader("Relevant Evidence")

                for score, item in results:

                    st.write(item["text"])

                    st.caption(
                        f"Source: {item['source']} | "
                        f"Page: {item['page']} | "
                        f"Keyword relevance: {score:.0%}"
                    )

                    st.markdown("---")

                st.info(
                    "These are relevant retrieved records, "
                    "not a verified final conclusion. "
                    "Check conflicting evidence before deciding."
                )

            else:

                st.error("Insufficient matching evidence.")


# ==========================================
# DOWNLOAD REPORT
# ==========================================

st.sidebar.markdown("---")

if st.session_state.evidence:

    report = io.StringIO()

    writer = csv.writer(report)

    writer.writerow([
        "Source",
        "Page",
        "Evidence"
    ])

    for item in st.session_state.evidence:

        writer.writerow([
            item["source"],
            item["page"],
            item["text"]
        ])

    st.sidebar.download_button(
        "Download Evidence Report",
        data=report.getvalue(),
        file_name="CERBERUS-X_Report.csv",
        mime="text/csv"
    )

st.sidebar.caption("CERBERUS-X | Evidence Intelligence")
