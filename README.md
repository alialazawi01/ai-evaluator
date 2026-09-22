# AI-Evaluator V1
A tool that tests AI chatbots and gives them a score report.

## Why it's needed
While building a RAG customer support chatbot at Affärsverken, we checked answers for accuracy,
tone, outdated info and off-topic questions. Doing this by hand was slow, and
it was easy to miss mistakes. I wanted a tool that runs these checks
automatically, so every change to a chatbot can be tested the same way and robustness is ensured.

## What it checks
- Accuracy: is the answer correct?
- Tone: does it sound the way it should?
- Stale / outdated info: does it give old information?
- Off-topic questions: does it refuse questions outside its scope?
- Performance: speed and token usage
- Difficulty: test cases grouped by easy / medium / hard

## How it works
[Test cases] → [Chatbot] → [Checks] → [Score report]

1. You write test cases (question + expected answer + difficulty)
2. The evaluator sends each question to the chatbot
3. Each answer is checked for accuracy, tone, stale info and off-topic handling
4. Speed and token usage are measured
5. Results are combined into a score report

## Future ideas
- Detect what type of AI system is being tested
- Generate test cases automatically
- Support more than chatbots (e.g. agents)

## Status
Work in progress.

## Tech
Python.
