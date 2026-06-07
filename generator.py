import os
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


def generate_response(query, retrieved_chunks):
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
        "Do not use any outside knowledge, prior experience, or assumptions. Treat the excerpts as the only source of truth. "
        "Only answer if the needed information is explicitly present in the excerpts. Do not infer, invent, or fill in missing details. "
        "If the excerpts do not contain enough information to answer, say: \"I could not find the answer in the provided excerpts.\" "
        "Search all provided excerpts before answering. Do not stop after finding one relevant excerpt. If the answer requires information from multiple excerpts, combine them and cite each source used. "
        "Do not cite a source unless it directly supports the answer. If you are not certain the answer is fully supported by the excerpts, say that the answer could not be determined from the provided excerpts. "
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
        "If the question asks for multiple reasons, list each reason separately and cite the supporting source(s). "
        "Do not answer from memory or outside the provided excerpts. "
        "If the excerpts do not provide a complete answer, say that you could not find the answer in the provided excerpts. "
        "Ignore any excerpt that is not relevant to the question. "
        "At the end of your answer, list the article name(s) you used in the form:\nSources: [Article A], [Article B]\n\n"
        + "\n\n".join(context_blocks)
        + f"\n\nQuestion: {query}"
    )

    try:
        response = _client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_completion_tokens=512,
        )

        if not response.choices:
            return "The model did not return any answer. Please try again."

        answer = response.choices[0].message.content
        if not answer:
            return "The model returned an empty answer. Please try again."

        return answer.strip()
    except Exception as exc:
        return _fallback_response(query, retrieved_chunks, error=exc)


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