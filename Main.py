from walkscore_calculator import WalkscoreCalculator
import time
#cities = ['北京','天津', '济南', '南京','上海', '杭州', '福州', '广州']
cities = ['南京']#, '福州', '杭州', '济南']
cities_epsg = {'石家庄':32650, '太原':32649, '呼和浩特':32649, '沈阳':32651, '长春':32651, '哈尔滨':32652, '南京':32650,
          '杭州':32650, '合肥':32650, '福州':32650, '南昌':32650, '济南':32650, '郑州':32649, '武汉':32650, '长沙':32649, 
          '广州':32649, '南宁':32649, '海口':32649, '成都':32648, '贵阳':32648, '昆明':32648, '拉萨':32646, '西安':32649, 
          '兰州':32648, '西宁':32647, '银川':32648, '乌鲁木齐':32645, '北京':32650, 
          '上海':32651, '天津':32650, '重庆':32648}
def Cul():
    for city in cities:
        WS_cal = WalkscoreCalculator(city)
        
        #权重表
        WS_cal.Set_Weights('../权重表/weightresultnonlocal.csv') 
        
        #路网
        #WS_cal.Set_Road_Linedata('D:/all_cities/高德路网_final/' + city + '.shp')
        WS_cal.Set_Road_Linedata('../OSM路网_投影_改/' + city + '.shp')
        #POI数据
        WS_cal.Set_POI_Pointdata('../Road_Points_新版/' + city + '.csv') 

        #结果数据
        WS_cal.Set_New_Road_Linedata('../Results_新版/' + city + '_nonlocal.shp')
        
        seg_length = 300

        start_time = time.time()
        WS_cal.Compute_Road_Walkscore(seg_length)
        end_time = time.time()
        print('完成! 一共用时：%f秒' % (end_time-start_time))        

if __name__ == "__main__":
    #POIcrawler()
    #POIfrom_csv_to_shp()
    #Roadcrawler()
    Cul()
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