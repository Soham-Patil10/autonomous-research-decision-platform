"""Continuous evaluation.

The distinguishing claim of this project is not "the agent works" — it is "here is
how well each layer works, measured, over time." Four families of metric:

  RAG     retrieval precision/recall, faithfulness, citation accuracy
  Agent   plan quality, tool-selection accuracy, recovery rate, escalation rate
  LLM     answer correctness, completeness, hallucination rate
  System  latency, tokens, cost per task, human-intervention rate

Everything is run against a versioned golden set so a change can be shown to be
an improvement rather than asserted to be one.
"""
