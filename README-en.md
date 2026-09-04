# 🏢 aiorg — AI Organization Framework

Declare an org chart in YAML; aiorg stands up one independent Claude Code session
(tmux) per member and routes instructions, reports and tasks between them through
a file-backed queue.

```bash
wsl                                    # on Windows, run inside WSL
cd /path/to/Claude-Code-Communication
./aiorg doctor                         # environment check
./aiorg templates                      # 10 org templates
./aiorg up --org solo                  # smallest one (2 members)
./aiorg launch && ./aiorg brief
./aiorg attach ceo                     # you talk only to the CEO
```

**Documentation is in Korean.** Start here:

- [docs/GETTING-STARTED.md](docs/GETTING-STARTED.md) — end-to-end walkthrough with `product-team`
- [docs/AIORG.md](docs/AIORG.md) — design and full reference
- [org/templates/README.md](org/templates/README.md) — the 10 templates
- `./aiorg help` — command reference

Members are all Claude sessions; a human talks only to the top member (CEO).
Everything the org needs — roles, reporting lines, code areas, working
directories — lives in one YAML file.

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