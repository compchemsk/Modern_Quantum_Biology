# Security

## How the Atlas is protected

| What | How |
|---|---|
| **Who can add papers** | Only accounts listed under `curators:` in `config/watch.yaml` (plus the repository owner). Two locks apply: the *Curate* workflow only starts for owners, members or collaborators, and the script then checks the curator list again. Commands from anyone else are ignored. |
| **Instant add** | An issue titled `Add: …` goes straight in only when the curator's own account opened it. From anyone else it is an ordinary suggestion. |
| **The website** | A static page with a strict Content-Security-Policy: no inline scripts, and it loads nothing except its own files, Google Fonts and GitHub's public API. It has no login and no write access to anything. |
| **Suggestions by email** | The form only opens the visitor's own email app; nothing is sent from the site and nothing is stored. The curator's address is not written out in the page source. |
| **Pull requests** | Contributors' pull requests run a read-only validation job without secrets. Only pushes to `main` can rebuild and commit. |
| **Untrusted text** | Issue titles and bodies are parsed as data (`yaml.safe_load`) and never run as shell commands. All text shown on the website is HTML-escaped. |
| **Secrets** | The only secret is `OPENALEX_API_KEY`, stored in GitHub's encrypted secrets and never printed. |
| **Dependencies** | Python stdlib plus pinned PyYAML. Dependabot keeps the GitHub Actions versions current. |

## Recommended repository settings
See [SETUP.md → Lock it down](SETUP.md#5-lock-it-down).

## Reporting a problem
Please use **Security → Report a vulnerability** on this repository (private) rather than a public issue.
