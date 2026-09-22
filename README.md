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
[Test cases] → [Core evaluator] → [Adapter] → [AI system]
                                      ↓
                                  [Checks] → [Score report]

- **Core evaluator:** the same for every AI type. Runs the test cases,
  collects results and builds the report.
- **Adapters:** each one knows how to talk to one type of AI system.
- **Checks:** plug-ins that score the output. Some work for every AI type,
  some only for one.

Adding a new AI type means adding a new adapter, not rewriting the tool.

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
- [ ] Test case format (input, expected output, difficulty)
- [ ] Run test cases and collect results
- [ ] Score report
- [ ] General checks: speed, token usage, cost

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
Work in progress. Currently working on Phase 1.

## Tech
Python (planned: FastAPI, React, Docker)
