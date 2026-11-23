---
name: alice
description: Quiz the user on the code or documents in the current folder so they come to understand what it does. Claude reads the material, writes multiple-choice questions, serves a ten-minute quiz in the browser, and keeps a heatmap of the user's understanding so each quiz concentrates on weak areas. Use when the user says "/alice", "ask Alice", "quiz me on this", "test my understanding of this code/repo/document", or asks to see their understanding heatmap. The user never writes questions; Claude does.
---

# Alice

Alice helps a person understand what a body of code or documents **does**. You write the
questions; a Python helper serves them in the browser, records the answers and computes a
heatmap of understanding (rows: topics; columns: Purpose, Flow, Edge cases, Rationale, Change).

**Helper:** `A:\Projects\Tools\Alice\Alice.cmd` — run it with the PowerShell or Bash tool. Its design is in
`A:\Projects\Tools\Alice\Documents\AlicePlan.md`; you do not need to read that to run a quiz.

## Rules that always apply

1. **The user never writes or chooses questions.** They are usually being quizzed on material
   they do not yet understand. Do not ask them what to ask.
2. **No spoilers.** Before and during the quiz, never show question text, options, answers or
   explanations in the conversation. Do the writing and checking in subagents (see steps 4 and
   5) so that the content stays out of the user's view, and describe progress in general terms
   ("writing ten questions on the retry logic").
3. **Every answer must be provable from the source.** A wrong "correct" answer destroys trust
   in the whole tool. If you cannot point at the lines that settle a question, do not ask it.
4. **Ask about behaviour, not names.** What happens if, why it is done this way, what breaks if
   it is removed, where you would change it. Never "what is this variable called".
5. Do not commit or push anything unless the user asks. Results are private to the user: never
   copy them into the subject's folder.

## Arguments

- none: quiz on the subject containing the current folder.
- a folder, file or topic name: restrict the quiz to topics that cover it.
- `status` or `heatmap`: show the heatmap in the conversation (step 2 only) and stop.
- a number: that many questions (default 10, about one minute each).
- `alice` (exactly that word, any case): the Easter egg below. Skip steps 0 to 7.

### Easter egg: `/alice alice`

Alice is named after a line in the song "White Rabbit", and this quiz is on its lyrics. The
questions are already written, so write none and check none. Run, in the background:

```
"A:\Projects\Tools\Alice\Alice.cmd" Run -s "A:\Projects\Tools\Alice\EasterEgg\WhiteRabbit" --quiz "A:\Projects\Tools\Alice\EasterEgg\WhiteRabbit\Quiz.json"
```

Tell the user only that Alice has something for them in the browser; do not say what it is
about, and rule 2 (no spoilers) still applies. When it finishes, give the score in one light
line and stop: no debrief, and no mention of changes to commit. Its results are kept under a
subject of their own, so they never touch the heatmap of the user's project.

## Step 0 — Find the subject and check the helper

The **subject root** is the nearest folder, from the current one upwards, that contains
`.alice\TopicMap.json`. If there is none, use the Git repository root; if there is no
repository, the current folder.

Run `"A:\Projects\Tools\Alice\Alice.cmd" Validate -s "<subject root>"`.

- Exit code 9: Python is missing. Relay the installation instructions the helper printed and stop.
- "File not found … TopicMap.json": this is a new subject; go to step 1.
- Invalid questions listed: repair or delete them (in a subagent) before going on.

## Step 1 — New subject: build the topic map (first time only)

Read enough of the subject to divide it into **topics by function** (what the system does),
not by file or folder. **Aim for 4 to 10 topics; a large subject may need up to about 15.**
This is a guide, not a limit: the helper accepts any number. Fewer, broader topics mean the
heatmap fills in sooner (each topic adds five cells, and a quiz asks about ten questions), but
never merge unrelated areas to meet the number, because a merged topic gives a blurred score.
Do not tell the user that Alice limits the number of topics.

For a large subject, delegate the reading to subagents and keep only their summaries. Each
topic lists the source files that implement it, with paths relative to the subject root and
forward slashes.

Write `<subject root>\.alice\TopicMap.json`:

```json
{
    "intSchemaVersion": 1,
    "strSubjectName": "Linea-Onion-WhiteChip",
    "strDescription": "One sentence on what the subject is.",
    "listTopics": [
        {
            "strId": "retry-and-timeout",
            "strName": "Retry and timeout handling",
            "strDescription": "One or two sentences on what this part does.",
            "listSourceFiles": [ { "strFile": "Src/Comms/Retry.cpp", "strHash": "" } ]
        }
    ]
}
```

`strSubjectName` and each `strId` may use only letters, digits, `-` and `_`. Use the repository
name for `strSubjectName`; it is the key under which every user's results are stored, so it
must never change afterwards.

**Show the user the topics (name and one line each) and ask them to confirm or adjust before
going on.** This is the one thing they are asked to approve. Then run
`"A:\Projects\Tools\Alice\Alice.cmd" Stamp -s "<subject root>"` to record the state of the source files.

## Step 2 — Ask the helper what to quiz

Run `"A:\Projects\Tools\Alice\Alice.cmd" Status -s "<subject root>" -n <questions>`. It prints JSON:

| Field                       | Meaning |
|-----------------------------|---------|
| `listTargets`               | The cells to ask about, one entry per question, already balanced between weak, untested, stale and review. **Follow it.** |
| `listCells`                 | Every cell: the user's `fScore` (null = never asked), and the bank's questions for that cell with the user's record on each (`intTimesAsked`, `bLastCorrect`, `bChallenged`). |
| `dictStaleTopics`           | Topics whose source has changed since the map was stamped. |
| `listChallengedQuestionIds` | Questions someone has disputed. Never put these in a quiz: `Run --ids` refuses a quiz that holds one. |
| `listInvalidQuestions`      | Questions that fail validation. |
| `listWarnings`              | Result files of the user's that could not be read and were left out. Normally empty. If not, tell the user which file, and that the heatmap is missing that quiz. |

For `status`/`heatmap`: show `listCells` as a table (topics down, kinds across, percentages,
`–` for never asked), name the three weakest cells, and stop.

If the user restricted the quiz to a folder, file or topic, keep only targets in matching
topics and fill the gaps with other cells of those topics, weakest first.

**Housekeeping before writing questions** (do it in a subagent; tell the user in one line):

- **Stale topics.** Re-read the changed files. For each bank question on that topic, check it
  is still true: correct it, or delete it if its point no longer exists. Update the topic's
  `listSourceFiles` if files were added, renamed or removed. Then run `Stamp`.
- **Challenges** (`.alice\Challenges\*.json`). Read the question, the challenger's note and the
  source. If the challenge is right, fix the question — or, if the fix changes what it asks,
  delete it and write a replacement under a new id. If the question was right, improve its
  wording or explanation so the confusion does not recur. Delete the challenge file either
  way, and after the quiz tell the user briefly what was decided.

## Step 3 — Choose a question for each target

For each entry in `listTargets`, in this order of preference:

1. A bank question for that cell with `intTimesAsked` 0 and not challenged.
2. Otherwise **write a new question** for that cell (step 4). This is the normal case for a
   weak cell: a missed idea should come back in different words, not as the same question.
3. Reuse a question the user has already seen only if the cell's source is too thin to support
   another good question; prefer the one asked longest ago.

Also choose or write **one rabbit hole question**: optional, harder, ideally linking two topics
(for example tracing one event through several modules). It is offered after the main quiz.

## Step 4 — Write the new questions (in a subagent)

Get ids with `"A:\Projects\Tools\Alice\Alice.cmd" NewIds -s "<subject root>" -n <count>`. Give a subagent
the targets, the topic descriptions and source file lists, the ids, and the whole of the
"Writing good questions" and "Question file" sections below. It writes one file per question to
`<subject root>\.alice\Questions\<id>.json` and reports only the ids and the cell each covers.

### Writing good questions

- **One idea per question**, answerable by someone who understands the code without having
  memorised it. Readable in about 30 seconds: stem under 60 words.
- **Match the kind:**
  - *Purpose* — what this part is for; what problem it solves.
  - *Flow* — what happens, in what order; how data and control move.
  - *EdgeCases* — failure modes, limits, unusual input, what happens when things go wrong.
  - *Rationale* — why it was built this way rather than the obvious alternative.
  - *Change* — where and how you would safely modify it; what else must change with it.
- **Exactly one option is correct, and the source proves it.** No "all of the above", no
  "none of the above", no trick wording, no negatives in the stem ("which is NOT…").
- **Wrong options are plausible misunderstandings** — what someone would believe after
  skimming the code, or what a similar system does. Never obviously silly. All four options
  alike in length and style, so the correct one cannot be spotted by its shape.
- **Every option has a `strWhy`**: one or two sentences on why it is right, or exactly where
  the misunderstanding lies. This is where most of the teaching happens.
- **`strExplanation`** gives the reasoning in two to four sentences: the *why* behind the
  answer, not a restatement of it.
- **Show code when the question is about specific code:** an exact copy of up to 25 lines in
  `strExcerpt`, with `strExcerptLanguage` (`c`, `cpp`, `python`, `javascript`, or `text`) and
  `intExcerptFirstLine`. Trim with a line containing only `...` if needed. The excerpt must not
  contain a comment that gives the answer away.
- **Cite the source** in `listSourceRefs`: the file, plus `strAnchor` (the function, class or
  heading name). Add `intLineFirst` only if useful; names survive edits, line numbers do not.
- **Rationale questions need evidence.** Ask "why" only where a comment, a design document, a
  commit message or the code itself makes the reason clear. Never invent a motive.
- Plain British English, professional tone, no jokes. Use backticks for identifiers.
- Do not ask about Alice, about the quiz, or about anything that is not in the subject.

### Question file

```json
{
    "intSchemaVersion": 1,
    "strId": "Q-3fa91c2e",
    "strTopicId": "retry-and-timeout",
    "strKind": "EdgeCases",
    "strStem": "The device stops replying half-way through a firmware upload. What does `SendBlock()` do?",
    "strExcerptLanguage": "cpp",
    "intExcerptFirstLine": 212,
    "strExcerpt": "optional: exact code copied from the source",
    "listOptions": [
        { "strText": "First option.",  "strWhy": "Why it is right, or where the misunderstanding lies." },
        { "strText": "Second option.", "strWhy": "…" },
        { "strText": "Third option.",  "strWhy": "…" },
        { "strText": "Fourth option.", "strWhy": "…" }
    ],
    "intCorrectOption": 2,
    "strExplanation": "Two to four sentences giving the reasoning.",
    "listSourceRefs": [ { "strFile": "Src/Comms/Retry.cpp", "strAnchor": "Retry::SendBlock", "intLineFirst": 212 } ],
    "strAuthor": "Claude",
    "strCreated": "19/11/2026"
}
```

`strKind` is one of `Purpose`, `Flow`, `EdgeCases`, `Rationale`, `Change`. There are exactly
four options; `intCorrectOption` is 0 to 3. Vary which position is correct (the page shuffles
the options anyway). `strCreated` is DD/MM/YYYY. Omit the three excerpt fields if there is no
excerpt.

## Step 5 — Check every new question blind (in a second, fresh subagent)

Give a **different** subagent the stem, excerpt and four options of each new question —
**without** `intCorrectOption`, `strWhy` or `strExplanation` — plus the source references. It
must work out the answer from the source alone and report, for each question, the option it
chose, the lines that prove it, and whether any other option could also be defended.

- Its answer matches and no other option is defensible: the question passes.
- Otherwise the question is wrong or ambiguous: have it rewritten and checked again, or drop it
  and write a different one. Never serve a question that failed this check.

Then run `Validate` again; it must report 0 invalid.

## Step 6 — Run the quiz

```
"A:\Projects\Tools\Alice\Alice.cmd" Run -s "<subject root>" --ids <id,id,...> --rabbit <id> --title "<short title>"
```

Order the ids so that topics are mixed and the quiz opens with one of the more approachable
questions. **Run it in the background** (`run_in_background`): the command opens the browser
and does not return until the user has finished, which can be longer than a foreground
command is allowed to run. Tell the user the quiz is open in their browser and that you will
pick up when they finish. Do not poll.

## Step 7 — Afterwards

The helper prints the score and the path of the result file. Read that file: each answer has
`strQuestionId`, `bCorrect`, `strConfidence` (`Sure`, `Think`, `Guess`) and `bChallenged`.

Keep the debrief short; the page has already shown every explanation and the heatmap.

- Start with anything answered wrong while **Sure**: those are the misconceptions worth a
  conversation. Offer to walk through them in the source.
- Mention right answers that were **Guess** as things that will come round again.
- Optionally invite the user to explain one missed idea back in their own words, and respond
  to what they say. Recalling is a stronger test than recognising. Never insist.
- Deal with any question they challenged, as under "Challenges" in step 2.
- Offer another quiz now, or tomorrow.

If new questions or a topic map were written, mention once that `.alice\` has changes to
commit, so colleagues get the same question bank.
