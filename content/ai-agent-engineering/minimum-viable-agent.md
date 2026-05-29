---
{
  "slug": "minimum-viable-agent",
  "title": "The Minimum Viable Agent | URXION AI Agent Engineering",
  "description": "Practical guide to minimum viable AI agent for reliable, evidence-first AI agents with arXiv references, checklists, failure modes, and URXION examples.",
  "h1": "The Minimum Viable Agent",
  "topic": "minimum viable AI agent",
  "short_answer": "A minimum viable agent should have explicit flow, tool authorization, schema validation, grounding for knowledge tasks, basic state, logging, tests, and human approval for high-impact actions before it gets more autonomy.",
  "definition": "A minimum viable agent is the smallest useful workflow that can complete one bounded task with explicit inputs, outputs, tools, validation, telemetry, and review gates. It is not a chatbot with many vague capabilities.",
  "why_it_matters": "Starting too broad creates brittle autonomy. A small governed workflow lets the team prove value, find failure modes, and add memory, tools, or delegation only when there is evidence that complexity is needed.",
  "framework": [
    "Choose one business workflow with a concrete output.",
    "Define required inputs, forbidden actions, and completion criteria.",
    "Use deterministic validation before and after the model call.",
    "Add tool access only through explicit contracts.",
    "Measure success, latency, cost, and review burden before expanding scope."
  ],
  "failure_modes": [
    "The agent is expected to handle every request in a domain.",
    "No one defines what a successful output looks like.",
    "Tool access is added before authorization policy.",
    "Memory is added before the stateless workflow is stable."
  ],
  "checklist": [
    "What single workflow is this agent responsible for?",
    "What inputs are required to proceed?",
    "What should the agent refuse or escalate?",
    "What tests prove the workflow works?",
    "What must be true before adding autonomy?"
  ],
  "sources": [
    [
      "2604.17240v1",
      "primary research reference"
    ],
    [
      "2603.07379v1",
      "supporting research reference"
    ],
    [
      "2603.20028v1",
      "supporting research reference"
    ]
  ],
  "faqs": [
    [
      "What is minimum viable AI agent?",
      "A minimum viable agent should have explicit flow, tool authorization, schema validation, grounding for knowledge tasks, basic state, logging, tests, and human approval for high-impact actions before it gets more autonomy."
    ],
    [
      "Why does this matter for production agents?",
      "Because reliable agents must be grounded, observable, testable, cost-aware, and reviewable before they affect business workflows."
    ],
    [
      "How does URXION apply this?",
      "URXION applies these patterns to RFP response, compliance review, SDR research, and custom AI workflow agents."
    ]
  ],
  "order": 4,
  "related": [
    "system-not-the-model",
    "agent-regression-testing",
    "agent-regression-testing"
  ],
  "author": "Sean Brennan, URXION",
  "updated": "2026-05-29"
}
---

# The Minimum Viable Agent

## Short answer
A minimum viable agent should have explicit flow, tool authorization, schema validation, grounding for knowledge tasks, basic state, logging, tests, and human approval for high-impact actions before it gets more autonomy.

## Definition
A minimum viable agent is the smallest useful workflow that can complete one bounded task with explicit inputs, outputs, tools, validation, telemetry, and review gates. It is not a chatbot with many vague capabilities.

## Why it matters
Starting too broad creates brittle autonomy. A small governed workflow lets the team prove value, find failure modes, and add memory, tools, or delegation only when there is evidence that complexity is needed.

## Practical framework
- Choose one business workflow with a concrete output.
- Define required inputs, forbidden actions, and completion criteria.
- Use deterministic validation before and after the model call.
- Add tool access only through explicit contracts.
- Measure success, latency, cost, and review burden before expanding scope.

## Design notes
Design minimum viable AI agent as a measurable workflow capability, not as a prompt preference. The implementation should identify which component owns the decision, which evidence is required, and which failure path applies when the evidence is missing.
For business workflows, minimum viable AI agent should produce artifacts a human can inspect: source links, state records, gap lists, approval notes, or test results. This makes the agent useful even when the final answer still needs review.
A practical release standard is to ask whether another engineer could replay the run and understand why the system chose its route. If the answer depends on hidden model reasoning, the workflow needs more explicit structure.

## Common failure modes
- The agent is expected to handle every request in a domain.
- No one defines what a successful output looks like.
- Tool access is added before authorization policy.
- Memory is added before the stateless workflow is stable.

## Implementation checklist
- What single workflow is this agent responsible for?
- What inputs are required to proceed?
- What should the agent refuse or escalate?
- What tests prove the workflow works?
- What must be true before adding autonomy?

## Implementation example
In a URXION-style workflow, minimum viable AI agent is treated as an operational design concern. The system records the input, identifies the required evidence, routes the task through the right checks, and produces review-ready artifacts with visible gaps instead of pretending the output is final. This matters for RFPs, compliance reviews, SDR research, and custom workflow agents because each domain needs traceability and human accountability.

## Review questions
- What evidence proves the minimum viable AI agent behavior worked on this run?
- What should happen if required evidence or authorization is missing?
- Which tests would fail if this behavior regressed next week?
- What does the human reviewer need to see before approving the output?

## Internal links
- See also: [System Not The Model](/resources/ai-agent-engineering/system-not-the-model)
- See also: [Agent Regression Testing](/resources/ai-agent-engineering/agent-regression-testing)
- See also: [Agent Regression Testing](/resources/ai-agent-engineering/agent-regression-testing)

## Research references
- [arXiv:2604.17240v1](https://arxiv.org/abs/2604.17240v1) — primary research reference
- [arXiv:2603.07379v1](https://arxiv.org/abs/2603.07379v1) — supporting research reference
- [arXiv:2603.20028v1](https://arxiv.org/abs/2603.20028v1) — supporting research reference

## FAQ
### What is minimum viable AI agent?
A minimum viable agent should have explicit flow, tool authorization, schema validation, grounding for knowledge tasks, basic state, logging, tests, and human approval for high-impact actions before it gets more autonomy.

### Why does this matter for production agents?
Because reliable agents must be grounded, observable, testable, cost-aware, and reviewable before they affect business workflows.

### How does URXION apply this?
URXION applies these patterns to RFP response, compliance review, SDR research, and custom AI workflow agents.

## How URXION applies this
URXION applies this evidence-first pattern in RFP response, compliance review, SDR research, and custom AI workflow agents. The goal is review-ready work, not unsupervised automation. When the system cannot support a claim, it should show the missing evidence and route the work for human review.
