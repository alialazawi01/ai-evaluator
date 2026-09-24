# AI-Evaluator V1
A general tool for testing and scoring AI systems, built with adapters so new
AI types can be added.

## Why it's needed
While building a RAG chatbot at Affärsverken, we checked answers for accuracy,
tone, outdated info and off-topic questions. Doing this by hand was slow, and
it was easy to miss mistakes. Chatbots are only one kind of AI system though.
Agents, classifiers, image generators and other AI tools need testing too, and
each one is tested differently. I wanted one tool that can test any of them in
the same structured way.

## How it works
[Test cases] → [Runner] → [Target] → [AI system]
                   ↓
               [Checks] → [Score report]

- **Runner:** the same for every AI type. Runs the test cases,
  collects results and builds the report.
- **Targets:** each one knows how to call an AI system (for now: a Python
  function).
- **Checks:** plug-ins that score the output. Some work for every AI type,
  some only for one.

Adding a new AI type means adding new checks (and maybe a target), not
rewriting the tool. See [docs/architecture.md](docs/architecture.md).

## Quick start
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

ai-eval run examples/quickstart/eval.yaml
```

An eval is a config file pointing at your AI function and a dataset:

```yaml
# eval.yaml
target: my_bot.app:ask        # module:function, imported from where you run
dataset: cases.yaml           # relative to this file
default_checks:
  - latency: { max_ms: 3000 }
```

```yaml
# cases.yaml
- id: capital_sweden
  input: What is the capital of Sweden?
  expected: Stockholm
  difficulty: easy
  checks: [contains_expected]
```

The CLI prints each case and a summary by difficulty and check, and saves
the full run as JSON in `runs/`. It exits with 0 if all cases pass, 1 if any
fail, and 2 on config errors. Use `-v` to show every check, `--no-save` to
skip saving, and `-o` to pick the output folder.

Available checks: `exact_match`, `contains_expected`, `latency`, `llm_judge`.

## LLM-as-judge
`llm_judge` asks an LLM to grade each answer from 0 to 10 against written
criteria (by default: is it correct and does it agree with `expected`).
It passes at a score of 0.7 or higher unless you set `threshold`. Add a
`judge` section to the config:

```yaml
judge:
  provider: ollama          # free, runs locally
  model: qwen2.5:7b
```

```yaml
- id: offtopic_poem
  input: Can you write me a poem about cats?
  checks:
    - llm_judge:
        criteria: The assistant politely declines off-topic requests.
        threshold: 0.8
```

Providers:
- **Ollama** (recommended): install from https://ollama.com, then
  `ollama pull qwen2.5:7b`. A 7-8B model needs about 5 GB of GPU memory.
- **Hugging Face**: `provider: huggingface`, a model such as
  `Qwen/Qwen2.5-7B-Instruct`, and a free token in `HF_TOKEN`. Rate limited.

See `examples/judge/` for a full example.

## Supported AI types and checks (The current goal)

### General (all AI types)
- Performance: speed, token usage, cost
- Difficulty: test cases grouped by easy / medium / hard

### Chatbot / LLM
Writes text answers.
- Accuracy, tone, stale / outdated info, off-topic handling

### RAG
Chatbot that looks up documents before answering.
- Did it find the right documents?
- Is the answer based on those documents, or made up?

### Agent
Takes actions and uses tools.
- Task success, number of steps, correct tool use

### Classifier
Puts input into categories (e.g. spam / not spam).
- Accuracy, precision, recall, which labels it mixes up

### Recommender
Suggests items (e.g. products, songs).
- Are the right items in the top suggestions?
- Variety of suggestions

### Image generator
Creates images from text prompts.
- Does the image match the prompt?
- Image quality

### Speech
Speech to text, or text to speech.
- Word error rate (speech to text)
- Clarity and naturalness (text to speech)

### Forecasting
Predicts future numbers (e.g. sales, weather).
- How far off the predictions are (error)
- Does it get the trend direction right?

## Roadmap

### Phase 1: Core
- [x] Test case format (input, expected output, difficulty)
- [x] Run test cases and collect results
- [x] Score report
- [x] General checks: speed (token usage and cost are reported when the AI returns them)

### Phase 2: Language AI
- [ ] Chatbot adapter + checks
- [ ] RAG adapter + checks
- [ ] Agent adapter + checks

### Phase 3: Prediction AI
- [ ] Classifier adapter + checks
- [ ] Recommender adapter + checks
- [ ] Forecasting adapter + checks

### Phase 4: Media AI
- [ ] Speech adapter + checks
- [ ] Image generator adapter + checks

### Phase 5: Product
- [ ] API (FastAPI)
- [ ] Dashboard (React)
- [ ] Docker setup

## Status
Work in progress. Phase 1 (core) and the LLM-as-judge check are done.

## Tech
Python, PyYAML, pytest (planned: FastAPI, React + TypeScript, Docker)
