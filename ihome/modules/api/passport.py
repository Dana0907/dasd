# 实现图片验证码和短信验证码的逻辑
import re, random
from flask import request, abort, current_app, jsonify, make_response, json, session
from datetime import datetime
from ihome import sr, db
from ihome.libs.captcha.pic_captcha import captcha
from ihome.models import User
from ihome.modules.api import api_blu
from ihome.utils import constants
from ihome.utils.response_code import RET


# 获取图片验证码
@api_blu.route("/imagecode")
def get_image_code():
    """
    1. 获取传入的验证码编号，并编号是否有值
    2. 生成图片验证码
    3. 保存编号和其对应的图片验证码内容到redis
    4. 返回验证码图片
    :return:
    """
    pass



# 获取短信验证码
@api_blu.route('/smscode', methods=["POST"])
def send_sms():
    """
    1. 接收参数并判断是否有值
    2. 校验手机号是正确
    3. 通过传入的图片编码去redis中查询真实的图片验证码内容
    4. 进行验证码内容的比对
    5. 生成发送短信的内容并发送短信
    6. redis中保存短信验证码内容
    7. 返回发送成功的响应
    :return:
    """
    pass



# 用户注册
@api_blu.route("/user", methods=["POST"])
def register():
    """
    1. 获取参数和判断是否有值
    2. 从redis中获取指定手机号对应的短信验证码的
    3. 校验验证码
    4. 初始化 user 模型，并设置数据并添加到数据库
    5. 保存当前用户的状态
    6. 返回注册的结果
    :return:
    """
    pass


# 用户登录
@api_blu.route("/session", methods=["POST"])
def login():
    """
    1. 获取参数和判断是否有值
    2. 从数据库查询出指定的用户
    3. 校验密码
    4. 保存用户登录状态
    5. 返回结果
    :return:
    """

    #  从参数中获取手机号及用户输入的密码
    mobile = request.json.get('mobile')
    password = request.json.get('password')

    #  验证参数的非空性
    if not all([mobile, password]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    #  验证手机号码格式的是否正确
    if not re.match(r'^1(3|4|5|7|8)\d{9}$', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg='手机号码格式异常')

    #  从数据库查询出指定的用户,并判断用户是否存在
    try:
        user = User.query.filter(User.mobile == mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询数据错误')

    if not user:
        return jsonify(errno=RET.USERERR, errmsg='用户未注册')

    #  判断用户输入的密码是否与该账号一致
    if not user.check_password(password):
        return jsonify(errno=RET.PWDERR, errmsg='密码错误')

    #  通过密码校验,在session中保存用户的登录信息
    session['user_id'] = user.id
    session['name'] = user.name

    # 更新用户最后一次登录时间
    try:
        user.last_login = datetime.now()
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)

    return jsonify(errno=RET.OK, errmsg="登录成功")


# 获取登录状态
@api_blu.route('/session')
def check_login():
    """
    检测用户是否登录，如果登录，则返回用户的名和用户id
    :return:
    """
    # 获取session中的用户id
    user_id = session.get('user_id')
    user = None

    # 根据用户id查询用户对象
    if user_id:
        try:
            user = User.query.get(user_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="查询数据库失败")

        # 判断是否存在该用户
        if user:
            data = {
                "name": user.name,
                "user_id": user.id
            }
            return jsonify(errno=RET.OK, errmsg="OK", data=data)
        else:
            return jsonify(errno=RET.SESSIONERR, errmsg="未登录")

    return jsonify(errno=RET.SESSIONERR, errmsg="未登录")


# 退出登录
@api_blu.route("/session", methods=["DELETE"])
def logout():
    """
    1. 清除session中的对应登录之后保存的信息
    :return:
    """
    session.pop('user_id', None)
    session.pop('name', None)
    return jsonify(errno=RET.OK, errmsg="OK")

