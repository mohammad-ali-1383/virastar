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

## Interaction
- Disable repeated submissions while a request is processing.
- Display validation errors near the input when possible.
- Display the corrected result only after a successful response.
- Do not replace the original input with the corrected text.
- Preserve line breaks in the input and result.
- Make the interface usable on desktop and mobile.
- Do not add accounts, history, a database, or unrelated features in V1.