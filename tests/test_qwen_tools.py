import asyncio
import os
import sys
import json
import httpx
import re
from groq import Groq

# เพิ่มพาธของ root โปรเจกต์เพื่อให้ import โมดูลในโฟลเดอร์ services ได้
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import services.manage_service as ms

def get_env_var(name):
    # ดึงค่าตัวแปรจาก Environment หรืออ่านไฟล์ .env ตรงๆ
    val = os.environ.get(name)
    if val:
        return val
    try:
        env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../.env'))
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip().startswith(f"{name}="):
                        return line.strip().split("=", 1)[1].strip()
    except Exception:
        pass
    return None

groq_api_key = get_env_var("GROQ_API_KEY")

def find_case_insensitive_path(vault_root: str, relative_path: str) -> str:
    """ค้นหาพาธจริงแบบไม่สนใจ Case-Sensitive สำหรับ Google Drive"""
    parts = relative_path.replace('\\', '/').split('/')
    current_path = vault_root
    
    for part in parts:
        if not part:
            continue
        if os.path.exists(current_path) and os.path.isdir(current_path):
            try:
                items = os.listdir(current_path)
                matched = next((item for item in items if item.lower() == part.lower()), None)
                if matched:
                    current_path = os.path.join(current_path, matched)
                else:
                    current_path = os.path.join(current_path, part)
            except Exception:
                current_path = os.path.join(current_path, part)
        else:
            current_path = os.path.join(current_path, part)
            
    return current_path

TH_TO_EN_STORE_MAP = {
    "รังสิต": "Rangsit", "ชิดลม": "Chidlom", "ลาดพร้าว": "Ladprao", "ปิ่นเกล้า": "Pinklao",
    "พระราม9": "Rama9", "พระราม 9": "Rama9", "พระราม2": "RAMA II", "พระราม 2": "RAMA II",
    "พระราม3": "RAMA III", "พระราม 3": "RAMA III", "บางนา": "Bangna", "อีสต์วิลล์": "Eastville",
    "แฟชั่น": "FashionIsland", "แฟชั่นไอส์แลนด์": "FashionIsland", "เมกาบางนา": "MegaBangna",
    "ศาลายา": "Sai4", "สาย4": "Sai4", "สาย 4": "Sai4", "แจ้งวัฒนะ": "Chaengwattana",
    "เชียงใหม่": "Chiangmai", "ภูเก็ต": "Phuket", "พัทยา": "Pattaya", "อุดร": "Udon",
    "ขอนแก่น": "Khon", "ระยอง": "Rayong", "ชลบุรี": "Chonburi", "ศรีราชา": "Sriracha",
    "หาดใหญ่": "Hadyai", "โคราช": "Nakornratchasima", "นครราชสีมา": "Nakornratchasima"
}

async def fetch_and_cache_store_map(force_refresh=False):
    """ดึงรายชื่อสาขาจาก Google Apps Script API และทำแคชเก็บไว้"""
    cache_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'stores_cache.json'))
    
    if not force_refresh and os.path.exists(cache_path):
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    return data
        except Exception:
            pass
            
    api_url = "https://script.google.com/macros/s/AKfycbzepwpESHIzuyG_5oKOFFsio9BmfN88Wa57EYHGy6RMEl3HYKZd8J8gO60Mu87NosdU5Q/exec?action=map"
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            r = await client.get(api_url, timeout=15.0)
            if r.status_code == 200:
                res_json = r.json()
                raw_sheets = res_json.get("sheets", [])
                filtered_stores = [s.strip() for s in raw_sheets if isinstance(s, str) and s.strip().startswith("TopsDigital-")]
                
                with open(cache_path, 'w', encoding='utf-8') as f:
                    json.dump(filtered_stores, f, ensure_ascii=False, indent=2)
                    
                return filtered_stores
    except Exception as e:
        print(f"⚠️ ไม่สามารถดึง Store Map API ได้: {e}")
        
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return []

def match_store_name(keyword: str, store_list: list):
    """ค้นหาชื่อสาขาโดยใช้อัลกอริทึมชั่งน้ำหนักความแม่นยำ (Weighted Matching & Confidence Scoring)"""
    if not keyword or not store_list:
        return None, []
        
    keyword_clean = keyword.strip()
    search_term = TH_TO_EN_STORE_MAP.get(keyword_clean, keyword_clean).lower()
    
    scores = {}
    
    for store in store_list:
        clean_name = store.replace("TopsDigital-", "").strip().lower()
        full_name_lower = store.lower()
        
        # 1. Exact Match (ตรงเป๊ะได้ 100 คะแนนเต็ม)
        if full_name_lower == keyword_clean.lower() or clean_name == search_term:
            scores[store] = 100
            continue
            
        # 2. Word Boundary / Part Match (คำตรงกันแบบแยกส่วน)
        parts = clean_name.replace("-", " ").split()
        if search_term in parts:
            scores[store] = 90
            continue
            
        # 3. Clean Name Starts With (เช่น "rangsit" ใน "rangsitcds")
        if clean_name.startswith(search_term):
            length_diff = len(clean_name) - len(search_term)
            score = max(50, 85 - (length_diff * 5))
            scores[store] = score
            continue
            
        # 4. Partial Substring Match
        if search_term in clean_name:
            scores[store] = 40
            
    if not scores:
        return None, []
        
    sorted_matches = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    best_match, best_score = sorted_matches[0]
    
    # หากรายการอันดับ 1 ได้คะแนนสูงเดี่ยวๆ (>= 90) เลือกตัวนี้ทันที
    if best_score >= 90:
        return best_match, []
        
    # หากคะแนนไม่สูงมาก หรือมีตัวเลือกคะแนนใกล้เคียงกันหลายตัว ให้ส่งกลับไปถามผู้ใช้
    top_candidates = [m[0] for m in sorted_matches if m[1] >= (best_score - 15)]
    if len(top_candidates) > 1 and best_score < 95:
        return None, top_candidates[:4]
        
    return best_match, []

def parse_xml_tool_call(content: str):
    """ดักจับและแปลง XML Tool Call ที่หลุดมาใน Content (สำหรับ Llama 3)"""
    if not content:
        return None
    # ค้นหารูปแบบ <function.name>args</function> หรือ <function_call...>
    match = re.search(r'<function\.(\w+)>(.*?)</function>', content, re.DOTALL)
    if match:
        name = match.group(1)
        args_str = match.group(2).strip()
        # เคลียร์วงเล็บสี่เหลี่ยมหรืออักขระขยะที่อาจจะติดมาตอนท้ายของ JSON
        if args_str.endswith(']'):
            args_str = args_str[:-1].strip()
        try:
            args = json.loads(args_str)
            return {"name": name, "args": args}
        except Exception:
            try:
                # ลองล้าง JSON จาก syntax เล็กๆ น้อยๆ อีกรอบ
                cleaned = re.sub(r'\]\s*$', '', args_str)
                args = json.loads(cleaned)
                return {"name": name, "args": args}
            except Exception:
                pass
    return None

async def execute_tool(name: str, args: dict) -> str:
    """ฟังก์ชันทำงานภายในเครื่องเพื่อเรียก API หรือสั่งการผ่าน Router Manager (ms)"""
    try:
        if name == "manage_service":
            service_name = args.get("service_name")
            action = args.get("action")
            
            if action == "start":
                return await ms.start_service(service_name)
            elif action == "stop":
                return await ms.stop_service(service_name)
            elif action == "status":
                status = ms.get_service_status(service_name)
                return f"Service {service_name} status: is_running={status['is_running']}, PID={status['pid']}"
                
        elif name == "get_service_manual":
            service_name = args.get("service_name")
            return ms.get_service_manual(service_name)
            
        elif name == "list_services":
            services = ms.list_services()
            result = []
            for s in services:
                result.append(f"- {s['service_name']}: is_running={s['is_running']}, port={s['port']}, desc={s['description']}")
            return "\n".join(result)
            
        elif name == "control_ptz":
            url = "http://localhost:5000/api/ptz"
            payload = {
                "axis": args.get("axis"),
                "value": args.get("value")
            }
            print(f"📤 [API Call] กำลังยิง API ไปที่ {url} ด้วย payload {payload}")
            async with httpx.AsyncClient() as client:
                r = await client.post(url, json=payload, timeout=5.0)
                return f"PTZ Action Response: {r.json()}"
                
        elif name == "trigger_web_ui":
            url = "http://localhost:3000/api/trigger"
            payload = {
                "action": args.get("action"),
                "message": args.get("message", "")
            }
            print(f"📤 [API Call] กำลังยิง API ไปที่ {url} ด้วย payload {payload}")
            async with httpx.AsyncClient() as client:
                r = await client.post(url, json=payload, timeout=5.0)
                return f"Web UI Action Response: status code {r.status_code}"
                
        elif name == "read_project_file":
            file_path = args.get("file_path")
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            target_path = os.path.abspath(os.path.join(project_root, file_path))
            if not target_path.startswith(project_root):
                return "Error: ไม่สามารถอ่านไฟล์นอกโปรเจกต์ได้"
            if os.path.exists(target_path):
                with open(target_path, "r", encoding="utf-8") as f:
                    return f.read()
            else:
                return f"Error: ไม่พบไฟล์ {file_path}"
                
        elif name == "read_vault_file":
            vault_type = args.get("vault_type", "actbotkung")
            file_path = args.get("file_path")
            if vault_type == "global":
                vault_root = "G:\\My Drive\\AI Agent Vault"
            else:
                vault_root = "I:\\.shortcut-targets-by-id\\1eFMZ3HJxeCzwhyUVzcb6d5oaDOnuQDt2\\ACTBOTKUNG"
            
            target_path = find_case_insensitive_path(vault_root, file_path)
            if not target_path.lower().startswith(vault_root.lower()):
                return "Error: ไม่สามารถอ่านไฟล์นอกถังความจำระยะยาวได้"
            if os.path.exists(target_path):
                with open(target_path, "r", encoding="utf-8") as f:
                    return f.read()
            else:
                return f"Error: ไม่พบไฟล์ {file_path} ในถังความจำ {vault_type}"
                
        elif name == "list_vault_files":
            vault_type = args.get("vault_type", "actbotkung")
            subdir = args.get("subdir", "")
            if vault_type == "global":
                vault_root = "G:\\My Drive\\AI Agent Vault"
            else:
                vault_root = "I:\\.shortcut-targets-by-id\\1eFMZ3HJxeCzwhyUVzcb6d5oaDOnuQDt2\\ACTBOTKUNG"
            
            target_path = find_case_insensitive_path(vault_root, subdir)
            if not target_path.lower().startswith(vault_root.lower()):
                return "Error: ไม่สามารถตรวจสอบไดเรกทอรีนอกถังความจำได้"
            
            if os.path.exists(target_path):
                if os.path.isdir(target_path):
                    items = os.listdir(target_path)
                    result = []
                    for item in items:
                        full_item = os.path.join(target_path, item)
                        is_dir = os.path.isdir(full_item)
                        result.append(f"{item}/" if is_dir else item)
                    return "\n".join(result)
                else:
                    return f"Error: {subdir} ไม่ใช่โฟลเดอร์"
            else:
                return f"Error: ไม่พบโฟลเดอร์ {subdir} ในถังความจำ {vault_type}"
                
        elif name == "search_vault_content":
            vault_type = args.get("vault_type", "actbotkung")
            query = args.get("query", "").lower()
            if vault_type == "global":
                vault_root = "G:\\My Drive\\AI Agent Vault"
            else:
                vault_root = "I:\\.shortcut-targets-by-id\\1eFMZ3HJxeCzwhyUVzcb6d5oaDOnuQDt2\\ACTBOTKUNG"
                
            if not query:
                return "Error: กรุณาระบุคำค้นหา"
                
            words = query.split()
            results = []
            for root_dir, dirs, files in os.walk(vault_root):
                for file in files:
                    if file.endswith(('.md', '.txt')):
                        file_path = os.path.join(root_dir, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read().lower()
                                if all(word in content for word in words):
                                    rel_path = os.path.relpath(file_path, vault_root)
                                    results.append(rel_path)
                        except Exception:
                            pass
            if results:
                return "พบคำค้นหาในไฟล์เหล่านี้:\n" + "\n".join(results)
            else:
                return f"ไม่พบคำค้นหาที่ตรงกับ '{query}' ในไฟล์ใดๆ ของถังความจำ {vault_type}"
                
        elif name == "call_http_api":
            method = args.get("method", "GET").upper()
            url = args.get("url")
            headers = args.get("headers", {})
            params = args.get("params", {})
            json_data = args.get("json_data")
            auth = args.get("auth", {})
            save_file_path = args.get("save_file_path")
            
            auth_obj = None
            if auth:
                auth_type = auth.get("type", "none")
                auth_val = auth.get("value", "")
                
                if auth_type == "basic" and isinstance(auth_val, list) and len(auth_val) == 2:
                    auth_obj = (auth_val[0], auth_val[1])
                elif auth_type == "env_basic" and auth_val:
                    env_keys = auth_val.split(',')
                    if len(env_keys) == 2:
                        user = get_env_var(env_keys[0].strip())
                        password = get_env_var(env_keys[1].strip())
                        if user and password:
                            auth_obj = (user, password)
                elif auth_type == "bearer" and auth_val:
                    headers["Authorization"] = f"Bearer {auth_val}"
                elif auth_type == "env_bearer" and auth_val:
                    token = get_env_var(auth_val.strip())
                    if token:
                        headers["Authorization"] = f"Bearer {token}"
            
            try:
                async with httpx.AsyncClient() as client:
                    r = await client.request(
                        method=method,
                        url=url,
                        headers=headers,
                        params=params,
                        json=json_data,
                        auth=auth_obj,
                        timeout=15.0
                    )
                    
                    response_text = r.text
                    
                    if save_file_path:
                        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
                        target_path = os.path.abspath(os.path.join(project_root, save_file_path))
                        if not target_path.lower().startswith(project_root.lower()):
                            return "Error: ไม่สามารถบันทึกไฟล์นอกพื้นที่โปรเจกต์ได้"
                        
                        os.makedirs(os.path.dirname(target_path), exist_ok=True)
                        with open(target_path, "w", encoding="utf-8") as f:
                            f.write(response_text)
                        return f"Successfully called API (HTTP Status: {r.status_code}) and saved response to {save_file_path}"
                    
                    if len(response_text) > 8000:
                        try:
                            parsed = r.json()
                            if isinstance(parsed, list):
                                summary = f"ข้อมูลเป็น List ขนาด {len(parsed)} รายการ ตัวอย่างรายการแรก:\n"
                                summary += json.dumps(parsed[0], ensure_ascii=False, indent=2)[:2000]
                                summary += "\n... (ข้อมูลถูกตัดทอนเนื่องจากมีขนาดใหญ่เกินไป)"
                                return summary
                            elif isinstance(parsed, dict):
                                keys = list(parsed.keys())
                                summary = f"ข้อมูลเป็น Object มีคีย์ทั้งหมด: {keys}\n"
                                summary += json.dumps({k: parsed[k] for k in keys[:3]}, ensure_ascii=False, indent=2)[:2000]
                                summary += "\n... (ข้อมูลถูกตัดทอนเนื่องจากมีขนาดใหญ่เกินไป)"
                                return summary
                        except Exception:
                            pass
                    return f"HTTP Status: {r.status_code}\n\n{response_text}"
            except Exception as e:
                return f"Error: เกิดข้อผิดพลาดในการยิง API: {str(e)}"
                
        elif name == "update_screen_sequence":
            screen_target = str(args.get("screen_target", "")).strip()
            sequence_id = str(args.get("sequence_id", "")).strip()
            user_confirmed = bool(args.get("user_confirmed", False))
            
            if not screen_target or not sequence_id:
                return "Error: กรุณาระบุชื่อหน้าจอ/MAC Address และ Sequence ID ที่ต้องการเปลี่ยน"
                
            digital_room_screens = {
                "A4AE125D42DE": "จอ 2 (จอซ้าย)",
                "A4AE125D4ACC": "จอ 3 (จอขวา)"
            }
            
            target_upper = screen_target.upper()
            mac_address = None
            screen_name = screen_target
            is_digital_room = False
            
            if target_upper in ["จอ 2", "จอ2", "จอซ้าย", "2", "LEFT", "A4AE125D42DE"]:
                mac_address = "A4AE125D42DE"
                screen_name = digital_room_screens[mac_address]
                is_digital_room = True
            elif target_upper in ["จอ 3", "จอ3", "จอขวา", "3", "RIGHT", "A4AE125D4ACC"]:
                mac_address = "A4AE125D4ACC"
                screen_name = digital_room_screens[mac_address]
                is_digital_room = True
            else:
                mac_address = target_upper
                if not is_digital_room and not user_confirmed:
                    return f"NEED_USER_CONFIRMATION: หน้าจอ '{screen_target}' ({mac_address}) เป็นจอนอกห้อง digital กรุณาถามผู้ใช้เพื่อขอคำยืนยันก่อนดำเนินการเปลี่ยน Sequence"
            
            user = get_env_var("USERNAME_TARGETR")
            password = get_env_var("PASSWORD_TARGETR")
            if not user or not password:
                return "Error: ไม่พบ USERNAME_TARGETR หรือ PASSWORD_TARGETR ใน .env"
                
            url = "https://stacks.targetr.net/api/bulk-data-update"
            payload = {
                "type": "screen",
                "ids": [mac_address],
                "data": {
                    "sequenceId": sequence_id
                }
            }
            
            try:
                async with httpx.AsyncClient() as client:
                    r = await client.post(
                        url,
                        json=payload,
                        auth=(user, password),
                        timeout=15.0
                    )
                    if r.status_code == 200:
                        return f"SUCCESS: อัปเดต Sequence ID ของ {screen_name} (MAC: {mac_address}) เป็น {sequence_id} เรียบร้อยแล้ว (HTTP 200 via Bulk Data Update API)"
                    else:
                        return f"Error: ยิง Bulk API ล้มเหลว (HTTP Status: {r.status_code}) - {r.text}"
            except Exception as e:
                return f"Error: เกิดข้อผิดพลาดในการเชื่อมต่อ TargetR API: {str(e)}"
                
        elif name == "trigger_screen_map":
            screen_target = str(args.get("screen_target", "")).strip()
            store_keyword = str(args.get("store_keyword", "")).strip()
            user_confirmed = bool(args.get("user_confirmed", False))
            
            if not screen_target or not store_keyword:
                return "Error: กรุณาระบุชื่อหน้าจอและชื่อสาขาห้างที่ต้องการเปิดแผนที่"
                
            digital_room_screens = {
                "A4AE125D42DE": "จอ 2 (จอซ้าย)",
                "A4AE125D4ACC": "จอ 3 (จอขวา)"
            }
            
            target_upper = screen_target.upper()
            mac_address = None
            screen_name = screen_target
            is_digital_room = False
            
            if target_upper in ["จอ 2", "จอ2", "จอซ้าย", "2", "LEFT", "A4AE125D42DE"]:
                mac_address = "A4AE125D42DE"
                screen_name = digital_room_screens[mac_address]
                is_digital_room = True
            elif target_upper in ["จอ 3", "จอ3", "จอขวา", "3", "RIGHT", "A4AE125D4ACC"]:
                mac_address = "A4AE125D4ACC"
                screen_name = digital_room_screens[mac_address]
                is_digital_room = True
            else:
                mac_address = target_upper
                if not is_digital_room and not user_confirmed:
                    return f"NEED_USER_CONFIRMATION: หน้าจอ '{screen_target}' ({mac_address}) เป็นจอนอกห้อง digital กรุณาถามผู้ใช้เพื่อขอคำยืนยันก่อนดำเนินการยิง Remote Trigger"
            
            user = get_env_var("USERNAME_TARGETR")
            password = get_env_var("PASSWORD_TARGETR")
            if not user or not password:
                return "Error: ไม่พบ USERNAME_TARGETR หรือ PASSWORD_TARGETR ใน .env"
                
            DASHBOARD_SEQUENCE_ID = "13822E1F644502"
            sequence_switched = False
            
            # Step 1: เช็ค Sequence ID ปัจจุบันของหน้าจอ
            try:
                async with httpx.AsyncClient() as client:
                    check_url = f"https://stacks.targetr.net/rest-api/v1/screens/{mac_address}"
                    check_res = await client.get(check_url, auth=(user, password), timeout=15.0)
                    if check_res.status_code == 200:
                        screen_info = check_res.json()
                        current_seq = screen_info.get("data", {}).get("sequenceId")
                        
                        # Step 2: หากไม่ใช่ Sequence Dashboard ให้สลับ Sequence แล้วหน่วงเวลา 10 วินาที
                        if current_seq != DASHBOARD_SEQUENCE_ID:
                            print(f"\n🔄 [Auto Switch Sequence] จอ {screen_name} กำลังเล่น Sequence '{current_seq}' -> สลับเป็น Dashboard ({DASHBOARD_SEQUENCE_ID})...")
                            bulk_url = "https://stacks.targetr.net/api/bulk-data-update"
                            bulk_payload = {
                                "type": "screen",
                                "ids": [mac_address],
                                "data": {"sequenceId": DASHBOARD_SEQUENCE_ID}
                            }
                            bulk_res = await client.post(bulk_url, json=bulk_payload, auth=(user, password), timeout=15.0)
                            if bulk_res.status_code == 200:
                                sequence_switched = True
                                print("⏳ กำลังหน่วงเวลา 10 วินาที เพื่อให้ Player สลับ Sequence หน้าเว็บ...")
                                await asyncio.sleep(10)
            except Exception as e:
                print(f"⚠️ ไม่สามารถตรวจสอบ Sequence ปัจจุบันได้: {e}")

            # Step 3: แมปรายชื่อสาขา
            stores = await fetch_and_cache_store_map(force_refresh=False)
            matched_store, candidates = match_store_name(store_keyword, stores)
            
            if not matched_store and not candidates:
                stores = await fetch_and_cache_store_map(force_refresh=True)
                matched_store, candidates = match_store_name(store_keyword, stores)
                
            if candidates:
                cand_str = ", ".join(candidates)
                return f"NEED_USER_CONFIRMATION: ไม่แน่ใจว่าคุณหมายถึงสาขาใดสำหรับคำว่า '{store_keyword}' กรุณาระบุเลือกสาขาที่คุณต้องการ: [{cand_str}]"
                
            if not matched_store:
                return f"Error: ไม่พบสาขาที่ตรงกับ '{store_keyword}' ในระบบ (กรุณาตรวจสอบชื่อสาขาอีกครั้ง)"
                
            import urllib.parse
            trigger_data = f"path_/map?store={matched_store}"
            encoded_trigger = urllib.parse.quote(trigger_data, safe='')
            
            trigger_url = f"https://stacks.targetr.net/api/screen-trigger/{mac_address}?name={encoded_trigger}"
            
            try:
                async with httpx.AsyncClient() as client:
                    r = await client.get(
                        trigger_url,
                        auth=(user, password),
                        timeout=15.0
                    )
                    if r.status_code == 200:
                        extra_msg = " (สลับ Sequence เป็น Dashboard และหน่วงเวลา 10 วินาทีแล้ว)" if sequence_switched else ""
                        return f"SUCCESS: ส่งคำสั่งเปิดแผนที่สาขา {matched_store} บน {screen_name} (MAC: {mac_address}) เรียบร้อยแล้ว{extra_msg} (HTTP 200 via Remote Trigger API)"
                    else:
                        return f"Error: ยิง Remote Trigger API ล้มเหลว (HTTP Status: {r.status_code}) - {r.text}"
            except Exception as e:
                return f"Error: เกิดข้อผิดพลาดในการเชื่อมต่อ TargetR API: {str(e)}"
                
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการรัน Tool {name}: {e}")
        return f"Error (โปรเซสหรือพอร์ตอาจจะปิดอยู่): {str(e)}"
    return "Unknown tool"

async def get_completion_with_fallback(messages, tools):
    """ฟังก์ชันสลับ AI Provider อัตโนมัติเมื่อเจอปัญหา Rate Limit หรือ Error (Groq -> DeepSeek -> OpenRouter -> Google Gemini)"""
    providers = [
        {
            "name": "Groq (Llama 3.3)",
            "key": get_env_var("GROQ_API_KEY"),
            "url": "https://api.groq.com/openai/v1/chat/completions",
            "model": "llama-3.3-70b-versatile"
        },
        {
            "name": "DeepSeek (V3)",
            "key": get_env_var("DEEPSEEK_API_KEY"),
            "url": "https://api.deepseek.com/chat/completions",
            "model": "deepseek-chat"
        },
        {
            "name": "OpenRouter (Free Tier)",
            "key": get_env_var("OPENROUTER_API_KEY"),
            "url": "https://openrouter.ai/api/v1/chat/completions",
            "model": "meta-llama/llama-3.3-70b-instruct:free"
        },
        {
            "name": "Google Gemini (2.5 Flash)",
            "key": get_env_var("NEXT_PUBLIC_GEMINI_API_KEY"),
            "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
            "model": "gemini-2.5-flash"
        }
    ]
    
    clean_messages = []
    for m in messages:
        if isinstance(m, dict):
            clean_messages.append(m)
        else:
            msg_dict = {"role": getattr(m, 'role', 'assistant'), "content": getattr(m, 'content', '') or ""}
            if hasattr(m, 'tool_calls') and m.tool_calls:
                msg_dict["tool_calls"] = [
                    {
                        "id": getattr(tc, 'id', 'call_dummy'),
                        "type": getattr(tc, 'type', 'function'),
                        "function": {
                            "name": tc.function.name if hasattr(tc.function, 'name') else tc.function['name'],
                            "arguments": tc.function.arguments if hasattr(tc.function, 'arguments') else tc.function['arguments']
                        }
                    } for tc in m.tool_calls
                ]
            clean_messages.append(msg_dict)

    payload = {
        "messages": clean_messages,
        "tools": tools,
        "tool_choice": "auto"
    }

    last_error = None
    for p in providers:
        if not p["key"]:
            continue
            
        payload["model"] = p["model"]
        headers = {
            "Authorization": f"Bearer {p['key']}",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(p["url"], json=payload, headers=headers, timeout=30.0)
                if r.status_code == 200:
                    data = r.json()
                    choice = data["choices"][0]["message"]
                    print(f"\n🤖 [ใช้ AI Provider: {p['name']}]")
                    return choice, p["name"]
                else:
                    err_msg = r.text[:150]
                    print(f"\n⚠️ [{p['name']}] ขัดข้อง (HTTP {r.status_code}: {err_msg}) -> กำลังสลับไปใช้ Provider ถัดไป...")
                    last_error = f"{p['name']} HTTP {r.status_code}"
        except Exception as e:
            print(f"\n⚠️ [{p['name']}] เกิดข้อผิดพลาด ({str(e)[:100]}) -> กำลังสลับไปใช้ Provider ถัดไป...")
            last_error = str(e)
            
    raise Exception(f"ไม่สามารถใช้งาน AI Provider ใดๆ ได้เลย (ความผิดพลาดล่าสุด: {last_error})")

# การลงทะเบียนโครงสร้างเครื่องมือสำหรับ Qwen (OpenAI Format)
tools = [
    {
        "type": "function",
        "function": {
            "name": "control_ptz",
            "description": "ควบคุมการขยับกล้อง Logitech MeetUp (pan, tilt, zoom)",
            "parameters": {
                "type": "object",
                "properties": {
                    "axis": {
                        "type": "string",
                        "enum": ["pan", "tilt", "zoom"],
                        "description": "แกนควบคุมที่ต้องการปรับ"
                    },
                    "value": {
                        "type": "number",
                        "description": "องศาหรือค่าที่ต้องการปรับ (เช่น 15.0 หรือ -15.0)"
                    }
                },
                "required": ["axis", "value"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "trigger_web_ui",
            "description": "ส่งคำสั่งควบคุมหน้าเว็บหลัก (เช่น toggle, start, stop, wakeAndGreet)",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["toggle", "start", "stop", "sendText", "wakeAndGreet"],
                        "description": "คำสั่งดำเนินการ"
                    },
                    "message": {
                        "type": "string",
                        "description": "ข้อความที่ต้องการส่งไปหน้าจอ"
                    }
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "manage_service",
            "description": "จัดการสถานะการทำงานของบริการย่อยเบื้องหลัง (เช่น camera-streamer, bluetooth-controller, hand-detection)",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_name": {
                        "type": "string",
                        "enum": ["camera-streamer", "bluetooth-controller", "hand-detection"],
                        "description": "ชื่อบริการที่ต้องการจัดการ"
                    },
                    "action": {
                        "type": "string",
                        "enum": ["start", "stop", "status"],
                        "description": "คำสั่งดำเนินการ"
                    }
                },
                "required": ["service_name", "action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_service_manual",
            "description": "ดึงคู่มือการใช้งานและ endpoints อย่างละเอียดของบริการย่อย เพื่อนำไปอ้างอิงวิธีการเรียกใช้งาน",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_name": {
                        "type": "string",
                        "enum": ["camera-streamer", "bluetooth-controller", "hand-detection", "web-speaker"],
                        "description": "ชื่อบริการที่ต้องการขอดึงคู่มือ"
                    }
                },
                "required": ["service_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_services",
            "description": "แสดงรายชื่อบริการย่อยทั้งหมดในระบบและสถานะการรันปัจจุบันเพื่อตรวจสอบความพร้อมใช้งาน",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_project_file",
            "description": "อ่านเนื้อหาภายในไฟล์สคริปต์หรือไฟล์เอกสารที่ต้องการในโปรเจกต์",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "พาธของไฟล์ที่ต้องการอ่าน (เช่น 'tests/test_qwen_tools.py' หรือ 'project.md')"
                    }
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_vault_file",
            "description": "อ่านเนื้อหาไฟล์ในถังความจำระยะยาว (Google Drive)",
            "parameters": {
                "type": "object",
                "properties": {
                    "vault_type": {
                        "type": "string",
                        "enum": ["global", "actbotkung"],
                        "description": "ประเภทถังความจำ (global = ถังส่วนกลางของ Jarvis, actbotkung = ถังเฉพาะของโปรเจกต์ actbotkung)"
                    },
                    "file_path": {
                        "type": "string",
                        "description": "พาธของไฟล์ที่ต้องการอ่าน สัมพัทธ์กับถังความจำ เช่น '00_INDEX.md' หรือ 'ID&PSS/00_ID&PSS_INDEX.md'"
                    }
                },
                "required": ["vault_type", "file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_vault_files",
            "description": "แสดงรายชื่อไฟล์และโฟลเดอร์ย่อยในถังความจำระยะยาว (Google Drive) เพื่อให้ทราบว่ามีไฟล์อะไรให้ใช้งานบ้าง",
            "parameters": {
                "type": "object",
                "properties": {
                    "vault_type": {
                        "type": "string",
                        "enum": ["global", "actbotkung"],
                        "description": "ประเภทถังความจำ"
                    },
                    "subdir": {
                        "type": "string",
                        "description": "โฟลเดอร์ย่อยที่ต้องการตรวจสอบ (ปล่อยว่างหากต้องการตรวจสอบที่ root เช่น '', 'ID&PSS', 'TARGET_R/DataModel')"
                    }
                },
                "required": ["vault_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_vault_content",
            "description": "ค้นหาคำสำคัญ (keyword) หรือข้อความในเนื้อหาของไฟล์ทั้งหมดในถังความจำระยะยาว (Google Drive)",
            "parameters": {
                "type": "object",
                "properties": {
                    "vault_type": {
                        "type": "string",
                        "enum": ["global", "actbotkung"],
                        "description": "ประเภทถังความจำ"
                    },
                    "query": {
                        "type": "string",
                        "description": "คำสำคัญหรือข้อความที่ต้องการค้นหา (เช่น 'dpop', 'api', 'pusher')"
                    }
                },
                "required": ["vault_type", "query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "call_http_api",
            "description": "ยิงคำขอ HTTP API (GET, POST, PUT, DELETE) ไปยังเว็บเซิร์ฟเวอร์ภายนอกเพื่อดึงหรือบันทึกข้อมูล [ข้อบังคับเหล็ก: ห้ามเรียกใช้เครื่องมือนี้เด็ดขาด หากยังไม่ได้ใช้ search_vault_content หรือ read_vault_file เพื่อค้นหาและอ่านคู่มือ API ในถังความจำระยะยาวก่อนอย่างน้อย 1 ครั้ง]",
            "parameters": {
                "type": "object",
                "properties": {
                    "method": {
                        "type": "string",
                        "enum": ["GET", "POST", "PUT", "DELETE"],
                        "description": "HTTP Method"
                    },
                    "url": {
                        "type": "string",
                        "description": "URL ปลายทางที่ต้องการส่งคำขอ (ต้องได้มาจากโครงสร้าง API ที่เปิดอ่านในถังความจำ)"
                    },
                    "headers": {
                        "type": "object",
                        "description": "HTTP Headers เพิ่มเติม (ส่งเป็น Key-Value Dict)"
                    },
                    "params": {
                        "type": "object",
                        "description": "Query Parameters (สำหรับใส่ใน URL)"
                    },
                    "json_data": {
                        "type": "object",
                        "description": "JSON payload ใน Request Body (สำหรับ POST/PUT)"
                    },
                    "auth": {
                        "type": "object",
                        "description": "การยืนยันตัวตน (Authentication)",
                        "properties": {
                            "type": {
                                "type": "string",
                                "enum": ["basic", "bearer", "env_basic", "env_bearer", "none"],
                                "description": "ประเภท Auth. หากใช้ 'env_basic' ให้ระบุชื่อตัวแปรใน .env ในฟิลด์ value แยกด้วยจุลภาค (เช่น USERNAME_TARGETR,PASSWORD_TARGETR)"
                            },
                            "value": {
                                "type": "string",
                                "description": "ค่าของ Auth หรือชื่อตัวแปรสิ่งแวดล้อมใน .env"
                            }
                        },
                        "required": ["type"]
                    },
                    "save_file_path": {
                        "type": "string",
                        "description": "ชื่อไฟล์หรือพาธที่ต้องการบันทึกผลลัพธ์ลงเครื่อง (เช่น 'screens_11107.json' หรือ 'tests/screens_response.json') หากส่งมา ผลลัพธ์จะถูกเขียนลงไฟล์นี้และแจ้งเฉพาะชื่อไฟล์ตอบกลับไป"
                    }
                },
                "required": ["method", "url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_screen_sequence",
            "description": "เครื่องมือสำเร็จรูปสำหรับเปลี่ยน/อัปเดต Sequence ID ของหน้าจอ TargetR ด้วย Bulk Data Update API (ปลอดภัย ไม่เขียนทับข้อมูลเดิม)",
            "parameters": {
                "type": "object",
                "properties": {
                    "screen_target": {
                        "type": "string",
                        "description": "ระบุชื่อจอ เช่น 'จอ 2', 'จอซ้าย', 'จอ 3', 'จอขวา' หรือ MAC Address / screenId (เช่น 'A4AE125D42DE')"
                    },
                    "sequence_id": {
                        "type": "string",
                        "description": "Sequence ID ใหม่ที่ต้องการเปลี่ยนให้หน้าจอเล่น (เช่น '1394D9631B6E41')"
                    },
                    "user_confirmed": {
                        "type": "boolean",
                        "description": "ส่งเป็น true หากเป็นจอนอกห้อง digital และได้รับการยืนยันจากผู้ใช้แล้ว"
                    }
                },
                "required": ["screen_target", "sequence_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "trigger_screen_map",
            "description": "เครื่องมือเปิด/เปลี่ยนหน้าเว็บแผนที่ห้างบนหน้าจอแบบเรียลไทม์ (Remote Trigger API) พร้อมระบบ Caching ค้นหารายชื่อสาขาอัตโนมัติ",
            "parameters": {
                "type": "object",
                "properties": {
                    "screen_target": {
                        "type": "string",
                        "description": "ชื่อจอ เช่น 'จอ 2', 'จอซ้าย', 'จอ 3', 'จอขวา' หรือ MAC Address"
                    },
                    "store_keyword": {
                        "type": "string",
                        "description": "ชื่อสาขาห้างภาษาไทยหรืออังกฤษ เช่น 'รังสิต', 'ชิดลม', 'ลาดพร้าว', 'TopsDigital-Rangsit'"
                    },
                    "user_confirmed": {
                        "type": "boolean",
                        "description": "ส่งเป็น true หากเป็นจอนอกห้อง digital และได้รับการยืนยันจากผู้ใช้แล้ว"
                    }
                },
                "required": ["screen_target", "store_keyword"]
            }
        }
    }
]

SYSTEM_INSTRUCTION = (
    "คุณคือ Jarvis AI ผู้ช่วยอัจฉริยะประจำห้อง digital (Orchestrator Brain)\n\n"

    "## ข้อมูลอุปกรณ์ในห้อง digital\n"
    "- ในห้อง digital มี Smart TV Sharp 2 เครื่อง ติดตั้งแอป dsloader (หรือ TargetR):\n"
    "  1. จอซ้าย (จอ 2): screenId / MAC Address = A4AE125D42DE\n"
    "  2. จอขวา (จอ 3): screenId / MAC Address = A4AE125D4ACC\n\n"

    "## กฎสิทธิ์และการควบคุม (Security & Permission Rules)\n"
    "1. สิทธิ์จอบริเวณห้อง digital: จอซ้าย (A4AE125D42DE) และ จอขวา (A4AE125D4ACC) คุณมีสิทธิ์สั่งอัปเดต/เปลี่ยน Sequence ได้ทันทีโดยไม่ต้องรอถามผู้ใช้ยืนยัน\n"
    "2. สิทธิ์จอนอกห้อง: หากคำสั่งเจาะจงไปที่จออื่นๆ นอกเหนือจาก 2 จอนี้ คุณต้องหยุดและถามผู้ใช้เพื่อขอคำยืนยันก่อนดำเนินการอัปเดตทุกครั้ง\n\n"

    "## กฎพฤติกรรมหลัก\n"
    "1. [กฎเหล็กการสืบค้นข้อมูลระยะยาว (Vault-First & Index Tracking)]:\n"
    "   - หากผู้ใช้ถามถึงข้อมูลความรู้ บันทึก หรือปัญหา ให้เริ่มต้นเรียกใช้ `read_vault_file` บนไฟล์ '00_INDEX.md' ของถังความจำ 'actbotkung' หรือ 'global' เสมอ เพื่อดูสารบัญหลัก\n"
    "   - ห้ามเดาพาธโฟลเดอร์ หรือเดาชื่อไฟล์ขึ้นมาเองเด็ดขาด! ให้ไต่ตามลิงก์ (เช่น [[Folder/00_FOLDER_INDEX]]) ที่ปรากฏในไฟล์ดัชนีของแต่ละระดับเพื่อหาไฟล์โน้ตเป้าหมาย\n"
    "   - หากต้องการค้นหาความรู้แบบกว้างๆ ให้เรียกใช้ `search_vault_content` เพื่อหาไฟล์ที่เกี่ยวข้อง แทนการเดาชื่อไฟล์\n"
    "   - กฎการตั้งชื่อไฟล์ในคลังความจำ: ไฟล์โน้ตจะใช้เครื่องหมาย '_' เสมอ (เช่น `8thWall_XR8_Troubleshooting.md`) ส่วน '-' จะใช้เฉพาะกับชื่อโฟลเดอร์หรือไฟล์ asset\n"
    "2. [กฎเหล็กตรวจสอบก่อนเรียก API]: ก่อนจะเรียกใช้เครื่องมือ `call_http_api` หรือส่งคำขอ API ภายนอก คุณต้องอ่านคู่มือและตรวจสอบโครงสร้าง API ในถังความจำระยะยาวก่อนเสมออย่างน้อย 1 ครั้ง\n"
    "3. ห้ามเปิดหรือรันบริการต่างๆ เล่นๆ เว้นแต่ผู้ใช้สั่งโดยตรง หรือเครื่องมือที่จำเป็นเกิด Connection Refused\n"
    "4. เมื่อบรรลุเป้าหมายแล้ว (เช่น บันทึกไฟล์หรือสั่งยิง API สำเร็จ) หยุดเรียกใช้เครื่องมืออื่นทันที และรายงานผลให้ผู้ใช้\n"
    "5. สื่อสารเป็นภาษาไทยหลัก อังกฤษเฉพาะศัพท์เทคนิค ห้ามตอบเป็นภาษาจีนหรือภาษาอื่นปน ตอบสั้นๆ กระชับ\n\n"

    "## เครื่องมือที่มี\n"
    "- trigger_screen_map: เครื่องมือเปิด/เปลี่ยนหน้าเว็บแผนที่สาขาห้างบนหน้าจอแบบเรียลไทม์ (Remote Trigger API) พร้อมระบบ Caching ค้นหารายชื่อสาขาอัตโนมัติ\n"
    "- update_screen_sequence: เครื่องมือสำเร็จรูปสำหรับเปลี่ยน Sequence ของหน้าจอ (ใช้ Bulk API ปลอดภัย มีระบบตรวจสิทธิ์จอบริเวณห้อง digital อัตโนมัติ)\n"
    "- call_http_api: ยิง HTTP Request (GET/POST/PUT/DELETE) รองรับ auth แบบ env_basic/env_bearer จาก .env\n"
    "- search_vault_content: ค้นหาคีย์เวิร์ดในถังความจำ Obsidian\n"
    "- read_vault_file: เปิดอ่านไฟล์ในถังความจำ\n"
    "- list_vault_files: แสดงรายชื่อไฟล์ในถังความจำ\n"
    "- control_ptz / manage_service / list_services / get_service_manual: ควบคุมบริการภายในเครื่อง\n\n"

    "## โครงสร้างโปรเจกต์\n"
    "- services/camera-streamer : Flask Server ควบคุมกล้อง (Port 5000)\n"
    "- services/hand-detection : ตรวจจับมือด้วย MediaPipe\n"
    "- services/bluetooth-controller : ควบคุมทีวีผ่าน ESP32-C3 (Port 5001)\n"
    "- web-speaker : Core Brain Web UI Next.js (Port 3000)\n"
)

async def main():
    if not groq_api_key:
        print("❌ ไม่พบ GROQ_API_KEY ในไฟล์ .env")
        sys.exit(1)
        
    client = Groq(api_key=groq_api_key)
    print("✅ เชื่อมต่อกับ Groq API (Qwen Model) สำเร็จ!")
    print("💡 พิมพ์คุยกับ Qwen ได้เลย เช่น 'หันกล้องไปทางซ้าย 10 องศา', 'ขอดูคู่มือของกล้อง', 'เช็คสถานะเซอร์วิส' (พิมพ์ exit เพื่อออก)")
    
    # เก็บประวัติการคุยเพื่อให้รักษา Context ได้
    conversation_history = [
        {"role": "system", "content": SYSTEM_INSTRUCTION}
    ]
    
    while True:
        try:
            user_msg = input("\n💬 พิมพ์คำสั่ง: ")
            if user_msg.strip().lower() == 'exit':
                print("👋 กำลังปิดโปรแกรม...")
                break
                
            if not user_msg.strip():
                continue
                
            conversation_history.append({"role": "user", "content": user_msg})
            
            # ลูปสำหรับรัน Tool Call (วนลูปได้สูงสุด 5 ครั้งเพื่อตอบสนองต่อผลลัพธ์ของเครื่องมือย่อย)
            for step in range(5):
                print("⏳ AI กำลังคิดวิเคราะห์...", end="\r")
                
                try:
                    response_message, provider_name = await get_completion_with_fallback(conversation_history, tools)
                except Exception as fallback_err:
                    print(f"\n❌ {fallback_err}")
                    break
                
                tool_calls = response_message.get("tool_calls") if isinstance(response_message, dict) else getattr(response_message, "tool_calls", None)
                msg_content = response_message.get("content") if isinstance(response_message, dict) else getattr(response_message, "content", "")
                xml_tool = parse_xml_tool_call(msg_content)
                
                if tool_calls:
                    conversation_history.append(response_message)
                    
                    for tool_call in tool_calls:
                        if isinstance(tool_call, dict):
                            name = tool_call["function"]["name"]
                            args_raw = tool_call["function"]["arguments"]
                            call_id = tool_call.get("id", "call_dummy")
                        else:
                            name = tool_call.function.name
                            args_raw = tool_call.function.arguments
                            call_id = tool_call.id
                            
                        args = json.loads(args_raw) if isinstance(args_raw, str) else args_raw
                        
                        print(f"\n🔧 [{provider_name}] สั่งเรียกใช้ Tool: {name} (Args: {args})")
                        
                        # รันคำสั่งจริงในเครื่องคอมพิวเตอร์
                        result = await execute_tool(name, args)
                        
                        # แสดงผลลัพธ์ของฟังก์ชันเพื่อช่วยในการตรวจสอบ
                        print(f"📥 ผลลัพธ์จาก Tool: {result[:500]}..." if len(result) > 500 else f"📥 ผลลัพธ์จาก Tool: {result}")
                        
                        # บันทึกผลลัพธ์ลงประวัติเพื่อให้โมเดลนำไปตัดสินใจต่อ
                        conversation_history.append({
                            "role": "tool",
                            "tool_call_id": call_id,
                            "name": name,
                            "content": result
                        })
                        
                        # หากผลลัพธ์สำเร็จ หรือต้องขอคำยืนยัน ให้แสดงผลลัพธ์และจบงานทันที
                        if result.startswith("SUCCESS:") or result.startswith("NEED_USER_CONFIRMATION:"):
                            print(f"\n🤖 Qwen: {result}")
                            conversation_history.append({"role": "assistant", "content": result})
                            should_exit_step = True
                            break
                    
                    if 'should_exit_step' in locals() and should_exit_step:
                        del should_exit_step
                        break
                    continue
                elif xml_tool:
                    name = xml_tool["name"]
                    args = xml_tool["args"]
                    print(f"\n🔧 [XML Tool Call Detected] AI สั่งเรียกใช้: {name} (Args: {args})")
                    
                    # ใส่ข้อความดิบเข้าไปในประวัติ
                    conversation_history.append(response_message)
                    
                    # รันคำสั่งจริงในเครื่องคอมพิวเตอร์
                    result = await execute_tool(name, args)
                    
                    # แสดงผลลัพธ์ของฟังก์ชันเพื่อช่วยในการตรวจสอบ
                    print(f"📥 ผลลัพธ์จาก Tool (XML): {result[:500]}..." if len(result) > 500 else f"📥 ผลลัพธ์จาก Tool (XML): {result}")
                    
                    # บันทึกผลลัพธ์กลับในฐานะ user เพื่อหลีกเลี่ยง API Error จาก dummy tool call id
                    conversation_history.append({
                        "role": "user",
                        "content": f"[ระบบทำงานเสร็จสิ้น: ผลลัพธ์จากการเรียกฟังก์ชัน {name} คือดังนี้]\n{result}\n\nกรุณาประมวลผลข้อมูลนี้เพื่อตอบคำถามของผู้ใช้"
                    })
                    
                    if result.startswith("SUCCESS:") or result.startswith("NEED_USER_CONFIRMATION:"):
                        print(f"\n🤖 Qwen: {result}")
                        conversation_history.append({"role": "assistant", "content": result})
                        break
                    continue
                else:
                    # หากไม่มีการเรียกใช้ Tool แสดงว่าได้คำตอบสุดท้ายแล้ว
                    answer = response_message.get("content") if isinstance(response_message, dict) else getattr(response_message, "content", "")
                    print(f"\n🤖 Qwen: {answer}")
                    # ใส่คำตอบลงประวัติเพื่อการสนทนาต่อเนื่อง
                    conversation_history.append({"role": "assistant", "content": answer})
                    break
                    
        except KeyboardInterrupt:
            print("\n👋 ปิดโปรแกรมทดสอบ.")
            break
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "rate_limit" in err_str:
                print(f"\n⚠️ Rate Limit: โควต้า Token ของ Groq หมดชั่วคราว กรุณารอสักครู่แล้วลองใหม่")
                # ไม่ break เพื่อให้ user ลองพิมพ์คำสั่งใหม่ได้
                continue
            print(f"\n❌ เกิดข้อผิดพลาด: {e}")
            # ไม่ break เพื่อให้ลองพิมพ์คำสั่งใหม่ได้
            continue
            
    # ปิดบริการย่อยทั้งหมดที่เปิดขึ้นมาระหว่างเทส
    await ms.cleanup_all()

if __name__ == "__main__":
    asyncio.run(main())
