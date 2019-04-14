from __future__ import unicode_literals

from django.http import HttpResponse
from django.template import loader
from django.db.models import Avg
from houseshow.models import Zufang
from pyecharts import Bar, Line, Grid
from pyecharts import Map, Bar3D
from pyecharts import Line, Pie, Scatter, EffectScatter

# zone_map_gz = {"tianhe": "天河", "baiyun": "白云", "panyu": "番禺", "haizhu": "海珠", "yuexiu": "越秀",
#             "huadu": "花都", "liwan": "荔湾", "zengcheng": "增城", "huangpu": "黄埔", "nansha": "南沙", "conghua": "从化"}
# zone_map_sz = {"futian": "福田", "nanshan": "南山", "baoan": "宝安", "longhua": "龙华", "luohu": "罗湖",
#                "longgang": "龙岗", "buji": "布吉", "pingshan": "坪山", "guangming": "光明", "dapeng": "大鹏", "yantian": "盐田"}
#
# zone_pingyin = {'广州': ["tianhe", "baiyun", "panyu", "haizhu", "yuexiu",
#             "huadu", "liwan", "zengcheng", "huangpu", "nansha", "conghua"],
#                 '深圳': ["futian", "nanshan", "baoan", "longhua", "luohu",
#                "longgang", "buji", "pingshan", "guangming", "dapeng", "yantian"]}

attr_zone_gz = ["天河", "白云", "番禺", "海珠", "越秀", "花都", "荔湾", "增城", "黄埔", "南沙", "从化"]
attr_zone_sz = ["福田", "南山", "宝安", "龙华", "罗湖", "龙岗", "布吉", "坪山", "盐田", "光明", "大鹏"]
city_zone = {'广州': attr_zone_gz, '深圳': attr_zone_sz}
room_map = {"yishi": "一室", "eshi": "二室", "sanshi": "三室", "sishi": "四室", "wushi": "四室以上"}

room_map2 = {"一室": 1, "二室": 2, "三室": 3, "四室": 4, "四室以上": 4}

area_map = [(0, 50), (50, 100), (100, 150), (150, 200), (200, 300), (300, 4000)]

price_map = [(0, 1000), (1000, 1500), (1500, 2000), (2000, 2500), (2500, 3000), (3000, 4000), (4000, 5000), (5000, 100000)]

attr_area = ["50㎡以下", "50-100㎡", "100-150㎡", "150-200㎡", "200-300㎡", "300㎡以上"]

attr_price = ["0-1000", "1000-1500", "1500-2000", "2000-2500", "2500-3000", "3000-4000", "4000-5000", "5000以上"]

attr = [str(i) for i in list(range(0, 300, 10))]    # 平均租金的x轴标签

attr_housetype = ["一室", "二室", "三室", "四室", "四室以上"]

REMOTE_HOST = "https://pyecharts.github.io/assets/js"


def index(request):
    city = path_resolute(request.path)[4]
    if len(city) == 0:
        city = "广州"
    house_num = Zufang.objects.filter(city=city).count()
    averge_price = int(Zufang.objects.filter(city=city).aggregate(Avg('price'))['price__avg'])
    averge_area = int(Zufang.objects.filter(city=city).aggregate(Avg('housearea'))['housearea__avg'])
    template = loader.get_template('houseshow/houseshow.html')

    attr_zone = city_zone[city]
    values_zone = [Zufang.objects.filter(city=city).filter(zone=i).count() for i in attr_zone]
    width = 600
    pie_zone = pie(attr_zone, values_zone, width, ["61%", "50%"])    # 显示房子在各区的分布情况，比例

    housetype = ["1室", "2室", "3室", "4室"]
    values_housetype = [Zufang.objects.filter(city=city).filter(housetype__regex="^\d+室").filter(housetype__contains=i).count() for i in housetype]
    values_housetype.append(Zufang.objects.filter(city=city).filter(housetype__regex="^\d+室").count()-sum(values_housetype))
    pie_housetype = pie(attr_housetype, values_housetype, 600, ["61%", "50%"])     # 显示各户型的比例组成

    attr_area = ["50㎡以下", "50-100㎡", "100-150㎡", "150-200㎡", "200-300㎡", "300㎡以上"]
    area = [(50, 100), (100, 150), (150, 200), (200, 300)]
    values_area = [Zufang.objects.filter(city=city).filter(housearea__lt=i[1]).filter(housearea__gte=i[0]).count() for i in area]
    values_area.insert(0, Zufang.objects.filter(city=city).filter(housearea__lt=50).count())
    values_area.append(Zufang.objects.filter(city=city).filter(housearea__gte=300).count())
    pie_area = pie(attr_area, values_area, 700, ["61%", "50%"])
    if city == '深圳':
        context = dict(
            myechart=pie_zone.render_embed(),
            myechart_housetype=pie_housetype.render_embed(),
            myechart_housearea=pie_area.render_embed(),
            host=REMOTE_HOST,
            script_list=pie_zone.get_js_dependencies(),
            house_num=house_num,
            averge_price=averge_price,
            averge_area=averge_area,
            city=city,
            zone_list=city_zone[city],
            city_list=list(city_zone.keys())
        )
    else:
        citymap = city_map(city=city)
        context = dict(
            myechart=pie_zone.render_embed(),
            myechart_housetype=pie_housetype.render_embed(),
            myechart_housearea=pie_area.render_embed(),
            myechart2=citymap.render_embed(),
            host=REMOTE_HOST,
            script_list=citymap.get_js_dependencies(),
            house_num=house_num,
            averge_price=averge_price,
            averge_area=averge_area,
            city=city,
            zone_list=city_zone[city],
            city_list=list(city_zone.keys())
        )
    return HttpResponse(template.render(context, request))


def houseinfo(request):
    path = request.path
    house_info = path_resolute(path)
    info = add_session(path)
    city = info['city'] if len((info['city'])) else '广州'
    (house_num, averge_price, averge_area) = count_num(house_info, city)
    template = loader.get_template('houseshow/houseinfo.html')
    multi = multiploy(house_info, city)
    context = dict(
        myechart=multi.render_embed(),
        host=REMOTE_HOST,
        script_list=multi.get_js_dependencies(),
        path=house_info,
        house_num=house_num,
        averge_price=averge_price,
        averge_area=averge_area,
        zone=info['zone'],
        zone_list=city_zone[city],
        housetype=info['housetype'],
        price=info['price'],
        area=info['area'],
        city=city,
        city_list=list(city_zone.keys())
    )
    return HttpResponse(template.render(context, request))


# 解析路径，作为条件从数据库拿数据
def path_resolute(path: str)->list:
    house_info = path.strip('/').split('/')
    zone = []
    price = []
    area = []
    housetype = []
    city = []
    for idx, v in enumerate(house_info):
        if 'city' in v:
            city.append(v.strip('city'))
        elif '元' in v:
            price.append(v.strip('info'))
        elif '㎡' in v:
            area.append(v.strip('info'))
        elif v.isascii():
            if len(v):
                housetype.append(v.strip('info')+'i')
        else:
            zone.append(v.strip('info'))
    if len(zone):
        zone = zone[-1]
    if len(price):
        price = price[-1].strip('元').split('-')
        if len(price) != 2:
            price.append('100000')
    if len(area):
        area = area[-1].strip('㎡').split('-')
    if len(housetype):
        housetype = room_map[housetype[-1]]
    if len(city):
        city = city[-1]
    return [zone, price, area, housetype, city]


def multiploy(house_args: list, city):
    if len(house_args[0]) != 0:
        if len(house_args[1]) != 0:
            if len(house_args[2]) != 0:
                if len(house_args[3]) != 0:    # 选择了区域、户型、价格、面积
                    grid = Grid(width=1200)
                    if room_map2[house_args[3]] == "四室以上":
                        values = [Zufang.objects.filter(city=city).filter(zone=house_args[0]).filter(housenum__gt=4).filter(housearea__gte=int(house_args[2][0])).filter(housearea__lt=int(house_args[2][1])).filter(price__gte=int(house_args[1][0])).filter(price__lt=int(house_args[1][1])).filter(per_price__gte=int(i)).filter(per_price__lt       =int(i)+10).count() for i in attr]
                    else:
                        values = [Zufang.objects.filter(city=city).filter(zone=house_args[0]).filter(housenum=room_map2[house_args[3]]).filter(housearea__gte=int(house_args[2][0])).filter(housearea__lt=int(house_args[2][1])).filter(price__gte=int(house_args[1][0])).filter(price__lt=int(house_args[1][1])).filter(per_price__gte=int(i)).filter(per_price__lt=int(i)+10).count() for i in attr]
                    bar = bar_ploy("每平米租金分布图", attr, values, title_pos="51%", xname="(元)", yname="(个)")

                    attr_interval_price = [str(i) for i in list(range(int(house_args[1][0]), int(house_args[1][1]), 50))]
                    if room_map2[house_args[3]] == "四室以上":
                        values_price = [Zufang.objects.filter(city=city).filter(zone=house_args[0]).filter(housenum__gt=4).filter(housearea__gte=int(house_args[2][0])).filter(housearea__lt=int(house_args[2][1])).filter(price__gte=int(i)).filter(price__lt=int(i)+50).count() for i in attr_interval_price]
                    else:
                        values_price = [Zufang.objects.filter(city=city).filter(zone=house_args[0]).filter(housenum=room_map2[house_args[3]]).filter(housearea__gte=int(house_args[2][0])).filter(housearea__lt =int(house_args[2][1])).filter(price__gte=int(i)).filter(price__lt=int(i)+50).count() for i in attr_interval_price]
                    bar_price = bar_ploy("价格分布图", attr_interval_price, values_price, title_pos="0%", xname="（元/平米）", yname="(个)")

                    grid.add(bar, grid_left="60%")
                    grid.add(bar_price, grid_right="60%")
                else:       # 选择了区域、价格、面积，没选户型
                    grid = Grid(width=1200)
                    # attr = [str(i) for i in list(range(0, 300, 10))]
                    values = [
                        Zufang.objects.filter(city=city).filter(zone=house_args[0]).filter(housearea__gte=int(house_args[2][0])).filter(
                            housearea__lt=int(house_args[2][1])).filter(price__gte=int(house_args[1][0])).filter(
                            price__lt=int(house_args[1][1])).filter(per_price__gte=int(i)).filter(
                            per_price__lt=int(i) + 10).count() for i in attr]
                    bar = bar_ploy("每平米租金分布图", attr, values, title_pos="51%", xname="(元)", yname="(个)")

                    values_price = [
                        Zufang.objects.filter(city=city).filter(zone=house_args[0]).filter(
                            housenum=room_map2[i]).filter(
                            housearea__gte=int(house_args[2][0])).filter(housearea__lt=int(house_args[2][1])).filter(
                            price__gte=int(house_args[1][0])).filter(price__lt=int(house_args[1][1])).count() for i in attr_housetype if i != "四室以上"]
                    values_price.append(Zufang.objects.filter(city=city).filter(zone=house_args[0]).filter(
                            housenum=room_map2["四室以上"]).filter(
                            housearea__gte=house_args[2][0]).filter(housearea__lt=int(house_args[2][1])).filter(
                            price__gte=house_args[1][0]).filter(price__lt=int(house_args[1][1])).count())
                    bar_price = bar_ploy("租房户型分布图", attr_housetype, values_price, title_pos="0%")

                    grid.add(bar, grid_left="60%")
                    grid.add(bar_price, grid_right="60%")
            else:   # 没选面积
                if len(house_args[3]) != 0:    # 选择了区域、价格、户型，没选面积
                    grid = Grid(width=1200)
                    line = Line("", title_pos="51%", title_color="#ffe8fe")
                    # attr = [str(i) for i in list(range(0, 300, 10))]
                    values = [
                        [Zufang.objects.filter(city=city).filter(zone=house_args[0]).filter(
                            housenum=room_map2[house_args[3]]).filter(
                            housearea__gte=j[0]).filter(
                            housearea__lt=j[1]).filter(price__gte=house_args[1][0]).filter(
                            price__lt=house_args[1][1]).filter(per_price__gte=int(i)).filter(
                            per_price__lt=int(i) + 10).count() for i in attr] for j in area_map]
                    values = value_to_percentage(values)

                    for idx, value in enumerate(values):
                        line.add(attr_area[idx],
                                 x_axis=attr,
                                 y_axis=value,
                                 xaxis_label_textcolor='#ffe8fe',
                                 yaxis_label_textcolor='#ffe8fe',
                                 xaxis_name="(元/㎡)",
                                 yaxis_name="%",
                                 xaxis_line_color="#ffe8fe",
                                 yaxis_line_color="#ffe8fe",
                                 xaxis_name_pos='end',
                                 is_toolbox_show=False,
                                 legend_pos='right',
                                 legend_text_color='#ffe8fe')

                    values_area = [
                        Zufang.objects.filter(city=city).filter(zone=house_args[0]).filter(
                            housenum=room_map2[house_args[3]]).filter(
                            housearea__gte=i[0]).filter(housearea__lt=i[1]).filter(
                            price__gte=house_args[1][0]).filter(price__lt=house_args[1][1]).count() for i in area_map]

                    bar_area = bar_ploy("租房面积分布图", attr_area, values_area, title_pos="0%", yname="(个)")

                    grid.add(line, grid_left="60%")
                    grid.add(bar_area, grid_right="60%")
                else:   # 选了区域、价格，没选户型、面积
                    grid = Grid(width=1200, height=600)
                    values_area = [
                        Zufang.objects.filter(city=city).filter(zone=house_args[0]).filter(
                            housearea__gte=i[0]).filter(housearea__lt=i[1]).filter(
                            price__gte=house_args[1][0]).filter(price__lt=int(house_args[1][1])).count() for i in area_map]

                    bar_area = bar_ploy("租房面积分布图", attr_area, values_area, title_pos="51%")


                    values_price = [
                        Zufang.objects.filter(city=city).filter(zone=house_args[0]).filter(
                            housenum=room_map2[i]).filter(
                            price__gte=int(house_args[1][0])).filter(price__lt=int(house_args[1][1])).count() for i in attr_housetype
                        if i != "四室以上"]
                    values_price.append(Zufang.objects.filter(city=city).filter(zone=house_args[0]).filter(
                        housenum__gt=room_map2["四室以上"]).filter(
                        price__gte=house_args[1][0]).filter(price__lt=int(house_args[1][1])).count())
                    bar_housetype = bar_ploy("租房户型分布图", attr_housetype, values_price, title_pos="0%")

                    value_price_along_housetype = [[Zufang.objects.filter(city=city).filter(zone=house_args[0]).filter(
                        price__gte=house_args[1][0]).filter(price__lt=int(house_args[1][1])).filter(
                        housearea__gte=i[0]).filter(housearea__lt=i[1]).filter(
                        housenum=room_map2[j]).count() for i in area_map] for j in room_map2 if j!="四室以上"]
                    value_price_along_housetype.append([Zufang.objects.filter(city=city).filter(zone=house_args[0]).filter(
                        price__gte=house_args[1][0]).filter(price__lt=int(house_args[1][1])).filter(
                        housearea__gte=i[0]).filter(housearea__lt=i[1]).filter(
                        housenum__gt=4).count() for i in area_map])
                    value_price_along_housetype = value_to_percentage(value_price_along_housetype)

                    bar_along_housetype = Bar("户型", title_top="55%", title_color="#ffe8fe")
                    for idx, value in enumerate(value_price_along_housetype):
                        bar_along_housetype.add(
                            attr_housetype[idx],
                            x_axis=attr_area,
                            y_axis=value,
                            xaxis_label_textcolor='#ffe8fe',
                            yaxis_label_textcolor='#ffe8fe',
                            xaxis_name="(/㎡)",
                            yaxis_name="%",
                            xaxis_line_color="#ffe8fe",
                            yaxis_line_color="#ffe8fe",
                            xaxis_name_pos='end',
                            is_toolbox_show=False,
                            legend_pos='10%',
                            legend_top='50%',
                            legend_text_color='#ffe8fe'
                        )

                        value_price_along_area = [[Zufang.objects.filter(city=city).filter(zone=house_args[0]).filter(
                                    price__gte=int(house_args[1][0])).filter(price__lt=int(house_args[1][1])).filter(
                            housearea__gte=j[0]).filter(housearea__lt=j[1]).filter(
                            housenum=room_map2[i]).count() if i!="四室以上"
                                                   else
                                                   Zufang.objects.filter(city=city).filter(zone=house_args[0]).filter(
                                                       price__gte=int(house_args[1][0])).filter(
                                                       price__lt=int(house_args[1][1])).filter(
                                                       housearea__gte=j[0]).filter(housearea__lt=j[1]).filter(
                                                       housenum__gt=4).count()
                                                   for i in room_map2] for j in area_map]
                        value_price_along_area = value_to_percentage(value_price_along_area)

                        bar_along_area = Bar("面积", title_top="55%", title_pos="51%", title_color="#ffe8fe")
                        for idx, value in enumerate(value_price_along_area):
                            bar_along_area.add(
                                attr_area[idx],
                                x_axis=attr_housetype,
                                y_axis=value,
                                xaxis_label_textcolor='#ffe8fe',
                                yaxis_label_textcolor='#ffe8fe',
                                xaxis_name="",
                                yaxis_name="%",
                                xaxis_line_color="#ffe8fe",
                                yaxis_line_color="#ffe8fe",
                                xaxis_name_pos='end',
                                is_toolbox_show=False,
                                legend_pos='right',
                                legend_top='50%',
                                legend_text_color='#ffe8fe'
                            )

                    grid.add(bar_area, grid_bottom="60%", grid_left="60%")
                    grid.add(bar_housetype, grid_bottom="60%", grid_right="60%")
                    grid.add(bar_along_housetype, grid_top="60%", grid_right="60%")
                    grid.add(bar_along_area, grid_top="60%", grid_left="60%")
        else:   # 没选价格
            if len(house_args[2]) != 0:
                if len(house_args[3]) != 0:    # 选了区域、面积、户型，没选价格
                    grid = Grid(width=1200)
                    values = [[
                        Zufang.objects.filter(city=city).filter(zone=house_args[0]).filter(
                            housearea__gte=int(house_args[2][0])).filter(
                            housearea__lt=int(house_args[2][1])).filter(price__gte=j[0]).filter(
                            price__lt=j[1]).filter(per_price__gte=int(i)).filter(
                            per_price__lt=int(i) + 10).count() for i in attr] for j in price_map]
                    values = value_to_percentage(values)
                    line = Line("每平米租金分布图", title_pos="51%", title_color="#ffe8fe")
                    for idx, value in enumerate(values):
                        line.add(attr_price[idx],
                                x_axis=attr,
                                y_axis=value,
                                xaxis_name="(元)",
                                yaxis_name="%",
                                xaxis_label_textcolor='#ffe8fe',
                                yaxis_label_textcolor='#ffe8fe',
                                xaxis_line_color="#ffe8fe",
                                yaxis_line_color="#ffe8fe",
                                xaxis_name_pos='end',
                                legend_pos='90%',
                                legend_text_color='#ffe8fe',
                                is_toolbox_show=False,
                                line_width=2,
                                )

                    values_price = [
                        Zufang.objects.filter(city=city).filter(zone=house_args[0]).filter(
                            housenum=room_map2[house_args[3]]).filter(
                            housearea__gte=int(house_args[2][0])).filter(housearea__lt=int(house_args[2][1])).filter(
                            price__gte=i[0]).filter(price__lt=i[1]).count() if house_args[3]!="四室以上" else
                        Zufang.objects.filter(city=city).filter(zone=house_args[0]).filter(
                            housenum__gt=4).filter(housearea__gte=int(house_args[2][0])).filter(
                            housearea__lt=int(house_args[2][1])).filter(
                            price__gte=i[0]).filter(price__lt=i[1]).count() for i in price_map]
                    bar_price = bar_ploy("租房价格分布图", attr_price, values_price, title_pos="0%")

                    grid.add(line, grid_left="60%")
                    grid.add(bar_price, grid_right="60%")
                else:   # 选了区域、面积，没选价格、户型
                    grid = Grid(width=1200, height=600)
                    values_price = [
                        Zufang.objects.filter(city=city).filter(zone=house_args[0]).filter(
                            housearea__gte=house_args[2][0]).filter(housearea__lt=house_args[2][1]).filter(
                            price__gte=i[0]).filter(price__lt=i[1]).count() for i in
                        price_map]

                    bar_price = bar_ploy("租房价格分布图", attr_price, values_price, title_pos="51%")

                    values_area = [
                        Zufang.objects.filter(city=city).filter(zone=house_args[0]).filter(
                            housenum=room_map2[i]).filter(housearea__gte=house_args[2][0]).filter(
                            housearea__lt=house_args[2][1]).count() for i in attr_housetype
                        if i != "四室以上"]
                    values_area.append(Zufang.objects.filter(city=city).filter(zone=house_args[0]).filter(
                            housenum__gt=4).filter(housearea__gte=house_args[2][0]).filter(
                            housearea__lt=house_args[2][1]).count())
                    bar_housetype = bar_ploy("租房户型分布图", attr_housetype, values_area, title_pos="0%")

                    value_price_along_housetype = [[Zufang.objects.filter(city=city).filter(zone=house_args[0]).filter(
                        price__gte=i[0]).filter(price__lt=i[1]).filter(
                        housearea__gte=house_args[2][0]).filter(housearea__lt=house_args[2][1]).filter(
                        housenum=room_map2[j]).count() for i in price_map] for j in room_map2 if j != "四室以上"]
                    value_price_along_housetype.append([Zufang.objects.filter(city=city).filter(zone=house_args[0]).filter(
                        price__gte=i[0]).filter(price__lt=i[1]).filter(
                        housearea__gte=house_args[2][0]).filter(housearea__lt=house_args[2][1]).filter(
                        housenum__gt=4).count() for i in price_map])
                    value_price_along_housetype = value_to_percentage(value_price_along_housetype)

                    bar_along_housetype = Bar("户型", title_top="55%", title_color="#ffe8fe")
                    for idx, value in enumerate(value_price_along_housetype):
                        bar_along_housetype.add(
                            attr_housetype[idx],
                            x_axis=attr_price,
                            y_axis=value,
                            xaxis_label_textcolor='#ffe8fe',
                            yaxis_label_textcolor='#ffe8fe',
                            xaxis_name="(元)",
                            yaxis_name="%",
                            xaxis_line_color="#ffe8fe",
                            yaxis_line_color="#ffe8fe",
                            xaxis_name_pos='end',
                            is_toolbox_show=False,
                            legend_pos='10%',
                            legend_top='50%',
                            legend_text_color='#ffe8fe'
                        )

                        value_housetype_along_price = [[Zufang.objects.filter(city=city).filter(zone=house_args[0]).filter(
                            price__gte=j[0]).filter(price__lt=j[1]).filter(
                            housearea__gte=house_args[2][0]).filter(housearea__lt=house_args[2][1]).filter(
                            housenum=room_map2[i]).count() if i != "四室以上"
                                                   else
                                                   Zufang.objects.filter(city=city).filter(zone=house_args[0]).filter(
                                                       price__gte=j[0]).filter(
                                                       price__lt=j[1]).filter(
                                                       housearea__gte=house_args[2][0]).filter(
                                                       housearea__lt=house_args[2][1]).filter(
                                                       housenum__gt=4).count()
                                                   for i in room_map2] for j in price_map]
                        value_housetype_along_price = value_to_percentage(value_housetype_along_price)

                        bar_along_price = Bar("价格", title_top="55%", title_pos="51%", title_color="#ffe8fe")
                        for idx, value in enumerate(value_housetype_along_price):
                            bar_along_price.add(
                                attr_price[idx],
                                x_axis=attr_housetype,
                                y_axis=value,
                                xaxis_label_textcolor='#ffe8fe',
                                yaxis_label_textcolor='#ffe8fe',
                                xaxis_name="",
                                yaxis_name="%",
                                xaxis_line_color="#ffe8fe",
                                yaxis_line_color="#ffe8fe",
                                xaxis_name_pos='end',
                                is_toolbox_show=False,
                                legend_pos='90%',
                                legend_top='50%',
                                legend_text_color='#ffe8fe'
                            )

                    grid.add(bar_price, grid_bottom="60%", grid_left="60%")
                    grid.add(bar_housetype, grid_bottom="60%", grid_right="60%")
                    grid.add(bar_along_housetype, grid_top="60%", grid_right="60%")
                    grid.add(bar_along_price, grid_top="60%", grid_left="60%")
            else:   # 没选面积
                if len(house_args[3]) != 0:    # 选了区域、户型，没选面积、价格
                    grid = Grid(width=1200, height=600)
                    values_price = [
                        Zufang.objects.filter(city=city).filter(zone=house_args[0]).filter(
                            housenum=room_map2[house_args[3]]).filter(
                            price__gte=i[0]).filter(price__lt=i[1]).count() if house_args[3]!="四室以上" else
                        Zufang.objects.filter(city=city).filter(zone=house_args[0]).filter(
                            housenum__gt=4).filter(
                            price__gte=i[0]).filter(price__lt=i[1]).count()for i in price_map]

                    bar_price = bar_ploy("租房价格分布图", attr_price, values_price, title_pos="51%")

                    values_area = [
                        Zufang.objects.filter(city=city).filter(zone=house_args[0]).filter(
                            housenum=room_map2[house_args[3]]).filter(housearea__gte=i[0]).filter(
                            housearea__lt=i[1]).count() if house_args[3]!="四室以上" else
                        Zufang.objects.filter(city=city).filter(zone=house_args[0]).filter(
                            housenum=room_map2[house_args[3]]).filter(housearea__gte=i[0]).filter(
                            housearea__lt=i[1]).count() for i in area_map if i != "四室以上"]
                    bar_area = bar_ploy("租房面积分布图", attr_area, values_area, title_pos="0%")

                    value_price_along_area = [[Zufang.objects.filter(city=city).filter(zone=house_args[0]).filter(
                        price__gte=i[0]).filter(price__lt=i[1]).filter(
                        housearea__gte=j[0]).filter(housearea__lt=j[1]).filter(
                        housenum=room_map2[house_args[3]]).count() if house_args[3]!="四室以上" else
                                                    Zufang.objects.filter(city=city).filter(zone=house_args[0]).filter(
                                                        price__gte=i[0]).filter(price__lt=i[1]).filter(
                                                        housearea__gte=j[0]).filter(housearea__lt=j[1]).filter(
                                                        housenum__gt=4).count()
                                                    for i in price_map] for j in area_map if j != "四室以上"]

                    value_price_along_area = value_to_percentage(value_price_along_area)

                    bar_along_area = Bar("面积", title_top="55%", title_color="#ffe8fe")
                    for idx, value in enumerate(value_price_along_area):
                        bar_along_area.add(
                            attr_area[idx],
                            x_axis=attr_price,
                            y_axis=value,
                            xaxis_label_textcolor='#ffe8fe',
                            yaxis_label_textcolor='#ffe8fe',
                            xaxis_name="(元)",
                            yaxis_name="%",
                            xaxis_line_color="#ffe8fe",
                            yaxis_line_color="#ffe8fe",
                            xaxis_name_pos='end',
                            is_toolbox_show=False,
                            legend_pos='0%',
                            legend_top='50%',
                            legend_text_color='#ffe8fe'
                        )

                        value_area_along_price = [[Zufang.objects.filter(city=city).filter(zone=house_args[0]).filter(
                            price__gte=j[0]).filter(price__lt=j[1]).filter(
                            housearea__gte=i[0]).filter(housearea__lt=i[1]).filter(
                            housenum=room_map2[house_args[3]]).count() if i != "四室以上" else
                                                   Zufang.objects.filter(city=city).filter(zone=house_args[0]).filter(
                                                       price__gte=j[0]).filter(price__lt=j[1]).filter(
                                                       housearea__gte=i[0]).filter(housearea__lt=i[1]).filter(
                                                       housenum__gt=4).count() for i in area_map] for j in price_map]
                        value_area_along_price = value_to_percentage(value_area_along_price)

                        bar_along_price = Bar("价格", title_top="55%", title_pos="51%", title_color="#ffe8fe")
                        for idx, value in enumerate(value_area_along_price):
                            bar_along_price.add(
                                attr_price[idx],
                                x_axis=attr_area,
                                y_axis=value,
                                xaxis_label_textcolor='#ffe8fe',
                                yaxis_label_textcolor='#ffe8fe',
                                xaxis_name="",
                                yaxis_name="%",
                                xaxis_line_color="#ffe8fe",
                                yaxis_line_color="#ffe8fe",
                                xaxis_name_pos='end',
                                is_toolbox_show=False,
                                legend_pos='90%',
                                legend_top='50%',
                                legend_text_color='#ffe8fe'
                            )

                    grid.add(bar_price, grid_bottom="60%", grid_left="60%")
                    grid.add(bar_area, grid_bottom="60%", grid_right="60%")
                    grid.add(bar_along_area, grid_top="60%", grid_right="60%")
                    grid.add(bar_along_price, grid_top="60%", grid_left="60%")
                else:   # 选了区域，没选户型、价格、面积
                    grid = Grid(width=1200, height=600)
                    values_housetype = [
                        Zufang.objects.filter(city=city).filter(zone=house_args[0]).filter(
                            housenum=room_map2[i]).count() if i != "四室以上" else
                        Zufang.objects.filter(city=city).filter(zone=house_args[0]).filter(
                            housenum__gt=4).count() for i in attr_housetype]
                    bar_housetype = bar_ploy("租房户型分布图", attr_housetype, values_housetype, title_pos="0%")

                    values_price = [
                        Zufang.objects.filter(city=city).filter(zone=house_args[0]).filter(
                            price__gte=i[0]).filter(price__lt=i[1]).count() for i in price_map]
                    bar_price = bar_ploy("租房价格分布图", attr_price, values_price, title_pos="51%")

                    values_area = [
                        Zufang.objects.filter(city=city).filter(zone=house_args[0]).filter(
                            housearea__gte=i[0]).filter(
                            housearea__lt=i[1]).count() for i in area_map]
                    bar_area = bar_ploy("租房面积分布图", attr_area, values_area, title_top="51%")

                    bar_temp = Bar()
                    grid.add(bar_housetype, grid_bottom="60%", grid_right="60%")
                    grid.add(bar_price, grid_bottom="60%", grid_left="60%")
                    grid.add(bar_area, grid_top="60%", grid_right="60%")
                    grid.add(bar_temp, grid_top="60%", grid_left="60%")
    else:   # 没选区域
        if len(house_args[1]) != 0:
            if len(house_args[2]) != 0:
                if len(house_args[3]) != 0:    # 选了价格、面积、户型
                    grid = Grid(width=1200)
                    values = [
                        Zufang.objects.filter(city=city).filter(
                            housearea__gte=int(house_args[2][0])).filter(
                            housearea__lt=int(house_args[2][1])).filter(price__gte=int(house_args[1][0])).filter(
                            price__lt=int(house_args[1][1])).filter(housenum=room_map2[house_args[3]]).filter(
                            per_price__gte=int(i)).filter(per_price__lt=int(i) + 10).count() if house_args[3]!="四室以上" else
                        Zufang.objects.filter(city=city).filter(
                            housearea__gte=int(house_args[2][0])).filter(
                            housearea__lt=int(house_args[2][1])).filter(price__gte=int(house_args[1][0])).filter(
                            price__lt=int(house_args[1][1])).filter(housenum__gt=4).filter(
                            per_price__gte=int(i)).filter(per_price__lt=int(i) + 10).count() for i in attr]
                    bar = bar_ploy("每平米租金分布图", attr, values, title_pos="51%", xname="(元)", yname="(个)")

                    values_zone = [
                        Zufang.objects.filter(city=city).filter(zone=i).filter(
                            housenum=room_map2[house_args[3]]).filter(
                            housearea__gte=int(house_args[2][0])).filter(housearea__lt=int(house_args[2][1])).filter(
                            price__gte=int(house_args[1][0])).filter(price__lt=int(house_args[1][1])).count() if house_args[3] != "四室以上" else
                        Zufang.objects.filter(city=city).filter(zone=i).filter(
                            housenum__gt=4).filter(
                            housearea__gte=int(house_args[2][0])).filter(housearea__lt=int(house_args[2][1])).filter(
                            price__gte=int(house_args[1][0])).filter(price__lt=int(house_args[1][1])).count()
                        for i in city_zone[city]]
                    bar_zone = bar_ploy("租房区域分布图", city_zone[city], values_zone, title_pos="0%")

                    grid.add(bar, grid_left="60%")
                    grid.add(bar_zone, grid_right="60%")
                else:   # 选了价格、面积，没选区域、户型
                    grid = Grid(width=1200, height=600)
                    values_zone = [
                        Zufang.objects.filter(city=city).filter(zone=i).filter(
                            housearea__gte=int(house_args[2][0])).filter(housearea__lt=int(house_args[2][1])).filter(
                            price__gte=int(house_args[1][0])).filter(price__lt=int(house_args[1][1])).count() for i in
                        city_zone[city]]
                    bar_zone = bar_ploy("租房区域分布图", city_zone[city], values_zone, title_pos="51%")

                    values_housetype = [
                        Zufang.objects.filter(city=city).filter(housenum=room_map2[i]).filter(
                            price__gte=int(house_args[1][0])).filter(
                            price__lt=int(house_args[1][1])).filter(
                            housearea__gte=int(house_args[2][0])).filter(
                            housearea__lt=int(house_args[2][1])).count() if i != "四室以上" else
                        Zufang.objects.filter(city=city).filter(housenum__gt=4).filter(
                            price__gte=int(house_args[1][0])).filter(
                            price__lt=int(house_args[1][1])).filter(
                            housearea__gte=int(house_args[2][0])).filter(
                            housearea__lt=int(house_args[2][1])).count() for i in attr_housetype]
                    bar_housetype = bar_ploy("租房户型分布图", attr_housetype, values_housetype, title_pos="0%")

                    value_zone_along_housetype = [[Zufang.objects.filter(city=city).filter(zone=i).filter(
                        price__gte=house_args[1][0]).filter(price__lt=int(house_args[1][1])).filter(
                        housearea__gte=house_args[2][0]).filter(housearea__lt=house_args[2][1]).filter(
                        housenum=room_map2[j]).count() for i in city_zone[city]] if j != "四室以上" else
                                                  [Zufang.objects.filter(city=city).filter(zone=i).filter(
                                                      price__gte=house_args[1][0]).filter(
                                                      price__lt=int(house_args[1][1])).filter(
                                                      housearea__gte=house_args[2][0]).filter(
                                                      housearea__lt=house_args[2][1]).filter(
                                                      housenum__gt=4).count() for i in city_zone[city]] for j in room_map2]
                    value_zone_along_housetype = value_to_percentage(value_zone_along_housetype)

                    bar_along_housetype = Bar("户型", title_top="55%", title_color="#ffe8fe")
                    for idx, value in enumerate(value_zone_along_housetype):
                        bar_along_housetype.add(
                            attr_housetype[idx],
                            x_axis=city_zone[city],
                            y_axis=value,
                            xaxis_label_textcolor='#ffe8fe',
                            yaxis_label_textcolor='#ffe8fe',
                            xaxis_name="",
                            yaxis_name="%",
                            xaxis_line_color="#ffe8fe",
                            yaxis_line_color="#ffe8fe",
                            xaxis_name_pos='end',
                            is_toolbox_show=False,
                            legend_pos='10%',
                            legend_top='50%',
                            legend_text_color='#ffe8fe'
                        )

                        value_housetype_along_zone = [[Zufang.objects.filter(city=city).filter(zone=j).filter(
                            price__gte=int(house_args[1][0])).filter(price__lt=int(house_args[1][1])).filter(
                            housearea__gte=int(house_args[2][0])).filter(housearea__lt=int(house_args[2][1])).filter(
                            housenum=room_map2[i]).count() if i != "四室以上" else
                                                       Zufang.objects.filter(city=city).filter(zone=j).filter(
                                                           price__gte=int(house_args[1][0])).filter(
                                                           price__lt=int(house_args[1][1])).filter(
                                                           housearea__gte=int(house_args[2][0])).filter(
                                                           housearea__lt=int(house_args[2][1])).filter(
                                                           housenum__gt=4).count()
                                                       for i in room_map2] for j in city_zone[city]]
                        value_housetype_along_zone = value_to_percentage(value_housetype_along_zone)

                        bar_along_zone = Bar("面积", title_top="55%", title_pos="51%", title_color="#ffe8fe")
                        for idx, value in enumerate(value_housetype_along_zone):
                            bar_along_zone.add(
                                city_zone[city][idx],
                                x_axis=attr_housetype,
                                y_axis=value,
                                xaxis_label_textcolor='#ffe8fe',
                                yaxis_label_textcolor='#ffe8fe',
                                xaxis_name="",
                                yaxis_name="%",
                                xaxis_line_color="#ffe8fe",
                                yaxis_line_color="#ffe8fe",
                                xaxis_name_pos='end',
                                is_toolbox_show=False,
                                legend_pos='right',
                                legend_top='50%',
                                legend_text_color='#ffe8fe'
                            )

                    grid.add(bar_zone, grid_bottom="60%", grid_left="60%")
                    grid.add(bar_housetype, grid_bottom="60%", grid_right="60%")
                    grid.add(bar_along_housetype, grid_top="60%", grid_right="60%")
                    grid.add(bar_along_zone, grid_top="60%", grid_left="60%")
            else:   # 没选面积
                if len(house_args[3]) != 0:    # 选了价格、户型，没选区域、面积
                    grid = Grid(width=1200, height=600)
                    values_zone = [
                        Zufang.objects.filter(city=city).filter(zone=i).filter(
                            housenum=room_map2[house_args[3]]).filter(
                            price__gte=int(house_args[1][0])).filter(price__lt=int(house_args[1][1])).count()
                        if house_args[3] != 0 else
                        Zufang.objects.filter(city=city).filter(zone=i).filter(
                            housenum__gt=4).filter(
                            price__gte=int(house_args[1][0])).filter(price__lt=int(house_args[1][1])).count()
                        for i in city_zone[city]]
                    bar_zone = bar_ploy("租房区域分布图", city_zone[city], values_zone, title_pos="51%")

                    values_area = [
                        Zufang.objects.filter(city=city).filter(housenum=room_map2[house_args[3]]).filter(
                            price__gte=int(house_args[1][0])).filter(
                            price__lt=int(house_args[1][1])).filter(
                            housearea__gte=i[0]).filter(
                            housearea__lt=i[1]).count() if house_args[3] != "四室以上" else
                        Zufang.objects.filter(city=city).filter(housenum__gt=4).filter(
                            price__gte=int(house_args[1][0])).filter(
                            price__lt=int(house_args[1][1])).filter(
                            housearea__gte=i[0]).filter(
                            housearea__lt=i[1]).count() for i in area_map]
                    bar_area = bar_ploy("租房面积分布图", attr_area, values_area, title_pos="0%")

                    value_zone_along_area = [[Zufang.objects.filter(city=city).filter(zone=i).filter(
                        price__gte=house_args[1][0]).filter(price__lt=int(house_args[1][1])).filter(
                        housearea__gte=j[0]).filter(housearea__lt=j[1]).filter(
                        housenum=room_map2[house_args[3]]).count() for i in city_zone[city]] if house_args[3] != "四室以上" else
                                                  [Zufang.objects.filter(city=city).filter(zone=i).filter(
                                                      price__gte=house_args[1][0]).filter(
                                                      price__lt=int(house_args[1][1])).filter(
                                                      housearea__gte=j[0]).filter(
                                                      housearea__lt=j[1]).filter(
                                                      housenum__gt=4).count() for i in city_zone[city]] for j in area_map]
                    value_zone_along_area = value_to_percentage(value_zone_along_area)

                    bar_along_area = Bar("面积", title_top="55%", title_color="#ffe8fe")
                    for idx, value in enumerate(value_zone_along_area):
                        bar_along_area.add(
                            attr_area[idx],
                            x_axis=city_zone[city],
                            y_axis=value,
                            xaxis_label_textcolor='#ffe8fe',
                            yaxis_label_textcolor='#ffe8fe',
                            xaxis_name="",
                            yaxis_name="%",
                            xaxis_line_color="#ffe8fe",
                            yaxis_line_color="#ffe8fe",
                            xaxis_name_pos='end',
                            is_toolbox_show=False,
                            legend_pos='0%',
                            legend_top='50%',
                            legend_text_color='#ffe8fe'
                        )

                        value_area_along_zone = [[Zufang.objects.filter(city=city).filter(zone=j).filter(
                            price__gte=int(house_args[1][0])).filter(price__lt=int(house_args[1][1])).filter(
                            housearea__gte=i[0]).filter(housearea__lt=i[1]).filter(
                            housenum=room_map2[house_args[3]]).count() if house_args[3] != "四室以上" else
                                                       Zufang.objects.filter(city=city).filter(zone=j).filter(
                                                           price__gte=int(house_args[1][0])).filter(
                                                           price__lt=int(house_args[1][1])).filter(
                                                           housearea__gte=i[0]).filter(
                                                           housearea__lt=i[1]).filter(
                                                           housenum__gt=4).count()
                                                       for i in area_map] for j in city_zone[city]]
                        value_area_along_zone = value_to_percentage(value_area_along_zone)

                        bar_along_zone = Bar("区域", title_top="55%", title_pos="51%", title_color="#ffe8fe")
                        for idx, value in enumerate(value_area_along_zone):
                            bar_along_zone.add(
                                city_zone[city][idx],
                                x_axis=attr_area,
                                y_axis=value,
                                xaxis_label_textcolor='#ffe8fe',
                                yaxis_label_textcolor='#ffe8fe',
                                xaxis_name="(/㎡)",
                                yaxis_name="%",
                                xaxis_line_color="#ffe8fe",
                                yaxis_line_color="#ffe8fe",
                                xaxis_name_pos='end',
                                is_toolbox_show=False,
                                legend_pos='95%',
                                legend_top='50%',
                                legend_text_color='#ffe8fe'
                            )

                    grid.add(bar_zone, grid_bottom="60%", grid_right="60%")
                    grid.add(bar_area, grid_bottom="60%", grid_left="60%")
                    grid.add(bar_along_area, grid_top="60%", grid_right="60%")
                    grid.add(bar_along_zone, grid_top="60%", grid_left="60%")
                else:   # 选了价格，没选户型、区域、面积
                    grid = Grid(width=1200, height=600)
                    values_housetype = [
                        Zufang.objects.filter(city=city).filter(price__gte=int(house_args[1][0])).
                            filter(price__lt=int(house_args[1][1])).filter(
                            housenum=room_map2[i]).count() if i != "四室以上" else
                        Zufang.objects.filter(city=city).filter(price__gte=int(house_args[1][0])).
                            filter(price__lt=int(house_args[1][1])).filter(
                            housenum__gt=4).count() for i in attr_housetype]
                    bar_housetype = bar_ploy("租房户型分布图", attr_housetype, values_housetype, title_pos="51%")

                    values_zone = [
                        Zufang.objects.filter(city=city).filter(zone=i).filter(
                            price__gte=house_args[1][0]).filter(price__lt=house_args[1][1]).count() for i in city_zone[city]]
                    bar_zone = bar_ploy("租房区域分布图", city_zone[city], values_zone, title_pos="0%")

                    values_area = [
                        Zufang.objects.filter(city=city).filter(price__gte=int(house_args[1][0])).filter(
                            price__lt=int(house_args[1][1])).filter(
                            housearea__gte=i[0]).filter(housearea__lt=i[1]).count() for i in area_map]
                    bar_area = bar_ploy("租房面积分布图", attr_area, values_area, title_top="51%")

                    bar_temp = Bar()
                    grid.add(bar_housetype, grid_bottom="60%", grid_left="60%")
                    grid.add(bar_zone, grid_bottom="60%", grid_right="60%")
                    grid.add(bar_area, grid_top="60%", grid_right="60%")
                    grid.add(bar_temp, grid_top="60%", grid_left="60%")
        else:   # 没选价格
            if len(house_args[2]) != 0:
                if len(house_args[3]) != 0:    # 选了面积、户型，没选区域、价格
                    grid = Grid(width=1200, height=600)
                    values_zone = [
                        Zufang.objects.filter(city=city).filter(zone=i).filter(
                            housearea__gte=int(house_args[2][0])).filter(
                            housearea__lt=int(house_args[2][1])).filter(
                            housenum=room_map2[house_args[3]]).count() if house_args[3] != "四室以上" else
                        Zufang.objects.filter(city=city).filter(zone=i).filter(
                            housearea__gte=int(house_args[2][0])).filter(
                            housearea__lt=int(house_args[2][1])).filter(
                            housenum__gt=4).count() for i in city_zone[city]]
                    bar_zone = bar_ploy("租房区域分布图", city_zone[city], values_zone, title_pos="51%")

                    values_price = [
                        Zufang.objects.filter(city=city).filter(housenum=room_map2[house_args[3]]).filter(
                            price__gte=i[0]).filter(
                            price__lt=i[1]).filter(
                            housearea__gte=int(house_args[2][0])).filter(
                            housearea__lt=int(house_args[2][1])).count() if house_args[3] != "四室以上" else
                        Zufang.objects.filter(city=city).filter(housenum__gt=4).filter(
                            price__gte=i[0]).filter(
                            price__lt=i[1]).filter(
                            housearea__gte=int(house_args[2][0])).filter(
                            housearea__lt=int(house_args[2][1])).count() for i in price_map]
                    bar_price = bar_ploy("租房价格分布图", attr_price, values_price, title_pos="0%")

                    value_zone_along_price = [[Zufang.objects.filter(city=city).filter(zone=i).filter(
                        price__gte=j[0]).filter(price__lt=j[1]).filter(
                        housearea__gte=int(house_args[2][0])).filter(
                        housearea__lt=int(house_args[2][1])).filter(
                        housenum=room_map2[house_args[3]]).count() for i in city_zone[city]] if j != "四室以上" else
                                              [Zufang.objects.filter(city=city).filter(zone=i).filter(price__gte=j[0]).filter(
                                                  price__lt=j[1]).filter(housearea__gte=int(house_args[2][0])).filter(
                                                  housearea__lt=int(house_args[2][1])).filter(
                                                  housenum__gt=4).count() for i in city_zone[city]] for j in price_map]
                    value_zone_along_price = value_to_percentage(value_zone_along_price)

                    bar_along_price = Bar("价格", title_top="55%", title_color="#ffe8fe")
                    for idx, value in enumerate(value_zone_along_price):
                        bar_along_price.add(
                            attr_price[idx],
                            x_axis=city_zone[city],
                            y_axis=value,
                            xaxis_label_textcolor='#ffe8fe',
                            yaxis_label_textcolor='#ffe8fe',
                            xaxis_name="",
                            yaxis_name="%",
                            xaxis_line_color="#ffe8fe",
                            yaxis_line_color="#ffe8fe",
                            xaxis_name_pos='end',
                            is_toolbox_show=False,
                            legend_pos='90%',
                            legend_top='50%',
                            legend_text_color='#ffe8fe'
                        )

                        value_price_along_zone = [[Zufang.objects.filter(city=city).filter(zone=j).filter(
                            price__gte=i[0]).filter(price__lt=i[1]).filter(
                            housearea__gte=int(house_args[2][0])).filter(housearea__lt=int(house_args[2][1])).filter(
                            housenum=room_map2[house_args[3]]).count() if house_args[3] != "四室以上" else
                                                       Zufang.objects.filter(city=city).filter(zone=j).filter(
                                                           price__gte=i[0]).filter(
                                                           price__lt=i[1]).filter(
                                                           housearea__gte=int(house_args[2][0])).filter(
                                                           housearea__lt=int(house_args[2][1])).filter(
                                                           housenum__gt=4).count()
                                                       for i in price_map] for j in city_zone[city]]
                        value_price_along_zone = value_to_percentage(value_price_along_zone)

                        bar_along_zone = Bar("区域", title_top="55%", title_pos="51%", title_color="#ffe8fe")
                        for idx, value in enumerate(value_price_along_zone):
                            bar_along_zone.add(
                                city_zone[city][idx],
                                x_axis=attr_price,
                                y_axis=value,
                                xaxis_label_textcolor='#ffe8fe',
                                yaxis_label_textcolor='#ffe8fe',
                                xaxis_name="(元)",
                                yaxis_name="%",
                                xaxis_line_color="#ffe8fe",
                                yaxis_line_color="#ffe8fe",
                                xaxis_name_pos='end',
                                is_toolbox_show=False,
                                legend_pos='0%',
                                legend_top='50%',
                                legend_text_color='#ffe8fe'
                            )

                    grid.add(bar_zone, grid_bottom="60%", grid_left="60%")
                    grid.add(bar_price, grid_bottom="60%", grid_right="60%")
                    grid.add(bar_along_price, grid_top="60%", grid_left="60%")
                    grid.add(bar_along_zone, grid_top="60%", grid_right="60%")
                else:   # 选了面积，没选户型、区域、价格
                    grid = Grid(width=1200, height=600)
                    values_zone = [
                        Zufang.objects.filter(city=city).filter(zone=i).filter(
                            housearea__gte=int(house_args[2][0])).filter(
                            housearea__lt=int(house_args[2][1])).count() for i in city_zone[city]]
                    bar_zone = bar_ploy("租房区域分布图", city_zone[city], values_zone, title_pos="0%")

                    values_price = [
                        Zufang.objects.filter(city=city).filter(housearea__gte=int(house_args[2][0])).filter(
                            housearea__lt=int(house_args[2][1])).filter(price__gte=i[0]).filter(
                            price__lt=i[1]).count() for i in price_map]
                    bar_price = bar_ploy("租房价格分布图", attr_price, values_price, title_pos="51%")

                    values_housetype = [
                        Zufang.objects.filter(city=city).filter(housearea__gte=int(house_args[2][0])).filter(
                            housearea__lt=int(house_args[2][1])).filter(
                            housenum=room_map2[i]).count() if i != "四室以上" else
                        Zufang.objects.filter(city=city).filter(housearea__gte=int(house_args[2][0])).filter(
                            housearea__lt=int(house_args[2][1])).filter(
                            housenum__gt=4).count() for i in attr_housetype]
                    bar_housetype = bar_ploy("租房户型分布图", attr_housetype, values_housetype, title_top="51%")

                    bar_temp = Bar()
                    grid.add(bar_zone, grid_bottom="60%", grid_right="60%")
                    grid.add(bar_price, grid_bottom="60%", grid_left="60%")
                    grid.add(bar_housetype, grid_top="60%", grid_right="60%")
                    grid.add(bar_temp, grid_top="60%", grid_left="60%")
            else:   # 没选面积
                if len(house_args[3]) != 0:    #选了户型，没选区域、价格、面积
                    grid = Grid(width=1200, height=600)
                    values_zone = [
                        Zufang.objects.filter(city=city).filter(zone=i).filter(
                            housenum=room_map2[house_args[3]]).count() if house_args[3] != "四室以上" else
                        Zufang.objects.filter(city=city).filter(zone=i).filter(
                            housenum__gt=4).count() for i in city_zone[city]]
                    bar_zone = bar_ploy("租房区域分布图", city_zone[city], values_zone, title_pos="0%")

                    values_price = [
                        Zufang.objects.filter(city=city).filter(housenum=room_map2[house_args[3]]).filter(
                            price__gte=i[0]).filter(price__lt=i[1]).count() if house_args[3] != "四室以上" else
                        Zufang.objects.filter(city=city).filter(housenum__gt=4).filter(
                            price__gte=i[0]).filter(price__lt=i[1]).count() for i in price_map]
                    bar_price = bar_ploy("租房价格分布图", attr_price, values_price, title_pos="51%")

                    values_area = [
                        Zufang.objects.filter(city=city).filter(housenum=room_map2[house_args[3]]).filter(
                            housearea__gte=i[0]).filter(
                            housearea__lt=i[1]).count() if house_args[3] != "四室以上" else
                        Zufang.objects.filter(city=city).filter(housenum__gt=4).filter(
                            housearea__gte=i[0]).filter(
                            housearea__lt=i[1]).count() for i in area_map]
                    bar_area = bar_ploy("租房面积分布图", attr_area, values_area, title_top="51%")

                    bar_temp = Bar()
                    grid.add(bar_zone, grid_bottom="60%", grid_right="60%")
                    grid.add(bar_price, grid_bottom="60%", grid_left="60%")
                    grid.add(bar_area, grid_top="60%", grid_right="60%")
                    grid.add(bar_temp, grid_top="60%", grid_left="60%")
                else:   # 什么都不选，不做处理
                    grid = Grid(width=1200)
                    pass
    return grid


def bar_ploy(name, attr, values, title_pos="", title_top="", xname="", yname=""):
    bar = Bar(title=name, title_pos=title_pos, title_top=title_top, title_color="#ffe8fe")
    bar.add("",
            x_axis=attr,
            y_axis=values,
            xaxis_label_textcolor='#ffe8fe',
            yaxis_label_textcolor='#ffe8fe',
            xaxis_name=xname,
            yaxis_name=yname,
            xaxis_line_color="#ffe8fe",
            yaxis_line_color="#ffe8fe",
            xaxis_name_pos='end',
            is_toolbox_show=False,
            )
    return bar


def line_ploy(name, attr, values,title_pos):
    line = Line(title=name, title_pos=title_pos)
    line.add("",
            x_axis=attr,
            y_axis=values,
            xaxis_label_textcolor='#ffe8fe',
            yaxis_label_textcolor='#ffe8fe',
            xaxis_name='（元/平米）',
            xaxis_name_pos='end',
            is_toolbox_show=False,
            )
    return line


def pie(attr, values, width, center):

    pie = Pie(width=width)
    pie.add("",
            attr,
            values,
            is_label_show=True,
            is_toolbox_show=False,
            legend_orient="vertical",
            legend_pos="8%",
            legend_top="14%",
            legend_text_color="#ffe8fe",
            center=center,
            )
    return pie


def city_map(city):
    map = Map("", width=1200, height=600)
    attr_map = [i+'区' for i in city_zone[city]]
    value_map = [Zufang.objects.filter(city=city).filter(zone=i.strip('区')).count() for i in attr_map]
    map.add(
        "",
        attr_map,
        value_map,
        maptype=city,
        is_visualmap=True,
        visual_text_color="#f44",
        is_toolbox_show=False,
        visual_top="220px",
        visual_pos="750px",
        is_roam=False,
        visual_range=[0, 8000],
        visual_range_color=['#4575b4', '#74add1', '#abd9e9', '#e0f3f8', '#ffffbf',
                        '#fee090', '#fdae61', '#f46d43', '#d73027', '#a50026'],
    )
    return map


def value_to_percentage(values: list)->list:
    value_temp = []
    for value in values:
        v_list = []
        for i in value:
            try:
                temp = int((i / sum(value)) * 100)
            except:
                temp = 0
            v_list.append(temp)
        value_temp.append(v_list)
    return value_temp


def count_num(house_info: list, city: str)->tuple:
    house = Zufang.objects
    for idx, info in enumerate(house_info):
        if idx==0 and len(info):
            house = house.filter(zone=info)
        elif idx==1 and len(info):
            house = house.filter(price__gte=info[0]).filter(price__lt=info[1])
        elif idx==2 and len(info):
            house = house.filter(housearea__gte=info[0]).filter(housearea__lt=info[1])
        elif idx==3 and len(info):
            if info != "四室以上":
                house = house.filter(housenum=room_map2[info])
            else:
                house = house.filter(housenum__gt=4)
        elif idx==4 and len(info):
            house = house.filter(city=info)

    house_num = house.count()
    if house_num == 0:
        averge_price = 0
        averge_area = 0
        return (house_num, averge_price, averge_area)
    averge_price = int(house.aggregate(Avg('price'))['price__avg'])
    averge_area = int(house.aggregate(Avg('housearea'))['housearea__avg'])
    return (house_num, averge_price, averge_area)


def add_session(path: str)->dict:
    li = path_resolute(path)
    info = {'zone': '',
            'housetype': '',
            'price': '',
            'area': '',
            'city': ''}
    if len(li[0]):
        info['zone'] = li[0]
    if len(li[1]):
        info['price'] = li[1][1]
    if len(li[2]):
        info['area'] = li[2][1]
    if len(li[3]):
        info['housetype'] = li[3]
    if len(li[4]):
        info['city'] = li[4]
    return info
