import importlib.util
import os
from pathlib import Path

import streamlit as st

from agent import Agent


TOOLS_DIR = os.path.join(os.path.dirname(__file__), "tools")


def _load_tool_module(module_name: str, file_name: str):
    file_path = os.path.join(TOOLS_DIR, file_name)
    spec = importlib.util.spec_from_file_location(module_name, file_path)

    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load tool module: {module_name}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pdf_tool = _load_tool_module("pdf_tool_frontend", "pdf_tool.py")

st.set_page_config(
    page_title="AI Agent",
    page_icon="🤖",
    layout="centered"
)

st.title("🤖 AI Agent")

# Create agent only once
if "agent" not in st.session_state:
    st.session_state.agent = Agent()

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

if "uploaded_attachment" not in st.session_state:
    st.session_state.uploaded_attachment = None

if "uploaded_file_signature" not in st.session_state:
    st.session_state.uploaded_file_signature = None

if "pdf_result" not in st.session_state:
    st.session_state.pdf_result = None

# Show previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input box
prompt = st.chat_input("Type your message...")

if prompt:

    attachments = []
    if st.session_state.uploaded_attachment is not None:
        attachments.append(st.session_state.uploaded_attachment)

    # Show user message
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.markdown(prompt)

    # Get AI response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = st.session_state.agent.run(prompt, attachments=attachments or None)

        st.markdown(response)

    st.session_state.messages.append({
        "role": "assistant",
        "content": response
    })

# Sidebar
with st.sidebar:
    st.header("Options")

    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.header("Document Tools")

    uploaded_file = st.file_uploader(
        "Upload a file for safe PDF conversion",
        type=["txt", "md", "csv", "json", "log", "html", "htm", "pdf", "png", "jpg", "jpeg", "gif", "bmp", "webp"],
        accept_multiple_files=False,
    )

    if uploaded_file is not None:
        signature = (uploaded_file.name, uploaded_file.size)

        if st.session_state.uploaded_file_signature != signature:
            try:
                saved_path = pdf_tool.save_uploaded_file(uploaded_file.name, uploaded_file.getvalue())
                st.session_state.uploaded_attachment = {
                    "name": uploaded_file.name,
                    "path": saved_path,
                    "type": uploaded_file.type,
                    "size": uploaded_file.size,
                }
                st.session_state.uploaded_file_signature = signature
                st.session_state.pdf_result = None
                st.success(f"Uploaded safely: {uploaded_file.name}")
            except Exception as error:
                st.session_state.uploaded_attachment = None
                st.session_state.uploaded_file_signature = None
                st.session_state.pdf_result = None
                st.error(str(error))

    action = st.selectbox(
        "Choose an action",
        ["Create PDF from text", "Convert uploaded file to PDF", "Extract text from PDF"],
    )

    default_title = "Document"
    edited_text = ""

    if st.session_state.uploaded_attachment is not None:
        source_path = st.session_state.uploaded_attachment["path"]
        source_name = st.session_state.uploaded_attachment["name"]
        source_suffix = Path(source_path).suffix.lower()
        default_title = Path(source_name).stem

        if action == "Create PDF from text" and source_suffix in {".txt", ".md", ".csv", ".json", ".log", ".html", ".htm"}:
            try:
                edited_text = Path(source_path).read_text(encoding="utf-8", errors="replace")
            except Exception:
                edited_text = ""
        elif action == "Extract text from PDF" and source_suffix == ".pdf":
            try:
                preview_result = pdf_tool.extract_text_from_pdf(source_path)
                edited_text = preview_result.get("extracted_text", "")
            except Exception as error:
                st.warning(str(error))

    text_area_value = st.text_area(
        "Edit the content that will become the PDF",
        value=edited_text,
        height=200,
    )

    title_input = st.text_input("PDF title", value=default_title)
    output_extension = ".txt" if action == "Extract text from PDF" else ".pdf"
    output_name_input = st.text_input("Output file name", value=f"{default_title}{output_extension}")

    if st.button("Run Document Tool"):
        try:
            if action == "Create PDF from text":
                result = pdf_tool.execute(
                    {
                        "action": "create_pdf",
                        "title": title_input,
                        "text": text_area_value,
                        "output_name": output_name_input,
                    }
                )
            elif action == "Convert uploaded file to PDF":
                if st.session_state.uploaded_attachment is None:
                    raise ValueError("Please upload a file first.")

                result = pdf_tool.execute(
                    {
                        "action": "convert_to_pdf",
                        "source_path": st.session_state.uploaded_attachment["path"],
                        "output_name": output_name_input,
                    }
                )
            else:
                if st.session_state.uploaded_attachment is None:
                    raise ValueError("Please upload a PDF first.")

                result = pdf_tool.execute(
                    {
                        "action": "extract_text",
                        "source_path": st.session_state.uploaded_attachment["path"],
                        "output_name": output_name_input,
                    }
                )

            st.session_state.pdf_result = result
            st.success("Document tool completed.")
        except Exception as error:
            st.session_state.pdf_result = None
            st.error(str(error))

    if st.session_state.pdf_result is not None:
        result = st.session_state.pdf_result
        output_path = result.get("output_path")

        if output_path and Path(output_path).exists():
            file_bytes = Path(output_path).read_bytes()
            download_name = result.get("download_name") or Path(output_path).name
            mime_type = "application/pdf" if download_name.lower().endswith(".pdf") else "text/plain"

            st.download_button(
                label="Download generated file",
                data=file_bytes,
                file_name=download_name,
                mime=mime_type,
            )

            if result.get("action") == "extract_text":
                st.text_area("Extracted text", value=result.get("extracted_text", ""), height=250)