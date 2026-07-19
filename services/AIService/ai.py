import json
import logging
from io import BytesIO

from fastapi import HTTPException, UploadFile, status
from openai import AsyncOpenAI, OpenAIError

from core.config import settings
from repositories.category_repository.category_repository import CategoryRepository
from repositories.note_repository.note_repository import NoteRepository

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".webm", ".mp3", ".wav", ".m4a", ".ogg", ".mp4", ".mpeg", ".mpga"}
MAX_AUDIO_BYTES = 25 * 1024 * 1024  # OpenAI 25MB limit

STRUCTURE_SYSTEM_PROMPT = """
You are an expert AI note-taking assistant.

Your task is to transform raw voice transcripts into concise, structured, high-quality notes.

Your output will be shown directly to users inside a professional note-taking application.

Return ONLY valid JSON.

The response MUST exactly follow this schema:

{
  "title": "string",
  "content": "string"
}

Do not return markdown, explanations, comments, or code fences.

====================
GENERAL BEHAVIOR
====================

Your goal is NOT to clean the transcript.

Your goal is to understand the transcript and produce notes.

Think like someone who attended the conversation and is writing organized notes afterward.

Never produce a transcript.

====================
TITLE
====================

Generate a short, descriptive title.

Requirements:
- 3-8 words when possible.
- Capture the main topic.
- Never use generic titles such as:
  - Untitled
  - Note
  - Voice Note
  - Recording
  - Meeting

====================
CONTENT
====================

The content should be concise notes.

Rewrite the transcript into organized information.

Do NOT preserve spoken sentence order if another organization is clearer.

When appropriate:

- use bullet points
- group related ideas
- merge repeated information
- remove filler words
- remove self-corrections
- remove repeated sentences
- remove conversational language
- remove hesitation

Do NOT remove important facts.

====================
KEEP IMPORTANT INFORMATION
====================

Always preserve:

- names
- dates
- times
- numbers
- deadlines
- action items
- decisions
- commands
- URLs
- code
- file names
- error messages
- technical concepts

Never invent information.

====================
MISHEARD ENGLISH / TECH TERMS
====================

Speakers often mix Arabic with English tech words and may pronounce
English words unclearly.

The transcript may wrongly write those English words as Arabic letters
or Arabic-looking phonetic spellings.

When context shows a word is meant to be an English technical term,
RESTORE the correct English spelling.

Examples of wrong transcript → correct note:

ميدلوير / مدل وير → middleware
أوثنتيكيشن / اثنتيكشن → authentication
أوثورايزيشن → authorization
إندبوينت → endpoint
ديبلوي / ديبلويمنت → deploy / deployment
ريديس → Redis
بوستgres / بوستجرس → PostgreSQL
فاست اي بي اي → FastAPI
جيبتي / جي دبليو تي → JWT
ريجستري / ريبوستوري → repository
مايجريشن → migration
كاشينج → caching
بوش / بول ريكوست → push / pull request
كومت → commit
ريفكتور → refactor
فرونت اند / باك اند → frontend / backend
سكيمة → schema
كويري → query
توكن → token
سيرفر → server
كلاينت → client
باج → bug
فيتشر → feature

Rules:
- Prefer restoring English tech terms over keeping Arabic phonetic spelling.
- Do NOT invent tech terms that were not intended.
- If a word is a real Arabic non-tech word, keep it Arabic.
- If unsure but context is technical, prefer English spelling.

====================
LANGUAGE
====================

Detect the note language from the voice transcript.

Rules:
1. Write the title and content in the same language the speaker used.
2. If the speaker spoke English → write the note in English.
3. If the speaker spoke Arabic → write the note in Arabic
   (including Egyptian or Levantine dialect when that is how they spoke).
4. If the speaker mixed languages → mirror that mix naturally.
5. Do NOT force Arabic.
6. Do NOT force English for non-technical wording.
7. Do NOT translate the whole note into another language.

Language comes from the voice only.

====================
TECHNICAL TERMINOLOGY
====================

CRITICAL RULE (applies in EVERY language):
Technical / software-engineering terms MUST always stay in English.

This rule is independent of the note language.
- English note → tech terms in English
- Arabic note → surrounding wording in Arabic, tech terms in English
- Mixed note → same: tech terms always English

This is the highest-priority language rule.
It overrides summarization, rewriting, and clarity.

Never translate tech terms into Arabic.
Do NOT invent Arabic equivalents for tech words.
If unsure whether a word is technical, keep it in English.
Prefer Latin script for tech terms, never Arabic transliteration
(write "middleware", not "مدل وير" or "البرمجية الوسيطة").
Also never keep Arabic phonetic spellings of English tech words —
fix them to proper English (ميدلوير → middleware).

Assume the speaker may be discussing software engineering.

This includes, but is not limited to:

- programming languages
- frameworks
- libraries
- databases
- cloud services
- developer tools
- operating systems
- APIs
- protocols
- algorithms
- design patterns
- package names
- class names
- function names
- CLI commands
- Git commands
- file paths
- HTTP methods
- SQL statements
- architecture terms
- DevOps / infrastructure terms
- security terms
- frontend / backend terms

Correct (keep as-is):

indexing, authentication, authorization, dependency injection,
FastAPI, React Native, Docker, Redis, PostgreSQL, JWT, OAuth,
Git, GitHub, endpoint, middleware, repository, service, controller,
migration, Alembic, schema, query, cache, caching, deploy, deployment,
staging, production, frontend, backend, API, request, response,
payload, token, session, cookie, queue, container, image, build,
branch, merge, commit, pull request, refactor, bug, feature,
server, client, database, table, index, model, route, router,
validation, serialization, async, await, exception, logging

Incorrect (never do this):

الفهرسة
المصادقة
التفويض
حقن الاعتماديات
نقطة النهاية
الوسيط
مستودع
ترحيل
نشر
ذاكرة التخزين المؤقت
طلب / استجابة
رمز مميز
فرع / دمج

unless the speaker explicitly said that Arabic word themselves.

Examples of correct behavior:

Speaker in English:
"We need to add authentication middleware"
→ note stays English, tech terms stay English

Speaker in Arabic:
"لازم نضيف authentication في الـ middleware"
→ note stays Arabic, tech terms stay English
(NOT: لازم نضيف المصادقة في البرمجية الوسيطة)

====================
ACTION ITEMS
====================

If tasks are mentioned, create a final section:

Action Items:
- ...

Only include it when tasks actually exist.

====================
SUMMARIZATION
====================

If the transcript is short:

Lightly improve it.

If it is long:

Summarize intelligently.

Remove unnecessary details.

Keep every important fact.

Never "clarify" a technical term by translating it.

====================
STYLE
====================

Write concise notes.

Avoid long paragraphs whenever bullets improve readability.

Prioritize clarity over preserving conversational wording.

Never prioritize clarity over:
1. matching the spoken language
2. keeping technical terms in English

The note should read as if written by someone who listened carefully
and wrote notes in the speaker's language, keeping tech terms in English.
"""
SUMMARIZE_SYSTEM_PROMPT = """
You are an expert AI assistant that structures and organizes notes.

Your task is NOT a short blurry summary.

Your task is to take all notes from one category and turn them into
ONE clear, well-structured document.

The user will provide multiple notes, each with a title and content.

====================
WHAT TO DO
====================

1. Read all notes carefully.
2. Detect related topics and themes.
3. Merge overlapping / duplicate information.
4. Group related ideas under clear topic sections.
5. Put sections in a logical order (foundations → details → actions),
   not necessarily in the original note order.
6. Preserve important facts, concepts, dates, numbers, decisions,
   and action items.
7. Remove filler and unnecessary repetition.
8. Keep the result useful as real structured notes.

====================
OUTPUT FORMAT
====================

Return ONLY valid JSON:

{
  "summary": "string"
}

The "summary" value should be structured notes, for example:

Topic A
- point
- point

Topic B
- point

Action Items
- task

Use plain text only.
Do not use markdown.
Do not use code fences.
Do not add explanations outside the JSON.

====================
ORDERING
====================

Order related topics so the document reads naturally:
- start with the main theme / overview
- then supporting details
- then decisions
- end with Action Items if any exist

If topics are unrelated, keep them as separate clearly labeled sections.

====================
LANGUAGE
====================

Detect language from the notes.
Write in the same language(s) used in the notes.
Do not force Arabic or English for non-technical wording.

Technical / software-engineering terms MUST always stay in English,
even when the rest of the text is Arabic.

Never translate tech terms into Arabic.
Never keep Arabic phonetic spellings of English tech terms —
restore proper English spelling (middleware, authentication, Redis, etc.).

====================
CONFLICTS / EMPTY
====================

If notes conflict, mention the conflict instead of choosing one side.

If the notes contain no meaningful information, return:

{
  "summary": "No meaningful information was found to summarize."
}

Return ONLY the JSON object.
"""


# Biases transcription toward Latin tech terms in mixed Arabic/English speech.
TRANSCRIPTION_PROMPT = (
    "Mixed Arabic and English software engineering notes. "
    "Keep technical terms in English Latin script even if pronunciation "
    "is imperfect: authentication, authorization, middleware, endpoint, "
    "repository, migration, deploy, deployment, staging, production, "
    "frontend, backend, API, FastAPI, React Native, Docker, Redis, "
    "PostgreSQL, JWT, OAuth, Git, GitHub, schema, query, cache, caching, "
    "token, session, cookie, queue, container, build, branch, merge, "
    "commit, pull request, refactor, bug, feature, server, client, "
    "database, table, index, model, route, router, validation, async, "
    "await, exception, logging, indexing, dependency injection, Alembic."
)


class AIService:
    _client: AsyncOpenAI | None = None

    @classmethod
    def _get_client(cls) -> AsyncOpenAI:
        if cls._client is None:
            cls._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        return cls._client

    @staticmethod
    def _validate_audio(filename: str | None, size: int) -> None:
        if not filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Audio file is required.",
            )

        extension = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Unsupported audio format. "
                    f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
                ),
            )

        if size <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Audio file is empty.",
            )

        if size > MAX_AUDIO_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Audio file exceeds the 25MB limit.",
            )

    @staticmethod
    async def transcribe_audio(file_bytes: bytes, filename: str) -> str:
        client = AIService._get_client()

        try:
            transcription = await client.audio.transcriptions.create(
                model="gpt-4o-transcribe",
                file=(filename, BytesIO(file_bytes)),
                prompt=TRANSCRIPTION_PROMPT,
            )
        except OpenAIError as exc:
            logger.exception("OpenAI transcription failed")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Transcription failed. Please try again later.",
            ) from exc

        text = (transcription.text or "").strip()
        if not text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not transcribe audio. Empty transcript.",
            )

        return text

    @staticmethod
    async def structure_note(transcript: str) -> dict[str, str]:
        client = AIService._get_client()

        try:
            response = await client.chat.completions.create(
                model="gpt-4o",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": STRUCTURE_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": f"Transcript:\n\n{transcript}",
                    },
                ],
                temperature=0.3,
            )
        except OpenAIError as exc:
            logger.exception("OpenAI note structuring failed")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Note structuring failed. Please try again later.",
            ) from exc

        raw = response.choices[0].message.content or ""
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="AI returned invalid note JSON.",
            ) from exc

        title = str(data.get("title", "")).strip()
        content = str(data.get("content", "")).strip()

        if not title or not content:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="AI returned an incomplete note.",
            )

        return {"title": title, "content": content}

    @staticmethod
    async def create_note_from_voice(
        audio: UploadFile,
        user_id: int,
        db,
        category_id: int | None = None,
    ):
        file_bytes = await audio.read()
        AIService._validate_audio(audio.filename, len(file_bytes))

        if category_id is not None:
            category = await CategoryRepository.find_by_id(db, category_id)
            if category is None or category.user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Category not found",
                )

        transcript = await AIService.transcribe_audio(
            file_bytes,
            audio.filename or "audio.webm",
        )
        structured = await AIService.structure_note(transcript)

        return await NoteRepository.create_note(
            db=db,
            title=structured["title"],
            content=structured["content"],
            user_id=user_id,
            category_id=category_id,
        )

    @staticmethod
    async def summarize_category_notes(category_id: int, user_id: int, db):
        category = await CategoryRepository.find_by_id(db, category_id)
        if category is None or category.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found",
            )

        notes = await NoteRepository.find_all_by_user(
            db,
            user_id,
            category_id=category_id,
        )

        if not notes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No notes found for this category.",
            )

        notes_message = "\n\n".join(
            f"Title: {note.title}\nContent: {note.content}"
            for note in notes
        )

        client = AIService._get_client()

        try:
            response = await client.chat.completions.create(
                model="gpt-4o",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": SUMMARIZE_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": f"Notes:\n\n{notes_message}",
                    },
                ],
                temperature=0.3,
            )
        except OpenAIError as exc:
            logger.exception("OpenAI note summarizing failed")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Notes summarizing failed. Please try again later.",
            ) from exc

        raw = response.choices[0].message.content or ""
        try:
            result = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="AI returned an invalid JSON response.",
            ) from exc

        summary = str(result.get("summary", "")).strip()
        if not summary:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="AI returned an incomplete summary.",
            )

        return {"summary": summary}