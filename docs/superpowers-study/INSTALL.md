# Superpowers Installation (Cursor)

## Marketplace install (recommended)

In Cursor Agent chat:

```text
/add-plugin superpowers
```

Or search **Superpowers** in the Cursor plugin marketplace (v5.1.0).

## Project-local install (this study)

This repo vendors Superpowers at `vendor/superpowers` (tag **v5.1.0**) and symlinks all 14 skills into `.cursor/skills/` for reproducible research without marketplace dependency.

```bash
# Already done during study setup:
ls .cursor/skills/   # 14 symlinks → vendor/superpowers/skills/*
```

## Verification checklist

| Check | Command / action | Expected |
|-------|------------------|----------|
| Plugin version | `cat vendor/superpowers/.cursor-plugin/plugin.json` | `"version": "5.1.0"` |
| Skill count | `ls vendor/superpowers/skills \| wc -l` | 14 |
| Project skills | `ls .cursor/skills/` | 14 symlinks |
| Session hook | `CURSOR_PLUGIN_ROOT=vendor/superpowers bash vendor/superpowers/hooks/session-start \| head -c 200` | JSON with `additional_context` containing `using-superpowers` |
| Hook config | `cat vendor/superpowers/hooks/hooks-cursor.json` | `sessionStart` → `run-hook.cmd session-start` |

## Session-start hook test

```bash
cd /path/to/endoscopy-resnet
export CURSOR_PLUGIN_ROOT="$(pwd)/vendor/superpowers"
bash vendor/superpowers/hooks/session-start | python3 -c "
import json, sys
d = json.load(sys.stdin)
assert 'additional_context' in d
assert 'using-superpowers' in d['additional_context']
print('PASS: session-start injects using-superpowers')
"
```

## Notes for Cursor vs Claude Code

- Upstream `using-superpowers` references a **Skill tool** (Claude Code). In Cursor, skills load via the plugin/skills system and `Read` on skill files.
- Session hook injects full `using-superpowers` content at session start when the marketplace plugin is installed.
- Project symlinks provide the same skill bodies for offline analysis and benchmark reference.
