# Session acceptance checklist

This checklist separates working scripts from an assistant actually using them. No private slides or conversation transcripts are included here.

| Case | What must be observed | Status in v1.1.0 |
| --- | --- | --- |
| Python + RDKit environment | Probe renders acrolein, validates its formula and checks the PNG | Automated local check |
| Missing dependencies | Probe reports the missing dependency and returns no successful image claim | Automated local check |
| Chat attachment package | Extract into a fresh directory, read the starter, execute the extracted probe | Automated local check; not an actual hosted Chat test |
| Native Work installation | Installed skill is discoverable; installed probe can run in the selected local runtime | Verified on the author's local host |
| Real ordinary Chat tutoring | User uploads starter, archive and slides; the assistant reads them, reports actual capabilities, explains the current page with generated diagrams, asks one question and waits | Requires validation in that actual chat; not claimed complete |
| Real PPT interpretation | Correct file, physical page, structures, conditions and explanation | Requires the user's slides and page-level review |

Use a small, redistributable slide extract for behavioral checks. Do not assume that page numbers written in a response prove the slide was read, that executable source proves it was run, or that a clickable local quiz proves the assistant received the answer.

For the next turn after an incorrect answer, inspect whether the assistant identifies the decisive error and changes a meaningful condition in a follow-up problem. This is an observable learning workflow, not a software test that can be proven by checking instruction text.
