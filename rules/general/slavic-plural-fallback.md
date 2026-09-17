Rules for Slavic languages (Polish, Russian, Ukrainian, and similar) when the source string uses a count variable but does **not** provide a `msgid_plural` entry (i.e., a single msgid handles all counts > 1 with a `{count}` placeholder).

## Problem

Polish, Russian, Ukrainian, and other Slavic languages require different noun forms depending on the count value:

- Polish: 1 → nominative singular, 2–4 → nominative plural, 5+ → genitive plural
- Russian/Ukrainian: 1 → nominative singular, 2–4 → genitive singular, 5+ → genitive plural

When only one msgid exists for all counts > 1, no single inflected noun form is correct for every possible count.

## Rule: use a count-neutral label construction

When the source has a single msgid containing `{count}` but no `msgid_plural`:

1. **Do not** use the genitive plural as a "universal" form — it is grammatically incorrect for counts 2–4 and will be noticed by native speakers.
2. **Restructure** the translation so the noun appears as a count-neutral category label (nominative plural) separated from the count variable. For example:

   - Source: `{count} browsers on {platform} device(s)`
   - Polish: `Przeglądarki: {count} na urządzeniach {platform}` ✓
   - Russian: `Браузеры: {count} на устройствах {platform}` ✓
   - Ukrainian: `Браузери: {count} на пристроях {platform}` ✓

3. If no count-neutral restructuring is possible without distorting the meaning, leave a comment in the PR explaining the limitation so the source-code owner can add proper plural support.
