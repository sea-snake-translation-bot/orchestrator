Rules for translation problems that no catalogue edit can fix, because the limitation is in how the source message is built rather than in any translation of it.

When you meet one, the catalogue is the wrong place to solve it. Translate as faithfully as the source allows, then record the defect so it can be fixed where it lives. A reworded translation that papers over the defect looks correct to a reviewer who only reads the diff, and it buries the real problem — often while quietly changing what the string says.

Recording it does more than inform someone. Where a repo enables `escalation` in `repos.yml`, a defect written to `$ESCALATIONS_FILE` starts the Escalate workflow, which fixes the message in that repo's source and pushes the fix onto the same translation PR — so the entry it regenerates can then be translated properly. That is the outcome to aim for: the defect fixed at the source and the catalogue correct because of it, not in spite of it. Your part is an accurate report; a vague one escalates to nothing.

## Rules

- Never reword a translation to sidestep a source defect. Say what the source cannot express, and translate the entry as closely to the original as the language permits in the meantime.
- Never change what the source asserts. If the English leaves something vague, the translation leaves it vague; if the English commits to a number, a gender or an order, the translation commits to the same one. Resolving an ambiguity is a change in meaning, not a translation choice.
- Never propose a general rule that encodes a workaround for a source defect. A rule that tells every future run to reword around a broken message makes the defect permanent and spreads it to other repos.
- Report once per defect, in a comment on the PR, naming the source file and line, what the message currently does, what no translation can express, and the concrete source change that would fix it.

## Defects to recognise

**A count interpolated into a message with no plural structure.** For example `{count} browsers on {platform}` as a single msgid, or a component picking between two separate msgids with a ternary on the count. That offers at most two forms. Polish, Russian, Ukrainian, Arabic and others need three or four, so no single inflected noun is right for every count, and the genitive plural that reads correctly for 5+ is wrong for 2–4. This is not fixable in the catalogue: the source has to use its plural macro so the entry becomes a real ICU plural with categories the target language can extend. Note that `rules/general/general.md` covers extending an ICU plural that already exists — this rule is for when there is no plural to extend. Do not restructure the noun into a count-neutral label to dodge the agreement; that changes register and hides the defect.

**A sentence concatenated from several msgids.** See `rules/general/split-string-links.md`, which covers the hyperlink case in detail and ends the same way: when no split can be made grammatical, report it and ask for one msgid with a `<0>…</0>` placeholder.

**An English-only device in the source text.** A parenthetical plural such as `device(s)`, a slash form such as `and/or`, or a bare noun standing for both numbers. These often carry a deliberate ambiguity — the writer does not know the number and is refusing to claim one. Mirror the parenthetical where the target language has that convention, and where it has none, drop the noun rather than commit to a number. Never resolve the hedge into a definite plural. When a `msgctxt` explains the ambiguity, it is telling you to keep it.

**A message whose meaning cannot be determined from the string alone,** with no `msgctxt` to disambiguate it. Ask for a context rather than guessing; a wrong guess is invisible in review and wrong in only one locale.

**Grammatical properties of the reader or subject assumed by the English,** such as gender or formality that the source has no variable for. Report what the target language needs; do not invent a form.
