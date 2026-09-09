#!/usr/bin/env python3
"""aiorg 상태 저장소.

조직도(YAML) 해석, 메시지 큐, 태스크 레코드, 이벤트 로그를 담당한다.
tmux 조작은 일절 하지 않는다 — 그쪽은 lib/tmuxlib.sh 의 몫이다.

모든 서브커맨드는 bash CLI(`aiorg`)가 호출한다. 사람이 직접 부를 일은 없다.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import random
import string
import sys
import time
import unicodedata
from datetime import datetime
from pathlib import Path


def dwidth(s: str) -> int:
    """터미널 표시 폭. 한글·이모지는 두 칸을 차지한다."""
    return sum(2 if unicodedata.east_asian_width(c) in ("W", "F") else 1 for c in s)


def pad(s: str, n: int) -> str:
    """표시 폭 기준 왼쪽 정렬. str.ljust 는 글자 수로 세어 한글에서 어긋난다."""
    return s + " " * max(0, n - dwidth(s))

# ---------------------------------------------------------------- 경로/유틸


def home() -> Path:
    h = os.environ.get("AIORG_HOME")
    return Path(h) if h else Path(__file__).resolve().parent.parent


def runtime() -> Path:
    p = home() / "runtime"
    p.mkdir(parents=True, exist_ok=True)
    return p


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def short_id(n: int = 6) -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))


def atomic_write_json(path: Path, obj) -> None:
    """같은 디렉터리에 임시 파일로 쓰고 rename — 반쯤 쓰인 파일을 남기지 않는다."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def load_json(path: Path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default


def log_event(etype: str, **data) -> None:
    # data 의 키가 "at"/"type" 과 겹치면 이벤트 종류 자체가 덮여 쓰인다.
    # (실제로 메시지 종류를 type= 으로 넘겨 msg.sent 가 directive 로 기록된 적이 있다.)
    # 겹치는 키는 접두사를 붙여 살려 둔다.
    rec = {"at": now_iso(), "type": etype}
    for k, v in data.items():
        rec["data_" + k if k in ("at", "type") else k] = v
    with (runtime() / "events.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def die(msg: str, code: int = 1):
    print("aiorg: " + msg, file=sys.stderr)
    sys.exit(code)


# ---------------------------------------------------------------- 조직도 해석

DEFAULT_ICONS = {"ceo": "\U0001F451", "manager": "\U0001F3AF", "engineer": "\U0001F527", "reviewer": "\U0001F50D"}

# 이모지 글리프가 없는 글꼴에서는 전부 물음표로 찍혀 조직도를 읽을 수 없다.
# 로케일이 UTF-8 이어도 글꼴 문제라 자동 판별이 안 되므로 환경변수로 끈다.
#   AIORG_ASCII=1 ./aiorg status
ASCII_ICONS = {"ceo": "@", "manager": "+", "engineer": "-", "reviewer": "?", "po": "=", "presales": "!"}


def ascii_mode() -> bool:
    v = os.environ.get("AIORG_ASCII", "")
    if v not in ("", "0", "false", "no"):
        return True
    for k in ("LC_ALL", "LC_CTYPE", "LANG"):
        val = os.environ.get(k)
        if val:
            return "utf-8" not in val.lower().replace("utf8", "utf-8")
    return True


def icon_of(m) -> str:
    """멤버의 표시 기호. ASCII 모드에서는 역할별 한 글자로 바꾼다."""
    if not ascii_mode():
        return m.get("icon", "*")
    return ASCII_ICONS.get(m.get("role", ""), "*")



def resolved_path() -> Path:
    return runtime() / "org.resolved.json"


def load_org(required: bool = True):
    org = load_json(resolved_path())
    if org is None and required:
        die("조직도가 아직 해석되지 않았습니다. `./aiorg up` 을 먼저 실행하세요.")
    return org


def templates_dir() -> Path:
    return home() / "org" / "templates"


def resolve_org_path(arg: str) -> Path:
    """조직도 인자를 실제 파일 경로로 푼다.

    순서대로 시도한다:
      1. 준 그대로 (절대경로 또는 AIORG_HOME 기준 상대경로)
      2. org/<인자>.yaml            — 내가 만든 조직도
      3. org/templates/<인자>.yaml  — 템플릿 이름만 준 경우
    덕분에 `--org enterprise` 처럼 짧게 쓸 수 있다.
    """
    candidates = []
    p = Path(arg)
    candidates.append(p if p.is_absolute() else home() / p)
    if "/" not in arg and not arg.endswith(".yaml"):
        candidates.append(home() / "org" / (arg + ".yaml"))
        candidates.append(templates_dir() / (arg + ".yaml"))
    for c in candidates:
        if c.exists():
            return c

    names = sorted(f.stem for f in templates_dir().glob("*.yaml")) if templates_dir().exists() else []
    hint = ("\n  사용 가능한 템플릿: " + ", ".join(names)) if names else ""
    die("조직도를 찾을 수 없습니다: " + arg + hint + "\n  목록은 ./aiorg templates")


def _merge_skills(role_skills, member_skills) -> list:
    """역할 스킬 + 멤버 스킬. 순서를 지키고 중복은 뺀다."""
    out = []
    for s in list(role_skills or []) + list(member_skills or []):
        if s not in out:
            out.append(s)
    return out


def resolved_workdir(w: str) -> Path:
    """조직도의 workdir 을 절대경로로. 상대경로는 AIORG_HOME 기준."""
    p = Path(w)
    return p if p.is_absolute() else (home() / str(w).lstrip("./"))


def cmd_resolve(args):
    import yaml

    src = resolve_org_path(args.file)

    raw = yaml.safe_load(src.read_text(encoding="utf-8")) or {}

    # 스키마 버전. 지금은 1 뿐이지만, 나중에 형식이 바뀌었을 때 옛 파일이
    # 알 수 없는 이유로 실패하는 대신 분명한 메시지를 받게 하려고 검사한다.
    ver = raw.get("version", 1)
    if ver != 1:
        die(str(src) + ": 지원하지 않는 조직도 형식입니다 (version: " + str(ver) + "). 이 프레임워크는 version 1 을 씁니다.")

    roles = raw.get("roles") or {}
    org_meta = raw.get("org") or {}
    members_raw = raw.get("members") or []
    if not members_raw:
        die(str(src) + ": members 가 비어 있습니다.")

    # 코드 영역. 기존 제품에 조직을 붙일 때 "프론트는 어디, 백엔드는 어디" 를
    # 조직도가 선언한다. 값은 workdir 기준 상대경로다.
    #   areas:
    #     backend: backend/
    #     frontend: { path: web/, desc: "React 앱" }
    areas = {}
    for name, spec in (org_meta.get("areas") or {}).items():
        if isinstance(spec, str):
            areas[name] = {"path": spec, "desc": ""}
        elif isinstance(spec, dict):
            if not spec.get("path"):
                die(str(src) + ": 영역 '" + name + "' 에 path 가 없습니다.")
            areas[name] = {"path": spec["path"], "desc": spec.get("desc") or ""}
        else:
            die(str(src) + ": 영역 '" + name + "' 은 경로 문자열이거나 {path, desc} 여야 합니다.")

    # 산출물 자리. 개발 착수 전후로 만드는 문서가 어디에 놓이는지 선언한다.
    # 정의하지 않으면 그 개념 자체가 없다 (작은 조직은 문서 없이 돌아도 된다).
    #
    #   artifacts:
    #     design: docs/design/
    #     adr:    { path: docs/adr/, when: decision, desc: "기술 선택 기록" }
    #
    # when: decision  결정 시점에만 쓸 수 있다. 사후 작성은 재구성이라 근거가 되지 못한다.
    # when: anytime   나중에 써도 된다 (현황 설명, 사용 안내 등). 기본값.
    artifacts = {}
    for name, spec in (org_meta.get("artifacts") or {}).items():
        if isinstance(spec, str):
            artifacts[name] = {"path": spec, "desc": "", "when": "anytime"}
        elif isinstance(spec, dict):
            if not spec.get("path"):
                die(str(src) + ": 산출물 '" + name + "' 에 path 가 없습니다.")
            when = spec.get("when") or "anytime"
            if when not in ("decision", "anytime"):
                die(str(src) + ": 산출물 '" + name + "' 의 when 은 decision 또는 anytime 이어야 합니다.")
            artifacts[name] = {"path": spec["path"], "desc": spec.get("desc") or "", "when": when}
        else:
            die(str(src) + ": 산출물 '" + name + "' 은 경로 문자열이거나 {path, desc, when} 이어야 합니다.")

    members, by_id = [], {}
    for order, m in enumerate(members_raw):
        mid = m.get("id")
        if not mid:
            die(str(src) + ": id 가 없는 멤버가 있습니다 (#" + str(order) + ").")
        if mid in by_id:
            die(str(src) + ": 멤버 id 중복 — " + mid)
        role = m.get("role")
        if not role:
            die(str(src) + ": " + mid + " 에 role 이 없습니다.")
        if role not in roles:
            die(str(src) + ": " + mid + " 의 role '" + role + "' 이 roles 에 정의되지 않았습니다.")
        rc = roles[role] or {}
        rec = {
            "id": mid,
            "title": m.get("title") or mid,
            "role": role,
            "reports_to": m.get("reports_to"),
            "session": m.get("session") or "org",
            "skills": m.get("skills") or [],
            "areas": m.get("areas") or [],
            "workdir": m.get("workdir") or "",
            "worktree": bool(m.get("worktree", False)),
            # Claude Code 스킬. 조직도의 skills(담당/역량 태그)와는 완전히 다른 것이다.
            # 이쪽은 실제로 호출되는 스킬 이름이다.
            # 역할이 주는 것에 멤버 것을 **더한다**. 덮어쓰지 않는다.
            # 프론트 담당에게 frontend-design 만 얹고 싶을 때 역할이 주던
            # 스킬을 되풀어 적지 않아도 되게 하려는 것이다.
            "use_skills": _merge_skills(rc.get("use_skills"), m.get("use_skills")),
            "instruction": m.get("instruction") or rc.get("instruction"),
            "icon": m.get("icon") or rc.get("icon") or DEFAULT_ICONS.get(role, "*"),
            "color": m.get("color") or rc.get("color") or "white",
            "can_assign": bool(m.get("can_assign", rc.get("can_assign", False))),
            "order": order,
        }
        if not rec["instruction"]:
            die(str(src) + ": " + mid + " 의 지시서 경로가 없습니다 (role '" + role + "' 에 instruction 필요).")
        members.append(rec)
        by_id[mid] = rec

    # 보고선 검증: 존재하는 상급자, 자기 참조 금지, 순환 금지
    for m in members:
        sup = m["reports_to"]
        if sup is None:
            continue
        if sup == m["id"]:
            die(str(src) + ": " + m["id"] + " 가 자기 자신에게 보고하도록 되어 있습니다.")
        if sup not in by_id:
            die(str(src) + ": " + m["id"] + " 의 reports_to '" + str(sup) + "' 라는 멤버가 없습니다.")
    for m in members:
        seen, cur = [], m["id"]
        while cur is not None:
            if cur in seen:
                die(str(src) + ": 보고선에 순환이 있습니다 — " + " -> ".join(seen + [cur]))
            seen.append(cur)
            cur = by_id[cur]["reports_to"]

    roots = [m["id"] for m in members if m["reports_to"] is None]
    if not roots:
        die(str(src) + ": 최상위 멤버(reports_to 없음)가 없습니다.")

    for m in members:
        for a in m["areas"]:
            if a not in areas:
                known = ", ".join(areas) or "(org.areas 가 비어 있습니다)"
                die(str(src) + ": " + m["id"] + " 의 영역 '" + a + "' 이 org.areas 에 없습니다. 정의된 영역: " + known)

    # skills 는 역할에 따라 뜻이 다르다.
    #   engineer : 기술 역량. 둘 다 python 을 하는 건 정상이므로 겹쳐도 된다.
    #   po       : 담당 제품 영역. 겹치면 두 사람이 같은 기능을 다르게 기획하고,
    #              개발팀은 어느 쪽을 만들지 알 수 없다.
    # 그 차이를 조직도가 role 에 exclusive_skills: true 로 선언한다.
    # 막지는 않는다 — 의도적으로 겹치게 둘 수도 있다. 다만 조용히 넘기지 않는다.
    warnings = []

    # 조직을 갈아끼우면 이전 조직의 태스크와 수신함이 runtime/ 에 그대로 남는다.
    # 담당자가 새 조직도에 없으면 그 일은 아무에게도 보이지 않고 아무도 하지 않는다.
    # 조용히 유실되는 것이 가장 나쁘므로 여기서 잡아 알린다.
    known = set(by_id)
    orphan_tasks = [
        t for t in all_tasks()
        if t.get("status") not in ("done", "cancelled") and t.get("assignee") and t["assignee"] not in known
    ]
    if orphan_tasks:
        who = sorted({t["assignee"] for t in orphan_tasks})
        warnings.append(
            "이전 조직의 미완료 태스크 " + str(len(orphan_tasks)) + "건이 남아 있습니다. "
            "담당자가 새 조직에 없습니다: " + ", ".join(who) + "\n"
            "      확인: ./aiorg task list --open\n"
            "      인계: ./aiorg task set --id <태스크id> --assignee <새 담당자>\n"
            "      종료: ./aiorg task set --id <태스크id> --status cancelled --note \"조직 개편으로 종료\""
        )

    # 작업 디렉터리가 없으면 거부한다. 경고로 넘기면 tmux 가 조용히 홈 디렉터리에
    # pane 을 띄우고, 구성원 전원이 엉뚱한 곳에서 일하게 된다.
    # 제품 저장소 경로를 오타냈을 때 이걸 못 잡으면 원인을 찾기 매우 어렵다.
    raw_wd = str(org_meta.get("workdir") or ".")
    wd = Path(resolved_workdir(raw_wd))
    if not wd.is_dir():
        # 원본 문자열로 판단해야 한다. 해석 후 경로에는 AIORG_HOME 이 앞에 붙어
        # 드라이브 문자가 가운데로 밀려나므로 못 잡는다.
        hint = ""
        if (len(raw_wd) > 1 and raw_wd[1] == ":") or "\\" in raw_wd:
            hint = "\n  Windows 경로는 WSL 형식으로 씁니다 — C:\\dev\\myapp 이면 /mnt/c/dev/myapp"
        elif src.parent == templates_dir():
            # 템플릿의 자리표시자 경로를 그대로 띄우려 한 경우.
            hint = (
                "\n  이 템플릿은 자리표시자 경로를 담고 있습니다. 복사해서 고쳐 쓰세요:"
                "\n    ./aiorg new " + src.stem + " mycorp"
                "\n    # org/mycorp.yaml 의 org.workdir 을 실제 제품 경로로 바꾼다"
                "\n    ./aiorg up --org mycorp"
            )
        die(
            str(src) + ": 작업 디렉터리가 없습니다 — " + str(wd)
            + "\n  org.workdir(" + raw_wd + ") 을 확인하세요."
            + "\n  비우면 이 저장소(" + str(home()) + ")가 기본입니다." + hint
        )

    # 작업 디렉터리가 프레임워크 저장소 자체면 산출물이 여기에 쌓인다.
    # 실제로 겪은 일이다: 조직이 url-shortener/ (.venv 포함) 와 docs/adr/, docs/qa/ 를
    # 이 저장소 안에 만들어서 손으로 지워야 했다. git 에 올릴 것도 아닌데 섞인다.
    # 코드를 쓰는 역할이 있을 때만 경고한다 — 기획만 하는 조직은 문서뿐이라 덜 문제다.
    if wd.resolve() == home().resolve():
        writers = [m["id"] for m in members if m["role"] in ("engineer",)]
        if writers:
            warnings.append(
                "작업 디렉터리가 이 프레임워크 저장소입니다 (" + str(wd) + ").\n"
                "      구성원이 만드는 코드와 문서가 여기에 쌓입니다. 코드를 쓰는 역할: "
                + ", ".join(writers) + "\n"
                "      제품 저장소를 따로 두는 편이 낫습니다:\n"
                "        org:\n"
                "          workdir: \"/경로/내제품\"\n"
                "      그냥 한 번 돌려보는 것이라면 그대로 두어도 됩니다. 다만 끝나고\n"
                "      git status 로 남은 것을 확인하세요 — 이 저장소에 커밋할 것이 아닙니다."
            )

    # 멤버별 작업 위치. 지정하지 않으면 조직 workdir 을 쓴다.
    for m in members:
        if not m["workdir"]:
            m["workdir_resolved"] = str(wd)
            continue
        p = Path(m["workdir"])
        full = p if p.is_absolute() else (wd / m["workdir"])
        if not full.is_dir():
            die(str(src) + ": " + m["id"] + " 의 workdir 이 없습니다 — " + str(full))
        m["workdir_resolved"] = str(full)

    # 영역 경로가 실제로 있는지 본다. 기존 제품에 붙일 때 경로를 잘못 적으면
    # 구성원이 엉뚱한 곳을 뒤지거나 아예 못 찾는다.
    missing = [n + " -> " + a["path"] for n, a in areas.items() if not (wd / a["path"]).exists()]
    if missing:
        warnings.append(
            "작업 디렉터리(" + str(wd) + ") 아래에 없는 영역 경로가 있습니다:\n"
            + "".join("      " + m + "\n" for m in missing)
            + "      경로를 고치거나, 아직 만들지 않은 영역이라면 그대로 두어도 됩니다."
        )
    unowned = [n for n in areas if not any(n in m["areas"] for m in members)]
    if unowned:
        warnings.append(
            "담당자가 없는 영역: " + ", ".join(unowned) + "\n"
            "      그 코드를 건드릴 사람이 조직에 없습니다. 멤버의 areas 에 넣거나 영역에서 빼세요."
        )

    # Claude Code 스킬을 그 자리에서 볼 수 있는지 본다.
    #
    # 실측한 규칙 (claude -p 로 확인):
    #   ~/.claude/skills/            어디서든 보인다 (사용자 레벨)
    #   <프로젝트 루트>/.claude/skills/  시작 위치에서 위로 거슬러 올라가 찾는다.
    #                               하위 디렉터리에서 실행해도 보인다.
    #   git 워킹트리                 자기 .git 을 가진 별개 프로젝트라 부모 저장소의
    #                               스킬에 닿지 못한다.
    repo_skills = home() / ".claude" / "skills"
    if repo_skills.is_dir():
        names = sorted(d.name for d in repo_skills.iterdir() if (d / "SKILL.md").exists())

        # 사용자 레벨(~/.claude/skills/)에 걸리면 작업 위치와 무관하게 보인다.
        # `aiorg skills --link` 가 거는 심링크가 그것이다.
        user_skills = Path.home() / ".claude" / "skills"
        unlinked = [n for n in names if not (user_skills / n).exists()]

        def sees_skills(start: Path) -> bool:
            """시작 위치에서 프로젝트 루트까지 올라가며 .claude/skills 를 찾는다."""
            cur = start
            while True:
                if (cur / ".claude" / "skills").is_dir():
                    return True
                if (cur / ".git").exists():
                    return False  # 프로젝트 경계. 더 올라가지 않는다.
                if cur.parent == cur:
                    return False
                cur = cur.parent

        blind = []
        for m in members:
            # 워킹트리는 자기 .git 을 가진 별개 프로젝트라 부모 저장소의
            # 스킬에 닿지 못한다. 아직 만들어지지 않았어도 결과는 같다.
            if m["worktree"]:
                blind.append(m["id"])
                continue
            if not sees_skills(Path(m.get("workdir_resolved") or str(wd))):
                blind.append(m["id"])
        if unlinked and blind:
            warnings.append(
                "이 저장소의 스킬(" + ", ".join(unlinked) + ")을 못 보는 멤버가 있습니다: "
                + ", ".join(blind) + "\n"
                "      Claude Code 는 세션이 시작한 디렉터리에서 스킬을 찾습니다.\n"
                "      ./aiorg skills --link 를 한 번 실행하면 어디서든 보입니다.\n"
                "      제품 저장소에서만 쓰려면 그 저장소의 .claude/skills/ 에 두세요."
            )

    inbox_root = runtime() / "inbox"
    if inbox_root.exists():
        stranded = []
        for d in sorted(inbox_root.glob("*")):
            if d.name in known or not d.is_dir():
                continue
            n = sum(1 for f in d.glob("*.json") if (load_json(f) or {}).get("state") != "read")
            if n:
                stranded.append(d.name + "(" + str(n) + ")")
        if stranded:
            warnings.append(
                "새 조직에 없는 멤버의 미확인 메시지가 남아 있습니다: " + ", ".join(stranded) + "\n"
                "      읽을 사람이 없습니다. 내용이 필요하면 runtime/inbox/<id>/ 를 직접 보세요."
            )

    for rname, rconf in roles.items():
        if not (rconf or {}).get("exclusive_skills"):
            continue
        holders = {}
        for m in members:
            if m["role"] != rname:
                continue
            for s in m["skills"]:
                holders.setdefault(str(s).strip().lower(), []).append(m["id"])
        for skill, who in holders.items():
            if len(who) > 1:
                warnings.append(
                    "역할 '" + rname + "' 은 담당이 겹치면 안 되는데 '" + skill
                    + "' 을(를) " + ", ".join(who) + " 가 함께 들고 있습니다.\n"
                    "      담당 영역을 겹치지 않게 나누거나, 의도한 것이라면 그대로 두어도 됩니다."
                )

    children = {m["id"]: [] for m in members}
    for m in members:
        if m["reports_to"]:
            children[m["reports_to"]].append(m["id"])

    sessions = {}
    for m in members:
        sessions.setdefault(m["session"], []).append(m["id"])

    layout = org_meta.get("layout") or "windows"
    if layout not in ("windows", "panes"):
        die(str(src) + ": org.layout 은 windows 또는 panes 여야 합니다 (받은 값: " + str(layout) + ")")
    resolved = {
        "source": str(src),
        "resolved_at": now_iso(),
        "org": {
            "name": org_meta.get("name") or "AI Organization",
            "workdir": org_meta.get("workdir") or ".",
            "session_prefix": org_meta.get("session_prefix") or "aiorg",
            "layout": layout,
        },
        "roles": roles,
        "areas": areas,
        "artifacts": artifacts,
        "members": members,
        "children": children,
        "roots": roots,
        "sessions": sessions,
    }
    atomic_write_json(resolved_path(), resolved)
    log_event("org.resolved", source=str(src), members=len(members), sessions=list(sessions))

    if args.quiet:
        for w in warnings:
            print("경고: " + w, file=sys.stderr)
        return
    print("조직도 해석 완료: " + str(src))
    print("  조직명 : " + resolved["org"]["name"])
    print("  멤버   : " + str(len(members)) + "명   배치: " + layout)
    for s, ids in sessions.items():
        print("  세션 " + pad(s, 10) + ": " + ", ".join(ids))
    for w in warnings:
        print()
        print("경고: " + w)


def cmd_templates(args):
    """템플릿 목록. 각 파일에서 이름·설명·멤버 수를 읽어 보여준다."""
    import yaml

    d = templates_dir()
    files = sorted(d.glob("*.yaml")) if d.exists() else []
    if not files:
        die("org/templates/ 에 템플릿이 없습니다.")

    rows = []
    for f in files:
        try:
            raw = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as e:
            rows.append((f.stem, "!", "YAML 오류: " + str(e).splitlines()[0]))
            continue
        meta = raw.get("org") or {}
        members = raw.get("members") or []
        sess = len({m.get("session", "org") for m in members})
        rows.append((f.stem, str(len(members)) + "명/" + str(sess) + "세션", meta.get("description") or meta.get("name") or ""))

    if args.json:
        print(json.dumps([{"name": r[0], "size": r[1], "description": r[2]} for r in rows], ensure_ascii=False))
        return

    head = ("템플릿", "규모", "설명")
    widths = [max(dwidth(r[i]) for r in (*rows, head)) + 2 for i in range(2)]
    print("".join(pad(head[i], widths[i]) for i in range(2)) + head[2])
    for r in rows:
        print("".join(pad(r[i], widths[i]) for i in range(2)) + r[2])
    print()
    print("바로 띄우기 : ./aiorg up --org <템플릿>   (existing-product 는 경로를 고쳐야 뜬다)")
    print("내 것으로 복사: ./aiorg new <템플릿> [이름]   -> org/<이름>.yaml")


def cmd_new(args):
    """템플릿을 org/<이름>.yaml 로 복사한다.

    템플릿은 손대지 않고, 복사본을 고쳐 쓰게 하려는 것이다.
    프레임워크를 갱신해도 내가 만든 조직도가 덮이지 않는다.
    """
    src = templates_dir() / (args.template + ".yaml")
    if not src.exists():
        src = resolve_org_path(args.template)

    name = args.name or args.template
    if name.endswith(".yaml"):
        name = name[: -len(".yaml")]
    dst = home() / "org" / (name + ".yaml")

    if dst.resolve() == src.resolve():
        die("원본과 같은 위치입니다. 다른 이름을 주세요: ./aiorg new " + args.template + " <이름>")
    if dst.exists() and not args.force:
        die("이미 있습니다: org/" + name + ".yaml\n  덮어쓰려면 --force, 아니면 다른 이름을 주세요.")

    body = src.read_text(encoding="utf-8")
    note = (
        "# " + name + ".yaml — org/templates/" + src.stem + " 에서 복사 (" + now_iso()[:10] + ")\n"
        "# 여기서부터는 당신 조직이다. 마음대로 고친다.\n"
        "#\n"
        "#   ./aiorg up --org " + name + "\n"
        "\n"
    )
    dst.write_text(note + body, encoding="utf-8")
    log_event("org.new", template=src.stem, dest="org/" + name + ".yaml")
    print("만들었습니다: org/" + name + ".yaml  (템플릿: " + src.stem + ")")
    print("  띄우기: ./aiorg up --org " + name)


def cmd_areas(args):
    """코드 영역과 담당자. 기존 제품에 조직을 붙였을 때 어디를 누가 맡는지 본다."""
    org = load_org()
    areas = org.get("areas") or {}
    wd = org["org"].get("workdir") or "."
    if not areas:
        print("이 조직도에는 코드 영역이 정의되어 있지 않습니다.")
        print("조직도의 org.areas 에 선언하면 여기에 보입니다. 예:")
        print("  org:")
        print("    workdir: /path/to/product")
        print("    areas:")
        print("      backend: backend/")
        print("      frontend: web/")
        return

    rows = []
    for name, a in areas.items():
        owners = [m["id"] for m in org["members"] if name in m.get("areas", [])]
        rows.append((name, a["path"], ", ".join(owners) or "없음", a.get("desc") or ""))

    if args.json:
        print(json.dumps({"workdir": wd, "areas": rows}, ensure_ascii=False))
        return

    print("작업 디렉터리: " + wd)
    print()
    head = ("영역", "경로", "담당", "설명")
    widths = [max(dwidth(r[i]) for r in (*rows, head)) + 2 for i in range(3)]
    print("".join(pad(head[i], widths[i]) for i in range(3)) + head[3])
    for r in rows:
        print("".join(pad(r[i], widths[i]) for i in range(3)) + r[3])


def cmd_artifacts(args):
    """산출물 자리. 무엇을 어디에 남기는지, 언제 쓸 수 있는지."""
    org = load_org()
    arts = org.get("artifacts") or {}
    if not arts:
        print("이 조직도에는 산출물 자리가 정의되어 있지 않습니다.")
        print("정의하면 구성원이 문서를 어디에 남길지 헤매지 않습니다. 예:")
        print("  org:")
        print("    artifacts:")
        print("      design: docs/design/")
        print("      adr: { path: docs/adr/, when: decision }")
        return

    rows = []
    for name, a in arts.items():
        when = "결정 시점에만" if a["when"] == "decision" else "언제든"
        rows.append((name, a["path"], when, a.get("desc") or ""))

    if args.json:
        print(json.dumps(arts, ensure_ascii=False))
        return

    head = ("산출물", "경로", "작성 시점", "설명")
    widths = [max(dwidth(r[i]) for r in (*rows, head)) + 2 for i in range(3)]
    print("".join(pad(head[i], widths[i]) for i in range(3)) + head[3])
    for r in rows:
        print("".join(pad(r[i], widths[i]) for i in range(3)) + r[3])
    if any(a["when"] == "decision" for a in arts.values()):
        print()
        print("'결정 시점에만' 은 나중에 쓰면 근거가 되지 못한다는 뜻이다.")
        print("무엇을 왜 골랐는지는 고를 때 적어야 한다. 사후에 쓰면 재구성이다.")


def cmd_members(args):
    org = load_org()
    ms = org["members"]
    if args.skill:
        want = args.skill.lower()
        ms = [m for m in ms if any(want in str(s).lower() for s in m["skills"])]
        if not ms:
            print("'" + args.skill + "' 을(를) 담당하는 멤버가 없습니다.")
            return
    if args.json:
        print(json.dumps(ms, ensure_ascii=False))
        return
    if args.ids:
        for m in ms:
            print(m["id"])
        return
    # skills 를 반드시 보여준다. 상급자가 누구에게 배정할지 판단하고,
    # PO 가 서로의 담당 영역을 확인하는 근거가 이 열이다.
    #
    # 열 너비는 실제 값에서 뽑는다. 고정 폭으로 두면 긴 직함에서 열이 붙어버린다.
    has_areas = any(m.get("areas") for m in ms)
    rows = [(
        m["id"], m["session"], m["role"], m["title"],
        ", ".join(m.get("areas") or []) or "-",
        ", ".join(str(s) for s in m["skills"]) or "-",
    ) for m in ms]
    head = ("ID", "부서", "역할", "직함", "코드영역", "담당/역량")
    cols = 5 if has_areas else 4
    idx = list(range(cols)) if has_areas else [0, 1, 2, 3]
    last = 5
    widths = {i: max(dwidth(r[i]) for r in (*rows, head)) + 2 for i in idx}
    print("".join(pad(head[i], widths[i]) for i in idx) + head[last])
    for r in rows:
        print("".join(pad(r[i], widths[i]) for i in idx) + r[last])


def cmd_sessions(args):
    org = load_org()
    for s, ids in org["sessions"].items():
        print(s + "\t" + " ".join(ids))


# ---------------------------------------------------------------- 수신자 선택자


def cmd_unbriefed(args):
    """지금 자리에서 아직 brief 를 못 받은 멤버를 나열한다.

    판정: 그 (멤버, pane) 의 마지막 기록이 member.brief 여야 briefed 다.
    마지막이 member.launch 면 그 뒤에 brief 가 없었다는 뜻이다. 같은 pane 에서
    claude 를 다시 띄우면 대화 맥락이 사라지므로 그 전의 brief 는 무효다 —
    그래서 pane 만으로는 부족하고, 기동과 안내의 순서를 봐야 한다.

    brief 를 빼먹으면 구성원이 자기가 조직의 일원인 줄 모른다. 대표조차
    혼자 다 만들려 든다. 그런데 겉으로는 전원 '대기' 로 보여서 알아챌 수 없다.
    """
    org = load_org()
    panes = {}
    if args.panes:
        pf = Path(args.panes)
        if pf.is_file():
            for line in pf.read_text(encoding="utf-8").splitlines():
                cols = line.split("	")
                if len(cols) >= 3:
                    panes[cols[0]] = cols[2]
    # 이벤트 로그는 append-only 이므로 순서가 곧 시간 순서다. 타임스탬프로
    # 비교하면 초 단위라 launch 와 brief 가 같은 초에 들어올 때 구분되지 않는다.
    last = {}
    log = runtime() / "events.jsonl"
    if log.is_file():
        with log.open(encoding="utf-8") as f:
            for line in f:
                try:
                    e = json.loads(line)
                except Exception:
                    continue
                t = e.get("type")
                if t not in ("member.launch", "member.brief"):
                    continue
                key = (e.get("member"), e.get("pane"))
                if None in key:
                    continue
                last[key] = t
    out = []
    for m in org["members"]:
        mid = m["id"]
        pane = panes.get(mid)
        if not pane:
            continue          # 자리가 없으면 brief 대상도 아니다
        # 마지막 기록이 기동이면 그 뒤에 brief 가 없다는 뜻이다. 기록이 아예
        # 없으면 판단할 근거가 없다 — 없는 근거로 경고하면 오탐이 된다.
        if last.get((mid, pane)) == "member.launch":
            out.append(mid)
    for mid in out:
        print(mid)


def cmd_layout(args):
    """tmux 배치를 한 표로 보여준다.

    조직도(누가 어느 부서인가)와 tmux(어느 세션·창·pane 인가)를 눈으로
    맞춰 보던 것을 한 자리에 모은 것이다. 관찰용이며 아무것도 바꾸지 않는다.

    tmux 사실(창 번호, pane, 상태)은 bash 쪽에서 모아 --rows 로 넘긴다.
    파이썬에서 tmux 를 부르지 않으려는 것이고, 정렬은 여기서 해야 한다 —
    str.ljust 는 글자 수로 세어 한글·이모지에서 어긋난다.
    """
    org = load_org()
    titles = {m["id"]: m.get("title", "") for m in org["members"]}
    rows = []
    if args.rows:
        f = Path(args.rows)
        if f.is_file():
            for line in f.read_text(encoding="utf-8").splitlines():
                c = line.split("\t")
                if len(c) >= 6:
                    rows.append(c[:6])
    if not rows:
        print("자리가 없습니다. ./aiorg up 을 먼저 실행하세요.")
        return

    badges = {
        "idle": "대기", "busy": "작업중", "starting": "부팅중",
        "prompt": "응답대기", "login": "로그인필요", "down": "미가동",
    }
    head = ["세션", "창", "자리", "멤버", "직함", "상태"]
    table = [head]
    for mid, sess, widx, wname, pane, state in rows:
        table.append([sess, widx, pane, mid, titles.get(mid, wname), badges.get(state, state)])
    widths = [max(dwidth(r[i]) for r in table) for i in range(6)]
    for i, r in enumerate(table):
        print("  " + "  ".join(pad(r[j], widths[j]) for j in range(6)).rstrip())
        if i == 0:
            print("  " + "  ".join("-" * widths[j] for j in range(6)))

    print("")
    if args.notify:
        print("  알림 지킴이 : " + args.notify)
    if args.layout:
        print("  배치        : " + args.layout)
    print("")
    print("  붙기   : ./aiorg attach <멤버>        나오기: Ctrl-b d")
    print("  엿보기 : ./aiorg peek <멤버>          (붙지 않고 화면만 본다)")


def cmd_adddirs(args):
    """이 멤버가 자기 작업 디렉터리 밖에서 읽어야 하는 곳을 나열한다.

    Claude Code 는 시작한 디렉터리 밖을 읽으려 하면 사람에게 묻는다. 조직은
    사람 없이 돌아가야 하므로 launch 가 --add-dir 로 미리 열어 준다.

    소스가 workdir 밖에 있는 배치에서 필요하다 — 예를 들어 산출물만 모으는
    디렉터리를 workdir 로 두고 areas 를 절대경로로 가리키는 경우, 팀장과
    리뷰어는 코드를 한 줄도 못 읽는다. 겉으로는 대화상자가 떠서 멈춘 것으로만
    보인다.
    """
    org = load_org()
    wd = Path(org["org"]["workdir"])
    me = None
    for m in org["members"]:
        if m["id"] == args.member:
            me = m
            break
    if me is None:
        return
    mine = Path(me.get("workdir_resolved") or str(wd))
    out = []
    for a in (org.get("areas") or {}).values():
        ap = Path(a["path"])
        full = ap if ap.is_absolute() else (wd / a["path"])
        try:
            full = full.resolve()
        except Exception:
            continue
        if not full.is_dir():
            continue
        try:
            full.relative_to(mine.resolve())
            continue          # 이미 자기 작업 디렉터리 안이다
        except ValueError:
            pass
        if str(full) not in out:
            out.append(str(full))
    for d in out:
        print(d)


MEMBER_COMMANDS = [
    "whoami", "help", "inbox", "send", "reply", "assign", "report",
    "task", "status", "members", "areas", "artifacts", "log",
]


OPERATOR_COMMANDS = [
    "up", "launch", "brief", "down", "clean", "scaffold",
    "skills", "attach", "layout", "peek",
]


def member_allow_rules():
    """구성원이 승인 없이 쓸 수 있어야 하는 규칙."""
    out = []
    for form in ("aiorg", "./aiorg"):
        for c in MEMBER_COMMANDS:
            out.append("Bash(" + form + " " + c + ":*)")
    return out


def operator_deny_rules():
    """구성원이 쓰면 안 되는 규칙.

    aiorg 자신도 이것을 거부하지만(AIORG_ME 로 판정), 두 겹으로 둔다.
    설정이 존중되는 상황에서는 도구 단계에서 먼저 막히는 편이 낫다.
    """
    out = []
    for form in ("aiorg", "./aiorg"):
        for c in OPERATOR_COMMANDS:
            out.append("Bash(" + form + " " + c + ":*)")
    return out


def cmd_permissions(args):
    """제품 저장소에 구성원용 권한 설정을 만들거나 점검한다.

    왜 제품 저장소인가: Claude Code 설정은 프로젝트 루트와 사용자 레벨에서만
    읽힌다. 구성원의 프로젝트 루트는 제품 저장소이므로, 이 프레임워크 저장소의
    .claude/settings.local.json 은 구성원에게 걸리지 않는다 — --add-dir 로
    열어 줘도 그렇다. 실측으로 확인했다.

    없으면 구성원이 aiorg 명령마다 승인을 요구받는다. 사람이 지켜보고 있지
    않으면 조직이 거기서 멈춘다.
    """
    dst = Path(args.workdir) / ".claude" / "settings.local.json"
    want = member_allow_rules()
    cur = {}
    if dst.is_file():
        try:
            cur = json.loads(dst.read_text(encoding="utf-8"))
        except Exception:
            print("aiorg: " + str(dst) + " 를 읽지 못했습니다. 손대지 않습니다.", file=sys.stderr)
            return
    perms = cur.setdefault("permissions", {})
    allow = perms.setdefault("allow", [])
    deny = perms.setdefault("deny", [])
    nodeny = [r for r in operator_deny_rules() if r not in deny]
    missing = [r for r in want if r not in allow]
    if args.check:
        print(len(missing) + len(nodeny))
        return
    if not missing and not nodeny:
        print("  있음   .claude/settings.local.json  (허용 " + str(len(want))
              + " / 거부 " + str(len(operator_deny_rules())) + ")")
        return
    allow.extend(missing)
    deny.extend(nodeny)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(cur, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("  만듦   .claude/settings.local.json  (허용 " + str(len(missing))
          + "건 / 거부 " + str(len(nodeny)) + "건 추가)")


def cmd_untrusted(args):
    """아직 신뢰 확인을 받지 않은 작업 디렉터리를 나열한다.

    Claude Code 는 처음 보는 폴더에서 뜰 때 사람에게 신뢰를 묻는다. 조직은
    사람 없이 돌아야 하는데 이것만은 예외라, 여덟 자리가 한꺼번에 대화상자
    앞에 멈춘다. brief 는 '대기' 인 멤버에게만 가므로 그 상태에서는
    "0 명에게 전달" 이 된다.

    미리 알면 한 번만 답하고 끝낼 수 있다. 기록은 ~/.claude.json 의
    projects.<경로>.hasTrustDialogAccepted 에 남는다.
    """
    org = load_org()
    wd = org["org"]["workdir"]
    want = {wd}
    for m in org["members"]:
        w = m.get("workdir_resolved")
        if w:
            want.add(w)
    cfg = Path.home() / ".claude.json"
    trusted = set()
    if cfg.is_file():
        try:
            proj = json.loads(cfg.read_text(encoding="utf-8")).get("projects", {})
            trusted = {k for k, v in proj.items()
                       if isinstance(v, dict) and v.get("hasTrustDialogAccepted")}
        except Exception:
            return          # 읽지 못하면 아무 말도 하지 않는다. 없는 근거로 경고하지 않는다
    for w in sorted(want):
        if w not in trusted:
            print(w)


def load_org_file(name: str):
    """조직도 파일 하나를 부작용 없이 읽는다.

    resolve 는 runtime/ 에 결과를 쓰고 검증까지 하지만, 그림만 그릴 때는
    그럴 이유가 없다. 템플릿을 띄우지 않고 훑어보려는 것이므로 workdir 이
    없어도 동작해야 한다.
    """
    import yaml

    src = templates_dir() / (name + ".yaml")
    if not src.exists():
        src = resolve_org_path(name)
    raw = yaml.safe_load(src.read_text(encoding="utf-8")) or {}
    roles = raw.get("roles") or {}
    members = []
    for m in raw.get("members") or []:
        role = m.get("role", "")
        rc = roles.get(role) or {}
        members.append({
            "id": m.get("id", ""),
            "title": m.get("title", ""),
            "role": role,
            "reports_to": m.get("reports_to") or "",
            "session": m.get("session") or "org",
            "icon": m.get("icon") or rc.get("icon") or DEFAULT_ICONS.get(role, "*"),
        })
    return src, raw.get("org") or {}, members


def cmd_chart(args):
    """조직도를 그림으로. ASCII 가 기본이고 --mermaid 는 문서에 붙일 용도다.

    손으로 그린 그림은 조직도를 고칠 때마다 어긋난다. 그려 두지 않고 그린다.
    """
    src, meta, members = load_org_file(args.name)
    by_id = {m["id"]: m for m in members}
    kids = {}
    roots = []
    for m in members:
        parent = m["reports_to"]
        if parent and parent in by_id:
            kids.setdefault(parent, []).append(m["id"])
        else:
            roots.append(m["id"])

    if args.mermaid:
        # 세션명과 멤버 id 가 같으면 subgraph 와 노드가 충돌해 그림이 깨진다.
        # 지금 템플릿에는 없지만 조직도는 사람이 쓰는 것이므로 접두사로 막는다.
        def nid(x):
            return "m_" + re.sub(r"[^0-9A-Za-z_]", "_", x)

        def sid(x):
            return "s_" + re.sub(r"[^0-9A-Za-z_]", "_", x)

        print("```mermaid")
        print("graph TD")
        # 부서(세션)별로 묶어 보여주면 tmux 배치와 대응이 눈에 들어온다
        depts = {}
        for m in members:
            depts.setdefault(m["session"], []).append(m)
        for dept, ms in depts.items():
            print('  subgraph ' + sid(dept) + '["' + dept + '"]')
            for m in ms:
                label = m["id"] + "<br/>" + m["title"]
                print('    ' + nid(m["id"]) + '["' + label + '"]')
            print("  end")
        for m in members:
            if m["reports_to"] and m["reports_to"] in by_id:
                print("  " + nid(m["reports_to"]) + " --> " + nid(m["id"]))
        print("```")
        return

    name = meta.get("name") or args.name
    print(name + "  (" + str(len(members)) + "명 / "
          + str(len({m["session"] for m in members})) + "세션)")
    print()
    width = max((dwidth(m["id"]) for m in members), default=8)

    def walk(mid, prefix, conn):
        m = by_id[mid]
        print(prefix + conn + icon_of(m) + " " + pad(m["id"], width)
              + "  " + m["title"] + "  [" + m["session"] + "]")
        ch = kids.get(mid, [])
        for i, c in enumerate(ch):
            last = i == len(ch) - 1
            walk(c, prefix + ("   " if conn in ("`- ", "") else "|  "),
                 "`- " if last else "|- ")

    for r in roots:
        walk(r, "", "")
    print()
    print("파일: " + str(src))


def cmd_expand(args):
    """선택자를 실제 멤버 id 목록으로 펼친다.

    dev-1          단일 멤버
    @all           전원
    @role:manager  해당 역할 전원
    @dept:dev      해당 세션(부서) 전원
    @reports       --me 의 직속 부하 전원
    @boss          --me 의 직속 상급자
    """
    org = load_org()
    by_id = {m["id"]: m for m in org["members"]}
    sel, me = args.selector, args.me
    out = []

    if sel == "@all":
        out = [m["id"] for m in org["members"]]
    elif sel == "@reports":
        if not me:
            die("@reports 는 발신자를 알 수 없으면 사용할 수 없습니다.")
        out = list(org["children"].get(me, []))
    elif sel == "@boss":
        if not me:
            die("@boss 는 발신자를 알 수 없으면 사용할 수 없습니다.")
        sup = by_id.get(me, {}).get("reports_to")
        out = [sup] if sup else []
    elif sel.startswith("@role:"):
        want = sel.split(":", 1)[1]
        out = [m["id"] for m in org["members"] if m["role"] == want]
    elif sel.startswith("@dept:"):
        want = sel.split(":", 1)[1]
        out = list(org["sessions"].get(want, []))
    elif sel.startswith("@"):
        die("알 수 없는 선택자입니다: " + sel)
    else:
        if sel not in by_id:
            die("'" + sel + "' 라는 멤버가 없습니다. 사용 가능: " + ", ".join(by_id))
        out = [sel]

    if args.exclude_me and me:
        out = [i for i in out if i != me]
    if not out:
        die("선택자 '" + sel + "' 가 아무 멤버도 가리키지 않습니다.")
    print("\n".join(out))


# ---------------------------------------------------------------- 메시지 큐

MSG_TYPES = ("directive", "report", "question", "answer", "review", "info")


def inbox_dir(mid: str) -> Path:
    p = runtime() / "inbox" / mid
    p.mkdir(parents=True, exist_ok=True)
    return p


def inbox_files(mid: str):
    return sorted(inbox_dir(mid).glob("*.json"))


def cmd_msg_new(args):
    org = load_org()
    by_id = {m["id"]: m for m in org["members"]}
    if args.to not in by_id:
        die("수신자 '" + args.to + "' 가 조직도에 없습니다.")
    if args.sender not in by_id:
        die("발신자 '" + args.sender + "' 가 조직도에 없습니다.")
    if args.type not in MSG_TYPES:
        die("메시지 종류는 " + ", ".join(MSG_TYPES) + " 중 하나여야 합니다.")
    # --task 는 태스크를 가리켜야 한다. 실제로 구성원이 답신하면서 메시지 id 를
    # 여기 넣은 적이 있다. 그대로 두면 task_id 필드에 메시지 id 가 박혀
    # 나중에 태스크를 되짚을 수 없게 된다.
    if args.task and not task_path(args.task).exists():
        hint = " (메시지 id 를 넣으신 것 같습니다. 답신은 --reply-to 를 씁니다.)" if args.task.startswith("msg_") else ""
        die("태스크 '" + args.task + "' 가 없습니다." + hint)

    body = Path(args.body_file).read_text(encoding="utf-8") if args.body_file else (args.body or "")
    body = body.rstrip("\n")
    if not body.strip():
        die("본문이 비어 있습니다.")

    mid = "msg_" + short_id(8)
    msg = {
        "id": mid,
        "from": args.sender,
        "to": args.to,
        "type": args.type,
        "subject": args.subject or body.strip().splitlines()[0][:60],
        "body": body,
        "task_id": args.task,
        "reply_to": args.reply_to,
        "created_at": now_iso(),
        "state": "queued",  # queued -> notified -> read
        "notified_at": None,
        "read_at": None,
    }
    # 파일명 앞의 밀리초 타임스탬프가 수신함의 정렬 순서를 만든다.
    fname = str(int(time.time() * 1000)).zfill(15) + "-" + mid + ".json"
    atomic_write_json(inbox_dir(args.to) / fname, msg)
    log_event("msg.sent", msg=mid, sender=args.sender, to=args.to, kind=args.type, subject=msg["subject"])
    print(mid)


def find_msg(mid: str):
    for d in (runtime() / "inbox").glob("*"):
        for f in d.glob("*.json"):
            m = load_json(f)
            if m and m.get("id") == mid:
                return f, m
    return None, None


def cmd_msg_mark(args):
    path, msg = find_msg(args.id)
    if not msg:
        die("메시지 '" + args.id + "' 를 찾을 수 없습니다.")
    msg["state"] = args.state
    stamp = args.state + "_at"
    if stamp in msg:
        msg[stamp] = now_iso()
    atomic_write_json(path, msg)
    log_event("msg." + args.state, msg=args.id, to=msg["to"])


def cmd_pending(args):
    """벨을 아직 못 울린(queued) 메시지가 있는 수신자 — 알림 재시도용."""
    org = load_org()
    for m in org["members"]:
        n = sum(1 for f in inbox_files(m["id"]) if (load_json(f) or {}).get("state") == "queued")
        if n:
            print(m["id"] + "\t" + str(n))


def cmd_unread_count(args):
    n = sum(1 for f in inbox_files(args.me) if (load_json(f) or {}).get("state") != "read")
    print(n)


def render_msg(i: int, m: dict) -> str:
    bar = "-" * 62
    head = [
        "[" + str(i) + "] " + m["id"] + "  (" + m["type"] + ")",
        "    보낸이 : " + m["from"] + "      받는이 : " + m["to"] + "      시각 : " + m["created_at"],
        "    제목   : " + m["subject"],
    ]
    if m.get("task_id"):
        head.append("    태스크 : " + m["task_id"])
    if m.get("reply_to"):
        head.append("    답신대상 : " + m["reply_to"])
    body = "\n".join("    " + line for line in m["body"].splitlines())
    return "\n".join(head) + "\n    " + bar + "\n" + body + "\n    " + bar + "\n"


def cmd_inbox(args):
    org = load_org()
    by_id = {m["id"]: m for m in org["members"]}
    if args.me not in by_id:
        die("'" + args.me + "' 가 조직도에 없습니다. AIORG_ME 환경변수를 확인하세요.")

    picked = []
    for f in inbox_files(args.me):
        m = load_json(f)
        if not m:
            continue
        if not args.all and m.get("state") == "read":
            continue
        picked.append((f, m))

    if args.json:
        print(json.dumps([m for _, m in picked], ensure_ascii=False, indent=2))
    elif not picked:
        print("수신함이 비어 있습니다. (수신자: " + args.me + ")")
    else:
        me = by_id[args.me]
        label = "전체" if args.all else "미확인"
        print("=== " + label + " 메시지 " + str(len(picked)) + "건 — " + icon_of(me) + " " + args.me + " (" + me["title"] + ") ===")
        print()
        for i, (_, m) in enumerate(picked, 1):
            print(render_msg(i, m))

    if picked and not args.peek:
        for f, m in picked:
            if m.get("state") != "read":
                m["state"], m["read_at"] = "read", now_iso()
                atomic_write_json(f, m)
                log_event("msg.read", msg=m["id"], to=args.me)


# ---------------------------------------------------------------- 태스크

TASK_STATES = ("open", "in_progress", "blocked", "review", "done", "cancelled")

# 표식에 공백을 넣지 않는다. 에이전트가 `task list` 출력을 awk/cut 으로
# 잘라 쓰기 때문에, 표식 안의 공백이 열 번호를 밀어버린다.
STATUS_MARK = {
    "open": "[o]",
    "in_progress": "[>]",
    "blocked": "[!]",
    "review": "[?]",
    "done": "[x]",
    "cancelled": "[-]",
}


def tasks_dir() -> Path:
    p = runtime() / "tasks"
    p.mkdir(parents=True, exist_ok=True)
    return p


def task_path(tid: str) -> Path:
    return tasks_dir() / (tid + ".json")


def load_task(tid: str) -> dict:
    t = load_json(task_path(tid))
    if not t:
        die("태스크 '" + tid + "' 를 찾을 수 없습니다.")
    return t


def all_tasks():
    ts = [load_json(f) for f in sorted(tasks_dir().glob("*.json"))]
    return [t for t in ts if t]


def cmd_task_new(args):
    org = load_org()
    by_id = {m["id"]: m for m in org["members"]}
    for who, label in ((args.assigner, "지시자"), (args.assignee, "담당자")):
        if who and who not in by_id:
            die(label + " '" + who + "' 가 조직도에 없습니다.")
    if args.parent:
        load_task(args.parent)

    tid = "t_" + short_id(8)
    task = {
        "id": tid,
        "title": args.title,
        "detail": args.detail or "",
        "assigner": args.assigner,
        "assignee": args.assignee,
        "status": "open",
        "parent": args.parent,
        "branch": args.branch,
        "artifacts": [],
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "history": [{"at": now_iso(), "by": args.assigner, "to_status": "open", "note": "생성"}],
    }
    atomic_write_json(task_path(tid), task)
    log_event("task.new", task=tid, title=args.title, assigner=args.assigner, assignee=args.assignee)
    print(tid)


def cmd_task_set(args):
    task = load_task(args.id)
    changed = []
    if args.status:
        if args.status not in TASK_STATES:
            die("태스크 상태는 " + ", ".join(TASK_STATES) + " 중 하나여야 합니다.")
        prev = task["status"]
        task["status"] = args.status
        changed.append("status " + prev + " -> " + args.status)
        task["history"].append(
            {"at": now_iso(), "by": args.by, "from_status": prev, "to_status": args.status, "note": args.note or ""}
        )
    if args.assignee:
        task["assignee"] = args.assignee
        changed.append("assignee -> " + args.assignee)
    if args.branch:
        task["branch"] = args.branch
        changed.append("branch -> " + args.branch)
    if args.artifact:
        task["artifacts"].extend(args.artifact)
        changed.append("artifacts += " + str(len(args.artifact)))
    if args.note and not args.status:
        task["history"].append({"at": now_iso(), "by": args.by, "note": args.note})
        changed.append("note")
    if not changed:
        die("변경할 내용이 없습니다. --status / --assignee / --branch / --artifact / --note 중 하나를 주세요.")

    task["updated_at"] = now_iso()
    atomic_write_json(task_path(task["id"]), task)
    log_event("task.update", task=task["id"], by=args.by, changes=changed)
    print(task["id"] + ": " + ", ".join(changed))


def cmd_task_list(args):
    ts = all_tasks()
    if args.assignee:
        ts = [t for t in ts if t.get("assignee") == args.assignee]
    if args.status:
        ts = [t for t in ts if t.get("status") in args.status]
    if args.open_only:
        ts = [t for t in ts if t.get("status") not in ("done", "cancelled")]
    if args.json:
        print(json.dumps(ts, ensure_ascii=False, indent=2))
        return
    if args.ids:
        # 셸에서 그대로 받아쓰기 위한 출력. 헤더도 장식도 없다.
        for t in ts:
            print(t["id"])
        return
    if not ts:
        print("해당하는 태스크가 없습니다.")
        return
    print(pad("상태", 5) + pad("ID", 13) + pad("담당", 14) + "제목")
    for t in ts:
        mark = STATUS_MARK.get(t["status"], "[?]")
        print(pad(mark, 5) + pad(t["id"], 13) + pad(t.get("assignee") or "-", 14) + t["title"])


def cmd_progress(args):
    """진행 중인 일과 각자의 최신 기록. "지금 뭐 하고 있나" 를 한 화면에."""
    ts = [t for t in all_tasks() if t.get("status") in ("in_progress", "review", "blocked")]
    if args.assignee:
        ts = [t for t in ts if t.get("assignee") == args.assignee]
    if not ts:
        print("진행 중인 태스크가 없습니다.")
        return

    ts.sort(key=lambda t: t.get("updated_at") or "")
    for t in ts:
        mark = STATUS_MARK.get(t["status"], "[?]")
        print(mark + " " + t["id"] + "  " + t["title"] + "  (" + (t.get("assignee") or "미배정") + ")")
        # 진짜 진행 기록만 센다. 태스크를 만들 때 자동으로 붙는 "생성" 이나
        # 상태 전이에 딸린 메모는 "지금 뭐 하고 있나" 에 답해주지 않는다.
        notes = [
            h for h in t.get("history", [])
            if h.get("note") and h.get("note") != "생성" and not h.get("to_status")
        ]
        if not notes:
            print("    기록 없음 — 착수 후 진행 기록이 없습니다 (마지막 갱신 " + (t.get("updated_at") or "?")[:16] + ")")
        else:
            for h in notes[-args.lines:]:
                who = h.get("by") or "?"
                print("    " + h["at"][5:16].replace("T", " ") + "  " + who + ": " + h["note"])
        print()

    stale = [t for t in ts if not [h for h in t.get("history", []) if h.get("note")]]
    if stale:
        print("기록이 없는 태스크: " + ", ".join(t["id"] for t in stale))
        print("담당자에게 진행 상황을 물어보세요.")


def cmd_task_show(args):
    t = load_task(args.id)
    if args.json:
        print(json.dumps(t, ensure_ascii=False, indent=2))
        return
    print("태스크 " + t["id"] + "  [" + t["status"] + "]")
    print("  제목   : " + t["title"])
    print("  지시자 : " + (t.get("assigner") or "-") + "      담당자 : " + (t.get("assignee") or "-"))
    if t.get("parent"):
        print("  상위   : " + t["parent"])
    if t.get("branch"):
        print("  브랜치 : " + t["branch"])
    if t.get("detail"):
        print("  상세   :")
        for line in t["detail"].splitlines():
            print("    " + line)
    if t.get("artifacts"):
        print("  산출물 :")
        for a in t["artifacts"]:
            print("    - " + a)
    print("  이력   :")
    for h in t["history"]:
        note = (" — " + h["note"]) if h.get("note") else ""
        print("    " + h["at"] + "  " + pad(h.get("by") or "?", 11) + pad(h.get("to_status") or "", 13) + note)


def cmd_task_tree(args):
    ts = {t["id"]: t for t in all_tasks()}
    kids = {}
    for t in ts.values():
        kids.setdefault(t.get("parent"), []).append(t["id"])

    def walk(tid, prefix, conn, child_prefix):
        t = ts[tid]
        mark = STATUS_MARK.get(t["status"], "[?]")
        print(prefix + conn + mark + " " + t["id"] + "  " + t["title"] + "  (" + (t.get("assignee") or "미배정") + ")")
        ch = kids.get(tid, [])
        for i, c in enumerate(ch):
            last = i == len(ch) - 1
            walk(c, child_prefix, "`- " if last else "|- ", child_prefix + ("   " if last else "|  "))

    roots = kids.get(None, [])
    if not roots:
        print("태스크가 없습니다.")
        return
    for r in roots:
        walk(r, "", "", "")


# ---------------------------------------------------------------- 현황판


def cmd_status(args):
    org = load_org()
    live = load_json(Path(args.live), {}) if args.live else {}
    tasks = all_tasks()

    if args.json:
        print(json.dumps({"org": org, "live": live, "tasks": tasks}, ensure_ascii=False, indent=2))
        return

    by_id = {m["id"]: m for m in org["members"]}
    unread = {}
    for m in org["members"]:
        unread[m["id"]] = sum(1 for f in inbox_files(m["id"]) if (load_json(f) or {}).get("state") != "read")
    active = {}
    for t in tasks:
        if t.get("status") in ("in_progress", "review", "blocked") and t.get("assignee"):
            active[t["assignee"]] = active.get(t["assignee"], 0) + 1

    print("=== " + org["org"]["name"] + " ===")
    print(" 조직도 : " + org["source"])
    print(" 멤버   : " + str(len(org["members"])) + "명    태스크 : 전체 " + str(len(tasks)) + "건 / 진행중 " + str(sum(active.values())) + "건")
    print("-" * 62)

    badges = {
        "idle": "대기",
        "busy": "작업중",
        "starting": "부팅중",
        "prompt": "응답대기",
        "login": "로그인필요",
        "down": "미가동",
    }

    def line(mid, prefix, conn):
        m = by_id[mid]
        state = live.get(mid, {}).get("state", "down")
        flags = []
        if unread[mid]:
            flags.append("미확인 " + str(unread[mid]))
        if active.get(mid):
            flags.append("진행 " + str(active[mid]))
        tail = ("   " + " / ".join(flags)) if flags else ""
        print(prefix + conn + icon_of(m) + " " + pad(mid, 12) + " " + pad(m["title"], 16) + " [" + badges.get(state, state) + "]" + tail)

    def walk(mid, prefix, conn, child_prefix):
        line(mid, prefix, conn)
        ch = org["children"].get(mid, [])
        for i, c in enumerate(ch):
            last = i == len(ch) - 1
            walk(c, child_prefix, "`- " if last else "|- ", child_prefix + ("   " if last else "|  "))

    for r in org["roots"]:
        walk(r, "", "", "")

    if live:
        groups = {}
        for m in org["members"]:
            groups.setdefault(live.get(m["id"], {}).get("state", "down"), []).append(m["id"])
        notes = []
        if groups.get("down"):
            notes.append("미가동: " + ", ".join(groups["down"]) + "  — `./aiorg launch` 로 claude 를 띄우세요.")
        if groups.get("prompt"):
            notes.append(
                "응답대기: " + ", ".join(groups["prompt"])
                + "  — 대화상자가 떠 있습니다. `./aiorg attach <멤버>` 로 붙어서 직접 답해야 합니다."
            )
        if groups.get("login"):
            notes.append(
                "로그인필요: " + ", ".join(groups["login"])
                + "  — claude 인증이 끊겼습니다. `./aiorg attach <멤버>` 로 붙어 /login 을 실행하세요."
            )
        if groups.get("starting"):
            notes.append("부팅중: " + ", ".join(groups["starting"]) + "  — 잠시 뒤 다시 확인하세요.")
        if notes:
            print()
            for n in notes:
                print(n)


def cmd_log(args):
    p = runtime() / "events.jsonl"
    if not p.exists():
        print("이벤트 로그가 없습니다.")
        return
    lines = p.read_text(encoding="utf-8").splitlines()
    for line in lines[-args.limit:]:
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if args.type and rec.get("type") not in args.type:
            continue
        if args.grep and args.grep not in line:
            continue
        rest = {k: v for k, v in rec.items() if k not in ("at", "type")}
        detail = "  ".join(str(k) + "=" + str(v) for k, v in rest.items())
        print(rec["at"] + "  " + pad(rec["type"], 15) + detail)


def cmd_event(args):
    data = {}
    for kv in args.kv:
        k, _, v = kv.partition("=")
        data[k] = v
    log_event(args.type, **data)


# ---------------------------------------------------------------- 진입점


def build_parser():
    p = argparse.ArgumentParser(prog="orgstate.py", description="aiorg 상태 저장소")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("resolve")
    s.add_argument("file")
    s.add_argument("--quiet", action="store_true")
    s.set_defaults(fn=cmd_resolve)

    s = sub.add_parser("members")
    s.add_argument("--json", action="store_true")
    s.add_argument("--ids", action="store_true")
    s.add_argument("--skill", help="해당 담당/역량을 가진 멤버만 (부분 일치)")
    s.set_defaults(fn=cmd_members)

    s = sub.add_parser("sessions")
    s.set_defaults(fn=cmd_sessions)

    s = sub.add_parser("areas")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_areas)

    s = sub.add_parser("artifacts")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_artifacts)

    s = sub.add_parser("templates")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_templates)

    s = sub.add_parser("new")
    s.add_argument("template")
    s.add_argument("name", nargs="?")
    s.add_argument("--force", action="store_true")
    s.set_defaults(fn=cmd_new)

    s = sub.add_parser("expand")
    s.add_argument("selector")
    s.add_argument("--me")
    s.add_argument("--exclude-me", action="store_true")
    s.set_defaults(fn=cmd_expand)

    s = sub.add_parser("msg-new")
    s.add_argument("--from", dest="sender", required=True)
    s.add_argument("--to", required=True)
    s.add_argument("--type", default="info")
    s.add_argument("--subject")
    s.add_argument("--body")
    s.add_argument("--body-file")
    s.add_argument("--task")
    s.add_argument("--reply-to")
    s.set_defaults(fn=cmd_msg_new)

    s = sub.add_parser("msg-mark")
    s.add_argument("--id", required=True)
    s.add_argument("--state", required=True)
    s.set_defaults(fn=cmd_msg_mark)

    s = sub.add_parser("pending")
    s.set_defaults(fn=cmd_pending)

    s = sub.add_parser("unread-count")
    s.add_argument("--me", required=True)
    s.set_defaults(fn=cmd_unread_count)

    s = sub.add_parser("inbox")
    s.add_argument("--me", required=True)
    s.add_argument("--all", action="store_true")
    s.add_argument("--peek", action="store_true")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_inbox)

    s = sub.add_parser("task-new")
    s.add_argument("--title", required=True)
    s.add_argument("--detail")
    s.add_argument("--assigner")
    s.add_argument("--assignee")
    s.add_argument("--parent")
    s.add_argument("--branch")
    s.set_defaults(fn=cmd_task_new)

    s = sub.add_parser("task-set")
    s.add_argument("--id", required=True)
    s.add_argument("--status")
    s.add_argument("--assignee")
    s.add_argument("--branch")
    s.add_argument("--artifact", action="append")
    s.add_argument("--note")
    s.add_argument("--by")
    s.set_defaults(fn=cmd_task_set)

    s = sub.add_parser("task-list")
    s.add_argument("--assignee")
    s.add_argument("--status", action="append")
    s.add_argument("--open-only", action="store_true")
    s.add_argument("--json", action="store_true")
    s.add_argument("--ids", action="store_true")
    s.set_defaults(fn=cmd_task_list)

    s = sub.add_parser("task-show")
    s.add_argument("--id", required=True)
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_task_show)

    s = sub.add_parser("task-tree")
    s.set_defaults(fn=cmd_task_tree)

    s = sub.add_parser("progress")
    s.add_argument("--assignee")
    s.add_argument("--lines", type=int, default=3)
    s.set_defaults(fn=cmd_progress)

    s = sub.add_parser("status")
    s.add_argument("--live")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_status)

    s = sub.add_parser("log")
    s.add_argument("--limit", type=int, default=40)
    s.add_argument("--type", action="append")
    s.add_argument("--grep")
    s.set_defaults(fn=cmd_log)

    s = sub.add_parser("adddirs")
    s.add_argument("--member", required=True)
    s.set_defaults(fn=cmd_adddirs)

    s = sub.add_parser("permissions")
    s.add_argument("workdir")
    s.add_argument("--check", action="store_true")
    s.set_defaults(fn=cmd_permissions)

    s = sub.add_parser("chart")
    s.add_argument("name")
    s.add_argument("--mermaid", action="store_true")
    s.set_defaults(fn=cmd_chart)

    s = sub.add_parser("untrusted")
    s.set_defaults(fn=cmd_untrusted)

    s = sub.add_parser("layout")
    s.add_argument("--rows")
    s.add_argument("--notify", default="")
    s.add_argument("--layout", default="")
    s.set_defaults(fn=cmd_layout)

    s = sub.add_parser("unbriefed")
    s.add_argument("--panes")
    s.set_defaults(fn=cmd_unbriefed)

    s = sub.add_parser("event")
    s.add_argument("--type", required=True)
    s.add_argument("--kv", action="append", default=[])
    s.set_defaults(fn=cmd_event)

    return p


def main():
    args = build_parser().parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
