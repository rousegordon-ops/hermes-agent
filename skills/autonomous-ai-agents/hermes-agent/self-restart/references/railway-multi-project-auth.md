# Railway Multi-Project Auth Diagnostic Notes

## Project IDs (pretty-amazement)
- PROJECT_ID: `c49b3e8b-a36d-4d24-a972-eab5e05b881d`
- ENVIRONMENT_ID: `38eea0f3-0bd3-48f4-abaf-ec3de09174de`
- SERVICE_ID: `c32be0a9-9d43-49a8-bf43-764915360dfb`
- DEPLOYMENT_ID: `e06b1c23-10eb-4c40-9bf2-2c943a603041`

## Symptom: Introspection works but mutations return "Not Authorized"

When a `RAILWAY_API_TOKEN` belongs to a **different project**, the Railway GraphQL API still accepts the token for schema introspection (returns 200 with 164 mutation fields), but all mutations and data queries return `{"errors": [{"message": "Not Authorized", "extensions": {"code": "INTERNAL_SERVER_ERROR"}}]}`.

**Diagnostic queries:**

```python
import os, urllib.request, json

token = os.environ.get("RAILWAY_API_TOKEN")
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json", "User-Agent": "railway-cli/4.44.0"}

# 1. Introspection — should return 200 with mutation list
introspection_query = '{"query":"{ __schema { mutationType { fields { name } } } }"}'

# 2. Project data query — returns "Not Authorized" if wrong project/missing membership
project_query = '{"query":"{ project(id: \\"c49b3e8b-a36d-4d24-a972-eab5e05b881d\\") { id name } }"}'
```

If introspection returns 164 mutations but `project(id:)` returns Not Authorized → token is from wrong project or account is not a project member.

## Key insight: introspection vs data query auth split

Railway's backboard API seems to authorize introspection (schema reads) separately from project data operations. This means:
- A token from a different project can SEE all available mutations (including `serviceInstanceRedeploy`)
- But cannot EXECUTE any of them on a project it doesn't have access to

This is why Mode C sub-causes must be distinguished by checking if the token can query project data, not just by whether introspection works.
