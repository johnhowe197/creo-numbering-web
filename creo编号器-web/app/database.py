"""
SQLite 数据访问层

存储结构：
- projects: 项目（一个根图号对应一个项目）
- nodes: 节点（含父级引用与兄弟顺序，编号在服务端原子分配）
"""

import sqlite3
from datetime import datetime
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent.parent / "data" / "numbering.db"


def now() -> str:
    """当前时间 ISO 字符串（秒级）"""
    return datetime.now().isoformat(timespec="seconds")


def get_connection() -> sqlite3.Connection:
    """获取数据库连接"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """初始化数据库表结构"""
    conn = get_connection()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                root_number TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS nodes (
                project_id INTEGER NOT NULL,
                number TEXT NOT NULL,
                node_type TEXT NOT NULL,
                name TEXT NOT NULL DEFAULT '',
                memo TEXT NOT NULL DEFAULT '',
                status_color TEXT NOT NULL DEFAULT '',
                parent TEXT,
                position INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (project_id, number),
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_nodes_project
                ON nodes(project_id, position);
            """
        )
        conn.commit()
    finally:
        conn.close()
