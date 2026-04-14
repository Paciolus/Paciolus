# LLM Code Hallucination Audit Prompt

> **Usage:** Invoke via `/audit` or reference this file directly to audit the codebase for common LLM-generated code hallucinations. See `.claude/agents/AUDIT_OWNERSHIP.md` for how this channel fits alongside `/audit`, the Digital Excellence Council, and the Accounting Expert Auditor.

---

## Prompt

```
You are performing a thorough audit of this codebase for common LLM code hallucinations — plausible-looking code that is subtly wrong. Work through each category below systematically. For every finding, report the file, line number, the specific issue, and a suggested fix.

### 1. Non-Existent APIs and Methods

Scan every import and method call. For each external library used in this project:
- Verify that every function, method, and class being called actually exists in that library.
- Flag any method name that looks plausible but does not exist (e.g., `df.to_markdown(index=False, tablefmt="grid")` when `to_markdown` doesn't accept `tablefmt`).
- Check for methods that exist on a *different* class in the same library but not on the one being used.
- Look for methods from one library being called on objects from a different library.

### 2. Fabricated or Confused Package Names

Inspect `requirements.txt`, `pyproject.toml`, `package.json`, `Cargo.toml`, `go.mod`, and any other dependency manifests:
- Flag any package name that does not exist in its respective registry (PyPI, npm, crates.io, etc.).
- Flag packages that exist but are likely the wrong package (name confusion / typosquatting risk).
- Check for packages that were renamed or superseded (e.g., using `sklearn` instead of `scikit-learn` in requirements).

### 3. Wrong Function Signatures

For every external function call:
- Verify parameter names are real keyword arguments the function accepts.
- Check that positional argument order matches the actual signature.
- Flag any invented keyword arguments (e.g., passing `timeout=` to a function that doesn't support it).
- Verify default value assumptions in comments or conditional logic match actual defaults.

### 4. Outdated or Version-Mismatched APIs

Cross-reference the library versions pinned in dependency files against the APIs being used:
- Flag any usage of APIs that were deprecated or removed in the version being used.
- Flag usage of APIs that only exist in a newer version than what's pinned.
- Look for mixed usage patterns from different major versions of the same library (e.g., TensorFlow v1 `tf.Session` alongside v2 `tf.function`).
- Check for React class component patterns in a codebase using only functional components, or vice versa.

### 5. Plausible but Incorrect Logic

Carefully review algorithmic logic for subtle errors:
- Off-by-one errors in loops, slicing, and boundary conditions.
- Incorrect comparison operators (e.g., `>` vs `>=`, `==` vs `===`).
- Regex patterns that don't match what comments or variable names claim they match.
- Math/formula errors — verify any non-trivial formula against its stated purpose.
- Sorting comparators with flipped signs or wrong return values.
- Boolean logic errors (De Morgan's law violations, wrong short-circuit behavior).
- String operations that silently fail on edge cases (empty strings, unicode, null).

### 6. Invented Configuration Options

Review all configuration files (Dockerfiles, CI/CD configs, nginx/Apache configs, database configs, cloud provider configs, linter configs):
- Flag any directive, key, or option that does not exist for the tool and version being used.
- Flag option values that are outside the valid set of values.
- Check for options that exist in a different config file format or tool version but not the current one.

### 7. Hallucinated File Paths and Environment Details

Check all hardcoded paths, environment variable references, and platform assumptions:
- Flag file paths that assume a specific OS layout without checking (e.g., hardcoded `/usr/local/bin/` paths on Windows).
- Flag environment variable references that are non-standard or likely don't exist.
- Flag assumptions about default file locations that vary by OS or installation method.
- Check that all referenced file paths within the project actually exist.

### 8. Fake Error Codes and Status Values

Audit all error handling:
- Verify HTTP status codes are real and used correctly (e.g., not using 422 when 400 is meant, or referencing non-existent codes).
- Verify database error codes, exception class names, and error constants actually exist in the libraries/systems being used.
- Check that caught exception types are real classes that can actually be raised by the code in the try block.
- Flag any error message strings that reference non-existent error codes or statuses.

---

## Output Format

For each finding, report:

**[CATEGORY]** Category name
**[SEVERITY]** Critical | High | Medium | Low
**[FILE]** path/to/file.ext:LINE
**[ISSUE]** Description of the hallucination
**[EVIDENCE]** Why this is wrong (reference actual API docs/signatures)
**[FIX]** Suggested correction

Severity guide:
- **Critical**: Will cause a runtime crash, security vulnerability, or data corruption.
- **High**: Will cause incorrect behavior that may not be immediately obvious.
- **Medium**: Will cause issues under specific conditions or edge cases.
- **Low**: Style/best-practice issue stemming from hallucinated conventions.

At the end, provide a summary table with counts by category and severity.
```

---

## Quick Start

### Option A: Run as a one-shot audit
```bash
claude -p "$(cat .claude/agents/LLM_HALLUCINATION_AUDIT_PROMPT.md)" --allowedTools "Read" "Grep" "Glob"
```

### Option B: Scope to specific files
```bash
claude -p "Audit only backend/routes/ using these checks: $(cat .claude/agents/LLM_HALLUCINATION_AUDIT_PROMPT.md)"
```

### Option C: Reference from within Claude Code
```
> Run the hallucination audit from .claude/agents/LLM_HALLUCINATION_AUDIT_PROMPT.md
```
