import requests
import base64
import time
import json
import os
import argparse

class DormitoryClient:
    def __init__(self):
        self.session = requests.Session()
        # 设置一些通用的请求头，模拟浏览器行为
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://hq.uestc.edu.cn',
            'Referer': 'https://hq.uestc.edu.cn/dormitory/dormitoryOnlineChooseRoom'
        })

    def set_student_attrs(self, student: dict):
        """仅将字典中存在的键设置为当前实例的属性，不额外增加无关字段。"""
        for key, value in (student or {}).items():
            setattr(self, key, value)

    def login(self, username=None, password=None, random_code=''):
        """登录并保持会话状态"""
        # 在程序运行前输出期待宿舍和舍友信息
        building = getattr(self, 'building', None)
        room = getattr(self, 'room', None)
        preferred_roommates = getattr(self, 'preferred_roommates', None)
        print("\n\n期望宿舍：", f"{building}{room}" if building and room else "未设置")
        print("期望舍友：", "、".join(preferred_roommates) if preferred_roommates else "未设置")

        # 优先使用传入参数；未提供则回退到实例属性
        if username is None:
            username = getattr(self, 'username', None)
        if password is None:
            password = getattr(self, 'password', None)
        if not username or not password:
            print("用户名或密码缺失，请在调用 login 时传入，或先通过 set_student_attrs 设置 'username' 与 'password'")
            return False
        # 对密码进行base64编码
        password_b64 = base64.b64encode(password.encode('utf-8')).decode('utf-8')
        url = 'https://hq.uestc.edu.cn/dormitory/dormitoryOnlineChooseRoom/dormitoryWebLogin'
        # url = "https://baidu.com"
        data = {
            'username': username,
            'password': password_b64,
            'randomCode': random_code
        }
        try:
            response = self.session.post(url, data=data)
            # print("登录响应状态码:", response.status_code)
            # print("登录响应内容:", response.text)   
            
            # 检查登录是否成功
            if response.status_code == 200:
                # 根据实际响应内容判断登录是否成功
                if 'success' in response.text.lower() or '"login":true' in response.text:
                    # print("登录响应内容:")
                    # print(response.text)
                    print("登录成功！会话已保持")
                    return True
                else:
                    print("登录可能失败，请检查响应内容")
                    print(response.text)
                    return False
            else:
                print(f"登录请求失败，状态码: {response.status_code}")
                return False
                
        except requests.Timeout:
            print("登录请求超时（超过10秒未响应）")
            return False
        except Exception as e:
            print("登录请求失败:", e)
            return False

    def get_available_rooms(self):
        """
        支持 self.room 为列表：按顺序尝试每个房间号；
        若前一个房间无可选床位则自动尝试下一个；
        一旦发现可选床位则自动选择第一个并返回结果。
        """
        try:
            url = 'https://hq.uestc.edu.cn/dormitory/dormitoryOnlineChooseRoom/getWebRoomList'
            # 兼容字符串与列表
            rooms_to_try = self.room if isinstance(self.room, list) else [self.room]
            if not rooms_to_try or all(not r for r in rooms_to_try):
                print("未设置目标房间 room，请在实例属性中提供，例如 ['328','330']")
                return None

            building = getattr(self, 'building', None)

            for target_room in rooms_to_try:
                if not target_room:
                    continue
                print(f"\n开始查询房间: {target_room}")
                data = {
                    'room_num': target_room,
                    'page': 0,
                    'limit': 18
                }
                response = self.session.post(url, data=data)
                # print("获取房间信息响应状态码:", response.status_code)
                if response.status_code != 200:
                    print(f"获取房间信息失败，状态码: {response.status_code}")
                    continue

                res_json = response.json()
                if not res_json.get('flag'):
                    print(f"查询房间 {target_room} 失败，flag 为 False")
                    continue

                room_list = res_json.get('data', [])
                if not room_list:
                    print(f"未查询到任何房间（room_num={target_room}）")
                    continue

                print("查询到的房间列表：")
                for idx, room in enumerate(room_list):
                    room_name = f"{room.get('showFloor', '')}{room.get('room_num', '')}"
                    number = room.get('number', 0)
                    num = room.get('num', 0)
                    room_id = room.get('room_id')
                    sex = room.get('sex')
                    sex_str = "男寝" if sex == 1 else "女寝"
                    info = f"{idx+1}. {room_name}（{number}人寝，空余床位：{num}，{sex_str}，room_id: {room_id}）"
                    print(info)

                # 优先根据 building + 精确房间号匹配，否则退回到 building 前缀匹配，否则用第一条
                matched_room = None
                for room in room_list:
                    room_name = f"{room.get('showFloor', '')}{room.get('room_num', '')}"
                    if building and building in room_name and str(room.get('room_num','')).strip() == str(target_room):
                        matched_room = room
                        break
                if not matched_room and building:
                    for room in room_list:
                        room_name = f"{room.get('showFloor', '')}{room.get('room_num', '')}"
                        if building in room_name:
                            matched_room = room
                            break
                if not matched_room:
                    matched_room = room_list[0]

                print(f"已匹配到房间：{matched_room.get('showFloor','')}{matched_room.get('room_num','')}（room_id: {matched_room.get('room_id')}）")
                room_id = matched_room.get('room_id')
                print(f"正在获取房间 {matched_room.get('showFloor','')}{matched_room.get('room_num','')} 的床位信息...")
                bed_info = self.get_bed_list(room_id)
                if not bed_info or not bed_info.get("flag"):
                    print("获取床位信息失败，继续尝试下一个房间")
                    continue

                beds = bed_info.get("data", [])
                print("\n床位信息如下：")
                selectable_beds = []
                occupied_names = []
                for idx, bed in enumerate(beds):
                    bed_num = bed.get("bed_num", idx+1)
                    name = bed.get("name")
                    status = bed.get("status")  # 1为可选，其他为不可选
                    show_name = name if name else "空"
                    status_str = "可选" if status == 1 else "不可选"
                    print(f"{idx+1}. 床位号: {bed_num} | 姓名: {show_name} | 状态: {status_str}")
                    if name:
                        occupied_names.append(str(name))
                    if status == 1:
                        selectable_beds.append({
                            "display_idx": idx+1,
                            "bed_id": bed.get("bed_id"),
                            "choose_bed_auth_counsellor_id": bed.get("choose_bed_auth_counsellor_id"),
                            "bed_num": bed_num
                        })

                if not selectable_beds:
                    print(f"房间 {target_room} 无可选床位，继续尝试下一个房间…")
                    continue

                preferred = getattr(self, 'preferred_roommates', []) or []
                preferred = [str(x) for x in preferred]

                # 舍友匹配逻辑
                if len(occupied_names) == 0:
                    print("该房间当前无人已选（空房），直接选择可用床位。")
                else:
                    # 只要房内已有同学在期望名单中，就继续；否则跳过该房间
                    has_preferred_inside = any(name in preferred for name in occupied_names)
                    if has_preferred_inside or len(preferred) == 0:
                        print("检测到期望舍友已在目标房间，继续选择床位。匹配到：", 
                              ", ".join([n for n in occupied_names if n in preferred]))
                    else:
                        print("房间已有同学选择，但不在期望舍友名单中，尝试下一个房间。")
                        continue

                print("\n可选床位列表：")
                for i, bed in enumerate(selectable_beds):
                    print(f"{i+1}. 床位号: {bed['bed_num']}")
                # 自动选择第一个可选床位
                bed_info_selected = selectable_beds[0]
                print(f"自动选择第一个可选床位，床位号: {bed_info_selected['bed_num']} ...")
                result = self.choose_room(
                    bed_info_selected["bed_id"],
                    bed_info_selected["choose_bed_auth_counsellor_id"],
                    getattr(self, 'captcha_file', 'captcha.jpg')
                )
                print("选择床位结果：", result)
                return result

            print("目标房间列表均无可选床位。")
            return None
        except Exception as e:
            print("获取房间信息失败:", e)
            return None
    
    def get_bed_list(self, room_id):
        """
        获取指定房间的床位信息，POST请求
        :param room_id: 房间ID
        :return: 返回床位信息的json数据，或None
        """
        try:
            url = 'https://hq.uestc.edu.cn/dormitory/dormitoryOnlineChooseRoom/getNewBedList'
            data = {'room_id': room_id}
            response = self.session.post(url, data=data)
            # print("获取床位信息响应状态码:", response.status_code)
            # print("床位信息响应内容:")
            # print(response.text)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"获取床位信息失败，状态码: {response.status_code}")
                return None
        except Exception as e:
            print("获取床位信息失败:", e)
            return None

    def choose_room(self, bed_id, choose_bed_auth_counsellor_id):
        """
        选择床位
        :param bed_id: 床位ID（从get_bed_list返回的数据中获取）
        :param choose_bed_auth_counsellor_id: ID（从get_bed_list返回的数据中获取）
        :return: 返回接口响应的json数据
        """
        try:
            url = 'https://hq.uestc.edu.cn/dormitory/dormitoryOnlineChooseRoom/studentChooseBed'
            data = {
                'bed_id': bed_id,
                'choose_bed_auth_counsellor_id': choose_bed_auth_counsellor_id,
                'code': ""
            }
            response = self.session.post(url, data=data)
            # print("选择床位响应状态码:", response.status_code)
            # print("选择床位响应内容:")
            # print(response.text)
            if response.status_code == 200:
                res_json = response.json()
                # print(res_json)
                if res_json.get("flag") and res_json.get("type") == 0:
                    print("恭喜同学成功抢到该床位！")
                else:
                    print("未能成功抢到床位，返回信息：", res_json.get("message", "无"))
                return res_json
            else:
                print(f"选择床位请求失败，状态码: {response.status_code}")
                return None
        except Exception as e:
            print("选择床位失败:", e)
            return None


# 全局学生信息字典，每个学生包含用户名、密码、目标楼栋号、房间号、期望舍友列
# 从指定 json 文件中读取学生信息
def load_students_info(json_path="test.json"):
    if not os.path.exists(json_path):
        print(f"未找到学生信息文件: {json_path}")
        return {}
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

def parse_args():
    parser = argparse.ArgumentParser(
        description="宿舍选房命令行工具",
        epilog="示例用法：\n"
               "  python choose_room.py --name1 person1 --name2 pesrson2 --json config.json\n"
               "参数说明：\n"
               "  --name1    第一位学生在json中的键名（必填）\n"
               "  --name2    第二位学生在json中的键名（必填）\n"
               "两者相同时，即只为一个学生选房，不同时，先为前者选房，再为后者选房\n"
               "  --json     学生信息json文件路径，默认 config.json\n"
               "  -t  登录失败后重试每次间隔时间，默认60s\n",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--name1", required=True, help="第一位学生在json中的键名")
    parser.add_argument("--name2", help="第二位学生在json中的键名")
    parser.add_argument("--json", default="config.json", help="学生信息json文件路径，默认 config.json")
    parser.add_argument("-t", default=60, help="每次间隔时间，默认60s")
    return parser.parse_args()


def main():
    print("==========欢迎使用宿舍选房命令行工具！==========")
    print("==========如需帮助，请加参数 -h 查看详细用法示例。==========\n")
    args = parse_args()
    all_students = load_students_info(args.json)
    if not all_students:
        print("学生信息为空，退出")
        return

    selected_keys = []
    if not args.name2 or args.name1 == args.name2:
        selected_keys.append(args.name1)
    else:
        for key in [args.name1, args.name2]:
            if key in all_students:
                selected_keys.append(key)
            else:
                print(f"未在 {args.json} 中找到学生: {key}")

    if not selected_keys:
        print("未找到任何匹配的学生配置，退出")
        return

    # 为选定学生依次执行
    for key in selected_keys:
        student = all_students[key]
        client = DormitoryClient()
        client.set_student_attrs(student)

        # 登录失败则重试，直到成功
        while True:
            if client.login():
                print(f"\n=== {key}登录成功，开始后续操作 ===\n")
                break
            else:
                print(f"登录失败，{args.t}s后重试...")
                time.sleep(args.t)

        print("\n=== 获取可用房间 ===\n")
        client.get_available_rooms()


if __name__ == '__main__':
    main()
