Rules for translating strings that are split to embed a hyperlink.

Some UI components render a sentence by concatenating two separate translation keys: the first key is the surrounding text and the second key is the hyperlink label. For example:

- `"If this keeps happening, copy these details and include them in a"` (text before link)
- `"support request"` (link text)

When translating these split-string pairs, you must verify that the two translated fragments, when concatenated, form a grammatically complete and natural sentence in the target language.

## Rules

- Always check whether the preposition or case required by the first fragment is satisfied by the declension/form used in the second fragment (e.g. Polish: after `dołącz je do` the following noun phrase must be in genitive).
- For languages with SOV word order (e.g. Urdu, Turkish, Japanese), the verb typically falls at the end of the sentence. If the verb is missing from the concatenated result, add it to the **second fragment's translation** (the link text) so the full sentence is grammatically complete. The link text may be longer than in English — that is acceptable.
- Never hard-code a word from the second fragment into the first fragment's translation; keep both fragments cleanly separated.
- If no split-string design can produce a grammatically correct sentence for a given language, leave a comment in the PR explaining the issue so the source-code owner can refactor the UI to use a single msgid with a `<0>…</0>` link placeholder.
