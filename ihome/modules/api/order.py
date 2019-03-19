from datetime import datetime
from sqlalchemy import or_
import time
from ihome import db, sr
from ihome.models import House, Order
from ihome.utils.common import login_required
from ihome.utils.response_code import RET
from . import api_blu
from flask import request, g, jsonify, current_app


# 预订房间
@api_blu.route('/orders', methods=['POST'])
# @login_required
def add_order():
    """
    下单
    1. 获取参数
    2. 校验参数
    3. 查询指定房屋是否存在
    4. 判断当前房屋的房主是否是登录用户
    5. 查询当前预订时间是否存在冲突
    6. 生成订单模型，进行下单
    7. 返回下单结果
    :return:
    """

    # 1.获取参数
    param_dict = request.json
    house_id = param_dict.get("house_id")
    start_date = param_dict.get("start_date")
    end_date = param_dict.get("end_date")

    # 2.校验参数
    if not all([house_id, start_date, end_date]):
        return jsonify(errno=RET.NODATA, errmsg="参数不足")
    # 3.查询指定房屋是否存在
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据库错误")

    if not house:
        return jsonify(errno=RET.NODATA, errmsg="查询房屋不存在")

    # 判断当前的房主是否是登录用户
    user_id = 8
    if user_id == house.user_id:
        return jsonify(errno=RET.ROLEERR, errmsg="用户身份错误")

    # 查询当前预定时间是否存在冲突
    # 查询入住时间是否满足条件
    end_date = datetime.strptime(end_date, '%Y-%m-%d')
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    days = (end_date - start_date).days
    if house.max_days == 0:
        if days <= house.min_days:
            return jsonify(errno=RET.PARAMERR, errmsg="不满足入住时间")
    else:
        if days >= house.max_days or days <= house.min_days:
            return jsonify(errno=RET.PARAMERR, errmsg="不满足入住时间")

    # 查询房屋的已有订单是否与当前订单时间冲突
    now = time.localtime()

    now_time = '%d-%02d-%02d' % (now.tm_year, now.tm_mon, now.tm_mday)

    now_time = datetime.strptime(now_time, '%Y-%m-%d')

    if end_date < now_time or start_date < now_time:
        return jsonify(errno=RET.PARAMERR, errmsg="不可预定当前日期以前的房间")

    filters1 = [Order.house_id == house_id, Order.begin_date < start_date, start_date < Order.end_date]
    filters2 = [Order.house_id == house_id, Order.begin_date > start_date, Order.end_date < end_date]
    filters3 = [Order.house_id == house_id, Order.begin_date < end_date, Order.end_date > end_date]

    try:
        order_exist = Order.query.filter(or_(*filters1, *filters2, *filters3)).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据异常")

    if order_exist:
        return jsonify(errno=RET.DATAERR, errmsg="该时间段房间已经被预定")

    # 生成订单模型
    new_order = Order()
    new_order.user_id = user_id
    new_order.house_id = house_id
    new_order.begin_date = start_date
    new_order.end_date = end_date
    new_order.days = days
    new_order.house_price = house.price
    new_order.amount = house.price * days

    try:
        db.session.add(new_order)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据异常")

    data = {
        "order_id": new_order.id
    }
    return jsonify(data=data, errno=RET.OK, errmsg="OK")










# 获取我的订单
@api_blu.route('/orders')
@login_required
def get_orders():
    """
    1. 去订单的表中查询当前登录用户下的订单
    2. 返回数据
    :return:
    """
    pass


# 接受/拒绝订单
@api_blu.route('/orders', methods=["PUT"])
@login_required
def change_order_status():
    """
    1. 接受参数：order_id
    2. 通过order_id找到指定的订单，(条件：status="待接单")
    3. 修改订单状态
    4. 保存到数据库
    5. 返回
    :return:
    """
    pass


# 评论订单
@api_blu.route('/orders/comment', methods=["PUT"])
@login_required
def order_comment():
    """
    订单评价
    1. 获取参数
    2. 校验参数
    3. 修改模型
    :return:
    """
    pass
