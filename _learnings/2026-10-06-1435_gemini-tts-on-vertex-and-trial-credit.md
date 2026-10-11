# Gemini TTS on Vertex: the trial credit only pays for Vertex, and the AI Studio style route does not exist there

**Symptom:** The Gemini key copied from kargin_project worked, but it was not the account with the Google Cloud
trial credit, and the calm style call that worked on AI Studio failed on Vertex.

**Findings (2026-10-06):**
- The `GEMINI_API_KEY` belongs to a different Cloud project than the Vertex project in `.env`. Found without any
  permission on the key's project: calling a Cloud API the key is not allowed to use returns an error whose
  `details[].metadata.consumer` is `projects/<number>`. The metric account got 403 on that project, so it is
  owned by another Google account.
- Google's free-trial page: "The $300 credit can't pay for Gemini API in AI Studio costs." First-party Gemini on
  Vertex is covered (the exclusion there is partner models offered as a managed API). So to spend the credit,
  call through Vertex with the metric account's application-default credentials (`gcloud auth
  application-default print-access-token` works even though the gcloud CLI itself has no active account).
- `client.interactions.create(model="gemini-3.8-flash-tts", ...)` on Vertex: `400 Unsupported model interaction`.
- What works on Vertex (google-genai 2.28.0): `generate_content` with the style on the text part:
  `types.Part(text=text, speech_metadata=types.SpeechMetadata(style="calm, clear and friendly teacher's voice"))`.
  Evidence: Russian Bayern line 12.0 s plain vs 15.0 s with the style (AI Studio calm: 15.1 s); English 12.2 s;
  transcripts 100% equal to the text, no extra words.
- `gemini-3.1-flash-lite` transcription works on Vertex too, so the transcription check runs on the same account.
