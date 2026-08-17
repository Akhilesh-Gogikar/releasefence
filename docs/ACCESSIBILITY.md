# Accessibility

ReleaseFence treats its CLI and generated HTML as functional interfaces.

## Baseline

- Reports use semantic `header`, `main`, `section`, and `article` landmarks with one page-level heading.
- A visible-on-focus skip link moves keyboard users directly to report content.
- Finding permalinks and controls retain a high-contrast focus outline.
- Severity is always written as text and never communicated by color alone.
- Evidence uses selectable text; the report contains no scripts, animation, or remote assets.
- CLI diagnostics go to stderr, machine JSON can go to stdout, and exit codes remain documented.

## Release checks

Before a tagged release, inspect green, amber, and red reports using keyboard-only navigation, browser zoom at 200%, a screen reader's landmark/heading list, and both light and forced-color/high-contrast modes. Check contrast for text, links, focus rings, and severity borders.

## Known limits

Very long paths and evidence can require horizontal scrolling inside code blocks. The HTML does not provide interactive filtering, and screen-reader behavior can vary by browser. These tradeoffs keep reports static, local, and script-free.

Report an accessibility bug with a synthetic report through the bug template. If the report itself contains sensitive repository evidence, use the private route in [SECURITY.md](../SECURITY.md).
