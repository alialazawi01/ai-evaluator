# Project Goal

## The problem
While building a RAG chatbot at Affärsverken, we checked answers for accuracy,
tone, outdated info and off-topic questions. Doing this by hand was slow, and
it was easy to miss mistakes.

At Ericsson we worked on an agentic AI system, and it was just as hard to test
as the Affärsverken chatbot.

Chatbots and agents are only two kinds of AI system. Classifiers, image
generators and other AI tools need testing too, and each one is tested
differently. Most teams end up building their own one-off test scripts.

That is why I decided to build an AI evaluator that can benchmark, test and
score AI systems, in order to find bugs more easily.

## The goal
Build one general tool that can test and score any type of AI system in the
same structured way.

## Design idea
```
[Test cases] → [Core evaluator] → [Adapter] → [AI system]
                                      ↓
                                  [Checks] → [Score report]
```

- **Core evaluator:** the same for every AI type. Runs test cases, collects
  results and builds the report.
- **Adapters:** each one knows how to talk to one type of AI system.
- **Checks:** plug-ins that score the output.

Adding a new AI type means adding a new adapter, not rewriting the tool.

## Who it's for
- Developers building AI features who want to test changes before release
- Teams comparing different AI models or prompts

## Not in scope (for now)
- Training or fine-tuning AI models
- Automatically detecting what type of AI system is being tested