"""Three memories, three jobs — do not collapse them into one store.

  working    (Redis)     scratch state within a run; expires with the task
  persistent (Postgres)  tasks, plans, approvals, reports; the audit trail
  semantic   (Chroma)    embeddings of past tasks and their outcomes, so the
                         supervisor can retrieve "we answered something like this
                         before, and here is what went wrong last time"

The semantic one is what makes the platform improve over time rather than repeat itself.
"""
