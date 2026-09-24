# Architecture (V1)

## How it is used
The user writes their AI system as normal Python and points the evaluator at
a function. A config file says what to test and how to judge it, and the CLI
runs it.

```python
# my_bot/app.py
def ask(question: str) -> str:
    ...
```

```yaml
# eval.yaml
target: my_bot.app:ask            # module:function
dataset: datasets/basics.yaml
judge:
  provider: ollama
  model: qwen2.5:7b
default_checks:
  - latency: { max_ms: 3000 }
```

```yaml
# datasets/basics.yaml
- id: capital_sweden
  input: What is the capital of Sweden?
  expected: Stockholm
  difficulty: easy
  checks: [contains_expected]

- id: offtopic_poem
  input: Write me a poem about cats
  difficulty: medium
  checks:
    - llm_judge:
        criteria: The assistant politely declines because it's off-topic.
```

```
$ ai-eval run eval.yaml
```

The CLI prints a summary (pass rate, breakdown by difficulty) and saves the
full run as JSON in `runs/`. It exits with code 1 if any case fails, so it can
be used in CI.

The same thing can be done from Python without the CLI. The config file only
builds these objects:

```python
from ai_evaluator import Runner, FunctionTarget
from ai_evaluator.checks import ContainsExpectedCheck, LatencyCheck

runner = Runner(
    target=FunctionTarget(ask),
    checks=[ContainsExpectedCheck(), LatencyCheck(max_ms=3000)],
)
report = runner.run(test_cases)
```

## Concepts

```
[Dataset] → [Runner] → [Target] → [AI system]
                ↓
            [Checks] (→ [Judge]) → [RunReport] → terminal / runs/*.json
```

| Concept | What it is |
|---|---|
| **TestCase** | One input, optional expected value, difficulty, and extra checks for this case |
| **Target** | Knows *how to call* the AI system and returns an `ExecutionResult` |
| **ExecutionResult** | What came back: output, latency, and optional tokens, cost, retrieved docs, agent steps |
| **Check** | Judges one `ExecutionResult` and returns a `CheckResult` (score 0–1, passed, reason) |
| **Judge** | An LLM used by the `llm_judge` check to grade answers |
| **Runner** | Runs every case through the target and the checks, and collects a `RunReport` |
| **RunReport** | All case results plus the summary. Its JSON form is the contract for the dashboard |

### Targets decide how to call, not what type of AI it is
A chatbot and a classifier behind the same kind of interface are called the
same way. So targets are split by *transport* (Python function, later HTTP or
hosted models), not by AI type. The AI "type" is expressed by which checks
are used, and later by presets (e.g. `chatbot` = a default set of checks).

### Function outputs
A target function can return:
- **Anything that is not a dict with an `output` key.** This becomes the
  output directly (e.g. a string, a label).
- **A dict with an `output` key.** Known keys fill the matching
  `ExecutionResult` fields, and unknown keys go into `metadata`:

```python
return {
    "output": "Stockholm",
    "retrieved_docs": [...],   # RAG
    "steps": [...],            # agent
    "input_tokens": 12,
    "output_tokens": 3,
}
```

This lets an AI grow from a plain chatbot into RAG or an agent without
changing the evaluator. Checks that need `retrieved_docs` or `steps` just read
those fields.

### Errors
One broken case must not stop the run.
- If the target raises, the case is recorded with `error` set and counts as
  failed. Its checks are not run.
- If a check raises, that check is recorded as failed with the error as its
  reason.

### Judges
The judge is pluggable, so free options can be used:
- **Ollama**: local, free, no rate limits (default)
- **Hugging Face Inference**: free token, rate limited

The judge is asked for strict JSON (`{"score": 0-1, "reason": "..."}`) at
temperature 0, and retried on invalid output. This keeps small models reliable
enough.

## Package layout

```
ai_evaluator/
  core/
    models.py        TestCase, ExecutionResult, CheckResult, CaseResult, RunReport
    target.py        Target ABC
    check.py         Check ABC
    runner.py        Runner
  targets/
    function.py      FunctionTarget
  checks/
    exact_match.py  contains.py  latency.py  llm_judge.py
    registry.py      check name → class, used by the config loader
  judges/
    base.py  ollama.py  huggingface.py
  config.py          loads eval.yaml and datasets
  report.py          terminal summary and JSON output
  cli.py             `ai-eval` command
tests/               pytest tests
datasets/            test case files
runs/                saved run reports (git ignored)
```

## Build order
1. Package setup, models, `FunctionTarget`, runner with error handling
2. Checks: `exact_match`, `contains_expected`, `latency`, plus check registry
3. YAML config and dataset loading, and the `ai-eval run` command
4. Report: terminal summary with difficulty breakdown, JSON file, exit code
5. LLM judge: Ollama, then Hugging Face

Later: `ai-eval compare`, `HttpTarget`, RAG and agent checks, then FastAPI and
a React + TypeScript dashboard that reads the JSON reports.
