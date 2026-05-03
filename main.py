from PIL import Image, ImageDraw, ImageFont
import random
import requests
import os
from datetime import datetime, timedelta

works_id = ["280193118", "313822769", "299835772", "305310185"]
get_user_id = "157090347"

session = requests.session()
mao_acount = os.environ["ACCOUNT"]
mao_password = os.environ["PASSWORD"]
canvas = Image.new("RGB", (140 * 4, 140), color=(255, 255, 255))
draw = ImageDraw.Draw(canvas)


def split_image(image_path, rows, cols, save_dir="split_images"):
    img = Image.open(image_path)
    width, height = img.size
    piece_width = width // cols
    piece_height = height // rows
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    count = 1
    for row in range(rows):
        for col in range(cols):
            left = col * piece_width
            top = row * piece_height
            right = left + piece_width
            bottom = top + piece_height

            piece = img.crop((left, top, right, bottom))
            piece.save(f"{save_dir}/piece_{count}.png")
            print(f"已保存:piece_{count}.png")
            count += 1


def is_same_day(timestamp1, timestamp2):
    date1 = datetime.fromtimestamp(timestamp1).date()
    date2 = datetime.fromtimestamp(timestamp2).date()
    return date1 == date2


def get_heatmap_data():
    try:
        rows = 8
        cols = 40
        data = [[0 for _ in range(rows)] for _ in range(cols)]

        works_data = session.get(
            f"https://api.codemao.cn/creation-tools/v2/user/center/work-list?type=newest&user_id={get_user_id}&offset=0&limit=20"
        )
        works_json = works_data.json()
        work_items = works_json.get("items", [])

        for col in range(cols):
            for row in range(rows):
                current_index = (cols - 1 - col) * rows + (rows - 1 - row)
                past_day = datetime.now() - timedelta(days=current_index)
                current_commit = 0

                for work in work_items:
                    if is_same_day(int(past_day.timestamp()), work["publish_time"]):
                        current_commit += 1

                if current_commit == 0:
                    data[col][row] = 0
                elif current_commit <= 1:
                    data[col][row] = 1
                elif current_commit <= 3:
                    data[col][row] = 2
                elif current_commit <= 5:
                    data[col][row] = 3
                else:
                    data[col][row] = 4

        return data

    except Exception as e:
        print("发生了错误:", e)
        rows = 8
        cols = 40
        data = [[0 for _ in range(rows)] for _ in range(cols)]
        return data


def draw_heatmap(data):
    cell_size = 14
    padding = 0
    start_x = 0
    start_y = 0
    rows = 8
    cols = 40

    heatmap_color = ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"]

    for col in range(cols):
        for row in range(rows):
            x1 = start_x + col * (cell_size + padding)
            y1 = start_y + row * (cell_size + padding)
            x2 = x1 + cell_size
            y2 = y1 + cell_size

            draw.rectangle(
                [x1, y1, x2, y2],
                fill=heatmap_color[data[col][row]],
                outline=(255, 255, 255),
                width=1,
            )


def save():
    canvas.save("img.png")


def updata_img():
    url = []
    try:
        for index in range(4):
            with open(f"split_images/piece_{index + 1}.png", "rb") as f:
                files = {"image": f}
                data = {"outputFormat": "png"}
                response = requests.post(
                    "https://img.scdn.io/api/v1.php", files=files, data=data
                )
                response_json = response.json()
                if response_json["success"]:
                    url.append(response_json["url"])
                else:
                    continue
        return url
    except Exception as e:
        print("上传图片失败:", e)
        return []


def updata_codemao(img_url):
    try:
        login_session = session.post(
            "https://api.codemao.cn/tiger/v3/web/accounts/login",
            json={"pid": "65edCTyg", "identity": mao_acount, "password": mao_password},
        )
        if login_session.status_code == 200:
            print("登录成功")
            for work in works_id:
                publish_response = session.put(
                    f"https://api-creation.codemao.cn/kitten/r2/work/{work}/publish",
                    json={
                        "work_id": work,
                        "name": f"热点图({get_user_id})",
                        "description": "Codemao热点图",
                        "operation": "Codemao热点图",
                        "labels": [],
                        "cover_url": img_url[works_id.index(work)],
                        "fork_enable": 0,
                        "cover_type": 1,
                        "version": "4.11.19",
                        "user_labels": [],
                        "bcmc_url": "https://creation.bcmcdn.com/445/kitten/d2ViXzIwMDJfMTI1NTMyMzVfMzEzODIyMjUyXzE3Nzc3Nzk5OTYzNzlfMTU4YjVkYjM=.json",
                        "work_url": "https://creation.bcmcdn.com/445/kitten/d2ViXzIwMDJfMTI1NTMyMzVfMzEzODIyMjUyXzE3Nzc3Nzk5OTYxOTJfZmExNjIwYzQ=.bcm4",
                        "if_default_cover": 1,
                    },
                )
                if publish_response.status_code == 200:
                    print(f"作品{work}更新成功!")
                else:
                    print(f"作品{work}更新失败!")
        else:
            print("登录失败: ", login_session.text)

    except Exception as e:
        print("发生了错误: ", e)


def main():
    draw_heatmap(get_heatmap_data())
    save()
    split_image("img.png", rows=1, cols=4)
    updata_codemao(updata_img())


if __name__ == "__main__":
    main()
