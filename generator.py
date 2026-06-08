import os
import re
from groq import Groq
from config import GROQ_API_KEY, LLM_MODEL

_client = None
_client_error = None

if GROQ_API_KEY:
    try:
        _client = Groq(api_key=GROQ_API_KEY)
    except Exception as exc:
        _client_error = exc
else:
    _client_error = RuntimeError("GROQ_API_KEY is not configured.")


# Keep memory bounded so we don't grow the prompt (and token cost) without limit.
MAX_HISTORY_TURNS = 6


def _history_messages(chat_history, max_turns=MAX_HISTORY_TURNS):
    """Return the last `max_turns` exchanges as OpenAI-style role/content dicts."""
    if not chat_history:
        return []

    valid = [
        {"role": m["role"], "content": m["content"]}
        for m in chat_history
        if isinstance(m, dict)
        and m.get("role") in ("user", "assistant")
        and m.get("content")
    ]
    # Each exchange is a user + assistant pair; keep the most recent ones.
    return valid[-(max_turns * 2):]


def contextualize_query(message, chat_history):
    """
    Rewrite a follow-up question into a standalone search query.

    When the latest message depends on earlier turns (pronouns like "it",
    "that plan", or an omitted subject), this resolves those references using
    the conversation so retrieval searches for the real topic rather than the
    bare follow-up. Returns the original message unchanged when there is no
    usable history, the model is unavailable, or anything goes wrong.
    """
    history = _history_messages(chat_history)
    if not history or _client is None:
        return message

    transcript = "\n".join(
        f"{'User' if m['role'] == 'user' else 'Advisor'}: {m['content']}"
        for m in history
    )
    system = (
        "You rewrite a user's latest message into a single standalone search query for a "
        "student loan document search. If the latest message refers to earlier turns (via "
        "pronouns such as 'it', 'that', 'they', or an omitted subject), resolve those "
        "references using the conversation so the query stands on its own. Preserve the "
        "user's wording and keywords. If the message is already self-contained, return it "
        "unchanged. Return ONLY the rewritten query text — no preamble, quotes, or labels."
    )
    user = (
        f"Conversation so far:\n{transcript}\n\n"
        f"Latest message: {message}\n\nStandalone query:"
    )
    try:
        response = _client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.0,
            max_completion_tokens=120,
        )
        rewritten = (response.choices[0].message.content or "").strip()
        return rewritten or message
    except Exception:
        # Never let rewriting break the chat — fall back to the raw message.
        return message


def generate_response(query, retrieved_chunks, chat_history=None):
    """
    Generate a grounded answer from retrieved rule chunks.


    `retrieved_chunks` is the list returned by retrieve(). Each item is a dict:
      - "text"                     : the chunk text
      - "student_loan_article"     : the article name
      - "distance"                 : similarity score (you can use this to filter weak matches)


My response should:
      1. Answer using only the retrieved context — not the model's general knowledge
      2. Make clear which article the answer comes from
      3. Say so clearly when the answer isn't in the loaded rules

    Return the response as a plain string.
    """
    if not retrieved_chunks:
        return (
            "I couldn't find anything relevant in the loaded articles. "
            "Try rephrasing your question — or check that your ingestion pipeline is working."
        )

    if _client is None:
        return _fallback_response(query, retrieved_chunks, error=_client_error)

    system_prompt = (
        "You are a student loan advisor. Answer the user's question using only the provided article excerpts. "
        "You may use the earlier conversation turns to interpret follow-up questions (for example, resolving "
        "references like 'it', 'that plan', or 'those borrowers' to what was discussed), but every factual "
        "claim in your answer must still be supported by the provided excerpts — not by the conversation alone. "
        "Do not use any outside knowledge, prior experience, or assumptions. Treat the excerpts as the only source of truth. "
        "Only answer if the needed information is explicitly present in the excerpts. Do not infer, invent, or fill in missing details. "
        "If the excerpts do not contain enough information to answer, say: \"I could not find the answer in the provided excerpts.\" "
        "Search ALL provided excerpts before answering. Do not stop after finding one relevant excerpt — read every excerpt, including lower-ranked ones, before you respond. "
        "Many questions have more than one supporting factor spread across different excerpts. Identify and report EVERY distinct factor, reason, or detail that any excerpt provides — do not stop once you have one. "
        "A weaker or lower-ranked excerpt can still contain an essential part of the answer; include it as long as it directly addresses the question. "
        "If the answer contains information from multiple excerpts, combine them into a complete answer and cite each article that supports any part of it. "
        "List every article that contains evidence for any claim you make. Do not omit a relevant source simply because another source also supports the claim. "
        "Do not cite a source unless it directly supports a claim in your answer. If you are not certain the answer is fully supported by the excerpts, say that the answer could not be determined from the provided excerpts. "
        "The final answer must end with a Sources line in this exact format: Sources: [Article A], [Article B]. "
        "Use the article NAME shown after each 'Source N:' label — never write the literal 'Source N' label in the Sources line. "
        "Do not include any extra text after the Sources line. "
        "Do not invent answers, do not fill in missing details, and do not infer beyond the text. "
        "If the provided excerpts do not contain enough information to answer, say that you couldn't find the answer in the provided article excerpts."
    )

    context_blocks = []
    for index, chunk in enumerate(retrieved_chunks, start=1):
        section_label = f" (Section: {chunk['section_header']})" if chunk.get("section_header") else ""
        context_blocks.append(
            f"Source {index}: {chunk['student_loan_article']}{section_label}\n{chunk['text']}"
        )

    prompt = (
        "The following student loan article excerpts are available as context. Answer the question using only this information. "
        "Use the excerpts directly and cite the article name(s) you used. "
        "List every article that provides evidence for any part of your answer. "
        "If the question asks why something happens, enumerate every distinct reason or factor supported by the excerpts — not just the first one you find — and cite the supporting source(s) for each. "
        "Do not answer from memory or outside the provided excerpts. "
        "If the excerpts do not provide a complete answer, say that you could not find the answer in the provided excerpts. "
        "Ignore any excerpt that is not relevant to the question. "
        "Do NOT put inline citations like '(Source 6)' or '(Source 1, Source 8)' inside the body of your answer. "
        "Place all attribution only in the final Sources line. "
        "The final answer must end with a Sources line in this exact format: Sources: [Article A], [Article B].\n\n"
        + "\n\n".join(context_blocks)
        + f"\n\nQuestion: {query}"
    )

    messages = [{"role": "system", "content": system_prompt}]
    # Include recent conversation turns so the model has memory of the exchange.
    messages.extend(_history_messages(chat_history))
    messages.append({"role": "user", "content": prompt})

    try:
        response = _client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            temperature=0.0,
            max_completion_tokens=512,
        )

        if not response.choices:
            return "The model did not return any answer. Please try again."

        answer = response.choices[0].message.content
        if not answer:
            return "The model returned an empty answer. Please try again."

        return _ensure_sources(answer.strip(), retrieved_chunks)
    except Exception as exc:
        return _fallback_response(query, retrieved_chunks, error=exc)


def _format_source_line(retrieved_chunks):
    seen_articles = []
    for chunk in retrieved_chunks:
        article = chunk.get("student_loan_article")
        if article and article not in seen_articles:
            seen_articles.append(article)

    if not seen_articles:
        return ""

    return "Sources: " + ", ".join(f"[{name}]" for name in seen_articles)


def _answer_has_sources(answer):
    # Match any "Sources:" line the model produced, with or without bracketed
    # article names, so we don't append a duplicate Sources line.
    return bool(re.search(r"\bSources?:\s*\S", answer, flags=re.IGNORECASE))


def _normalize_source_line(answer, retrieved_chunks):
    """Rewrite the model's trailing Sources line to use real article names.

    The model sometimes cites positional labels ("Source 8") instead of the
    article name. Map any "Source N" tokens back to retrieved_chunks[N-1] and
    keep any names the model already wrote in brackets, de-duplicating in order.
    """
    match = re.search(r"(?im)^[^\S\n]*Sources?:[^\S\n]*(.*)$", answer)
    if not match:
        return answer

    raw = match.group(1)
    names = []

    def _add(name):
        name = name.strip()
        if name and name not in names:
            names.append(name)

    # Tokens are either bracketed names "[...]" or positional "Source N".
    for token in re.finditer(r"\[([^\]]+)\]|Source\s+(\d+)", raw, flags=re.IGNORECASE):
        bracketed, source_num = token.group(1), token.group(2)
        if bracketed:
            _add(bracketed)
        elif source_num:
            idx = int(source_num) - 1
            if 0 <= idx < len(retrieved_chunks):
                _add(retrieved_chunks[idx].get("student_loan_article", ""))

    if not names:
        # The model may have written bare article names (no brackets, no "Source N").
        # Match any retrieved article names that appear in the line, in order.
        present = [
            (raw.find(art), art)
            for art in {c.get("student_loan_article", "") for c in retrieved_chunks}
            if art and art in raw
        ]
        for _, art in sorted(present):
            _add(art)

    if not names:
        return answer

    new_line = "Sources: " + ", ".join(f"[{name}]" for name in names)
    return answer[: match.start()] + new_line


def _strip_inline_source_labels(answer):
    """Remove inline positional citations like "(Source 6)" or "(Source 1, Source 8)".

    These are the ordinal labels we attach to each retrieved excerpt. They are
    useful to the model while reasoning but confusing in the final answer, where
    they don't visibly match the article-name Sources line. Attribution belongs
    only in that final Sources line.
    """
    # A parenthetical that contains only "Source N" references (comma/"and"-separated).
    pattern = r"\s*\(\s*Sources?\s+\d+(?:\s*(?:,|and)\s*Sources?\s+\d+)*\s*\)"
    cleaned = re.sub(pattern, "", answer, flags=re.IGNORECASE)
    # Tidy any space left before sentence punctuation.
    cleaned = re.sub(r"\s+([.,;:])", r"\1", cleaned)
    return cleaned


def _ensure_sources(answer, retrieved_chunks):
    answer = _strip_inline_source_labels(answer)
    if _answer_has_sources(answer):
        return _normalize_source_line(answer, retrieved_chunks)

    sources_line = _format_source_line(retrieved_chunks)
    if not sources_line:
        return answer

    return answer.strip() + "\n\n" + sources_line


def _fallback_response(query, retrieved_chunks, error=None):
    source_texts = []
    for index, chunk in enumerate(retrieved_chunks, start=1):
        source_texts.append(
            f"Source {index}: {chunk['student_loan_article']}\n{chunk['text']}"
        )

    answer = (
        "I couldn't generate a model-crafted answer. Here are the relevant excerpts retrieved from the loaded articles:\n\n"
        + "\n\n".join(source_texts)
    )

    if error:
        answer += f"\n\n[Error detail: {error}]"
    return answer