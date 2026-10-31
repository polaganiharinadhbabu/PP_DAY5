# Day 5 — Advanced Backend Engineering

**Name:** Polagani Harinadh Babu  
**Date:** 30 October 2026  
**Topic:** Advanced Backend Engineering with Python and FastAPI

---

## Task 1: Build CRUD Endpoints for Notes

**Objective:** Create API endpoints to create, read, update and delete notes using input and response models.

### Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/v1/notes` | Create a note |
| GET | `/v1/notes` | Retrieve notes |
| GET | `/v1/notes/{id}` | Retrieve a note by ID |
| PATCH | `/v1/notes/{id}` | Update a note |
| DELETE | `/v1/notes/{id}` | Delete a note |

### Requirements

- Use Pydantic models to validate input data.
- Define a response model for notes.
- Validate the note title, body and status.
- Return appropriate HTTP status codes.
- Return `404 Not Found` when a note does not exist.
- Return `201 Created` when a note is created.
- Return `204 No Content` after successful deletion if the endpoint returns no body.

## Task 2: Add Search and Pagination

**Objective:** Allow users to search notes by text or status and retrieve results using pagination.

### Requirements

- Support text search.
- Support filtering by note status.
- Add a `limit` parameter.
- Add an `offset` parameter.
- Set a minimum limit of 1 and maximum limit of 100.
- Ensure the offset cannot be negative.

### Example Request

`GET /v1/notes?limit=20&offset=0`

Search by status:

`GET /v1/notes?status=draft&limit=20&offset=0`

The API should return only the records matching the requested search and pagination parameters.

## Task 3: Allowlist Sort Fields and Use Parameterized Database Queries

**Objective:** Make database queries safer and prevent untrusted input from being used directly in SQL statements.

### Requirements

- Define an allowlist of supported sorting fields.
- Reject unsupported sorting fields.
- Use parameterized database queries for user-provided values.
- Avoid constructing SQL statements by concatenating untrusted input.
- Handle invalid query parameters appropriately.

### Expected Result

The API should allow sorting only by approved fields and safely pass search values to the database.

## Task 4: Protect Routes with an API-Key Dependency

**Objective:** Protect API endpoints using an API-key authentication dependency.

### Requirements

- Create a reusable FastAPI dependency for API-key validation.
- Reject requests with a missing API key.
- Reject requests with an invalid API key.
- Allow requests with a valid API key when other requirements are satisfied.
- Write tests for all three scenarios.
- Store the API key in an environment variable.
- Never commit real secrets to GitHub.

### Expected Results

| Test | Expected Result |
|---|---|
| Missing API key | `401 Unauthorized` |
| Invalid API key | `401 Unauthorized` |
| Valid API key | Request proceeds if authorized |

## Task 5: Add and Document Rate Limiting

**Objective:** Restrict the number of requests a client can make within a defined time window.

### Requirements

Document the following:

1. **Rate-limit key:** How the client is identified.
2. **Time window:** The period used to count requests.
3. **Request limit:** The maximum number of requests allowed.
4. **429 response body:** The error structure returned when the limit is exceeded.
5. **Retry-After:** The time the client should wait before retrying.

### Expected Behavior

When the client exceeds the configured limit, the API should return:

`429 Too Many Requests`

The response should include the documented error body and appropriate `Retry-After` behavior.

For multiple application workers, use shared rate-limit state, such as Redis, instead of relying only on a process-local in-memory counter.

## Task 6: Build a WebSocket Endpoint

**Objective:** Implement real-time communication with room isolation and proper disconnection cleanup.

### Endpoint

`/ws/notes`

### Requirements

- Establish a WebSocket connection.
- Validate client identity and room permissions.
- Track connections by room.
- Prevent messages from leaking between rooms.
- Validate incoming messages.
- Handle client disconnections.
- Remove disconnected clients from the connection manager.
- Consider Redis Pub/Sub when communication must work across multiple application processes.

### Expected Result

Clients should receive only messages they are authorized to receive, and disconnected clients should be removed from their rooms.

## Task 7: Add a Celery Task for Note Summaries

**Objective:** Process note-summary generation as a background task.

### Requirements

- Create a Celery task for generating a note summary.
- Use Redis as the message broker.
- Submit the task through the FastAPI application.
- Return a task ID when the task is accepted.
- Implement a task-status endpoint.
- Protect the task-status endpoint.
- Verify that a requester is allowed to access the requested task.
- Configure bounded retries for appropriate transient failures.

### Endpoints

Submit a background task through the relevant note-summary endpoint.

Check its status using:

`GET /v1/tasks/{task_id}`

### Expected Behavior

The API should return `202 Accepted` when the task is accepted for background processing, along with the task ID.

The task-status endpoint should return the documented task state and enforce the required access controls.

## Task 8: Write Tests for API Behavior and Failures

**Objective:** Verify successful operations, validation, security and failure handling.

### Required Test Cases

| Test Scenario | Expected Behavior |
|---|---|
| Create a valid note | Successful creation |
| Retrieve an existing note | Note is returned |
| Update an existing note | Note is updated |
| Delete an existing note | Successful deletion |
| Retrieve a missing note ID | `404 Not Found` |
| Submit invalid input | Validation error |
| Submit duplicate or conflicting data | Appropriate conflict handling |
| Send a missing API key | `401 Unauthorized` |
| Send an invalid API key | `401 Unauthorized` |
| Send a valid API key | Request proceeds if authorized |
| Exceed the rate limit | `429 Too Many Requests` |
| Disconnect a WebSocket client | Connection cleanup |
| Access a restricted room | Access denied |
| Submit a background task | Task is queued |
| Simulate a task retry | Configured retry behavior |
| Simulate dependency failure | Appropriate failure handling |

### Testing Tools and Practices

- Use Pytest.
- Use FastAPI `TestClient` for HTTP endpoint tests.
- Use fixtures for reusable test setup.
- Override dependencies where necessary.
- Clear dependency overrides after tests.
- Mock external services when appropriate.
- Test response status codes, response bodies, permissions and side effects.
- Record actual test results and coverage.

Do not claim that tests passed until they have actually been executed.

## Task 9: Document Setup, Configuration, Migrations and Limitations

**Objective:** Provide clear instructions so another developer can configure, run and test the application.

### Documentation Requirements

The README must include:

1. Project overview and features.
2. Required technologies and dependencies.
3. Environment-variable configuration.
4. Database setup.
5. Database migration commands.
6. Application run commands.
7. Redis setup.
8. Celery worker run commands.
9. API documentation and endpoints.
10. Test execution commands.
11. Actual test coverage results.
12. Known limitations.

### Security Requirements

- Store secrets in environment variables.
- Provide an `.env.example` file containing placeholders only.
- Add `.env` to `.gitignore`.
- Never commit real API keys, passwords or database credentials.
- Avoid exposing sensitive information in responses and logs.

### Example Folder Structure

```text
Day-5/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── app/
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── database.py
│   ├── dependencies.py
│   ├── routes/
│   ├── services/
│   └── tasks/
├── migrations/
└── tests/
```

This is a suggested structure; adapt it to the actual implementation.

### Final Verification Checklist

- [ ] CRUD endpoints implemented.
- [ ] Search and bounded pagination implemented.
- [ ] Sort fields allowlisted and database queries parameterized.
- [ ] API-key dependency and authentication tests implemented.
- [ ] Rate limit and `Retry-After` behavior documented and tested.
- [ ] WebSocket room isolation and disconnect cleanup implemented.
- [ ] Celery note-summary task and protected task-status endpoint implemented.
- [ ] Required success and failure tests executed.
- [ ] Environment variables and database migrations documented.
- [ ] Run commands, test commands, coverage and known limitations documented.
- [ ] No real secrets committed to GitHub.

---

## Conclusion

These tasks cover the development of a Notes API using FastAPI, with database safety, authentication, rate limiting, real-time communication, background processing and automated testing.

The goal is to build a backend that is secure, reliable, testable and properly documented.

**Submission:** https://forms.gle/o5kdFJZSV58NUVN28

**Note:** This README documents the tasks and expected behavior. The corresponding application code, tests and configuration must also be implemented and verified before claiming the assignment is complete.
