# 🏢 aiorg — AI Organization Framework

Declare an org chart in YAML; aiorg stands up one independent Claude Code session
(tmux) per member and routes instructions, reports and tasks between them through
a file-backed queue.

**Every member is a Claude session, and you talk only to the CEO.**
Give the CEO a goal; it is split down to the department leads, the engineers build,
and results travel back up.

```
👑 ceo       대표  [exec]
   |- 🎯 dev-lead  개발팀장  [dev]
   |  |- 🔧 dev-1     백엔드 개발자  [dev]
   |  `- 🔧 dev-2     프론트엔드 개발자  [dev]
   |- 📋 po        제품 책임자  [product]
   |- 📣 presales  프리세일즈  [biz]
   `- 🎯 qa-lead   품질팀장  [qa]
      `- 🔍 qa-1      코드 리뷰어  [qa]
```

The bracket is the tmux session (department). Produced by `./aiorg chart product-team`.

> **The framework speaks Korean.** Role instructions, templates, CLI output and the
> docs are written in Korean, so the members work in Korean too. This page is a
> summary for readers who do not; the reference docs it links to are Korean.

## Quick start

tmux is required. On Windows, run inside WSL.

```bash
./aiorg doctor                    # environment check (tmux, python3, PyYAML, claude, skills)
./aiorg skills --link             # make the bundled skills visible anywhere (once)
```

**The org does not work in this repository.** Point it at a product repository.

```bash
mkdir -p ~/myproduct && cd ~/myproduct && git init && cd -
./aiorg new product-team mycorp   # copy the template to org/mycorp.yaml
#   edit org.workdir in org/mycorp.yaml -> "/home/you/myproduct"
```

```bash
./aiorg up --org mycorp           # build tmux sessions + the notification watcher
./aiorg scaffold                  # artifact directories + member permissions, in the product repo
./aiorg launch                    # start claude in every seat
./aiorg status                    # wait until everyone is 대기 (idle)
./aiorg brief                     # tell each member who they are  <- skip this and no org forms
./aiorg attach ceo                # give the CEO a goal. Ctrl-b d to leave
```

Watch from outside the org — you do not need to attach.

```bash
./aiorg status                    # who is doing what, and where it is stuck
./aiorg task tree                 # the task tree
./aiorg peek dev-1                # that seat's screen only (nothing is typed into it)
./aiorg layout                    # who sits in which session, window and pane
```

## Documentation (Korean)

| | |
|---|---|
| [docs/CHEATSHEET.md](docs/CHEATSHEET.md) | **commands only**, for quick lookup |
| [docs/GETTING-STARTED.md](docs/GETTING-STARTED.md) | end to end, from an empty repository |
| [docs/EXISTING-PRODUCT.md](docs/EXISTING-PRODUCT.md) | attaching to an **existing product** (areas, worktrees, several repos) |
| [docs/AIORG.md](docs/AIORG.md) | design rationale and every setting |
| `./aiorg help` | command summary |

## Ten org templates

```bash
./aiorg templates                 # list
./aiorg chart enterprise          # draw an org chart
```

`solo`(2) · `minimal`(4) · `startup`(5) · `research`(5) · `product-team`(8) ·
`two-po`(8) · `quality-first`(8) · `existing-product`(8) · `research-build`(10) ·
`enterprise`(14). Charts are in [org/templates/README.md](org/templates/README.md).

**To change the organization, edit the org chart YAML.** The scripts stay untouched.
Role instructions live in [org/roles/](org/roles/), and each document *is* that
role's behaviour.

## What a human puts in — two paths

| | Telling the CEO | Dropping a file in `docs/voc/raw/` |
|---|---|---|
| what it is | the owner's intent | what a customer said |
| weight | **a decision.** No evidence is asked for | **evidence.** The PO and CEO decide whether to adopt it |

**Members have no customer contact.** Told to "bring me the VOC" they will invent
something plausible. So the source is pinned to a human — if it is not in `raw/`,
it is not VOC.

**Cost works the same way.** There is no billing system to read, so numbers come
only from what a human puts in `docs/finops/raw/`. When it is empty the PO reports
"no cost data available".

## Enforced by code, not by convention

Written rules were not followed, repeatedly. Each time, the machine was made to
refuse instead.

- **commit guard** — a hook rejects member commits into this framework repository
- **operator commands** — `aiorg` refuses `up`, `down`, `clean` from a member seat
- **git worktrees** — members sharing one checkout overwrite each other's branches
- **session ownership** — copy the repo and run two orgs; neither kills the other
- **warnings** — unowned code areas, members that never got briefed, a dead
  notification watcher, a working directory not yet trusted

## Requirements

`tmux` · `git` · `python3` + `PyYAML` · `claude`. `./aiorg doctor` checks them.
Under WSL, the `claude` inside WSL is a **separate install with its own login**
from the Windows one.

---

## Below is the predecessor demo

The original `setup.sh` / `agent-send.sh` / `instructions/` tmux demo, kept for
reference. It has been superseded by aiorg and is no longer maintained.

# 🤖 Tmux Multi-Agent Communication Demo

A demo system for agent-to-agent communication in a tmux environment.

**📖 Read this in other languages:** [日本語](README.md)

## 🎯 Demo Overview

Experience a hierarchical command system: PRESIDENT → BOSS → Workers

### 👥 Agent Configuration

```
📊 PRESIDENT Session (1 pane)
└── PRESIDENT: Project Manager

📊 multiagent Session (4 panes)  
├── boss1: Team Leader
├── worker1: Worker A
├── worker2: Worker B
└── worker3: Worker C
```

## 🚀 Quick Start

### 0. Clone Repository

```bash
git clone https://github.com/nishimoto265/Claude-Code-Communication.git
cd Claude-Code-Communication
```

### 1. Setup tmux Environment

⚠️ **Warning**: Existing `multiagent` and `president` sessions will be automatically removed.

```bash
./setup.sh
```

### 2. Attach Sessions

```bash
# Check multiagent session
tmux attach-session -t multiagent

# Check president session (in another terminal)
tmux attach-session -t president
```

### 3. Launch Claude Code

**Step 1: President Authentication**
```bash
# First, authenticate in PRESIDENT session
tmux send-keys -t president 'claude' C-m
```
Follow the authentication prompt to grant permission.

**Step 2: Launch All Multiagent Sessions**
```bash
# After authentication, launch all multiagent sessions at once
for i in {0..3}; do tmux send-keys -t multiagent:0.$i 'claude' C-m; done
```

### 4. Run Demo

Type directly in PRESIDENT session:
```
You are the president. Follow the instructions.
```

## 📜 About Instructions

Role-specific instruction files for each agent:
- **PRESIDENT**: `instructions/president.md`
- **boss1**: `instructions/boss.md` 
- **worker1,2,3**: `instructions/worker.md`

**Claude Code Reference**: Check system structure in `CLAUDE.md`

**Key Points:**
- **PRESIDENT**: "You are the president. Follow the instructions." → Send command to boss1
- **boss1**: Receive PRESIDENT command → Send instructions to all workers → Report completion
- **workers**: Execute Hello World → Create completion files → Last worker reports

## 🎬 Expected Operation Flow

```
1. PRESIDENT → boss1: "You are boss1. Start Hello World project"
2. boss1 → workers: "You are worker[1-3]. Start Hello World task"  
3. workers → Create ./tmp/ files → Last worker → boss1: "All tasks completed"
4. boss1 → PRESIDENT: "All completed"
```

## 🔧 Manual Operations

### Using agent-send.sh

```bash
# Basic sending
./agent-send.sh [agent_name] [message]

# Examples
./agent-send.sh boss1 "Urgent task"
./agent-send.sh worker1 "Task completed"
./agent-send.sh president "Final report"

# Check agent list
./agent-send.sh --list
```

## 🧪 Verification & Debug

### Log Checking

```bash
# Check send logs
cat logs/send_log.txt

# Check specific agent logs
grep "boss1" logs/send_log.txt

# Check completion files
ls -la ./tmp/worker*_done.txt
```

### Session Status Check

```bash
# List sessions
tmux list-sessions

# List panes
tmux list-panes -t multiagent
tmux list-panes -t president
```

## 🔄 Environment Reset

```bash
# Delete sessions
tmux kill-session -t multiagent
tmux kill-session -t president

# Delete completion files
rm -f ./tmp/worker*_done.txt

# Rebuild (with auto cleanup)
./setup.sh
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

## 🤝 Contributing

Contributions via pull requests and issues are welcome!

---

🚀 **Experience Agent Communication!** 🤖✨ 