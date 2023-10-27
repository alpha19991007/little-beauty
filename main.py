import os
import sys
import requests
import random
from datetime import datetime, date
from zhdate import ZhDate
from time import localtime


def get_access_token():
    try:
        app_id = config["app_id"]
        app_secret = config["app_secret"]
        post_url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={app_id}&secret={app_secret}"
        access_token = requests.get(post_url).json()['access_token']
        return access_token
    except Exception as err:
        print(f"获取access_token失败，请检查app_id和app_secret是否正确: {err}")


def get_config(configpath="./config.txt"):
    try:
        with open(configpath, encoding="utf-8") as f:
            global config
            config = eval(f.read())
    except FileNotFoundError:
        print("请检查config.txt文件是否与程序位于同一路径")
        sys.exit(1)
    except SyntaxError:
        print("请检查配置文件格式是否正确")
        sys.exit(1)


def get_tianhang():
    try:
        key = config["tian_api"]
        url = f"http://api.tianapi.com/caihongpi/index?key={key}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'}
        response = requests.get(url, headers=headers).json()
        chp = response["newslist"][0]["content"]
        return chp
    except Exception as err:
        print(err)


def get_star():
    try:
        key = config["tian_api"]
        url = f"https://apis.tianapi.com/star/index?key={key}&astro=scorpio"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'}
        response = requests.get(url, headers=headers).json()
        contents = response.get('result', {}).get("list", [])
        _data = {}
        for i in contents:
            _data[i.get('type')] = i.get('content')
        return _data
    except Exception as err:
        print(err)
        return {}


def get_text(string):
    """获取字符串并截取"""
    i = 0
    for str in string:
        _n = len(str.encode())
        if i + _n <= 60:
            i += _n
        else:
            return i
    return i


def get_two_test(string):
    """字符串截取前 60字节, 与后 60 字节"""
    num = get_text(string)
    e = string.encode()[:num]
    f = string.encode()[num:]
    return e.decode(), f.decode()


def get_weather(region):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'}
    key = config["weather_key"]
    region_url = f"https://geoapi.qweather.com/v2/city/lookup?location={region}&key={key}"
    response = requests.get(region_url, headers=headers).json()
    if response["code"] == "404":
        print("推送消息失败，请检查地区名是否有误！")
        return
    elif response["code"] == "401":
        print("推送消息失败，请检查和风天气key是否正确！")
        return
    else:
        # 获取地区的location--id
        location_id = response["location"][0]["id"]
    weather_url = f"https://devapi.qweather.com/v7/weather/now?location={location_id}&key={key}"
    response = requests.get(weather_url, headers=headers).json()
    weather = response["now"]["text"]                            # 天气
    temp = response["now"]["temp"] + u"\N{DEGREE SIGN}" + "C"    # 当前温度
    wind_dir = response["now"]["windDir"]                        # 风向
    url = f"https://devapi.qweather.com/v7/weather/3d?location={location_id}&key={key}"
    response = requests.get(url, headers=headers).json()        # 获取逐日天气预报
    max_temp = response["daily"][0]["tempMax"] + u"\N{DEGREE SIGN}" + "C"   # 最高气温
    min_temp = response["daily"][0]["tempMin"] + u"\N{DEGREE SIGN}" + "C"   # 最低气温
    sunrise = response["daily"][0]["sunrise"]                               # 日出时间
    sunset = response["daily"][0]["sunset"]                                 # 日落时间
    url = f"https://devapi.qweather.com/v7/air/now?location={location_id}&key={key}"
    response = requests.get(url, headers=headers).json()
    category = ""
    pm2p5 = ""
    if response["code"] == "200":
        category = response["now"]["category"]       # 空气质量
        pm2p5 = response["now"]["pm2p5"]             # pm2.5
    id = random.randint(1, 16)
    url = f"https://devapi.qweather.com/v7/indices/1d?location={location_id}&key={key}&type={id}"
    response = requests.get(url, headers=headers).json()
    proposal = ""
    if response["code"] == "200":
        proposal += response["daily"][0]["text"]
    return weather, temp, max_temp, min_temp, wind_dir, sunrise, sunset, category, pm2p5, proposal


def get_birthday(birthday, year, today):
    birthday_year = birthday.split("-")[0]
    # 判断是否为农历生日
    if birthday_year[0] == "r":
        r_mouth = int(birthday.split("-")[1])
        r_day = int(birthday.split("-")[2])
        # 获取农历生日的生日
        try:
            year_date = ZhDate(year, r_mouth, r_day).to_datetime().date()
        except TypeError:
            print("请检查生日的日子是否在今年存在")
            os.system("pause")
            sys.exit(1)

    else:
        # 获取国历生日的今年对应月和日
        birthday_month = int(birthday.split("-")[1])
        birthday_day = int(birthday.split("-")[2])
        # 今年生日
        year_date = date(year, birthday_month, birthday_day)
    # 计算生日年份，如果还没过，按当年减，如果过了需要+1
    if today > year_date:
        if birthday_year[0] == "r":
            # 获取农历明年生日的月和日
            r_last_birthday = ZhDate((year + 1), r_mouth, r_day).to_datetime().date()
            birth_date = date((year + 1), r_last_birthday.month, r_last_birthday.day)
        else:
            birth_date = date((year + 1), birthday_month, birthday_day)
        birth_day = str(birth_date.__sub__(today)).split(" ")[0]
    elif today == year_date:
        birth_day = 0
    else:
        birth_date = year_date
        birth_day = str(birth_date.__sub__(today)).split(" ")[0]
    return birth_day


def send_message(to_user, access_token, region_name, weather, temp, wind_dir, max_temp, min_temp,
                 sunrise, sunset, category, pm2p5, proposal, chp, stardata):
    url = "https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={}".format(
        access_token)
    week_list = ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"]
    year = localtime().tm_year
    month = localtime().tm_mon
    day = localtime().tm_mday
    today = datetime.date(datetime(year=year, month=month, day=day))
    week = week_list[today.isoweekday() % 7]
    # 获取在一起的日子的日期格式
    love_year = int(config["love_date"].split("-")[0])
    love_month = int(config["love_date"].split("-")[1])
    love_day = int(config["love_date"].split("-")[2])
    love_date = date(love_year, love_month, love_day)
    # 获取在一起的日期差
    love_days = str(today.__sub__(love_date)).split(" ")[0]
    # 获取所有生日数据
    birthdays = {}
    for k, v in config.items():
        if k[0:5] == "birth":
            birthdays[k] = v
    print(chp)
    star1, star2 = get_two_test(stardata.get('今日概述'))
    star2, star3 = get_two_test(star2)
    star3, star4 = get_two_test(star3)                
    data = {
        "touser": to_user,
        "template_id": config["template_id"],
        "url": "http://weixin.qq.com/download",
        "topcolor": "#FF0000",
        "data": {
            "date": {
                "value": f"{today} {week} {temp} {weather}"
            },
            "region": {
                "value": region_name
            },
            "minmax_tmp": {
                "value": f"{min_temp} ～ {max_temp}"
            },
            "category": {
                "value": f"{category} pm2.5: {pm2p5}"
            },
            "sun": {
                "value": f"{sunrise} - {sunset}"
            },
            "love_day": {"value": love_days},
            "chp1": {
                "value": get_two_test(chp)[0]
            },
            "chp2": {
                "value": get_two_test(chp)[1]
            },
            "yun1": {
                "value": f"{stardata.get('综合指数')} 爱情指数: {stardata.get('爱情指数')}"
            },
            "yun2": {
                "value": f"{stardata.get('工作指数')} 财运指数: {stardata.get('财运指数')}"
            },
            "yun3": {
                "value": f"{stardata.get('健康指数')} 幸运颜色: {stardata.get('幸运颜色')}"
            },
            "yun4": {
                "value": f"{stardata.get('幸运数字')} 贵人星座: {stardata.get('贵人星座')}"
            },
            "star1": {
                "value": star1
            },
            "star2": {
                "value": star2
            },
            "star3": {
                "value": star3
            }
            "star4": {
                "value": star4
            }
        }
    }
    print(data['data'])
    for key, value in birthdays.items():
        # 获取距离下次生日的时间
        birth_day = get_birthday(value["birthday"], year, today)
        if birth_day == 0:
            birthday_data = "{}生日哦，祝{}生日快乐！".format(
                value["name"], value["name"])
        else:
            birthday_data = "距离{}的生日还有{}天".format(value["name"], birth_day)
        # 将生日数据插入data
        data["data"][key] = {"value": birthday_data}
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
    }
    response = requests.post(url, headers=headers, json=data).json()
    if response["errcode"] == 40037:
        print("推送消息失败，请检查模板id是否正确")
    elif response["errcode"] == 40036:
        print("推送消息失败，请检查模板id是否为空")
    elif response["errcode"] == 40003:
        print("推送消息失败，请检查微信号是否正确")
    elif response["errcode"] == 0:
        print("推送消息成功")
    else:
        print(f"{response}")


if __name__ == "__main__":
    get_config()    # 读取配置文件
    accessToken = get_access_token()    # 获取access_token
    if not accessToken:
        print("获取accessToken 失败, 退出脚本")
        exit()
    _region = config["region"]
    weather, temp, max_temp, min_temp, wind_dir, sunrise, sunset, category, pm2p5, proposal = get_weather(_region)
    stardata = get_star()
    chp = get_tianhang()
    users = config['user']
    for user in users:
        send_message(user, accessToken, _region, weather, temp, wind_dir, max_temp, min_temp, sunrise, sunset, category, pm2p5, proposal, chp, stardata)
