# <a simple script that track a list of tapebox>
# Tapebox
# Copyright (C) 2023 Chesium
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses/.

from json import load, loads, dump
from requests import request
from copy import deepcopy
from datetime import datetime
from os import path

urlPrefix = "https://apiv4.tapechat.net/unuser/getQuestionFromUser/"

ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.10240"

# 系统代理
pr = {
    'http': '127.0.0.1:7890',
    'https': '127.0.0.1:7890'
}

# * 若出现错误 Can't connect to HTTPS URL because the SSL module is not available.
# * 找到 libcrypto-1_1-x64.dll 和 libssl-1_1-x64.dll
# * 复制到 <..>\Anaconda3\DLLs
# * 参考：https://blog.csdn.net/Sky_Tree_Delivery/article/details/109078288

# 下载指定链接
def dl(link):
    # try:                                                                    # 若未使用系统代理
    #     res = request('GET', link, headers={'User-agent': ua}, proxies=pr)  # 可删去这三行
    # except:                                                                 #
    res = request('GET', link, headers={'User-agent': ua})
    return res.text

# 将unix时间戳转换为特定格式
def ft(st):
    return [st, datetime.fromtimestamp(st).strftime("%Y-%m-%d %H:%M:%S")]

# 程序入口
if __name__ == '__main__':
    # 输出目录，可自行设置（采用相对路径）
    prefix            = '/.dist'
    boxid_path        = prefix+'/boxid.json'
    alreadyReadL_path = prefix+"/al.json"
    newAns_path       = prefix+"/new.json"
    history_path      = prefix+"/his.json"

    # 读入归档文件
    r = path.dirname(__file__)
    with open(r+boxid_path, 'r', encoding='utf8') as f:
        boxes = load(f)
    with open(r+newAns_path, 'r', encoding='utf8') as f:
        newAns = load(f)
    with open(r+alreadyReadL_path, 'r', encoding='utf8') as f:
        alReadId = load(f)
    with open(r+history_path, 'r', encoding='utf8') as f:
        history = load(f)

    # 遍历新消息Json文件，将 already=1 的项删除，并将其 id 添加至 alReadId 中
    newdata_t = deepcopy(newAns)
    for name, person in newAns.items():
        for id, msg in person.items():
            if msg["already"] == 1:
                alReadId.append(id)
                del newdata_t[name][id]
    newAns = deepcopy(newdata_t)

    # 下载每个提问箱的 json 文件，将 id 不在 alReadId 中的添加至 newAns 中 
    i = 1
    for person in boxes:
        print("%s:[%d/%d]" % (person["name"], i, len(boxes)))
        i += 1
        # (uninited )init personal data
        if person["name"] not in history.keys():
            history[person["name"]] = {
                "name": person["name"],
                "n": 0,
                "rn": 0,
                "hn": [],
                "boxid": person["boxid"],
                "q": {},
            }
        if person["name"] not in newAns.keys():
            newAns[person["name"]] = {}

        # download box data => x
        txt = dl(urlPrefix+person["boxid"])
        x = loads(txt)

        for q in x["content"]["data"]:
            msgdata = {
                "qT": ft(q["createdTime"]),
                "aT": ft(q["answerAt"]),
                "q": q["title"],
                "a": q["answer"]["txtContent"],
                "id": q["visitCode"]
            }
            history[person["name"]]["q"][msgdata["id"]] = msgdata
            # Check if MSG is new
            if msgdata["id"] not in alReadId:
                msgdata.update({'already': 0})
                newAns[person["name"]][msgdata["id"]] = msgdata

        history[person["name"]].update({
            "n": x["content"]["total"],
            "rn": len(history[person["name"]]["q"]),
        })
        history[person["name"]]["hn"].append({
            "n": x["content"]["total"],
            "t": [
                datetime.now().timestamp(),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ]
        })

    # 更新归档文件
    with open(r+newAns_path, 'w', encoding='utf8') as f:
        dump(newAns, f, ensure_ascii=False)
    with open(r+alreadyReadL_path, 'w', encoding='utf8') as f:
        dump(alReadId, f, ensure_ascii=False)
    with open(r+history_path, 'w', encoding='utf8') as f:
        dump(history, f, ensure_ascii=False)
