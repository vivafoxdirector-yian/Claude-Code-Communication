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
        die(
            str(src) + ": 작업 디렉터리가 없습니다 — " + str(wd)
            + "\n  org.workdir(" + raw_wd + ") 을 확인하세요."
            + "\n  비우면 이 저장소(" + str(home()) + ")가 기본입니다." + hint
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
    print("바로 띄우기 : ./aiorg up --org <템플릿>")
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
        print("=== " + label + " 메시지 " + str(len(picked)) + "건 — " + me["icon"] + " " + args.me + " (" + me["title"] + ") ===")
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
        print(prefix + conn + m["icon"] + " " + pad(mid, 12) + " " + pad(m["title"], 16) + " [" + badges.get(state, state) + "]" + tail)

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

    s = sub.add_parser("status")
    s.add_argument("--live")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_status)

    s = sub.add_parser("log")
    s.add_argument("--limit", type=int, default=40)
    s.add_argument("--type", action="append")
    s.add_argument("--grep")
    s.set_defaults(fn=cmd_log)

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
