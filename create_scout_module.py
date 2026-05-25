import os

# 创建瞭望数据源模型
scout_model_content = '''import sqlite3
from app.models.db import get_connection

class ScoutSourceRepository:
    @staticmethod
    def create(name: str, url_pattern: str, request_method: str = "GET", 
               headers: str = "", enabled: bool = True) -> bool:
        try:
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO scout_source(name, url_pattern, request_method, headers, enabled) VALUES(?, ?, ?, ?, ?)",
                    (name, url_pattern, request_method, headers, 1 if enabled else 0)
                )
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    @staticmethod
    def get_all(page: int = 1, page_size: int = 20):
        offset = (page - 1) * page_size
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM scout_source ORDER BY create_at DESC LIMIT ? OFFSET ?",
                (page_size, offset)
            ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def get_total_count():
        with get_connection() as conn:
            row = conn.execute("SELECT COUNT(*) as total FROM scout_source").fetchone()
        return row["total"] if row else 0

    @staticmethod
    def get_by_id(id: int):
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM scout_source WHERE id = ?", (id,)).fetchone()
        return dict(row) if row else None

    @staticmethod
    def get_by_name(name: str):
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM scout_source WHERE name = ?", (name,)).fetchone()
        return dict(row) if row else None

    @staticmethod
    def update(id: int, name: str = None, url_pattern: str = None, 
               request_method: str = None, headers: str = None, enabled: bool = None) -> bool:
        update_fields = []
        params = []

        if name:
            update_fields.append("name = ?")
            params.append(name)
        if url_pattern:
            update_fields.append("url_pattern = ?")
            params.append(url_pattern)
        if request_method:
            update_fields.append("request_method = ?")
            params.append(request_method)
        if headers:
            update_fields.append("headers = ?")
            params.append(headers)
        if enabled is not None:
            update_fields.append("enabled = ?")
            params.append(1 if enabled else 0)
        
        if not update_fields:
            return False

        params.append(id)
        update_sql = "UPDATE scout_source SET " + ",".join(update_fields) + " WHERE id = ?"

        try:
            with get_connection() as conn:
                conn.execute(update_sql, params)
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    @staticmethod
    def delete(id: int) -> bool:
        with get_connection() as conn:
            cursor = conn.execute("DELETE FROM scout_source WHERE id = ?", (id,))
            conn.commit()
        return cursor.rowcount > 0

    @staticmethod
    def toggle_status(id: int) -> bool:
        with get_connection() as conn:
            conn.execute("UPDATE scout_source SET enabled = 1 - enabled WHERE id = ?", (id,))
            conn.commit()
        return True

    @staticmethod
    def batch_delete(ids: list) -> int:
        if not ids:
            return 0
        
        placeholders = ",".join("?" * len(ids))
        with get_connection() as conn:
            cursor = conn.execute("DELETE FROM scout_source WHERE id IN (" + placeholders + ")", ids)
            conn.commit()
        return cursor.rowcount
'''

with open(r'f:\20260515cNy\day4\cnAgentOS\app\models\scout_source.py', 'w', encoding='utf-8') as f:
    f.write(scout_model_content)
print('Created scout_source.py model')

# 创建瞭望管理控制器
scout_controller_content = '''import json
import tornado.web
import requests

from app.controllers.base import BaseHandler
from app.models.scout_source import ScoutSourceRepository

class ScoutListHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        xsrf_token = self.xsrf_token.decode('utf-8')
        self.render("scout_list.html", xsrf_token=xsrf_token)

class ScoutApiHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        try:
            page = int(self.get_argument("page", 1))
            page_size = int(self.get_argument("limit", 20))
        except ValueError:
            page = 1
            page_size = 20
        
        sources = ScoutSourceRepository.get_all(page, page_size)
        total = ScoutSourceRepository.get_total_count()
        
        self.write(json.dumps({
            "code": 0,
            "msg": "success",
            "count": total,
            "data": sources
        }))

    @tornado.web.authenticated
    def post(self):
        action = self.get_body_argument("action", "")
        
        if action == "add":
            self._add_source()
        elif action == "edit":
            self._edit_source()
        elif action == "delete":
            self._delete_source()
        elif action == "batchDelete":
            self._batch_delete()
        elif action == "toggle":
            self._toggle_status()
        elif action == "collect":
            self._collect_data()
        elif action == "batchCollect":
            self._batch_collect()
        else:
            self.set_status(400)
            self.write(json.dumps({"code": 1, "msg": "无效的操作"}))

    def _add_source(self):
        name = self.get_body_argument("name", "").strip()
        url_pattern = self.get_body_argument("url_pattern", "").strip()
        request_method = self.get_body_argument("request_method", "GET").strip().upper()
        headers = self.get_body_argument("headers", "")
        enabled = self.get_body_argument("enabled", "true") == "true"
        
        if not name or not url_pattern:
            self.write(json.dumps({"code": 1, "msg": "名称和URL模板不能为空"}))
            return
        
        if ScoutSourceRepository.create(name, url_pattern, request_method, headers, enabled):
            self.write(json.dumps({"code": 0, "msg": "添加成功"}))
        else:
            self.write(json.dumps({"code": 1, "msg": "名称已存在"}))

    def _edit_source(self):
        id = self.get_body_argument("id", "")
        name = self.get_body_argument("name", "").strip()
        url_pattern = self.get_body_argument("url_pattern", "").strip()
        request_method = self.get_body_argument("request_method", "").strip().upper()
        headers = self.get_body_argument("headers", "")
        enabled = self.get_body_argument("enabled", "")
        
        if not id:
            self.write(json.dumps({"code": 1, "msg": "ID不能为空"}))
            return
        
        try:
            id = int(id)
        except ValueError:
            self.write(json.dumps({"code": 1, "msg": "无效的ID"}))
            return
        
        update_params = {}
        if name:
            update_params["name"] = name
        if url_pattern:
            update_params["url_pattern"] = url_pattern
        if request_method:
            update_params["request_method"] = request_method
        if headers:
            update_params["headers"] = headers
        if enabled != "":
            update_params["enabled"] = enabled == "true"
        
        if not update_params:
            self.write(json.dumps({"code": 1, "msg": "至少需要修改一项"}))
            return
        
        if ScoutSourceRepository.update(id, **update_params):
            self.write(json.dumps({"code": 0, "msg": "修改成功"}))
        else:
            self.write(json.dumps({"code": 1, "msg": "修改失败，名称可能已存在"}))

    def _delete_source(self):
        id = self.get_body_argument("id", "")
        
        if not id:
            self.write(json.dumps({"code": 1, "msg": "ID不能为空"}))
            return
        
        try:
            id = int(id)
        except ValueError:
            self.write(json.dumps({"code": 1, "msg": "无效的ID"}))
            return
        
        if ScoutSourceRepository.delete(id):
            self.write(json.dumps({"code": 0, "msg": "删除成功"}))
        else:
            self.write(json.dumps({"code": 1, "msg": "删除失败"}))

    def _batch_delete(self):
        ids_str = self.get_body_argument("ids", "")
        
        if not ids_str:
            self.write(json.dumps({"code": 1, "msg": "请选择要删除的数据源"}))
            return
        
        try:
            ids = [int(id.strip()) for id in ids_str.split(",") if id.strip()]
        except ValueError:
            self.write(json.dumps({"code": 1, "msg": "无效的ID列表"}))
            return
        
        deleted_count = ScoutSourceRepository.batch_delete(ids)
        self.write(json.dumps({
            "code": 0,
            "msg": "成功删除 " + str(deleted_count) + " 条记录"
        }))

    def _toggle_status(self):
        id = self.get_body_argument("id", "")
        
        if not id:
            self.write(json.dumps({"code": 1, "msg": "ID不能为空"}))
            return
        
        try:
            id = int(id)
        except ValueError:
            self.write(json.dumps({"code": 1, "msg": "无效的ID"}))
            return
        
        if ScoutSourceRepository.toggle_status(id):
            source = ScoutSourceRepository.get_by_id(id)
            status = "启用" if source["enabled"] else "禁用"
            self.write(json.dumps({"code": 0, "msg": "已" + status}))
        else:
            self.write(json.dumps({"code": 1, "msg": "操作失败"}))

    def _parse_headers(self, headers_str):
        headers = {}
        if headers_str:
            for line in headers_str.strip().split("\\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    headers[key.strip()] = value.strip()
        return headers

    def _collect_data(self):
        id = self.get_body_argument("id", "")
        keywords = self.get_body_argument("keywords", "")
        
        if not id:
            self.write(json.dumps({"code": 1, "msg": "ID不能为空"}))
            return
        
        try:
            id = int(id)
        except ValueError:
            self.write(json.dumps({"code": 1, "msg": "无效的ID"}))
            return
        
        source = ScoutSourceRepository.get_by_id(id)
        if not source:
            self.write(json.dumps({"code": 1, "msg": "数据源不存在"}))
            return
        
        if not source["enabled"]:
            self.write(json.dumps({"code": 1, "msg": "数据源未启用"}))
            return
        
        try:
            url = source["url_pattern"]
            if "{关键字}" in url:
                if not keywords:
                    self.write(json.dumps({"code": 1, "msg": "请输入采集关键字"}))
                    return
                url = url.replace("{关键字}", keywords)
            
            headers = self._parse_headers(source["headers"])
            
            response = requests.request(
                method=source["request_method"],
                url=url,
                headers=headers,
                timeout=30
            )
            
            self.write(json.dumps({
                "code": 0,
                "msg": "采集成功",
                "data": {
                    "url": url,
                    "status_code": response.status_code,
                    "content_length": len(response.text),
                    "headers": dict(response.headers)
                }
            }))
            
        except Exception as e:
            self.write(json.dumps({"code": 1, "msg": "采集失败: " + str(e)}))

    def _batch_collect(self):
        ids_str = self.get_body_argument("ids", "")
        keywords = self.get_body_argument("keywords", "")
        
        if not ids_str:
            self.write(json.dumps({"code": 1, "msg": "请选择要采集的数据源"}))
            return
        
        try:
            ids = [int(id.strip()) for id in ids_str.split(",") if id.strip()]
        except ValueError:
            self.write(json.dumps({"code": 1, "msg": "无效的ID列表"}))
            return
        
        results = []
        success_count = 0
        fail_count = 0
        
        for id in ids:
            source = ScoutSourceRepository.get_by_id(id)
            if not source or not source["enabled"]:
                continue
            
            try:
                url = source["url_pattern"]
                if "{关键字}" in url:
                    if not keywords:
                        results.append({"name": source["name"], "status": "failed", "msg": "未提供关键字"})
                        fail_count += 1
                        continue
                    url = url.replace("{关键字}", keywords)
                
                headers = self._parse_headers(source["headers"])
                
                response = requests.request(
                    method=source["request_method"],
                    url=url,
                    headers=headers,
                    timeout=30
                )
                
                results.append({
                    "name": source["name"],
                    "status": "success",
                    "status_code": response.status_code,
                    "content_length": len(response.text)
                })
                success_count += 1
                
            except Exception as e:
                results.append({"name": source["name"], "status": "failed", "msg": str(e)})
                fail_count += 1
        
        self.write(json.dumps({
            "code": 0,
            "msg": "批量采集完成，成功 " + str(success_count) + " 条，失败 " + str(fail_count) + " 条",
            "data": results
        }))

class ScoutCollectHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        source_id = self.get_argument("source_id", "")
        source_info = None
        if source_id:
            try:
                source_info = ScoutSourceRepository.get_by_id(int(source_id))
            except ValueError:
                pass
        xsrf_token = self.xsrf_token.decode('utf-8')
        self.render("scout_collect.html", source_info=source_info, xsrf_token=xsrf_token)
'''

with open(r'f:\20260515cNy\day4\cnAgentOS\app\controllers\scout.py', 'w', encoding='utf-8') as f:
    f.write(scout_controller_content)
print('Created scout.py controller')

# 创建瞭望管理列表模板
scout_list_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Scout Management</title>
    <link rel="stylesheet" href="/static/dist/layui-v2.13.6/layui/css/layui.css">
</head>
<body>
    <div style="margin: 20px;">
        <h2>Scout Data Source Management</h2>
        <input type="hidden" id="xsrf_token" value="{{ xsrf_token }}">
        <div class="layui-btn-group">
            <button id="addBtn" class="layui-btn">Add Source</button>
            <button id="batchCollectBtn" class="layui-btn layui-btn-primary" disabled>Batch Collect</button>
            <button id="batchDeleteBtn" class="layui-btn layui-btn-danger" disabled>Batch Delete</button>
        </div>
        <table id="scoutTable" class="layui-table"></table>
    </div>

    <script type="text/html" id="barDemo">
        <a class="layui-btn layui-btn-xs" lay-event="edit">Edit</a>
        <a class="layui-btn layui-btn-xs" lay-event="collect">Collect</a>
        <a class="layui-btn layui-btn-danger layui-btn-xs" lay-event="del">Delete</a>
    </script>

    <script type="text/html" id="statusTpl">
        {{ '{{' }}# if(d.enabled == 1) { {{ '}}' }}
        <span class="layui-badge layui-bg-green">Enabled</span>
        {{ '{{' }}# } else { {{ '}}' }}
        <span class="layui-badge layui-bg-gray">Disabled</span>
        {{ '{{' }}# } {{ '}}' }}
    </script>

    <script src="/static/dist/layui-v2.13.6/layui/layui.js"></script>
    <script>
        layui.use(["table", "layer", "form"], function() {
            var table = layui.table;
            var layer = layui.layer;
            var form = layui.form;
            
            var tableIns = table.render({
                elem: "#scoutTable",
                url: "/api/scout",
                method: "get",
                page: true,
                limit: 20,
                cols: [[
                    {type: "checkbox"},
                    {field: "id", title: "ID", width: 80},
                    {field: "name", title: "Name", width: 150},
                    {field: "url_pattern", title: "URL Pattern", width: 300},
                    {field: "request_method", title: "Method", width: 80},
                    {field: "enabled", title: "Status", width: 100, templet: "#statusTpl"},
                    {field: "create_at", title: "Created", width: 180},
                    {title: "Actions", width: 180, toolbar: "#barDemo"}
                ]]
            });

            table.on("checkbox(scoutTable)", function(obj) {
                var checkStatus = table.checkStatus("scoutTable");
                $("#batchDeleteBtn").prop("disabled", checkStatus.data.length === 0);
                $("#batchCollectBtn").prop("disabled", checkStatus.data.length === 0);
            });

            table.on("tool(scoutTable)", function(obj) {
                var data = obj.data;
                if (obj.event === "edit") {
                    editSource(data);
                } else if (obj.event === "collect") {
                    collectData(data);
                } else if (obj.event === "del") {
                    deleteSource(data.id);
                }
            });

            function getXsrfToken() {
                return document.getElementById("xsrf_token").value;
            }

            $("#addBtn").click(function() {
                layer.open({
                    type: 1,
                    title: "Add Data Source",
                    area: ["600px", "450px"],
                    content: $("#addModal").html(),
                    success: function(layero, index) {
                        form.render();
                        form.on("submit(addSubmit)", function(data) {
                            $.ajax({
                                url: "/api/scout",
                                type: "POST",
                                data: {
                                    action: "add",
                                    name: data.field.name,
                                    url_pattern: data.field.url_pattern,
                                    request_method: data.field.request_method,
                                    headers: data.field.headers,
                                    enabled: data.field.enabled === "on" ? "true" : "false",
                                    _xsrf: getXsrfToken()
                                },
                                success: function(res) {
                                    if (res.code === 0) {
                                        layer.msg("Added", {icon: 1});
                                        tableIns.reload();
                                        layer.close(index);
                                    } else {
                                        layer.msg(res.msg, {icon: 2});
                                    }
                                }
                            });
                            return false;
                        });
                    }
                });
            });

            function editSource(data) {
                var modalHtml = $("#editModal").html();
                modalHtml = modalHtml.replace(/__ID__/g, data.id)
                                    .replace(/__NAME__/g, data.name)
                                    .replace(/__URL__/g, data.url_pattern)
                                    .replace(/__METHOD__/g, data.request_method)
                                    .replace(/__HEADERS__/g, data.headers || "");
                
                layer.open({
                    type: 1,
                    title: "Edit Data Source",
                    area: ["600px", "450px"],
                    content: modalHtml,
                    success: function(layero, index) {
                        form.render();
                        if (data.enabled == 1) {
                            layero.find("input[name='enabled']").prop("checked", true);
                        }
                        form.on("submit(editSubmit)", function(formData) {
                            $.ajax({
                                url: "/api/scout",
                                type: "POST",
                                data: {
                                    action: "edit",
                                    id: data.id,
                                    name: formData.field.name,
                                    url_pattern: formData.field.url_pattern,
                                    request_method: formData.field.request_method,
                                    headers: formData.field.headers,
                                    enabled: formData.field.enabled === "on" ? "true" : "false",
                                    _xsrf: getXsrfToken()
                                },
                                success: function(res) {
                                    if (res.code === 0) {
                                        layer.msg("Updated", {icon: 1});
                                        tableIns.reload();
                                        layer.close(index);
                                    } else {
                                        layer.msg(res.msg, {icon: 2});
                                    }
                                }
                            });
                            return false;
                        });
                    }
                });
            }

            function collectData(data) {
                layer.prompt({title: "Enter Keywords", formType: 0}, function(keywords, index) {
                    $.ajax({
                        url: "/api/scout",
                        type: "POST",
                        data: {
                            action: "collect",
                            id: data.id,
                            keywords: keywords,
                            _xsrf: getXsrfToken()
                        },
                        success: function(res) {
                            if (res.code === 0) {
                                layer.msg("Collected successfully", {icon: 1});
                                console.log(res.data);
                            } else {
                                layer.msg(res.msg, {icon: 2});
                            }
                        }
                    });
                    layer.close(index);
                });
            }

            function deleteSource(id) {
                layer.confirm("Delete this source?", function(index) {
                    $.ajax({
                        url: "/api/scout",
                        type: "POST",
                        data: {action: "delete", id: id, _xsrf: getXsrfToken()},
                        success: function(res) {
                            if (res.code === 0) {
                                layer.msg("Deleted", {icon: 1});
                                tableIns.reload();
                            } else {
                                layer.msg(res.msg, {icon: 2});
                            }
                        }
                    });
                    layer.close(index);
                });
            }

            $("#batchDeleteBtn").click(function() {
                var checkStatus = table.checkStatus("scoutTable");
                var ids = checkStatus.data.map(function(item) { return item.id; });
                layer.confirm("Delete " + ids.length + " sources?", function(index) {
                    $.ajax({
                        url: "/api/scout",
                        type: "POST",
                        data: {action: "batchDelete", ids: ids.join(","), _xsrf: getXsrfToken()},
                        success: function(res) {
                            if (res.code === 0) {
                                layer.msg("Deleted", {icon: 1});
                                tableIns.reload();
                            } else {
                                layer.msg(res.msg, {icon: 2});
                            }
                        }
                    });
                    layer.close(index);
                });
            });

            $("#batchCollectBtn").click(function() {
                layer.prompt({title: "Enter Keywords for Batch Collect", formType: 0}, function(keywords, index) {
                    var checkStatus = table.checkStatus("scoutTable");
                    var ids = checkStatus.data.map(function(item) { return item.id; });
                    
                    $.ajax({
                        url: "/api/scout",
                        type: "POST",
                        data: {
                            action: "batchCollect",
                            ids: ids.join(","),
                            keywords: keywords,
                            _xsrf: getXsrfToken()
                        },
                        success: function(res) {
                            if (res.code === 0) {
                                layer.msg(res.msg, {icon: 1});
                                console.log(res.data);
                            } else {
                                layer.msg(res.msg, {icon: 2});
                            }
                        }
                    });
                    layer.close(index);
                });
            });
        });
    </script>

    <div id="addModal" style="display:none;">
        <div style="padding:20px;">
            <form class="layui-form" lay-filter="addForm">
                <div class="layui-form-item">
                    <label class="layui-form-label">Name</label>
                    <div class="layui-input-block">
                        <input type="text" name="name" required lay-verify="required" placeholder="Enter name" class="layui-input">
                    </div>
                </div>
                <div class="layui-form-item">
                    <label class="layui-form-label">URL Pattern</label>
                    <div class="layui-input-block">
                        <input type="text" name="url_pattern" required lay-verify="required" placeholder="e.g. https://example.com/search?q={关键字}" class="layui-input">
                    </div>
                </div>
                <div class="layui-form-item">
                    <label class="layui-form-label">Method</label>
                    <div class="layui-input-block">
                        <select name="request_method">
                            <option value="GET">GET</option>
                            <option value="POST">POST</option>
                        </select>
                    </div>
                </div>
                <div class="layui-form-item">
                    <label class="layui-form-label">Headers</label>
                    <div class="layui-input-block">
                        <textarea name="headers" placeholder="Header lines, one per line" class="layui-textarea" rows="4"></textarea>
                    </div>
                </div>
                <div class="layui-form-item">
                    <label class="layui-form-label">Enabled</label>
                    <div class="layui-input-block">
                        <input type="checkbox" name="enabled" checked lay-skin="switch">
                    </div>
                </div>
                <div class="layui-form-item">
                    <div class="layui-input-block">
                        <button class="layui-btn" lay-submit lay-filter="addSubmit">Add</button>
                        <button type="button" class="layui-btn layui-btn-primary" onclick="layer.closeAll()">Cancel</button>
                    </div>
                </div>
            </form>
        </div>
    </div>

    <div id="editModal" style="display:none;">
        <div style="padding:20px;">
            <form class="layui-form" lay-filter="editForm">
                <input type="hidden" name="id" value="__ID__">
                <div class="layui-form-item">
                    <label class="layui-form-label">Name</label>
                    <div class="layui-input-block">
                        <input type="text" name="name" required lay-verify="required" value="__NAME__" class="layui-input">
                    </div>
                </div>
                <div class="layui-form-item">
                    <label class="layui-form-label">URL Pattern</label>
                    <div class="layui-input-block">
                        <input type="text" name="url_pattern" required lay-verify="required" value="__URL__" class="layui-input">
                    </div>
                </div>
                <div class="layui-form-item">
                    <label class="layui-form-label">Method</label>
                    <div class="layui-input-block">
                        <select name="request_method">
                            <option value="GET">GET</option>
                            <option value="POST">POST</option>
                        </select>
                    </div>
                </div>
                <div class="layui-form-item">
                    <label class="layui-form-label">Headers</label>
                    <div class="layui-input-block">
                        <textarea name="headers" placeholder="Header lines, one per line" class="layui-textarea" rows="4">__HEADERS__</textarea>
                    </div>
                </div>
                <div class="layui-form-item">
                    <label class="layui-form-label">Enabled</label>
                    <div class="layui-input-block">
                        <input type="checkbox" name="enabled" lay-skin="switch">
                    </div>
                </div>
                <div class="layui-form-item">
                    <div class="layui-input-block">
                        <button class="layui-btn" lay-submit lay-filter="editSubmit">Save</button>
                        <button type="button" class="layui-btn layui-btn-primary" onclick="layer.closeAll()">Cancel</button>
                    </div>
                </div>
            </form>
        </div>
    </div>
</body>
</html>'''

with open(r'f:\20260515cNy\day4\cnAgentOS\app\templates\scout_list.html', 'w', encoding='utf-8') as f:
    f.write(scout_list_content)
print('Created scout_list.html template')

# 创建采集页面模板
scout_collect_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Data Collection</title>
    <link rel="stylesheet" href="/static/dist/layui-v2.13.6/layui/css/layui.css">
</head>
<body>
    <div style="margin: 20px;">
        <h2>Data Collection</h2>
        <input type="hidden" id="xsrf_token" value="{{ xsrf_token }}">
        
        <div class="layui-form-item">
            <label class="layui-form-label">Source</label>
            <div class="layui-input-block">
                <input type="text" id="sourceName" readonly class="layui-input layui-disabled">
                <input type="hidden" id="sourceId">
            </div>
        </div>
        
        <div class="layui-form-item">
            <label class="layui-form-label">Keywords</label>
            <div class="layui-input-block">
                <input type="text" id="keywords" placeholder="Enter keywords" class="layui-input">
            </div>
        </div>
        
        <button id="collectBtn" class="layui-btn">Start Collection</button>
        
        <div id="resultArea" style="margin-top: 20px; display: none;">
            <h3>Collection Result</h3>
            <pre id="resultContent"></pre>
        </div>
    </div>

    <script src="/static/dist/layui-v2.13.6/layui/layui.js"></script>
    <script>
        layui.use(["layer"], function() {
            var layer = layui.layer;
            
            {% if source_info %}
            document.getElementById("sourceId").value = "{{ source_info.id }}";
            document.getElementById("sourceName").value = "{{ source_info.name }}";
            {% endif %}

            document.getElementById("collectBtn").onclick = function() {
                var sourceId = document.getElementById("sourceId").value;
                var keywords = document.getElementById("keywords").value;
                
                if (!sourceId) {
                    layer.msg("Please select a source", {icon: 2});
                    return;
                }
                
                if (!keywords) {
                    layer.msg("Please enter keywords", {icon: 2});
                    return;
                }
                
                $.ajax({
                    url: "/api/scout",
                    type: "POST",
                    data: {
                        action: "collect",
                        id: sourceId,
                        keywords: keywords,
                        _xsrf: document.getElementById("xsrf_token").value
                    },
                    success: function(res) {
                        if (res.code === 0) {
                            layer.msg("Collected successfully", {icon: 1});
                            document.getElementById("resultArea").style.display = "block";
                            document.getElementById("resultContent").textContent = JSON.stringify(res.data, null, 2);
                        } else {
                            layer.msg(res.msg, {icon: 2});
                        }
                    },
                    error: function() {
                        layer.msg("Collection failed", {icon: 2});
                    }
                });
            };
        });
    </script>
</body>
</html>'''

with open(r'f:\20260515cNy\day4\cnAgentOS\app\templates\scout_collect.html', 'w', encoding='utf-8') as f:
    f.write(scout_collect_content)
print('Created scout_collect.html template')

# 更新数据库初始化文件添加新表
db_content = '''import sqlite3
import os

def get_connection():
    db_path = os.path.join(os.path.dirname(__file__), "../data", "app.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    return sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)

def init_db():
    with get_connection() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS user (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, salt TEXT NOT NULL, role TEXT DEFAULT 'user', create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        
        conn.execute("CREATE TABLE IF NOT EXISTS model_service (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, model TEXT NOT NULL, api_key TEXT NOT NULL, base_url TEXT NOT NULL, max_tokens INTEGER DEFAULT 4096, temperature REAL DEFAULT 0.7, is_default INTEGER DEFAULT 0, token_usage INTEGER DEFAULT 0, create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, update_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        
        conn.execute("CREATE TABLE IF NOT EXISTS scout_source (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, url_pattern TEXT NOT NULL, request_method TEXT DEFAULT 'GET', headers TEXT, enabled INTEGER DEFAULT 1, create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, update_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        
        conn.commit()
    print("Database initialized successfully")
'''

with open(r'f:\20260515cNy\day4\cnAgentOS\app\models\db.py', 'w', encoding='utf-8') as f:
    f.write(db_content)
print('Updated db.py with scout_source table')

# 更新 app.py 添加新路由
app_py_content = '''import tornado.ioloop
import tornado.web
from tornado.httpserver import HTTPServer
import os

from app.models.db import init_db
from app.models.user import UserRepository

# 导入控制器
from app.controllers.auth import LoginHandler, LogoutHandler
from app.controllers.home import AdminHandler, IndexHandler, WelcomeHandler
from app.controllers.user import UserListHandler, UserApiHandler, UserInfoHandler
from app.controllers.model import ModelListHandler, ModelApiHandler, ModelTokenStatsHandler, ModelChatHandler, ModelChatApiHandler
from app.controllers.role import RoleListHandler, RoleApiHandler
from app.controllers.permission import PermissionListHandler, PermissionApiHandler
from app.controllers.function import FunctionListHandler, ModuleListHandler, FunctionApiHandler, ModuleApiHandler
from app.controllers.scout import ScoutListHandler, ScoutApiHandler, ScoutCollectHandler

def make_app():
    return tornado.web.Application(
        [
            (r"/", IndexHandler),
            (r"/auth/login", LoginHandler),
            (r"/auth/logout", LogoutHandler),
            (r"/admin", AdminHandler),
            (r"/admin/welcome", WelcomeHandler),
            (r"/admin/users", UserListHandler),
            (r"/api/users", UserApiHandler),
            (r"/api/user/info", UserInfoHandler),
            (r"/admin/roles", RoleListHandler),
            (r"/api/roles", RoleApiHandler),
            (r"/admin/permissions", PermissionListHandler),
            (r"/api/permissions", PermissionApiHandler),
            (r"/admin/functions", FunctionListHandler),
            (r"/admin/modules", ModuleListHandler),
            (r"/api/functions", FunctionApiHandler),
            (r"/api/modules", ModuleApiHandler),
            (r"/admin/models", ModelListHandler),
            (r"/api/models", ModelApiHandler),
            (r"/api/models/token-stats", ModelTokenStatsHandler),
            (r"/admin/models/chat", ModelChatHandler),
            (r"/api/models/chat", ModelChatApiHandler),
            (r"/admin/scout", ScoutListHandler),
            (r"/api/scout", ScoutApiHandler),
            (r"/admin/scout/collect", ScoutCollectHandler),
        ],
        template_path=os.path.join(os.path.dirname(__file__), "app", "templates"),
        static_path=os.path.join(os.path.dirname(__file__), "app", "static"),
        cookie_secret="cnAgentOS-2026-secret-key-change-in-production",
        debug=True,
        xsrf_cookies=True,
        login_url="/auth/login",
    )

def init_admin_user():
    if not UserRepository.get_user_by_username("admin"):
        UserRepository.create_user("admin", "admin888", "admin")
        print("默认管理员用户创建成功: admin/admin888")
    else:
        user = UserRepository.get_user_by_username("admin")
        if user and user["role"] != "admin":
            UserRepository.update_user(user["id"], role="admin")
            print("已更新admin用户角色为超级管理员")

if __name__ == "__main__":
    init_db()
    init_admin_user()
    
    app = make_app()
    server = HTTPServer(app)
    server.bind(10086)
    server.start()
    print("====== Server 启动成功 ====== 端口：10086 =======", flush=True)
    tornado.ioloop.IOLoop.current().start()
'''

with open(r'f:\20260515cNy\day4\cnAgentOS\app.py', 'w', encoding='utf-8') as f:
    f.write(app_py_content)
print('Updated app.py with scout routes')

print('\nScout management module created successfully!')