import streamlit as st
from PIL import Image
import os
from openai.error import OpenAIError

from knowledge_gpt.components.sidebar import sidebar
from knowledge_gpt.utils import (
    embed_docs,
    get_answer,
    get_sources,
    parse_docx,
    parse_pdf,
    parse_txt,
    search_docs,
    text_to_docs,
    wrap_text_in_html,
)


def clear_submit():
    st.session_state["submit"] = False


st.set_page_config(page_title="DocGPT", page_icon="📖", layout="wide")
st.header("📖DocGPT")


hide_default_format = """
       <style>
       #MainMenu {visibility: hidden; }
       footer {visibility: hidden;}
       </style>
       """
st.markdown(hide_default_format, unsafe_allow_html=True)

sidebar()

uploaded_file = st.file_uploader(
    "Upload a pdf, docx, or txt file 上传文件",
    type=["pdf", "docx", "txt"],
    help="Scanned documents are not supported yet! 扫描的文件不支持",
    on_change=clear_submit,
)

index = None
doc = None
if uploaded_file is not None:
    if uploaded_file.name.endswith(".pdf"):
        doc = parse_pdf(uploaded_file)
    elif uploaded_file.name.endswith(".docx"):
        doc = parse_docx(uploaded_file)
    elif uploaded_file.name.endswith(".txt"):
        doc = parse_txt(uploaded_file)
    else:
        raise ValueError("File type not supported!")
    text = text_to_docs(doc)
    try:
        with st.spinner("Indexing document... This may take a while⏳"):
            index = embed_docs(text)
        st.session_state["api_key_configured"] = True
    except OpenAIError as e:
        st.error(e._message)

query = st.text_area("Ask a question about the document 对文件提问题", on_change=clear_submit)
with st.expander("Advanced Options"):
    show_all_chunks = st.checkbox("Show all chunks retrieved from vector search")
    show_full_doc = st.checkbox("Show parsed contents of the document")

if show_full_doc and doc:
    with st.expander("Document"):
        # Hack to get around st.markdown rendering LaTeX
        st.markdown(f"<p>{wrap_text_in_html(doc)}</p>", unsafe_allow_html=True)

button = st.button("Submit 提交")
if button or st.session_state.get("submit"):
    if not st.session_state.get("api_key_configured"):
        st.error("Please configure your OpenAI API key!")
    elif not index:
        st.error("Please upload a document!")
    elif not query:
        st.error("Please enter a question!")
    else:
        st.session_state["submit"] = True
        # Output Columns
        answer_col, sources_col = st.columns(2)
        sources = search_docs(index, query)

        try:
            answer = get_answer(sources, query)
            if not show_all_chunks:
                # Get the sources for the answer
                sources = get_sources(answer, sources)

            with answer_col:
                st.markdown("#### Answer")
                st.markdown(answer["output_text"].split("SOURCES: ")[0])

            with sources_col:
                st.markdown("#### Sources")
                for source in sources:
                    st.markdown(source.page_content)
                    st.markdown(source.metadata["source"])
                    st.markdown("---")

        except OpenAIError as e:
            st.error(e._message)


# Load the images
image1 = Image.open("knowledge_gpt/wechatqrcode_kyle.jpg")
image2 = Image.open("knowledge_gpt/zhifubaoqrcode_kyle.jpg")
image3 = Image.open("knowledge_gpt/paypalqrcode.png")

# Display the image with text on top
st.write("Each document costs about $1 for OpenAI API call. Please consider pay to keep this service alive! Thank you!")
st.write("每篇文章调用OpenAI API的费用约为¥7人民币，请帮助支付以便我能够一直提供这个AI小程序，谢谢您！")
#st.image(img, caption=None, width=200)

# Divide the app page into two columns
col1, col2, col3 = st.columns(3)

# Display the first image in the first column
with col1:
    st.image(image1, caption="WeChat Pay", width=200)

# Display the second image in the second column
with col2:
    st.image(image2, caption="支付宝", width=200)

# Display the third image in the third column
with col3:
    st.image(image3, caption="PayPal", width=200)


