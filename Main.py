from walkscore_calculator import WalkscoreCalculator
import time


cities = ['南京']
cities_epsg = {'石家庄':32650, '太原':32649, '呼和浩特':32649, '沈阳':32651, '长春':32651, '哈尔滨':32652, '南京':32650,
          '杭州':32650, '合肥':32650, '福州':32650, '南昌':32650, '济南':32650, '郑州':32649, '武汉':32650, '长沙':32649, 
          '广州':32649, '南宁':32649, '海口':32649, '成都':32648, '贵阳':32648, '昆明':32648, '拉萨':32646, '西安':32649, 
          '兰州':32648, '西宁':32647, '银川':32648, '乌鲁木齐':32645, '北京':32650, 
          '上海':32651, '天津':32650, '重庆':32648}
def Cul():
    for city in cities:
        WS_cal = WalkscoreCalculator(city)
        
        #权重表（csv格式）
        WS_cal.Set_Weights('../权重表/weightresultnonlocal.csv') 
        
        #路网（shp格式）
        WS_cal.Set_Road_Linedata('../OSM路网_投影_改/' + city + '.shp')

        #POI数据（csv格式）
        WS_cal.Set_POI_Pointdata('../Road_Points_新版/' + city + '.csv') 

        #结果数据（shp格式）
        WS_cal.Set_New_Road_Linedata('../Results_新版/' + city + '_nonlocal.shp')
        
        #道路出发点间隔
        seg_length = 300

        start_time = time.time()
        WS_cal.Compute_Road_Walkscore(seg_length)
        end_time = time.time()
        print('完成! 一共用时：%f秒' % (end_time-start_time))        

if __name__ == "__main__":
    Cul()
