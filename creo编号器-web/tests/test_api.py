"""后端 API 测试（编号规则 v2），标准库 unittest，无额外依赖"""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import database as db  # noqa: E402
from app.main import app  # noqa: E402


def create_project(client, root="05S01101", name="标准化中部槽"):
    resp = client.post("/api/projects", json={"root_number": root, "name": name})
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def add_comp(client, pid, parent, mode="auto", number=""):
    return client.post(
        f"/api/projects/{pid}/components",
        json={"parent_number": parent, "mode": mode, "number": number},
    )


def add_part(client, pid, parent, mode="auto", number=""):
    return client.post(
        f"/api/projects/{pid}/parts",
        json={"parent_number": parent, "mode": mode, "number": number},
    )


def desktop_data_path():
    return Path(__file__).resolve().parents[2] / "creo编号器" / "05S01101.json"


class NumberingApiTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="numbering_test_")
        db.DB_PATH = Path(self.tmp) / "test_numbering.db"
        db.init_db()
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_project_crud(self):
        pid = create_project(self.client)
        self.assertGreater(pid, 0)

        projects = self.client.get("/api/projects").json()
        self.assertEqual(projects[0]["root_number"], "05S01101")

        detail = self.client.get(f"/api/projects/{pid}").json()
        self.assertEqual(detail["nodes"][0]["node_type"], "root")

        self.assertEqual(self.client.delete(f"/api/projects/{pid}").status_code, 200)
        self.assertEqual(self.client.get(f"/api/projects/{pid}").status_code, 404)

    def test_project_rename_name(self):
        """项目可设置/修改中文名称"""
        pid = create_project(self.client)
        resp = self.client.patch(
            f"/api/projects/{pid}", json={"name": "标准化中部槽"}
        )
        self.assertEqual(resp.status_code, 200, resp.text)
        self.assertEqual(resp.json()["name"], "标准化中部槽")

        projects = self.client.get("/api/projects").json()
        self.assertEqual(projects[0]["name"], "标准化中部槽")
        self.assertNotEqual(projects[0]["name"], projects[0]["root_number"])

    def test_host_level_rules(self):
        """主机层：只手动输入字母组件，不创建零件"""
        pid = create_project(self.client)

        resp = add_comp(self.client, pid, "05S01101")
        self.assertEqual(resp.status_code, 201, resp.text)
        self.assertEqual(resp.json()["number"], "05S01101-00")

        resp = add_comp(self.client, pid, "05S01101-00")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("手动输入", resp.json()["detail"])

        self.assertEqual(
            add_comp(self.client, pid, "05S01101-00", "manual", "05S01101-ZBC").status_code,
            201,
        )
        self.assertEqual(
            add_comp(self.client, pid, "05S01101-00", "manual", "05S01101-KTC").status_code,
            201,
        )

        resp = add_part(self.client, pid, "05S01101-00")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("主机层", resp.json()["detail"])

    def test_alpha_component_rules(self):
        """字母组件：组件走全局数字，零件走宿主序列（共享）"""
        pid = create_project(self.client)
        add_comp(self.client, pid, "05S01101")
        add_comp(self.client, pid, "05S01101-00", "manual", "05S01101-ZBC")
        add_comp(self.client, pid, "05S01101-00", "manual", "05S01101-KTC")

        resp = add_comp(self.client, pid, "05S01101-ZBC")
        self.assertEqual(resp.status_code, 201, resp.text)
        self.assertEqual(resp.json()["number"], "05S01101-01")

        resp = add_part(self.client, pid, "05S01101-ZBC")
        self.assertEqual(resp.status_code, 201, resp.text)
        self.assertEqual(resp.json()["number"], "05S01101-00-1")

        resp = add_part(self.client, pid, "05S01101-KTC")
        self.assertEqual(resp.json()["number"], "05S01101-00-2")

        resp = add_part(self.client, pid, "05S01101-ZBC")
        self.assertEqual(resp.json()["number"], "05S01101-00-3")

        resp = add_comp(self.client, pid, "05S01101-01")
        self.assertEqual(resp.status_code, 201, resp.text)
        self.assertEqual(resp.json()["number"], "05S01101-0101")

        resp = add_part(self.client, pid, "05S01101-01")
        self.assertEqual(resp.json()["number"], "05S01101-01-1")

    def test_normal_component_rules(self):
        """普通数字组件：追加法与分叉法"""
        pid = create_project(self.client)
        add_comp(self.client, pid, "05S01101")
        add_comp(self.client, pid, "05S01101-00", "manual", "05S01101-ZBC")
        add_comp(self.client, pid, "05S01101-ZBC")

        self.assertEqual(
            add_comp(self.client, pid, "05S01101-01").json()["number"], "05S01101-0101"
        )
        self.assertEqual(
            add_comp(self.client, pid, "05S01101-01").json()["number"], "05S01101-0102"
        )
        self.assertEqual(
            add_part(self.client, pid, "05S01101-01").json()["number"], "05S01101-01-1"
        )
        self.assertEqual(
            add_part(self.client, pid, "05S01101-01").json()["number"], "05S01101-01-2"
        )

    def test_manual_validation(self):
        pid = create_project(self.client)
        add_comp(self.client, pid, "05S01101")

        resp = add_comp(self.client, pid, "05S01101-00", "manual", "05S01101-00-1")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("零件", resp.json()["detail"])

        add_comp(self.client, pid, "05S01101-00", "manual", "05S01101-ZBC")
        resp = add_comp(self.client, pid, "05S01101-00", "manual", "05S01101-ZBC")
        self.assertEqual(resp.status_code, 409)

        resp = add_comp(self.client, pid, "05S01101-00", "manual", "LS001-ABC")
        self.assertEqual(resp.status_code, 400)

        resp = add_comp(self.client, pid, "05S01101-00", "manual", "05S01101-")
        self.assertEqual(resp.status_code, 400)

    def test_rename_and_delete(self):
        pid = create_project(self.client)
        add_comp(self.client, pid, "05S01101")
        add_comp(self.client, pid, "05S01101-00", "manual", "05S01101-ZBC")
        add_comp(self.client, pid, "05S01101-ZBC")
        add_comp(self.client, pid, "05S01101-01")

        resp = self.client.patch(
            f"/api/projects/{pid}/nodes/05S01101-01",
            json={"new_number": "05S01101-02"},
        )
        self.assertEqual(resp.status_code, 200, resp.text)
        detail = self.client.get(f"/api/projects/{pid}").json()
        # 重命名只更新父子引用，子节点图号不变
        child = [n for n in detail["nodes"] if n["number"] == "05S01101-0101"]
        self.assertTrue(child)
        self.assertEqual(child[0]["parent"], "05S01101-02")

        resp = self.client.patch(
            f"/api/projects/{pid}/nodes/05S01101-ZBC",
            json={"new_number": "05S01101-ZBC-1"},
        )
        self.assertEqual(resp.status_code, 400)

        resp = self.client.delete(f"/api/projects/{pid}/nodes/05S01101-02")
        self.assertEqual(resp.status_code, 200)
        numbers = [n["number"] for n in
                   self.client.get(f"/api/projects/{pid}").json()["nodes"]]
        self.assertNotIn("05S01101-02", numbers)
        self.assertNotIn("05S01101-0201", numbers)

    def test_import_desktop_json(self):
        data_path = desktop_data_path()
        if not data_path.exists():
            self.skipTest("缺少桌面版数据文件 05S01101.json")
        payload = json.loads(data_path.read_text(encoding="utf-8"))

        resp = self.client.post("/api/import", json=payload)
        self.assertEqual(resp.status_code, 201, resp.text)
        self.assertEqual(resp.json()["node_count"], 39)

        resp = self.client.post("/api/import", json=payload)
        self.assertEqual(resp.status_code, 409)

        projects = self.client.get("/api/projects").json()
        pid = projects[0]["id"]
        nodes = self.client.get(f"/api/projects/{pid}").json()["nodes"]
        zbc = [n for n in nodes if n["number"] == "05S01101-ZBC"][0]
        self.assertEqual(zbc["node_type"], "component")

    def test_import_after_alpha_add(self):
        data_path = desktop_data_path()
        if not data_path.exists():
            self.skipTest("缺少桌面版数据文件 05S01101.json")
        payload = json.loads(data_path.read_text(encoding="utf-8"))
        pid = self.client.post("/api/import", json=payload).json()["id"]

        resp = add_part(self.client, pid, "05S01101-ZBC")
        self.assertEqual(resp.status_code, 201, resp.text)
        self.assertEqual(resp.json()["number"], "05S01101-00-1")

    def _setup_batch_project(self):
        pid = create_project(self.client, root="TB008S")
        self.assertEqual(
            add_comp(self.client, pid, "TB008S").json()["number"], "TB008S-00"
        )
        self.assertEqual(
            add_comp(self.client, pid, "TB008S-00", "manual", "TB008S-0101").status_code,
            201,
        )
        return pid

    def test_batch_count(self):
        """批量数量：一次连续生成 40 个零件"""
        pid = self._setup_batch_project()
        resp = self.client.post(
            f"/api/projects/{pid}/batch",
            json={
                "parent_number": "TB008S-0101",
                "node_type": "part",
                "count": 40,
            },
        )
        self.assertEqual(resp.status_code, 201, resp.text)
        created = resp.json()["created"]
        self.assertEqual(len(created), 40)
        self.assertEqual(created[0], "TB008S-0101-1")
        self.assertEqual(created[-1], "TB008S-0101-40")

        # 继续生成从 41 开始
        resp = self.client.post(
            f"/api/projects/{pid}/batch",
            json={"parent_number": "TB008S-0101", "node_type": "part", "count": 2},
        )
        self.assertEqual(resp.json()["created"], ["TB008S-0101-41", "TB008S-0101-42"])

    def test_batch_target(self):
        """批量补齐到目标号"""
        pid = self._setup_batch_project()
        resp = self.client.post(
            f"/api/projects/{pid}/batch",
            json={
                "parent_number": "TB008S-0101",
                "node_type": "part",
                "target_number": "TB008S-0101-40",
            },
        )
        self.assertEqual(resp.status_code, 201, resp.text)
        self.assertEqual(len(resp.json()["created"]), 40)
        self.assertEqual(resp.json()["created"][-1], "TB008S-0101-40")

        # 已录到目标号 -> 返回空
        resp = self.client.post(
            f"/api/projects/{pid}/batch",
            json={
                "parent_number": "TB008S-0101",
                "node_type": "part",
                "target_number": "TB008S-0101-40",
            },
        )
        self.assertEqual(resp.json()["created"], [])

    def test_batch_list(self):
        """批量粘贴图号列表（含重复与非法校验）"""
        pid = self._setup_batch_project()
        resp = self.client.post(
            f"/api/projects/{pid}/batch",
            json={
                "parent_number": "TB008S-0101",
                "node_type": "part",
                "numbers": [
                    "TB008S-0101-1",
                    "TB008S-0101-2",
                    "TB008S-0101-3",
                ],
            },
        )
        self.assertEqual(resp.status_code, 201, resp.text)
        self.assertEqual(len(resp.json()["created"]), 3)

        # 重复图号 -> 409
        resp = self.client.post(
            f"/api/projects/{pid}/batch",
            json={
                "parent_number": "TB008S-0101",
                "node_type": "part",
                "numbers": ["TB008S-0101-1"],
            },
        )
        self.assertEqual(resp.status_code, 409)

        # 非法格式 -> 400
        resp = self.client.post(
            f"/api/projects/{pid}/batch",
            json={
                "parent_number": "TB008S-0101",
                "node_type": "part",
                "numbers": ["TB008S-0101-abc"],
            },
        )
        self.assertEqual(resp.status_code, 400)


if __name__ == "__main__":
    unittest.main(verbosity=2)
