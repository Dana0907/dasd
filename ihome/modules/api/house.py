import datetime

from flask import current_app, jsonify, request, g, session
from ihome import sr, db
from ihome.models import Area, House, Facility, HouseImage, Order, User
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
    user_id = g.user_id
    if not user_id:
        return jsonify(errno=RET.USERERR, errmsg="请先登录")

    try:
        user = User.query.get(user_id)

    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno = RET.DATAERR, errmsg = "数据库数据出错")

    user_house = user.houses
    house_list = user_house
    house_dict = []
    for house1 in house_list if house_list else None:
        house_dict.append(house1.to_basic_dict())





    return jsonify(errno = RET.OK, errmsg = "OK", data = house_dict)
# 获取地区信息
@api_blu.route("/areas")
def get_areas():
    """
    1. 查询出所有的城区
    2. 返回
    :return:
    """
    try:
        area_list = Area.query.all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg="数据库查询数据出错")
    area_dict = []
    for area in area_list if area_list else None:
        area_dict.append(area.to_dict())

    return jsonify(errno=RET.OK, errmsg="OK", data= area_dict)
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
    pass


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
    pass


# 房屋详情
@api_blu.route('/houses/<int:house_id>')
@login_required
def get_house_detail(house_id):
    """

    :param house_id:
    :return:
    """

    # 获取用户id
    user_id = g.user_id

    if not user_id:
        user_id = -1
        # 判断参数是否有值
    if not house_id:
        return jsonify(errno=RET.PARAMERR, errmsg='参数缺失')

    try:
        # 通过房屋id查询出房屋模型
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据查询出错')

    # 将数据打包成data字典
    data = {
        "house": house.to_full_dict(),
        'user_id': user_id,
    }
    # 返回数据
    return jsonify(errno=RET.OK, errmsg='OK', data=data)


# 获取首页展示内容
@api_blu.route('/houses/index')
def house_index():
    """
    获取首页房屋列表
    :return:
    """
    try:
        # 通过房屋id查询出房屋模型
        num = constants.HOME_PAGE_MAX_HOUSES - 1
        house_1, house_2 = None, None
        # 按价格排,最便宜的num个
        house_1 = House.query.order_by(House.price).limit(num)
        # 按更新时间排最晚的一个
        house_2 = House.query.order_by(House.update_time.desc()).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据查询出错')
    # 将house字典添加到列表中
    house_list = []
    house_list.append(house_2.to_basic_dict())
    for h in house_1 if house_1 else None:
        house_list.append(h.to_basic_dict())
    # 返回数据
    return jsonify(errno=RET.OK, errmsg='OK', data=house_list)


# 搜索房屋/获取房屋列表
@api_blu.route('/houses')
def get_house_list():
    # 获取参数
    args = request.args
    area_id = args.get('aid', '')
    start_date_str = args.get('sd', '')
    end_date_str = args.get('ed', '')
    # 排序方法
    sort_key = args.get('sk', 'new')
    page = args.get('p', '1')

    try:
        # 判断分页参数
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')



    if not args:
        # 没有任何查询条件
        try:
            # 按创建时间降序查询数据并分页
            page_house = House.query.order_by(House.create_time.desc()).paginate(page, constants.HOUSE_LIST_PAGE_CAPACITY, False)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg='数据库查询出错')
        # 分页处理
        houses = page_house.items
        total_page = page_house.pages

        houses_list = []
        # 遍历添加房屋字典
        for house in houses:
            houses_list.append(house.to_basic_dict())
        data = {
            "total_page": total_page,
            "houses": houses_list
        }
        return jsonify(errno=RET.OK, errmsg='OK', data=data)

    # 对日期进行相关处理
    try:
        start_date = None
        end_date = None
        if start_date_str:
            start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d')
        if end_date_str:
            end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d')
        # 如果开始时间大于或者等于结束时间,就报错
        if start_date and end_date:
            assert start_date < end_date, Exception('开始时间大于结束时间')
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='日期错误')

    # 定义查询条件列表
    filters = []
    # 如果存在区域id存在
    if area_id:
        filters.append(House.area_id == area_id)
    # 定义数组保存冲突订单
    conflict_order = None
    if start_date and end_date:
        # 如果订单的开始时间 < 结束时间 and 订单的结束时间 > 开始时间
        conflict_order = Order.query.filter(Order.begin_date < end_date, Order.end_date > start_date)
    elif start_date:
        # 订单的结束时间 > 开始时间
        conflict_order = Order.query.filter(Order.end_date > start_date)
    elif end_date:
        # 订单的开始时间 < 结束时间
        conflict_order = Order.query.filter(Order.begin_date < end_date)

    try:
        # 如果存在冲突订单
        if conflict_order:
            # 取得冲突订单的房屋id
            conflict_house_id = [order.house_id for order in conflict_order]
            # 添加订单不冲突条件
            filters.append(House.id.notin_(conflict_house_id))
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='订单判断错误')

    # 创建排序规则字典
    sork_dict = {
        'booking': House.query.filter(*filters).order_by(House.order_count.desc()),
        "price-inc": House.query.filter(*filters).order_by(House.price.asc()),
        "price-des": House.query.filter(*filters).order_by(House.price.desc()),
        # 默认排序 按创建时间
        "new": House.query.filter(*filters).order_by(House.create_time.desc())
    }
    # 获取查询到的house对象
    try:
        houses_sork = sork_dict[sort_key]
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库查询出错')

    if houses_sork:
        # 使用paginate进行分布
        house_pages = houses_sork.paginate(page, constants.HOUSE_LIST_PAGE_CAPACITY, False)
        # 获取当前页对象
        houses = house_pages.items
        # 获取总页数
        total_page = house_pages.pages
        houses_list = []
        # 遍历添加房屋字典
        for house in houses:
            houses_list.append(house.to_basic_dict())
        data = {
            "total_page": total_page,
            "houses": houses_list
        }
        # 返回数据
        return jsonify(errno=RET.OK, errmsg='OK', data=data)





















