import gradio as gr
from ingest import load_documents, chunk_document
from retriever import embed_and_store, retrieve, get_collection
from generator import generate_response


# ---------------------------------------------------------------------------
# Ingestion — runs once on startup
# ---------------------------------------------------------------------------

def run_ingestion():
    """
    Load student loan article documents, chunk them, and store in ChromaDB.

    If the vector store is already populated, ingestion is skipped.
    To re-ingest (e.g. after changing your chunking strategy), delete the
    ./chroma_db folder and restart the app.
    """
    collection = get_collection()

    if collection.count() > 0:
        print(f"Vector store already populated ({collection.count()} chunks). Skipping ingestion.")
        print("To re-ingest, delete the ./chroma_db folder and restart.")
        return

    print("Ingesting student loan article documents...")
    documents = load_documents()
    all_chunks = []

    for doc in documents:
        chunks = chunk_document(doc)
        all_chunks.extend(chunks)

    if all_chunks:
        embed_and_store(all_chunks)
        print(f"Ingestion complete. {len(all_chunks)} chunks stored.")
    else:
        print(
            "\n⚠️  No chunks produced. Make sure chunk_document() is implemented in ingest.py.\n"
            "    The assistant will start, but won't be able to answer questions yet.\n"
        )


# ---------------------------------------------------------------------------
# Chat handler
# ---------------------------------------------------------------------------

def chat(message, history):
    if not message.strip():
        return ""

    retrieved = retrieve(message)
    answer = generate_response(message, retrieved)

    if retrieved:
        chunk_debug = []
        for index, chunk in enumerate(retrieved, start=1):
            snippet = chunk["text"].replace("\n", " ").strip()
            chunk_debug.append(
                f"{index}. {chunk['student_loan_article']} (distance={chunk['distance']:.4f}, words={len(snippet.split())})\n"
                f"   {snippet}"
            )
        debug_text = "Retrieved chunks:\n" + "\n\n".join(chunk_debug) + "\n\n---\n"
    else:
        debug_text = "No chunks were retrieved for this query.\n\n---\n"

    return debug_text + answer


# ---------------------------------------------------------------------------
# Gradio UI
# ---------------------------------------------------------------------------

with gr.Blocks(
    theme=gr.themes.Soft(primary_hue="indigo"),
    title="Student Loan Advisor",
) as demo:

    gr.HTML("""
        <div style="text-align:center; padding:1.25rem 0 0.5rem;">
            <h1 style="font-size:2rem; font-weight:700; color:#312e81; margin:0;">
                🎓 Student Loan Advisor
            </h1>
            <p style="color:#6b7280; font-size:1rem; margin:0.4rem 0 0;">
                Ask anything about your student loan articles — answers grounded in your loaded documents.
            </p>
        </div>
    """)

    with gr.Row():
        with gr.Column(scale=3):
            gr.ChatInterface(
                fn=chat,
                type="messages",
                chatbot=gr.Chatbot(
                    height=440,
                    type="messages",
                    placeholder=(
                        "<div style='text-align:center; color:#9ca3af; margin-top:3rem;'>"
                        "Ask a student loan question to get started — answers stay grounded in the documents."
                        "</div>"
                    ),
                ),
                textbox=gr.Textbox(
                    placeholder='e.g. "How do I defer payments while in school?"',
                    container=False,
                    scale=7,
                ),
                examples=[
                    "Why could RAP become more expensive over time despite its low starting percentages?",
                    "What must a Parent PLUS borrower do to keep access to an income-driven plan, and which plan can they get?",
                    "WHow do 'old IBR' and 'new IBR' differ?      ",
                    "What is the apparent contradiction in the Education Department's PAYE rules?",
                    "What risk does consolidating loans pose to forgiveness progress?",
                ],
                cache_examples=False,
            )

        with gr.Column(scale=1, min_width=280):
            gr.HTML("""
                <div style="background:#f5f3ff; border:1px solid #ddd6fe;
                            border-radius:10px; padding:1rem; margin-top:0.5rem;">
                    <p style="font-size:0.8rem; font-weight:700; color:#4c1d95;
                               margin:0 0 0.5rem; letter-spacing:0.05em;">
                        📚 LOADED ARTICLES
                    </p>
                    <ul style="font-size:0.85rem; color:#5b21b6; list-style:none;
                                padding:0; margin:0; line-height:1.8; white-space:normal; overflow-wrap:anywhere;">
                        <li>Should You Switch Your Student Loans To The New Repayment Assistance Plan?</li>
                        <li>These Student Loan Borrowers May Get Locked Out Of Key Repayment Plan Unless They Act Quickly</li>
                        <li>How Will Your Student Loan Payment Change With the Repayment Assistance Plan (RAP)</li>
                        <li>Education Department Sends Mass Warnings To Student Loan Borrowers To Change Repayment Plans, Or Else</li>
                        <li>Student Loan Borrowers Will Have Two New Repayment Options Come July 1. Here's How to Pick One</li>
                        <li>4 things student loan borrowers should do before July 1</li>
                        <li>Beautiful Bill Act Updates</li>
                        <li>Student Loan Repayments Are Being Overhauled. What Borrowers Should Know.</li>
                        <li>Income-driven repayment plans are changing: What borrowers need to know in 2026</li>
                        <li>Upcoming Changes to Income-Driven Repayment Plans</li>
                        <li>Big Bill Means Big Changes For Student Loan Borrowers: What You Need to Know</li>
                        <li>Federal Student Loan Repayment Plans</li>
                        <li>Federal Student Loan Repayment Options</li>
                        <li>One Big Beautiful Bill Act – Important Definitions</li>
                    </ul>
                    <hr style="border:none; border-top:1px solid #ddd6fe; margin:0.75rem 0;">
                    <p style="font-size:0.75rem; color:#7c3aed; margin:0; line-height:1.5;">
                        Answers are grounded in the loaded documents only. If the
                        information isn't present, the assistant will say so.
                    </p>
                </div>
            """)


if __name__ == "__main__":
    print("\n" + "="*50)
    print("  Student Loan Advisor — starting up")
    print("="*50 + "\n")
    run_ingestion()
    demo.launch()