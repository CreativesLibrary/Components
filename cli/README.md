# components-skill

Install the [`components`](https://github.com/AnayDhawan/Components) skill into your coding agent's config directory.

`components` is a **sourcing skill**: describe an effect ("a laptop opening on scroll", "animated beams behind the features"), and your agent matches it to a proven React + Tailwind showpiece, fetches the real component live from its registry, and adapts it to your brand tokens. It ships pointers, never pasted code.

## Install

```bash
npx components-skill@latest add
```

That writes `.claude/skills/components/` into the current project. Nothing is installed globally and the package has **zero dependencies**.

## Usage

```bash
npx components-skill@latest add                  # Claude Code, this project
npx components-skill@latest add --agent all      # every supported agent
npx components-skill@latest add --agent cursor   # just Cursor
npx components-skill@latest add --global         # ~/.claude/skills/components
npx components-skill@latest add --dry-run        # list what would be written, write nothing
npx components-skill@latest update               # refresh, keeping your edits
npx components-skill@latest list                 # what is installed where, and whether it is current
npx components-skill@latest search "laptop opening"   # find a showpiece before installing
npx components-skill@latest tokens                    # read this project's brand tokens
```

### Options

| Flag | Meaning |
|------|---------|
| `--agent <name>` | `claude` \| `codex` \| `cursor` \| `gemini` \| `all`. Default `claude`. Comma-separated lists work too. `add`/`update`/`list` (where `list` defaults to every agent). |
| `--global` | Install into your user config dir instead of the current project. Not supported for Cursor, which has no documented user-level rules directory. |
| `--force` | On `update`, overwrite files you have edited locally. |
| `--dry-run` | On `add`, print every file that would be written and the install root it goes under, plus the manifest. Creates no directories and writes no files. |
| `--library <name>` | On `search`, restrict results to one source library (`aceternity`, `magicui`, `cult-ui`, `reactbits`, `21st.dev`, `shadcn`, `tremor`, or a port library such as `vue-bits`, `inspira-ui`, `svelte-bits`). |
| `--framework <fw>` | On `search`, which port to search: `react` (default), `vue`, or `svelte`. Composes with `--library`. |
| `--json` | On `search`, `tokens`, and `list`, print machine-readable JSON instead of a summary. |
| `-v`, `--version` | Print the version. |

## `search`: find a showpiece before you install

The registry has 39 showpieces plus 12 plain fallbacks; `search` looks up name, alias, effect, and library entirely offline, against the same `components.json` `add` bundles:

```
$ npx components-skill@latest search marquee
  marquee            [showpiece/magicui]  infinite scrolling row/grid of logos or cards
      aliases: logo wall, infinite scroll row, testimonial carousel

$ npx components-skill@latest search card --library cult-ui
  texture-card       [showpiece/cult-ui]  layered texture/border card with tactile depth
      aliases: tactile card, textured gradient card, layered border card
```

Every query term must match (name, alias, effect, or library); exits `1` with no results.

`--framework vue` or `--framework svelte` searches the ports instead. Only showpieces that carry that variant come back, reported with the port's library and `ref`; plain fallbacks are React only. `--library` applies after that, so the two compose:

```
$ npx components-skill@latest search text --framework vue --library vue-bits
  blur-text          [showpiece/vue-bits vue] words blur-fade into focus sequentially
      aliases: blur fade-in text, text unblur reveal
```

`--json` prints an array an agent can read without scraping the table. Each row has `id` (the registry name), `kind`, `framework`, `library`, `ref`, `fetch`, `effect`, `aliases`, `license`, and `deps`. No matches prints `[]` and exits `1`.

### Where things land

| Agent | Path |
|-------|------|
| Claude Code | `.claude/skills/components/` |
| Codex CLI | `.codex/skills/components/` |
| Cursor | `.cursor/rules/components.mdc` + payload at `.cursor/components/` |
| Gemini CLI | `.gemini/extensions/components/` |

## `update` will not overwrite your edits

An installed skill is just text in your repo, and editing it to fit a project is a reasonable thing to do. So `add` records a SHA-256 of every file it writes, in `.components-skill-manifest.json` at the install root.

`update` re-hashes those files first. Anything that no longer matches is treated as yours: it is reported and **left alone**, while everything else is refreshed.

```
$ npx components-skill@latest update
Updating components skill...
  Claude Code: 1 file(s) changed since install, NOT overwritten:
      .claude/skills/components/SKILL.md
    Re-run with --force to overwrite, or move your edits aside first.
  Claude Code: 5 file(s) updated to v1.1.1 -> /path/to/project

1 locally-modified file(s) left alone.
```

Deleted files are restored. `--force` overwrites everything.

## `list`: what is installed, and is it current

`list` reads the same manifest `update` does, for every agent, in this project and in your user config dir:

```
$ npx components-skill@latest list
components-skill v1.2.0

Project (/path/to/project):
  Claude Code  v1.1.1    outdated (run `components-skill update`)
      .claude/skills/components
      1 file(s) edited locally, kept by update
  Codex CLI    -         not installed
  ...

Global (user config dir):
  Claude Code  v1.2.0    up to date
      /home/you/.claude/skills/components
  Cursor       -         unsupported (no user-level location for this agent)
```

`not installed` means no manifest entry for that agent at that root. `outdated` means an older CLI installed it and `update` would refresh it. Edited and missing files are counted with the same checksum comparison `update` uses. `--global` limits it to the user config dir, `--agent` to named agents, and `--json` prints the rows.

## `tokens`: read the target project's brand tokens

`references/adaptation.md` § 1 tells an agent to find the project's token source and map demo colors onto it, but nothing ever read that source into a form another step could compare against. `tokens` does that read: CSS custom properties in the project's global stylesheet (`:root` for light, `.dark` / `[data-theme="dark"]` / `prefers-color-scheme` for dark), a Tailwind v4 `@theme` block, and a best-effort read of a legacy `tailwind.config.*`'s `theme.extend.colors` as a fallback.

```
$ npx components-skill@latest tokens
Project: /path/to/your-project
Token source: src/app/globals.css (CSS custom properties)
Dark mode: class

Known adaptation tokens (references/adaptation.md § 1):
  [x] --background           0 0% 100%
  [x] --primary              222 47% 11%
  [ ] --accent               (not found)
  ...

Missing 6/20. Adapt onto the closest existing token, or run `npx shadcn@latest init` first...
```

`--json` prints the full structure (`light`, `dark`, `tailwindConfigColors`, `knownTokens`, `missingKnownTokens`) instead, for a tool to consume rather than a human to read. Entirely offline and read-only: it never writes to the target project.

## Offline by design

The bundles are built into the package at publish time, so `add` copies from disk and never reaches the network. An installer that needs to fetch from GitHub fails in exactly the environments where you most want it to work (offline, proxied, locked-down CI), and it would pin behaviour to whatever is on `main` rather than to the version you asked for.

## Links

- Skill repo, full showpiece list and licenses: [AnayDhawan/Components](https://github.com/AnayDhawan/Components)
- Issues: [github.com/AnayDhawan/Components/issues](https://github.com/AnayDhawan/Components/issues)

Apache-2.0. Components fetched *via* the skill carry their own upstream licenses.
