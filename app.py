import streamlit as st
from dotenv import load_dotenv

from src.task10_generation import generate_with_citation


load_dotenv()

st.set_page_config(
    page_title="Di Sản AI — ColdBrew",
    page_icon="🏛️",
    layout="wide",
)

if "messages" not in st.session_state:
    st.session_state.messages = []


def show_sources(sources: list[dict], retrieval_source: str) -> None:
    """Liệt kê nguồn đã dùng; ID khớp với citation [chunk-id] trong câu trả lời."""
    if not sources:
        st.caption(f"Không có nguồn (retrieval: {retrieval_source}).")
        return
    with st.expander(f"Nguồn đã dùng ({len(sources)}) — retrieval: {retrieval_source}"):
        for source in sources:
            metadata = source["metadata"]
            link = f" — [link gốc]({metadata['url']})" if metadata.get("url") else ""
            st.markdown(
                f"**{metadata['title']}**{link}  \n"
                f"`{source['id']}` · {source['retrieval_method']} · score {source['score']:.4f}"
            )
            st.caption(source["content"][:400])


with st.sidebar:
    st.title("Di Sản AI")
    st.caption(
        "Hỏi đáp về phong tục, trang phục và lễ hội truyền thống Việt Nam, "
        "dựa trên văn bản pháp luật về di sản/lễ hội và bài viết của Cục Di sản văn hóa, UNESCO."
    )
    top_k = st.slider("Số chunks", 3, 10, 5)

st.title("Chatbot Văn hóa & Lễ hội")
st.caption(
    "Câu trả lời trích dẫn chunk nguồn dạng [chunk-id]; mở mục \"Nguồn đã dùng\" để đối chiếu. "
    "Câu hỏi ngoài phạm vi tài liệu sẽ được từ chối."
)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            show_sources(message["sources"], message["retrieval_source"])

query = st.chat_input("Ví dụ: Có được rải tiền trên đường đưa tang không?")

if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("Đang tìm nguồn và trả lời..."):
            result = generate_with_citation(query, top_k=top_k)
        st.markdown(result["answer"])
        show_sources(result["sources"], result["retrieval_source"])

    st.session_state.messages.append({
        "role": "assistant",
        "content": result["answer"],
        "sources": result["sources"],
        "retrieval_source": result["retrieval_source"],
    })
