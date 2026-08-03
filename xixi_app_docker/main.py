from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional
import os

app = FastAPI()

# ==========================================
# 🛡️ 跨域配置
# ==========================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有前端来源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有请求方法
    allow_headers=["*"],  # 允许所有请求头
)

# ==========================================
# 🗄️ 数据库配置
# ==========================================
DB_CONFIG = {
    "dbname": "xixi_frontend",
    "user": "kwindboy",
    "password": "jiangwen1",  # 请填入实际密码
    "host": "192.168.100.67",
    "port": 5432
}
def get_db_connection():
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

# ==========================================
# 1. 模块一：账户与登录/注册
# ==========================================
class LoginRequest(BaseModel):
    login_name: str
    password: str

class RegisterRequest(BaseModel):
    login_name: str
    password: str
    display_name: str
    birthday: str

@app.post("/api/login")
def login(data: LoginRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT id, login_name, display_name, password_hash, birthday FROM baby_accounts WHERE login_name = %s",
            (data.login_name,)
        )
        account = cursor.fetchone()
        if not account or account['password_hash'] != data.password:
            raise HTTPException(status_code=400, detail="用户名或密码错误")
            
        return {
            "message": "登录成功",
            "account_id": str(account['id']),
            "display_name": account['display_name'],
            "birthday": str(account['birthday']) if account.get('birthday') else ""
        }
    finally:
        cursor.close()
        conn.close()

@app.post("/api/register")
def register(data: RegisterRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM baby_accounts WHERE login_name = %s", (data.login_name,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="该用户名已被注册，请换一个")
            
        cursor.execute(
            "INSERT INTO baby_accounts (login_name, password_hash, display_name, birthday) VALUES (%s, %s, %s, %s) RETURNING id",
            (data.login_name, data.password, data.display_name, data.birthday)
        )
        new_id = cursor.fetchone()['id']
        conn.commit()
        
        return {
            "message": "注册成功",
            "account_id": str(new_id),
            "display_name": data.display_name,
            "birthday": data.birthday
        }
    finally:
        cursor.close()
        conn.close()
# ==========================================
# 🍼 模块二：喝奶记录 (Milk Logs)
# ==========================================
class MilkLogCreateRequest(BaseModel):
    account_id: str
    amount_ml: int
    notes: Optional[str] = ""
    created_at: str

class MilkLogUpdateRequest(BaseModel):
    amount_ml: int
    notes: Optional[str] = ""
    created_at: str

@app.get("/api/milk_logs/{account_id}")
def get_milk_logs(account_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT * FROM milk_logs WHERE account_id = %s ORDER BY created_at DESC", 
            (account_id,)
        )
        return {"code": 200, "data": cursor.fetchall()}
    finally:
        cursor.close()
        conn.close()

@app.post("/api/milk_logs")
def create_milk_log(data: MilkLogCreateRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO milk_logs (account_id, amount_ml, notes, created_at) VALUES (%s, %s, %s, %s)",
            (data.account_id, data.amount_ml, data.notes, data.created_at)
        )
        conn.commit()
        return {"code": 200, "message": "添加成功"}
    finally:
        cursor.close()
        conn.close()

@app.put("/api/milk_logs/{log_id}")
def update_milk_log(log_id: int, data: MilkLogUpdateRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE milk_logs SET amount_ml = %s, notes = %s, created_at = %s WHERE id = %s",
            (data.amount_ml, data.notes, data.created_at, log_id)
        )
        conn.commit()
        return {"code": 200, "message": "修改成功"}
    finally:
        cursor.close()
        conn.close()

@app.delete("/api/milk_logs/{log_id}")
def delete_milk_log(log_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM milk_logs WHERE id = %s", (log_id,))
        conn.commit()
        return {"code": 200, "message": "删除成功"}
    finally:
        cursor.close()
        conn.close()


# ==========================================
# 🌟 模块三：日常活动记录 (Activity Logs)
# ==========================================
class ActivityLogCreateRequest(BaseModel):
    account_id: str
    type: str
    notes: Optional[str] = ""
    created_at: str

class ActivityLogUpdateRequest(BaseModel):
    type: str
    notes: Optional[str] = ""
    created_at: str

@app.get("/api/activity_logs/{account_id}")
def get_activity_logs(account_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT * FROM activity_logs WHERE account_id = %s ORDER BY created_at DESC", 
            (account_id,)
        )
        return {"code": 200, "data": cursor.fetchall()}
    finally:
        cursor.close()
        conn.close()

@app.post("/api/activity_logs")
def create_activity_log(data: ActivityLogCreateRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO activity_logs (account_id, type, notes, created_at) VALUES (%s, %s, %s, %s)",
            (data.account_id, data.type, data.notes, data.created_at)
        )
        conn.commit()
        return {"code": 200, "message": "添加成功"}
    finally:
        cursor.close()
        conn.close()

@app.put("/api/activity_logs/{log_id}")
def update_activity_log(log_id: int, data: ActivityLogUpdateRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE activity_logs SET type = %s, notes = %s, created_at = %s WHERE id = %s",
            (data.type, data.notes, data.created_at, log_id)
        )
        conn.commit()
        return {"code": 200, "message": "修改成功"}
    finally:
        cursor.close()
        conn.close()

@app.delete("/api/activity_logs/{log_id}")
def delete_activity_log(log_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM activity_logs WHERE id = %s", (log_id,))
        conn.commit()
        return {"code": 200, "message": "删除成功"}
    finally:
        cursor.close()
        conn.close()
# ==========================================
# 🌐 模块四：静态资源与前端页面托管 (必须放在最底部)
# ==========================================
app.mount("/assets", StaticFiles(directory="dist/assets"), name="assets")

# 捕获所有非 API 的路由，统统返回 Vue 的 index.html，交由前端路由接管
@app.get("/{catchall:path}")
def serve_vue_app(catchall: str):
    # 1. 尝试去 dist 目录下寻找浏览器请求的真实文件 (比如 manifest.webmanifest 或 favicon.ico)
    file_path = os.path.join("dist", catchall)
    
    # 2. 如果这个文件确实存在，就把它原本返回
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    
    # 3. 如果文件不存在（说明是 Vue Router 的页面跳转逻辑），统统返回 index.html
    return FileResponse("dist/index.html")