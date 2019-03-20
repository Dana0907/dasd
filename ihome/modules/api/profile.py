import re

from flask import request, current_app, jsonify, session, g, render_template

from ihome import db
from ihome.models import User
from ihome.modules.api import api_blu
from ihome.utils import constants
from ihome.utils.common import login_required
from ihome.utils.constants import QINIU_DOMIN_PREFIX
from ihome.utils.image_storage import storage_image
from ihome.utils.response_code import RET


# 获取用户信息
@api_blu.route('/user')
@login_required
def get_user_info():
    """
    获取用户信息
    1. 获取到当前登录的用户模型
    2. 返回模型中指定内容
    :return:
    """
    user_id = g.user_id

    try:
        user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='获取用户异常')

    if not user:
        return jsonify(errno=RET.NODATA, errmsg='用户不存在')

    data = user.to_dict()
    if not data['name']:
        data['name'] = data['mobile']

    return jsonify(errno=RET.OK, data=data)


@api_blu.route('/change_info')
def change_info():
    return render_template('profile/profile.html', errno=RET.OK)


# 修改用户名
@api_blu.route('/user/name', methods=["POST"])
@login_required
def set_user_name():
    """
    0. 判断用户是否登录
    1. 获取到传入参数
    2. 将用户名信息更新到当前用户的模型中
    3. 返回结果
    :return:
    """
    name = request.json.get('name')
    if not name:
        return jsonify(errno=RET.PARAMERR, errmsg='未检测到,提交的用户名')
    user_id = g.user_id
    try:
        user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询用户资料失败')
    user.name = name
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='保存用户资料失败')
    return jsonify(errno=RET.OK, errmsg='改名称成功')


# 上传个人头像
@api_blu.route('/avatar', methods=['POST'])
@login_required
def set_user_avatar():
    """
    0. 判断用户是否登录
    1. 获取到上传的文件
    2. 再将文件上传到七牛云
    3. 将头像信息更新到当前用户的模型中
    4. 返回上传的结果<avatar_url>
    :return:
    """
    user_id = g.user_id
    try:
        user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='获取用户异常,请重新登录')

    if not user:
        return jsonify(errno=RET.NODATA, errmsg='用户不存在,请重新登录')
    try:
        data = request.files.get('avatar').read()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.NODATA, errmsg='文件读取出错')

    try:
        url_name = storage_image(data)  # 图片名
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.NODATA, errmsg='获取服务器头像异常')

    # 保存头像信息
    user.avatar_url = url_name

    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='保存头像信息失败')

    avatar_url = constants.QINIU_DOMIN_PREFIX + url_name  # 头像地址
    return jsonify(errno=RET.OK, errmsg='更改成功', avatar_url=avatar_url)


# 获取用户实名信息
@api_blu.route('/get_auth')
@login_required
def get_user_auth():
    user_id = g.user_id
    try:
        user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询用户信息异常')

    data = user.to_auth_info()
    return jsonify(errno=RET.OK, errmsg='成功', data=data)


# 设置用户实名信息
@api_blu.route('/auth', methods=["POST"])
@login_required
def set_user_auth():
    """
    1. 取到当前登录用户id
    2. 取到传过来的认证的信息
    3. 通过id查找到当前用户
    4. 更新用户的认证信息
    5. 保存到数据库
    6. 返回结果
    :return:
    """
    params = request.json
    real_name = params.get('real_name')
    id_card = params.get('id_card')
    if not all([real_name, id_card]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    regex = '^[1-9]\d{7}((0\d)|(1[0-2]))(([0|1|2]\d)|3[0-1])\d{3}$|^[1-9]\d{5}[1-9]\d{3}((0\d)|(1[0-2]))(([0|1|2]\d)|3[0-1])\d{3}([0-9]|X)$'
    if not re.match(regex, id_card):
        print('错误的身份证号')
        return jsonify(errno=RET.PARAMERR, errmsg='错误的身份证号')

    user_id = g.user_id
    user = User.query.get(user_id)
    user.id_card = id_card
    user.real_name = real_name

    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='保存实名认证异常')

    return jsonify(errno=RET.OK, errmsg='成功')
