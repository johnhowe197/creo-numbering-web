"""
FastAPI 入口：Creo 模型树自动取号器 Web 版

编号规则（v2）：
- 根图号：创建组件 -> 两位数字（-00 起）
- 主机层（根的直接子级两位数字，如 -00）：只放字母组件（手动输入），不创建零件
- 字母组件（如 -ZBC）：创建组件 -> 根前缀+两位数字（全局编号）；
  创建零件 -> 宿主（字母组件的父级）的零件序列（如 -00-1），所有字母组件共享
- 普通数字组件（如 -10）：创建组件 -> 追加法（-1001）；创建零件 -> 分叉法（-10-1）
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import database as db
from . import numbering as num


@asynccontextmanager
async def lifespan(_app: FastAPI):
    db.init_db()
    yield


app = FastAPI(title="Creo 模型树自动取号器", lifespan=lifespan)


# ---------------- 请求模型 ----------------


class ProjectCreate(BaseModel):
    root_number: str
    name: str = ""


class ProjectUpdate(BaseModel):
    name: str | None = None


class NodeCreate(BaseModel):
    parent_number: str
    mode: str = "auto"  # auto | manual
    number: str = ""    # manual 时的图号


class BatchCreate(BaseModel):
    parent_number: str
    node_type: str
    count: int = 0              # 模式1：连续生成 count 个
    target_number: str = ""     # 模式2：补齐到目标号（如 05S01101-10-40）
    numbers: list[str] = []     # 模式3：批量录入指定图号列表


class NodeUpdate(BaseModel):
    name: str | None = None
    memo: str | None = None
    status_color: str | None = None
    new_number: str | None = None


class ImportData(BaseModel):
    project: dict
    nodes: dict


# ---------------- 数据访问辅助 ----------------


def get_project_or_404(conn, project_id: int) -> dict:
    row = conn.execute(
        "SELECT * FROM projects WHERE id = ?", (project_id,)
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="项目不存在")
    return dict(row)


def get_node_or_404(conn, project_id: int, number: str) -> dict:
    row = conn.execute(
        "SELECT * FROM nodes WHERE project_id = ? AND number = ?",
        (project_id, number),
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"节点不存在: {number}")
    return dict(row)


def all_numbers(conn, project_id: int) -> list:
    rows = conn.execute(
        "SELECT number FROM nodes WHERE project_id = ?", (project_id,)
    ).fetchall()
    return [r["number"] for r in rows]


def next_position(conn, project_id: int, parent: str | None) -> int:
    row = conn.execute(
        "SELECT COALESCE(MAX(position), -1) + 1 AS p FROM nodes "
        "WHERE project_id = ? AND parent IS ?",
        (project_id, parent),
    ).fetchone()
    return row["p"]


def list_nodes(conn, project_id: int) -> list:
    rows = conn.execute(
        "SELECT * FROM nodes WHERE project_id = ? ORDER BY position ASC",
        (project_id,),
    ).fetchall()
    return [dict(r) for r in rows]


# ---------------- 编号计算（规则 v2） ----------------


def compute_new_number(conn, project_id: int, parent_number: str, node_type: str,
                       mode: str, manual_number: str) -> str:
    """按规则 v2 计算新图号；不合法时抛出 HTTPException"""
    project = get_project_or_404(conn, project_id)
    parent_node = get_node_or_404(conn, project_id, parent_number)
    if parent_node["node_type"] == "part":
        raise HTTPException(status_code=400, detail="零件不能作为父级")

    numbers = all_numbers(conn, project_id)
    parent_alpha = num.is_alpha_component(parent_number)
    host_level = num.is_host_level(
        parent_number, parent_node["parent"], project["root_number"]
    )

    # 1. 主机层：只手动输入字母组件；不创建零件
    if host_level:
        if node_type == "part":
            raise HTTPException(
                status_code=400,
                detail=f"{parent_number} 为主机层，不创建零件，"
                       "零件请添加到其下的字母组件（如 -ZBC）中",
            )
        if mode == "auto":
            raise HTTPException(
                status_code=400,
                detail=f"{parent_number} 为主机层，请手动输入字母组件图号（如 -ZBC）",
            )

    # 2. 字母组件：创建组件 -> 全局数字；创建零件 -> 宿主零件序列
    elif parent_alpha:
        if node_type == "component":
            if mode == "auto":
                prefix = num.get_prefix(parent_number)
                ok, result, _ = num.next_component_for_alpha(prefix, numbers)
                if not ok:
                    raise HTTPException(status_code=400, detail=result)
                return result
        else:  # part
            host = num.part_host_number(parent_number, parent_node["parent"])
            if mode == "auto":
                ok, result, _ = num.get_next_part_number(host, numbers)
                if not ok:
                    raise HTTPException(status_code=400, detail=result)
                return result

    # 3. 根 / 普通数字组件：自动走原规则
    elif mode == "auto":
        ok, result, _ = num.generate_number(parent_number, node_type, numbers)
        if not ok:
            raise HTTPException(status_code=400, detail=result)
        return result

    # 手动输入的通用校验
    return _validate_manual(conn, project, node_type, manual_number)


def _validate_manual(conn, project: dict, node_type: str, manual_number: str) -> str:
    """校验手动输入的图号并返回规范化结果"""
    new_number = (manual_number or "").strip()
    if not new_number:
        raise HTTPException(status_code=400, detail="请输入图号")
    numbers = all_numbers(conn, project["id"])
    if new_number in numbers:
        raise HTTPException(status_code=409, detail=f"图号已存在: {new_number}")
    err = num.validate_node_number(new_number)
    if err:
        raise HTTPException(status_code=400, detail=err)
    if node_type == "component" and num.is_part(new_number):
        raise HTTPException(
            status_code=400,
            detail="组件图号不能以 -数字 结尾（该格式为零件）",
        )
    if node_type == "part" and not num.is_part(new_number):
        raise HTTPException(
            status_code=400,
            detail="零件图号必须以 -数字 结尾（如 05S01101-10-1）",
        )
    prefix = num.get_prefix(project["root_number"])
    if not new_number.startswith(prefix + "-"):
        raise HTTPException(
            status_code=400, detail=f"图号应以根前缀 {prefix}- 开头"
        )
    return new_number


def _insert_node(conn, project_id: int, parent_number: str,
                 node_type: str, number: str) -> str:
    """在事务中插入单个节点，返回图号"""
    pos = next_position(conn, project_id, parent_number)
    now = db.now()
    conn.execute(
        "INSERT INTO nodes (project_id, number, node_type, name, memo, "
        "status_color, parent, position, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (project_id, number, node_type, "", "", "",
         parent_number, pos, now, now),
    )
    return number


def _batch_by_count(conn, project_id: int, parent_number: str,
                    node_type: str, count: int) -> list:
    """连续生成 count 个图号（从下一个可用号开始）"""
    created = []
    for _ in range(count):
        new_number = compute_new_number(
            conn, project_id, parent_number, node_type, "auto", ""
        )
        created.append(
            _insert_node(conn, project_id, parent_number, node_type, new_number)
        )
    return created


def _batch_to_target(conn, project_id: int, parent_number: str,
                     node_type: str, target_number: str) -> list:
    """补齐图号直到目标号（如已录到目标号则返回空）"""
    target = target_number.strip()
    project = get_project_or_404(conn, project_id)
    if not target:
        raise HTTPException(status_code=400, detail="请输入目标图号")
    err = num.validate_node_number(target)
    if err:
        raise HTTPException(status_code=400, detail=err)
    numbers = set(all_numbers(conn, project_id))
    if target in numbers:
        return []  # 已录到目标号

    created = []
    guard = 0
    while True:
        guard += 1
        if guard > 2000:
            raise HTTPException(status_code=400, detail="目标号过远，批量生成已终止")
        new_number = compute_new_number(
            conn, project_id, parent_number, node_type, "auto", ""
        )
        if new_number in numbers:
            raise HTTPException(status_code=500, detail="批量生成出现重复图号")
        _insert_node(conn, project_id, parent_number, node_type, new_number)
        created.append(new_number)
        numbers.add(new_number)
        if new_number == target:
            return created
        # 若新号已越过目标（如目标 -5 但新号 -6），说明目标不在连续序列
        if _number_order(new_number) > _number_order(target):
            raise HTTPException(
                status_code=400,
                detail=f"目标号 {target} 无法通过连续生成补齐（中间可能缺失或已存在）",
            )


def _number_order(number: str) -> int:
    """提取图号末尾数字序号（用于批量补号比较）"""
    import re
    m = re.search(r"(\d+)$", number)
    return int(m.group(1)) if m else 0


# ---------------- 项目路由 ----------------


@app.get("/api/projects")
def list_projects():
    conn = db.get_connection()
    try:
        rows = conn.execute(
            "SELECT p.id, p.root_number, p.name, p.created_at, p.updated_at, "
            "COUNT(n.number) AS node_count "
            "FROM projects p LEFT JOIN nodes n ON n.project_id = p.id "
            "GROUP BY p.id ORDER BY p.id DESC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


@app.post("/api/projects", status_code=201)
def create_project(payload: ProjectCreate):
    root_number = payload.root_number.strip()
    if not root_number:
        raise HTTPException(status_code=400, detail="请输入根图号")
    err = num.validate_node_number(root_number)
    if err:
        raise HTTPException(status_code=400, detail=err)

    conn = db.get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        exists = conn.execute(
            "SELECT 1 FROM projects WHERE root_number = ?", (root_number,)
        ).fetchone()
        if exists:
            raise HTTPException(status_code=409, detail=f"项目已存在: {root_number}")

        now = db.now()
        cur = conn.execute(
            "INSERT INTO projects (root_number, name, created_at, updated_at) "
            "VALUES (?, ?, ?, ?)",
            (root_number, payload.name or root_number, now, now),
        )
        pid = cur.lastrowid
        # 根图号：无横杠 -> root；带横杠 -> component
        node_type = "component" if "-" in root_number else "root"
        conn.execute(
            "INSERT INTO nodes (project_id, number, node_type, name, memo, "
            "status_color, parent, position, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, NULL, 0, ?, ?)",
            (pid, root_number, node_type, payload.name or root_number, "", "", now, now),
        )
        conn.commit()
        return {"id": pid, "root_number": root_number}
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"创建失败: {e}")
    finally:
        conn.close()


@app.get("/api/projects/{project_id}")
def get_project(project_id: int):
    conn = db.get_connection()
    try:
        project = get_project_or_404(conn, project_id)
        nodes = list_nodes(conn, project_id)
        return {**project, "nodes": nodes}
    finally:
        conn.close()


@app.delete("/api/projects/{project_id}")
def delete_project(project_id: int):
    conn = db.get_connection()
    try:
        get_project_or_404(conn, project_id)
        conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        conn.commit()
        return {"ok": True}
    finally:
        conn.close()


@app.patch("/api/projects/{project_id}")
def update_project(project_id: int, payload: ProjectUpdate):
    """更新项目信息（当前支持修改项目名称）"""
    conn = db.get_connection()
    try:
        get_project_or_404(conn, project_id)
        now = db.now()
        if payload.name is not None:
            conn.execute(
                "UPDATE projects SET name = ?, updated_at = ? WHERE id = ?",
                (payload.name.strip(), now, project_id),
            )
        conn.commit()
        return {"id": project_id, "name": (payload.name or "").strip()}
    except HTTPException:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------------- 节点路由 ----------------


def _add_node(project_id: int, payload: NodeCreate, node_type: str) -> dict:
    conn = db.get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        get_project_or_404(conn, project_id)
        get_node_or_404(conn, project_id, payload.parent_number)
        new_number = compute_new_number(
            conn, project_id, payload.parent_number, node_type,
            payload.mode, payload.number,
        )
        pos = next_position(conn, project_id, payload.parent_number)
        now = db.now()
        conn.execute(
            "INSERT INTO nodes (project_id, number, node_type, name, memo, "
            "status_color, parent, position, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (project_id, new_number, node_type, "", "", "",
             payload.parent_number, pos, now, now),
        )
        conn.execute(
            "UPDATE projects SET updated_at = ? WHERE id = ?", (now, project_id)
        )
        conn.commit()
        return {"number": new_number, "node_type": node_type,
                "parent": payload.parent_number}
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"添加失败: {e}")
    finally:
        conn.close()


@app.post("/api/projects/{project_id}/components", status_code=201)
def add_component(project_id: int, payload: NodeCreate):
    return _add_node(project_id, payload, "component")


@app.post("/api/projects/{project_id}/parts", status_code=201)
def add_part(project_id: int, payload: NodeCreate):
    return _add_node(project_id, payload, "part")


@app.post("/api/projects/{project_id}/batch", status_code=201)
def batch_create(project_id: int, payload: BatchCreate):
    """批量添加节点：count 连续生成 / target 补齐到目标号 / numbers 批量录入"""
    if payload.node_type not in ("component", "part"):
        raise HTTPException(status_code=400, detail="无效的图号类型")

    conn = db.get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        get_project_or_404(conn, project_id)
        parent = get_node_or_404(conn, project_id, payload.parent_number)
        if parent["node_type"] == "part":
            raise HTTPException(status_code=400, detail="零件不能作为父级")

        if payload.numbers:
            created = []
            project = get_project_or_404(conn, project_id)
            for number in payload.numbers:
                valid = _validate_manual(conn, project, payload.node_type, number)
                created.append(_insert_node(
                    conn, project_id, payload.parent_number,
                    payload.node_type, valid,
                ))
        elif payload.target_number:
            created = _batch_to_target(
                conn, project_id, payload.parent_number,
                payload.node_type, payload.target_number,
            )
        elif payload.count and payload.count > 0:
            if payload.count > 2000:
                raise HTTPException(status_code=400, detail="单次最多批量生成 2000 个")
            created = _batch_by_count(
                conn, project_id, payload.parent_number,
                payload.node_type, payload.count,
            )
        else:
            raise HTTPException(status_code=400, detail="批量参数无效")

        conn.execute(
            "UPDATE projects SET updated_at = ? WHERE id = ?",
            (db.now(), project_id),
        )
        conn.commit()
        # 返回节点对象数组，与单个添加接口保持一致
        created_objs = [
            {"number": n, "node_type": payload.node_type, "parent": payload.parent_number}
            for n in created
        ]
        return {"created": created_objs}
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"批量添加失败: {e}")
    finally:
        conn.close()


@app.patch("/api/projects/{project_id}/nodes/{number}")
def update_node(project_id: int, number: str, payload: NodeUpdate):
    conn = db.get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        node = get_node_or_404(conn, project_id, number)
        now = db.now()
        current = number

        if payload.new_number is not None and payload.new_number.strip() != number:
            new_number = _validate_manual(
                conn, get_project_or_404(conn, project_id),
                node["node_type"], payload.new_number,
            )
            # 类型一致性：组件不能改成零件格式，零件不能改成组件格式
            if node["node_type"] == "component" and num.is_part(new_number):
                raise HTTPException(status_code=400, detail="组件图号不能以 -数字 结尾（该格式为零件）")
            if node["node_type"] == "part" and not num.is_part(new_number):
                raise HTTPException(status_code=400, detail="零件图号必须以 -数字 结尾（如 05S01101-10-1）")
            conn.execute(
                "UPDATE nodes SET number = ?, updated_at = ? "
                "WHERE project_id = ? AND number = ?",
                (new_number, now, project_id, number),
            )
            conn.execute(
                "UPDATE nodes SET parent = ? WHERE project_id = ? AND parent = ?",
                (new_number, project_id, number),
            )
            current = new_number

        fields, values = [], []
        for field in ("name", "memo", "status_color"):
            value = getattr(payload, field)
            if value is not None:
                fields.append(f"{field} = ?")
                values.append(value)
        if fields:
            fields.append("updated_at = ?")
            values.append(now)
            values.extend([project_id, current])
            conn.execute(
                f"UPDATE nodes SET {', '.join(fields)} "
                "WHERE project_id = ? AND number = ?",
                values,
            )
        conn.commit()
        return {"number": current}
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"更新失败: {e}")
    finally:
        conn.close()


@app.delete("/api/projects/{project_id}/nodes/{number}")
def delete_node(project_id: int, number: str):
    conn = db.get_connection()
    try:
        node = get_node_or_404(conn, project_id, number)
        if node["node_type"] == "root":
            raise HTTPException(status_code=400, detail="不能删除根节点")
        conn.execute(
            "WITH RECURSIVE sub(number) AS ("
            "  SELECT ?"
            "  UNION ALL"
            "  SELECT n.number FROM nodes n JOIN sub s ON n.parent = s.number "
            "  WHERE n.project_id = ?"
            ") DELETE FROM nodes WHERE project_id = ? "
            "AND number IN (SELECT number FROM sub)",
            (number, project_id, project_id),
        )
        conn.commit()
        return {"ok": True}
    except HTTPException:
        raise
    finally:
        conn.close()


# ---------------- 导入（桌面版 JSON） ----------------


@app.post("/api/import", status_code=201)
def import_project(payload: ImportData):
    project = payload.project or {}
    root = (project.get("root") or "").strip()
    nodes = payload.nodes or {}
    if not root or not nodes or root not in nodes:
        raise HTTPException(status_code=400, detail="数据格式无效：缺少根图号或节点")

    conn = db.get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        exists = conn.execute(
            "SELECT 1 FROM projects WHERE root_number = ?", (root,)
        ).fetchone()
        if exists:
            raise HTTPException(status_code=409, detail=f"项目已存在: {root}")

        now = db.now()
        cur = conn.execute(
            "INSERT INTO projects (root_number, name, created_at, updated_at) "
            "VALUES (?, ?, ?, ?)",
            (root, project.get("name") or root, now, now),
        )
        pid = cur.lastrowid
        for number, nd in nodes.items():
            parent = nd.get("parent")
            pos = 0
            if parent and parent in nodes:
                children = nodes[parent].get("children", []) or []
                pos = children.index(number) if number in children else len(children)
            node_type = nd.get("node_type", "component")
            conn.execute(
                "INSERT INTO nodes (project_id, number, node_type, name, memo, "
                "status_color, parent, position, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (pid, number, node_type, nd.get("name", ""), nd.get("memo", ""),
                 nd.get("status_color", ""), parent, pos,
                 nd.get("created", now), now),
            )
        conn.commit()
        return {"id": pid, "root_number": root, "node_count": len(nodes)}
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"导入失败: {e}")
    finally:
        conn.close()


# ---------------- 前端静态资源 ----------------

FRONTEND_DIST = Path(__file__).resolve().parent.parent / "web" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="web")
