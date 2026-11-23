# Setup & curator guide

## 1. Push the files (Git Bash)

```bash
cd ~/Desktop
git clone https://github.com/compchemsk/Modern_Quantum_Biology.git
cd Modern_Quantum_Biology
cp -r ~/Downloads/Modern_Quantum_Biology/. .
git add -A
git commit -m "BioQubit Atlas"
git branch -M main
git push -u origin main
```

To use a different repository name, change `repo:` in `config/site.yaml` before pushing (or edit it on GitHub afterwards). Everything else follows automatically.

## 2. Let the robot write
**Settings → Actions → General → Workflow permissions →** choose **Read and write permissions**, then **Save**.

## 3. Turn on the website
**Settings → Pages →** set Source to **Deploy from a branch**, Branch to **main**, and Folder to **/docs**, then **Save**.
After 1–2 minutes (green tick under **Actions**) the site is at <https://compchemsk.github.io/Modern_Quantum_Biology/>.

## 4. Add the OpenAlex key (free)
1. Make an account at <https://openalex.org> and copy your key from <https://openalex.org/settings/api>.
2. **Settings → Secrets and variables → Actions → New repository secret**. Name it `OPENALEX_API_KEY` and paste the key.

## 5. Lock it down
These settings take a minute each and close the remaining doors:

| Setting | Where | Choose |
|---|---|---|
| Protect `main` from force-push and deletion | **Settings → Rules → Rulesets → New branch ruleset**. Target: default branch. | Enable **Restrict deletions** and **Block force pushes**. Leave "Require a pull request" **off**, because the robot commits directly. |
| Fork pull requests can't run workflows unattended | **Settings → Actions → General → Fork pull request workflows** | **Require approval for all external contributors** |
| Private security reports | **Settings → Code security** | Turn on **Private vulnerability reporting** |
| Dependabot alerts | **Settings → Code security** | Turn on **Dependabot alerts** |
| Your account | github.com → **Settings → Password and authentication** | Turn on **two-factor authentication**. Approval is only as safe as your login. |
| If spam issues ever appear | **Settings → Moderation options → Interaction limits** | Limit to prior contributors temporarily |

## 6. Notifications and first run
* Click **Watch → All Activity** on the repo and install **GitHub Mobile**. New candidates reach your phone.
* **Actions → Literature watcher → Run workflow**, then enter `90` days for the first catch-up.

---

## Daily curating

| You receive… | Do this |
|---|---|
| A **candidate issue** from the watcher | Comment `/approve` (or `/approve lov` for another section), or `/reject`. |
| A **suggestion email** from the website | Open the site's **Curator desk** (footer link), paste the DOI and click **Add on GitHub**, then submit. The issue title starts with `Add:`, and because you opened it, the paper goes straight in. |
| A **suggestion issue** from someone | The bot posts a prepared entry. Comment `/approve` or `/reject`. |

The **Curator desk** on the website lists everything waiting for your decision, with shortcuts to run the watcher or edit the data. It can't change anything itself; every action happens on GitHub under your login.

Sections: `biological-qubits`, `radical-pair`, `methods`, `flavin-spin`, `lov`, `posner`, `theory`, `reviews`.

## Where things live

| To change | Edit |
|---|---|
| Repository name, your email, site title | `config/site.yaml` |
| The papers themselves | `data/papers.yaml` |
| Books, reviews, software on the site | `config/resources.yaml` |
| What the watcher looks for | `config/watch.yaml` |
| Sections | `config/categories.yaml` |
| Website look and behaviour | `docs/index.html`, `docs/assets/app.css`, `docs/assets/app.js` |

Edit any of these on GitHub and commit. The *Build & validate* workflow regenerates README, RESOURCES, CITATION, BibTeX and the website data within a minute.

Never commit PDFs; `.gitignore` blocks them.
