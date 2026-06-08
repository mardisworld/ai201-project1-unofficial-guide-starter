import os
import re

import gradio as gr
from config import DOCS_PATH
from ingest import load_documents, chunk_document
from retriever import embed_and_store, retrieve, get_collection
from generator import generate_response, contextualize_query


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

def _normalize_chat_history(chat_history):
    if not chat_history:
        return []

    normalized = []
    for item in chat_history:
        if isinstance(item, dict) and "role" in item and "content" in item:
            normalized.append(item)
        elif isinstance(item, (list, tuple)) and len(item) == 2:
            user, assistant = item
            normalized.append({"role": "user", "content": user})
            normalized.append({"role": "assistant", "content": assistant})
        else:
            # Fall back to preserving unknown items if they are already valid dicts
            normalized.append(item)
    return normalized


ORIGINAL_STRATEGY = "Original (semantic)"
HYBRID_STRATEGY = "Hybrid (semantic + BM25)"
ALL_ARTICLES = "All articles"


def _article_sort_key(name):
    leading = re.match(r"\s*(\d+)", name or "")
    return (int(leading.group(1)) if leading else 9999, name or "")


def _available_articles():
    """Distinct article names for the metadata-filter dropdown, numerically sorted."""
    try:
        data = get_collection().get(include=["metadatas"])
        articles = {
            m.get("student_loan_article")
            for m in data["metadatas"]
            if m.get("student_loan_article")
        }
        if articles:
            return sorted(articles, key=_article_sort_key)
    except Exception:
        pass

    # Fallback (e.g. collection not yet built): derive from the documents folder.
    try:
        articles = [
            os.path.splitext(fn)[0].replace("_", " ").title()
            for fn in os.listdir(DOCS_PATH)
            if fn.lower().endswith(".pdf")
        ]
        return sorted(articles, key=_article_sort_key)
    except Exception:
        return []


def _chunk_metrics(chunk):
    """Format the per-chunk scores for the debug panel, depending on strategy."""
    if chunk.get("rrf_score") is not None:
        dense = chunk.get("dense_rank")
        bm25 = chunk.get("bm25_rank")
        return (
            f"rrf={chunk['rrf_score']:.4f}, "
            f"dense_rank={dense if dense is not None else '-'}, "
            f"bm25_rank={bm25 if bm25 is not None else '-'}"
        )
    distance = chunk.get("distance")
    similarity = chunk.get("similarity", 0.0) or 0.0
    distance_str = f"{distance:.4f}" if distance is not None else "n/a"
    return f"score={similarity:.4f}, distance={distance_str}"


def chat(message, chat_history=None, strategy=ORIGINAL_STRATEGY, article_filter=ALL_ARTICLES):
    if not message.strip():
        return chat_history or [], "", ""

    chat_history = _normalize_chat_history(chat_history or [])

    # Conversational memory: rewrite a follow-up into a standalone query using
    # the conversation, then retrieve on that, then generate with the history.
    search_query = contextualize_query(message, chat_history)

    # Metadata filtering: optionally restrict retrieval to a single article.
    where = None
    if article_filter and article_filter != ALL_ARTICLES:
        where = {"student_loan_article": article_filter}

    # Retrieval strategy is chosen in the UI. The original semantic path is
    # untouched; the hybrid path is an optional, separately-implemented module.
    if strategy == HYBRID_STRATEGY:
        from hybrid_retriever import hybrid_retrieve
        retrieved = hybrid_retrieve(search_query, where=where)
    else:
        retrieved = retrieve(search_query, where=where)

    answer = generate_response(message, retrieved, chat_history=chat_history)

    debug_text = f"Strategy: {strategy}\n"
    debug_text += f"Filter: {article_filter}\n\n"
    if search_query.strip() != message.strip():
        debug_text += f"Rewritten query (used for retrieval):\n  {search_query}\n\n"

    if retrieved:
        chunk_debug = []
        for index, chunk in enumerate(retrieved, start=1):
            snippet = chunk["text"].replace("\n", " ").strip()
            chunk_debug.append(
                f"{index}. {chunk['student_loan_article']} ({_chunk_metrics(chunk)}, words={len(snippet.split())})\n"
                f"   {snippet}"
            )
        debug_text += "Retrieved chunks:\n" + "\n\n".join(chunk_debug)
    else:
        debug_text += "No chunks were retrieved for this query."

    debug_text += "\n\n---\n"
    chat_history.append({"role": "user", "content": message})
    chat_history.append({"role": "assistant", "content": answer})
    return chat_history, "", debug_text


# ---------------------------------------------------------------------------
# Gradio UI
# ---------------------------------------------------------------------------

with gr.Blocks() as demo:

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
        with gr.Column(scale=1, min_width=280):
            debug_box = gr.Textbox(
                label="Retrieval debug",
                interactive=False,
                lines=12,
            )
            gr.HTML("""
                <div style="background:#f5f3ff; border:1px solid #ddd6fe;
                            border-radius:10px; padding:1rem; margin-top:0.5rem;">
                    <p style="font-size:0.8rem; font-weight:700; color:#4c1d95;
                               margin:0 0 0.5rem; letter-spacing:0.05em;">
                        📚 LOADED ARTICLES/ Source Key
                    </p>
                    <ul style="font-size:0.85rem; color:#5b21b6; list-style:none;
                                padding:0; margin:0; line-height:1.8; white-space:normal; overflow-wrap:anywhere;">
                        <li>1. Should You Switch Your Student Loans To The New Repayment Assistance Plan?</li>
                        <li>2. These Student Loan Borrowers May Get Locked Out Of Key Repayment Plan Unless They Act Quickly</li>
                        <li>3. How Will Your Student Loan Payment Change With the Repayment Assistance Plan (RAP)</li>
                        <li>4. Education Department Sends Mass Warnings To Student Loan Borrowers To Change Repayment Plans, Or Else</li>
                        <li>5. Student Loan Borrowers Will Have Two New Repayment Options Come July 1. Here's How to Pick One</li>
                        <li>6. 4 things student loan borrowers should do before July 1</li>
                        <li>7. Beautiful Bill Act Updates</li>
                        <li>8. Student Loan Repayments Are Being Overhauled. What Borrowers Should Know.</li>
                        <li>9. Income-driven repayment plans are changing: What borrowers need to know in 2026</li>
                        <li>10. Upcoming Changes to Income-Driven Repayment Plans</li>
                        <li>11. Big Bill Means Big Changes For Student Loan Borrowers: What You Need to Know</li>
                        <li>12. Federal Student Loan Repayment Plans</li>
                        <li>13. Federal Student Loan Repayment Options</li>
                        <li>14. One Big Beautiful Bill Act – Important Definitions</li>
                    </ul>
                    <hr style="border:none; border-top:1px solid #ddd6fe; margin:0.75rem 0;">
                    <p style="font-size:0.75rem; color:#7c3aed; margin:0; line-height:1.5;">
                        Answers are grounded in the loaded documents only. If the
                        information isn't present, the assistant will say so.
                    </p>
                </div>
            """)

        with gr.Column(scale=3):
            strategy_radio = gr.Radio(
                choices=[ORIGINAL_STRATEGY, HYBRID_STRATEGY],
                value=ORIGINAL_STRATEGY,
                label="Retrieval strategy",
                info="Original = semantic search only. Hybrid = semantic + BM25 keyword search (Reciprocal Rank Fusion).",
            )
            article_dropdown = gr.Dropdown(
                choices=[ALL_ARTICLES] + _available_articles(),
                value=ALL_ARTICLES,
                label="Limit to article (metadata filter)",
                info="Restrict retrieval to one source document, or search all.",
            )
            chatbot = gr.Chatbot(
                height=440,
                label="Advisor Chat",
                placeholder=(
                    "Ask a student loan question to get started — answers stay grounded in the documents."
                ),
            )
            textbox = gr.Textbox(
                placeholder='e.g. "How do I defer payments while in school?"',
                container=False,
                scale=7,
            )
            # Clicking an example fills the textbox; the user then submits, so the
            # currently-selected retrieval strategy (and conversation) is respected.
            examples = gr.Examples(
                examples=[
                    "Why could RAP become more expensive over time despite its low starting percentages?",
                    "What must a Parent PLUS borrower do to keep access to an income-driven plan, and which plan can they get?",
                    "How do 'old IBR' and 'new IBR' differ?",
                    "What is the apparent contradiction in the Education Department's PAYE rules?",
                    "What risk does consolidating loans pose to forgiveness progress?",
                ],
                inputs=textbox,
            )
            textbox.submit(
                chat,
                [textbox, chatbot, strategy_radio, article_dropdown],
                [chatbot, textbox, debug_box],
            )


if __name__ == "__main__":
    print("\n" + "="*50)
    print("  Student Loan Advisor — starting up")
    print("="*50 + "\n")
    run_ingestion()
    demo.launch(
        theme=gr.themes.Soft(primary_hue="indigo"),
    )