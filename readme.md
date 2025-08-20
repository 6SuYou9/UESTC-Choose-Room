# 电子科技大学宿舍选房自动化工具
# 配置
1. 在`config.json`中增加自己信息，一个人一个键值对，填入学号密码和楼栋号，宿舍列表优先级为从左到右，如下即先选328，再选330。
2. 舍友列表置空的话，只要目标房间有空床即自动选一个空床位。若非空，示例：当328已有一名学生选房但不是你舍友(即已选学生姓名不是你舍友名字)时会自动选下一个宿舍，即330，但若该学生是你舍友，则会选328宿舍的空床位。
```json
{
    "xxx": {
        "username": "学号",
        "password": "密码",
        "building": "20栋",
        "room": ["328","330"],
        "preferred_roommates": ["舍友名(真名汉字)"]
    },
    "yyy": {
        "username": "学号",
        "password": "密码",
        "building": "20栋",
        "room": ["328","330"],
        "preferred_roommates": ["舍友名(真名汉字)"]
    }
}
```
3. 环境配置
```bash
pip install requests -i https://pypi.tuna.tsinghua.edu.cn/simple
```
# 使用方式
--name1和--name2的参数都是config.json中的键，对应一个人
1. 简单使用：给xxx抢json中指定楼栋的宿舍
```bash
python .\choose_room.py --name1 xxx
```
2. 使用：给xxx抢json中指定楼栋的宿舍后，给yyy抢，可以匹配舍友，即若json中两人舍友互相填选对方姓名，即可选同一宿舍。若填的宿舍列表均不符合条件则不抢。
```bash
python .\choose_room.py --name1 xxx --name2 yyy
```

# 参数说明
* --name1    第一位学生在json中的键名（必填）
* --name2    第二位学生在json中的键名（必填）
* 注意：两者相同时，即只为一个学生选房，不同时，先为前者选房，再为后者选房
* --json     学生信息json文件路径，默认 config.json
* -t  登录失败后重试每次间隔时间，默认60s   建议不要太快，不然可能会被封ip

# 链接
本项目地址：https://github.com/6SuYou9/UESTC-Choose-Room