# Delivery Intent DOCX generation prompt (template-first)

Use this prompt when generating a Word DOCX so it **matches the corporate template** (front matter, header/footer, and an updatable Word Table of Contents).

## Inputs
- **Template DOCX (must be used as the starting document):** `incoming/TEMPLATE Delivery Intent.docx`
- **Source content (authoritative):** `docs/Identity-Redesign-DI/Delivery-Intent.md`
- **Output DOCX:** `docs/Identity-Redesign-DI/Delivery-Intent.docx`

## Prompt (copy/paste)

You are a document assembly engine. Your job is to produce a Word `.docx` that preserves the template’s layout and styles.

**Hard requirements (do not violate):**
1. Start from the provided template file `incoming/TEMPLATE Delivery Intent.docx`. Do **not** create a new blank document.
2. Preserve **header/footer**, page setup, margins, section breaks, and all existing template styles.
3. Preserve the existing Word Table of Contents **as a Word TOC field**, not a manually-typed or static TOC.
   - The template already contains a TOC field like: `TOC \o "1-3" \z \u \h \n`.
   - Keep it intact so it can be updated in Word.
4. Do not delete template front matter sections (e.g., Instructions, Document history). Populate them if placeholders exist.
5. Do not remove or alter section/field structures that control template behavior:
   - Do not delete section breaks.
   - Do not replace the TOC field with static text.
   - Do not rewrite the document as a fresh conversion output.
6. Only replace content where the template clearly indicates placeholders. Treat these as placeholders:
   - Any text wrapped in angle brackets like `<...>`.
   - Any instruction sentences like `Insert narrative details...` / `Please work with your EA...` / `Provide details...`.
   - Empty table rows intended for content entry (keep the table; populate cells).
   Do not delete non-placeholder template text.
7. All section headings that should appear in the TOC must use Word styles:
   - Major sections: **Heading 1**
   - Subsections: **Heading 2**
   - Sub-subsections: **Heading 3**
   Do not fake headings with bold/size changes.
8. Where the template provides tables, **fill the existing tables** (do not replace them with new tables unless the template explicitly has no table).
9. Do not change the template color theme, fonts, or spacing rules. Use the existing styles.

**Content rules:**
- Use `docs/Identity-Redesign-DI/Delivery-Intent.md` as the source of truth.
- Map the content into the template’s primary sections:
  - `Architectural Review Board (ARB)`
  - `Information Security`
  - `Artificial Intelligence`
  - `Foundational`
  - `Appendix`
- If the markdown contains content that doesn’t fit a specific template subsection, place it in the closest appropriate section under a new Heading 2/3, but only inside the corresponding template parent Heading 1 section.

**Insertion guidance (be strict):**
- Do not insert Delivery Intent content into the template’s “Instructions” section.
- Keep front matter present even if not fully populated.
- When moving Markdown content into the template, prefer:
  - Filling the template’s existing subsections first.
  - Adding new subsections only when the template has no suitable placeholder.
- If the Markdown includes a top-of-document header image, do not import it into the body. The template header/footer should control document branding.

**Output:**
- Write the result to `docs/Identity-Redesign-DI/Delivery-Intent.docx`.
- Do not output explanations; output only the final DOCX.

## Validation checklist (run after generation)
Open the output DOCX in Microsoft Word and verify:
1. Header/footer looks identical to the template.
2. Front matter pages are present.
3. The TOC is a field-driven TOC.
   - In Word: click the TOC → “Update Field” → “Update entire table”.
4. Headings show as Heading 1/2/3 styles (Home → Styles) and the updated TOC populates expected entries.

## Common failure modes to avoid
- Converting markdown directly to DOCX with a reference doc (often loses template front matter/TOC behavior).
- Replacing the TOC with a static list.
- Creating headings by formatting text instead of applying Heading styles.
- Deleting section breaks (can break headers/footers).

