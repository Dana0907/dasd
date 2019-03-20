import datetime

from flask import current_app, jsonify, request, g, session
from ihome import sr, db
from ihome.models import Area, House, Facility, HouseImage, Order
from ihome.modules.api import api_blu
from ihome.utils import constants
from ihome.utils.common import login_required
from ihome.utils.constants import AREA_INFO_REDIS_EXPIRES, QINIU_DOMIN_PREFIX, HOUSE_LIST_PAGE_CAPACITY, \
    HOME_PAGE_MAX_HOUSES, HOME_PAGE_DATA_REDIS_EXPIRES
from ihome.utils.image_storage import storage_image
from ihome.utils.response_code import RET


# 我的发布列表
@api_blu.route('/user/houses')
@login_required
def get_user_house_list():
    """
    获取用户房屋列表
    1. 获取当前登录用户id
    2. 查询数据
    :return:
    """
    pass


# 获取地区信息
@api_blu.route("/areas")
def get_areas():
    """
    1. 查询出所有的城区
    2. 返回
    :return:
    """
    pass


# 上传房屋图片
@api_blu.route("/houses/<int:house_id>/images", methods=['POST'])
@login_required
def upload_house_image(house_id):
    """
    1. 取到上传的图片
    2. 进行七牛云上传
    3. 将上传返回的图片地址存储
    4. 进行返回
    :return:
    """
    # 获取参数
    house_image = request.files.get('images')
    house_id = house_id
    user = g.ih_user_profile

    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    # 将图片上传到七牛云
    try:
        image_name = storage_image(house_image.read())
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="上传图片到七牛云异常")
        # 图片名称没有值
    if not image_name:
        return jsonify(errno=RET.DBERR, errmsg="上传图片到七牛云异常")

    image = HouseImage()
    image.url = constants.QINIU_DOMIN_PREFIX + image_name
    image.house_id = house_id

    data = {
        "url": image.url,

    }

    try:
        db.session.add(image)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        # 数据库回滚
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errormsg="保存数据对象异常")

    return jsonify(error=RET.OK, errmsg="上传图片成功", data=data)


# 发布房源
@api_blu.route("/houses", methods=["POST"])
@login_required
def save_new_house():
    """
    1. 接收参数并且判空
    2. 将参数的数据保存到新创建house模型
    3. 保存house模型到数据库
    前端发送过来的json数据
    {
        "title":"",
        "price":"",
        "area_id":"1",
        "address":"",
        "room_count":"",
        "acreage":"",
        "unit":"",
        "capacity":"",
        "beds":"",
        "deposit":"",
        "min_days":"",
        "max_days":"",
        "facility":["7","8"]
    }
    :return:
    """
    # POST请求,获取参数

    title = request.form.get('title')
    price = request.form.get('price')
    area_id = request.form.get('area_id')
    address = request.form.get('address')
    room_count = request.form.get('room_count')
    acreage = request.form.get('acreage')
    unit = request.form.get('unit')
    capacity = request.form.get('capacity')
    beds = request.form.get('beds')
    deposit = request.form.get('deposit')
    min_days = request.form.get('min_days')
    max_days = request.form.get('max_days')
    facility = request.form.get('facility')
    user = g.ih_user_profile
    # 非空判断
    if not all([title, price, area_id, address, room_count, acreage, unit, capacity, beds, deposit, min_days, max_days,
                facility]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不足")

    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    house = House()
    # 标题
    house.title = str(title)
    # 价格
    house.price = str(price)
    house.area_id = int(area_id)
    house.address = str(address)
    house.room_count = int(room_count)
    house.acreage = int(acreage)
    house.unit = str(unit)
    house.capacity = int(capacity)
    house.beds = str(beds)
    house.deposit = str(deposit)
    house.min_days = int(min_days)
    house.max_days = int(max_days)
    house.facility = facility
    house.user_id = g.ih_user_profile.id
    house_id = g.ih_house_info.id

    # 3.2 保存回数据库
    try:
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        # 数据库回滚
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errormsg="保存房源对象异常")

    return jsonify(error=RET.OK, errmsg="发布房源成功", data={house_id})


# 房屋详情
@api_blu.route('/houses/<int:house_id>')
def get_house_detail(house_id):
    """
    1. 通过房屋id查询出房屋模型
    :param house_id:
    :return:
    """
    pass


# 获取首页展示内容
@api_blu.route('/houses/index')
def house_index():
    """
    获取首页房屋列表
    :return:
    """
    pass


# 搜索房屋/获取房屋列表
@api_blu.route('/houses')
def get_house_list():
    pass
