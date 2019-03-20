import datetime

from ihome import db, sr
from ihome.models import House, Order
from ihome.utils.common import login_required
from ihome.utils.response_code import RET
from . import api_blu
from flask import request, g, jsonify, current_app, session, render_template


# 预订房间
@api_blu.route('/orders', methods=['POST'])
@login_required
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
    pass


# 获取我的订单""/api/v1.0/orders?role=custom""
@api_blu.route("/orders", methods=["GET"])
@login_required
def get_orders():
    """
    1. 去订单的表中查询当前登录用户下的订单
    2. 返回数据
    :return
    """
    # 获取用户id
    user_id = g.user_id

    # 获取请求数据中的角色
    role = request.args.get("role", "")
    # 获取订单数据
    try:
        # 以房东的身份查询自己发布的房屋
        if role == "landlord":
            # 查询到房东的房屋列表
            houses = House.query.filter(House.user_id == user_id).all()
            # 获取房东每个房子的id
            house_ids = []
            for house in houses:
                house_ids.append(house.id)
            # 查询房东所发布的客户订单
            orders = Order.query.filter(Order.house_id.in_(house_ids)).order_by(Order.create_time).all()

            # 以客户的身份查询订单
        else:
            orders = Order.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库订单查询异常")

    # 将订单转换成字典列表
    order_dict = []
    for order in orders if orders else []:
        order_dict.append(order.to_dict())

    # 返回数据
    return jsonify(errno=RET.OK, errmsg="ok", data={"orders": order_dict})


# 接受/拒绝订单"http://192.168.131.143:5001/api/v1.0/orders?role=landlord
@api_blu.route("/orders/<int:order_id>/status", methods=["PUT"])
@login_required
def change_order_status(order_id):
    """
    1. 接受参数：order_id
    2. 通过order_id找到指定的订单，(条件：status="待接单")
    3. 修改订单状态
    4. 保存到数据库
    5. 返回
    :return:
    """
    # 获取用户id
    user_id = g.user_id
    # 获取请求参数
    req_data = request.get_json()

    if not req_data:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    # 获取前端用户请求为接单还是拒单，
    action = req_data.get("action")
    if action not in ["accept", "reject"]:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    # 在数据库中根据订单号查询订单状态为等待接单状态的订单
    try:
        order = Order.query.filter(Order.id == order_id, Order.status == "WAIT_ACCEPT").first()
        # 获取订单对应的 house对象
        house = House.query.get(order.house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询订单信息失败")

    if not order or house.user_id != user_id:
        return jsonify(errno=RET.REQERR, errmsg="用户操作错误")

    # 房东选择接单，对应订单的状态为等待评论，拒单需要房东填写拒单的原因
    if action == "accept":
        order.status = "WAIT_PAYMENT"
    elif action == "reject":
        reason = req_data.get("reason")
        if not reason:
            return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
        order.status = "REJECTED"
        order.comment = reason
    # 将订单修改后提交到数据库中
    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="订单存入数据库失败")
    # 返回数据
    return jsonify(errno=RET.OK, errmsg="OK")


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
