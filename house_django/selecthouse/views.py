from houseshow.views import path_resolute, zone_map, room_map2
from houseshow.models import Zufang
from django.http import HttpResponse
from django.template import loader

# Create your views here.


def selecthouse(request):
    house = house_resolute(request.path)
    request.session['path'] = request.path
    template = loader.get_template('selecthouse/selecthouse.html')
    count = house.count()
    page_count = count // 20 + 1
    context = dict(
        house=house[:20],
        page=range(1, page_count+1),
        page_count=page_count,
        temp=range(1, 9),
        active_num=1,
        first=1,
    )
    return HttpResponse(template.render(context, request))

def choose_page(request, page):
    page = int(page)
    house = house_resolute(request.session['path'])
    template = loader.get_template("selecthouse/selecthouse.html")
    page_count = house.count() // 20 + 1
    bias_first = page - 1
    bias_last = page_count-page
    if page_count <= 10:
        page_num = [str(i) for i in range(1, page_count+1)]
    else:
        if bias_first < 7 and bias_last > 4:
            page_num = [str(i) for i in range(1, page)]
            temp = [str(i) for i in range(page, 11)]
            temp[-1] = str(page_count)
            temp[-2] = str(page_count-1)
            temp[-3] = str(page_count-2)
            temp[-4] = '...'
            page_num.extend(temp)
            try:
                idx = page_num.index(str(page))
                if page_num[idx+1] == '...':
                    page_num[idx-2] = '...'
                    page_num[idx-1] = str(page)
                    page_num[idx] = str(page+1)
            except:
                idx2 = page_num.index('...')
                page_num[idx2-1] = page + 1
                page_num[idx2-2] = page
                page_num[idx2-3] = '...'
        elif bias_first < 7 and bias_last <= 3:
            page_num = [str(i) for i in range(1, page)]
            temp = [str(i) for i in range(page, 10)]
            temp[-1] = str(page_count)
            temp[-2] = '...'
        elif bias_last < 6:

            temp = [str(i) for i in range(page, page_count+1)]
            page_num = [str(i) for i in range(1, 10-len(temp)+1)]
            page_num[-1] = str(page-1)
            page_num[-2] = '...'
            page_num.extend(temp)
        else:
            page_num = ['1', '2', '...', str(page-2), str(page-1), str(page), str(page+1), str(page+2), '...', str(page_count)]
    context = dict(
        template=template,
        house=house[(page-1)*20: page*20],
        page=str(page),
        page_num=page_num,
        first=0,
    )
    return HttpResponse(template.render(context, request))


def house_resolute(path):
    house_info = path_resolute(path.replace('selecthouse/', ''))
    house = Zufang.objects
    for idx, info in enumerate(house_info):
        if idx == 0 and len(info):
            house = house.filter(zone=zone_map[info])
        elif idx == 1 and len(info):
            house = house.filter(price__gte=info[0]).filter(price__lt=info[1])
        elif idx == 2 and len(info):
            house = house.filter(housearea__gte=info[0]).filter(housearea__lt=info[1])
        elif idx == 3 and len(info):
            if info != "四室以上":
                house = house.filter(housenum=room_map2[info])
            else:
                house = house.filter(housenum__gt=4)
    return house
