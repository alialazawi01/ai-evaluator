# Planned Features

## Supported AI types and checks

### General (all AI types)
- Performance: speed, token usage, cost
- Difficulty: test cases grouped by easy / medium / hard

### Chatbot / LLM
- Accuracy, tone, stale / outdated info, off-topic handling

### RAG
- Did it find the right documents?
- Is the answer based on those documents, or made up?

### Agent
- Task success, number of steps, correct tool use

### Classifier
- Accuracy, precision, recall, which labels it mixes up

### Recommender
- Are the right items in the top suggestions?
- Variety of suggestions

### Image generator
- Does the image match the prompt?
- Image quality

### Speech
- Word error rate (speech to text)
- Clarity and naturalness (text to speech)

### Forecasting
- How far off the predictions are
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