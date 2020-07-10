from walkscore_calculator import WalkscoreCalculator
import time
import csv


cities_epsg = {'石家庄':32650, '太原':32649, '呼和浩特':32649, '沈阳':32651, '长春':32651, '哈尔滨':32652, '南京':32650,
          '杭州':32650, '合肥':32650, '福州':32650, '南昌':32650, '济南':32650, '郑州':32649, '武汉':32650, '长沙':32649, 
          '广州':32649, '南宁':32649, '海口':32649, '成都':32648, '贵阳':32648, '昆明':32648, '拉萨':32646, '西安':32649, 
          '兰州':32648, '西宁':32647, '银川':32648, '乌鲁木齐':32645, '北京':32650, 
          '上海':32651, '天津':32650, '重庆':32648}
def Cul(city, weight_table, road, src_poi, catch_road_poi, result, part_num):
    WS_cal = WalkscoreCalculator(city)
    seg_length = 300
    poi_num = 100 #提取的最近邻poi数目
    
    print('城市：' + city)
    WS_cal.flag = input("是否写入？1为写入，2为不写入，其他字符为退出\n")
    if WS_cal.flag not in ['1', '2']:
        return
    WS_cal.Set_Weights(weight_table)  
    #WS_cal.Set_Road_Linedata('D:/all_cities/高德路网_final/' + city + '.shp')
    WS_cal.Set_Road_Linedata(road) 
    WS_cal.Set_POI_Pointdata(src_poi, catch_road_poi) 
    WS_cal.Set_New_Road_Linedata(result)
    start_time = time.time()
    WS_cal.Compute_Road_Walkscore(seg_length, poi_num, part_num)
    end_time = time.time()
    print('完成! 一共用时：%f秒' % (end_time-start_time)) 
    if WS_cal.flag == '1':
        hyper_paras = [weight_table, road, src_poi, catch_road_poi, result, str(seg_length), time.asctime(time.localtime(start_time)), time.asctime(time.localtime(time.time())), str(end_time-start_time), str(poi_num)]        
        temp_id = None
        with open('../log.csv', 'r', newline='') as log:
            rows = list(csv.reader(log))
            temp_id = int(rows[-1][0]) + 1            
        with open('../log.csv', 'a', newline='') as log:
            writer = csv.writer(log)
            writer.writerow([temp_id] + hyper_paras)

if __name__ == "__main__":
    cities = ['西宁']
    part_num = 3
    for city in cities:
        weight_table = '../权重表/原始权重表.csv'         #权重表
        road = '../城市路网/' + city + '.shp'      #路网 
        src_poi = '../POI/' + city + '.csv'      #原始poi数据
        catch_road_poi = '../抓路点/' + city + '.csv'     #抓路后的POI数据
        result = '../结果/' + city + '_原始' + '_part' + str(part_num) + '.shp'#结果数据
        Cul(city, weight_table, road, src_poi, catch_road_poi, result, part_num)
'''
[2014434, 0]
完成! 一共用时：3218.523764秒
seg_length=350
28300个点 没用kdtree

35355个点 大约45分钟
一开始的几个预期时间只有18-19分钟，后来会涨上去，应该是前面几个周围的POI少，所以路网距离都不需要怎么算

OSM路网，91452个点，四个控制台，单个大概200分钟，cpu基本满了
OSM路网，91452个点weightresultlocal_test权重表实测，8567秒
OSM路网，91452个点weightresultnonlocal_test权重表实测，11628.481088秒
'''