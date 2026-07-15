import streamlit as st
import requests
import json
import os

API_URL = os.environ.get("API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="LedgerLens", layout="wide")
st.title("LedgerLens")

page = st.sidebar.radio("Navigate", ["Upload", "Pending Review", "Gallery"])


# ---------------------------------------------------------
# PAGE 1: Upload
# ---------------------------------------------------------
if page == "Upload":
    st.header("Upload a receipt or invoice")

    uploaded_file = st.file_uploader("Choose an image", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        if st.button("Process document"):
            with st.spinner("Extracting data..."):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                response = requests.post(f"{API_URL}/ingest", files=files)

            if response.status_code == 200:
                result = response.json()
                st.success(f"Document #{result['document_id']} processed — status: {result['status']}")
                st.json(result["invoice"])
                if result["flagged_fields"]:
                    st.warning(f"{len(result['flagged_fields'])} field(s) flagged for review.")
            else:
                st.error(f"Failed: {response.text}")


# ---------------------------------------------------------
# PAGE 2: Pending Review
# ---------------------------------------------------------
elif page == "Pending Review":
    st.header("Documents awaiting review")

    response = requests.get(f"{API_URL}/review")
    pending_docs = response.json()

    if not pending_docs:
        st.success("No documents pending review.")
    else:
        st.write(f"{len(pending_docs)} document(s) pending review.")

        for doc in pending_docs:
            st.subheader(f"Document #{doc['document_id']} — {doc['filename']}")
            invoice_data = json.loads(doc["extracted_json"])

            with st.form(key=f"review_form_{doc['document_id']}"):
                vendor = st.text_input("Vendor", value=invoice_data["vendor"])
                date = st.text_input("Date", value=invoice_data.get("date") or "")
                currency = st.text_input("Currency", value=invoice_data["currency"])
                subtotal = st.number_input("Subtotal", value=invoice_data["subtotal"])
                tax = st.number_input("Tax", value=invoice_data["tax"])
                total = st.number_input("Total", value=invoice_data["total"])

                st.write("Line items:")
                corrected_items = []
                for i, item in enumerate(invoice_data["line_items"]):
                    st.write(f"Item {i + 1}")
                    desc = st.text_input(f"Description {i}", value=item["description"], key=f"desc_{doc['document_id']}_{i}")
                    qty = st.number_input(f"Quantity {i}", value=item["quantity"], key=f"qty_{doc['document_id']}_{i}")
                    price = st.number_input(f"Unit price {i}", value=item["unit_price"], key=f"price_{doc['document_id']}_{i}")
                    amount = st.number_input(f"Amount {i}", value=item["amount"], key=f"amount_{doc['document_id']}_{i}")
                    corrected_items.append({
                        "description": desc,
                        "quantity": qty,
                        "unit_price": price,
                        "amount": amount,
                        "confidence": 1.0,
                    })

                submitted = st.form_submit_button("Approve")

                if submitted:
                    corrected_invoice = {
                        "vendor": vendor,
                        "invoice_number": invoice_data.get("invoice_number"),
                        "date": date,
                        "currency": currency,
                        "subtotal": subtotal,
                        "tax": tax,
                        "total": total,
                        "line_items": corrected_items,
                        "overall_confidence": 1.0,
                    }

                    approve_response = requests.post(
                        f"{API_URL}/approve/{doc['document_id']}",
                        json=corrected_invoice,
                    )

                    if approve_response.status_code == 200:
                        st.success(f"Document #{doc['document_id']} approved!")
                        st.rerun()
                    else:
                        st.error(f"Failed: {approve_response.text}")


# ---------------------------------------------------------
# PAGE 3: Gallery
# ---------------------------------------------------------
elif page == "Gallery":
    st.header("All uploaded documents")

    response = requests.get(f"{API_URL}/documents")
    all_docs = response.json()

    if not all_docs:
        st.info("No documents uploaded yet.")
    else:
        for doc in all_docs:
            ext = doc["filename"].split(".")[-1]
            col1, col2, col3 = st.columns([1, 1, 2])

            with col1:
                st.write("Original")
                st.image(f"{API_URL}/images/{doc['document_id']}/original.{ext}")

            with col2:
                st.write("Watermarked")
                st.image(f"{API_URL}/images/{doc['document_id']}/watermarked.{ext}")

            with col3:
                st.write(f"**Document #{doc['document_id']}**")
                st.write(f"Filename: {doc['filename']}")
                st.write(f"Status: `{doc['status']}`")
                st.write(f"Uploaded: {doc['created_at']}")

            st.divider()