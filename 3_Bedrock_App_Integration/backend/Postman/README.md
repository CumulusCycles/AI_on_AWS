# Postman Collection — Bedrock App Integration API

Collection and environment for testing the backend. Files use legacy names (“Bedrock_Chat_API”) but work with the damage assessment app.

## Files

- **Bedrock_Chat_API.postman_collection.json** — All endpoints (Health, Config, Chat, Conversations, Admin).
- **Bedrock_Chat_API.postman_environment.json** — Local defaults: `base_url`, `user_id`, `conversation_id` (auto-filled from responses).

## Import

1. **Collection**: Postman → Import → choose `Bedrock_Chat_API.postman_collection.json`.
2. **Environment**: Environments → Import → `Bedrock_Chat_API.postman_environment.json` → select it in the env dropdown.

## Environment Variables

| Variable | Example | Notes |
|----------|---------|-------|
| `base_url` | `http://localhost:8000` | Backend URL |
| `user_id` | `test-user-123` | For `user_id` in requests |
| `conversation_id` | (auto) | Set from chat/conversation responses |

Edit via the environment dropdown → Edit.

## Collection Layout

1. **Health & Config** — `/health`, `/config`
2. **Chat** — Initial Assessment (3 images), Follow-up, Custom params
3. **Conversations** — Create, List, Get, Delete
4. **Admin** — Analytics, Timeline, Conversations, Models, System, Recent, Bulk delete

## Usage

### Damage assessment

- **Initial**: Use **Initial Assessment (Text + 3 Images Required)**. Set `message`, add 3 files (wide-angle, straight-on, closeup), ≤ 3.75 MB each, JPEG/PNG/GIF/WebP. No `conversation_id`. `conversation_id` in the response is stored for follow-ups.
- **Follow-up**: Use **Chat with Conversation Context**. Set `message`, leave `files` empty for text-only. Uses stored `conversation_id`.

### Conversations

Optional: **Create Conversation** to get a `conversation_id` before chat. For damage assessment, **Initial Assessment** creates the conversation; you can skip Create.

### Admin

No auth. Use the Admin requests with the same environment; `base_url` must point at the backend.

### Auto‑populated `conversation_id`

Some requests write `conversation_id` from the response into the environment so the next request can use it.

## Other Environments

Duplicate the environment and set `base_url` for staging/production. Same variables: `base_url`, `user_id`, `conversation_id`.

## Notes

- Postman does **not** need AWS credentials; the backend uses its own.
- File uploads: use form-data and the `files` key.
- Use `{{variable}}` in URLs and bodies.

## Troubleshooting

| Problem | Check |
|---------|--------|
| Connection refused | Backend running; `base_url` (e.g. `http://localhost:8000`) |
| 404 | Correct path and method; backend on the right port |
| 400 (upload) | 3 images for initial; ≤ 3.75 MB; JPEG/PNG/GIF/WebP |
| Conversation not found | Use a valid `conversation_id` from a previous response, or run **Initial Assessment** (no `conversation_id`) to create one |
