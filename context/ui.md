# User Interface Specification

## Visual Style
- Minimal, modern, clean, and responsive.
- Persian language with right-to-left (RTL) layout.
- Use readable Persian typography, clear spacing, and restrained colors.
- Avoid unnecessary animations, decorative elements, and complex navigation.

## Main Page
1. A clear title describing the Persian proofreading service.
2. A short explanation of what the service corrects.
3. A large textarea for entering Persian text.
4. A character counter showing the current length and maximum length of 1000 characters.
5. A primary button labeled «اصلاح متن».
6. A loading state while a request is processing.
7. A result panel below the input showing the corrected text.
8. A copy button for copying the corrected result.
9. Clear Persian error messages for invalid input or service failures.

## Privacy and Consent
- Pressing «اصلاح متن» opens a Persian consent dialog **before** any request is sent.
- The dialog offers exactly two choices, both of which run the correction:
  - «موافقم، ذخیره شود» — correct the text and allow storing the original and corrected text for
    quality evaluation.
  - «فقط متنم را اصلاح کن» — correct the text without storing either text in evaluation logs.
- Dismissing the dialog (Escape, clicking the backdrop, or the close button) sends nothing and asks
  for nothing.
- The dialog explains both choices in plain Persian and never blocks the correction itself.
- The choice is sent as `store_for_evaluation` and enforced by the backend
  (`correction-logging.md`); the interface must not claim storage succeeded.

## Interaction
- Disable repeated submissions while a request is processing.
- Ask for consent on every submission; never reuse a previous answer silently.
- Display validation errors near the input when possible.
- Display the corrected result only after a successful response.
- Do not replace the original input with the corrected text.
- Preserve line breaks in the input and result.
- Make the interface usable on desktop and mobile.
- Do not add accounts, history, a database, or unrelated features in V1.