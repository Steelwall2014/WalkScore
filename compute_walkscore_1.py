from attenuator import Attenuate
from osgeo import ogr
from networkx_readshp import *
import time
from get_distance import net_Distance
'''
这个是分块的算法，先算400m内的POI点满不满足要求，不满足再找400m外1600m内的，以此类推
'''
'''计算道路步行指数'''
def Compute_Walkscore_Road(start_points_info, weight_tables:dict, MultiType_poi_points_geo:dict, road_geo, Multi_roads_geos, G):          
    '''计算步行指数'''
    road_values = 0

    for start_pointInfo in start_points_info:    
        '''遍历一条道路上所有的出发点'''
        value = 0   #每一个出发点的步行指数
        temp_geo_start = start_pointInfo.point_geo

        for poi_type, SingleType_poi_points_geo in MultiType_poi_points_geo.items():
            '''遍历每一个种类和对应的poi点'''

            distances = []
            weight_table = weight_tables[poi_type]
            needed_poi_number = len(weight_table)

            buffer_400 = temp_geo_start.Buffer(400)
            buffer_400To1600 = temp_geo_start.Buffer(1600).Difference(buffer_400)
            buffer_1600To2400 = temp_geo_start.Buffer(2400).Difference(temp_geo_start.Buffer(1600))
            
            poi_points_geo_in_400buffer = SingleType_poi_points_geo.Intersection(buffer_400)
            count_in_400buffer = poi_points_geo_in_400buffer.GetGeometryCount()
            i = 0
            for i in range(min(count_in_400buffer, needed_poi_number)):
                value += weight_table[i]
                i += 1

            needed_poi_number = needed_poi_number - count_in_400buffer
            
            if needed_poi_number > 0:      
                poi_points_geo_in_400To1600buffer = SingleType_poi_points_geo.Intersection(buffer_400To1600)
                count_in_400To1600buffer = poi_points_geo_in_400To1600buffer.GetGeometryCount()
                for j in range(count_in_400To1600buffer):
                    temp_poi_point_geo = poi_points_geo_in_400To1600buffer.GetGeometryRef(j)
                    
                    distance = temp_geo_start.Distance(temp_poi_point_geo)
                    distance = net_Distance(G, road_geo, Multi_roads_geos, temp_geo_start, temp_poi_point_geo)
                    distances.append(distance)
                distances.sort()
                k = 0
                for i in range(i, i + min(count_in_400To1600buffer, needed_poi_number)):
                    value += weight_table[i] * Attenuate(distances[k])
                    i += 1
                    k += 1
                poi_points_geo_in_400To1600buffer = SingleType_poi_points_geo.Intersection(buffer_400To1600)
                count_in_400To1600buffer = poi_points_geo_in_400To1600buffer.GetGeometryCount()
                
                needed_poi_number = needed_poi_number - count_in_400To1600buffer
            
            if needed_poi_number > 0:
                buffer_1600To2400 = temp_geo_start.Buffer(2400).Difference(temp_geo_start.Buffer(1600))
                poi_points_geo_in_1600To2400buffer = SingleType_poi_points_geo.Intersection(buffer_1600To2400)
                count_in_1600To2400buffer = poi_points_geo_in_1600To2400buffer.GetGeometryCount()
                for i in range(i, i + min(count_in_1600To2400buffer, needed_poi_number)):
                    value += weight_table[i] * 0.12
                    i += 1
    
        road_values += value
    walkscore = road_values / len(start_points_info)
    return walkscore*100/15

'''面域步行指数暂时没用'''
def Compute_Walkscore_Region(start_points_info, weight_tables:dict, MultiType_poi_points_geo:ogr.Geometry):
    '''计算面域步行指数'''
    count = len(start_points_info)
    print('一共有%d个点' % count)
    print('开始计算面域步行指数...')
    for start_pointInfo in start_points_info:    
        '''遍历所有的出发点'''
        value = 0   #每一个出发点的步行指数
        print('第%d/%d个点' % (start_pointInfo.point_id, count))
        start_time = time.time()
        temp_geo_start = start_pointInfo.point_geo
        for poi_type, SingleType_poi_points_geo in MultiType_poi_points_geo.items():
            '''遍历每一个种类和对应的poi点'''
            distances = []
            weight_table = weight_tables[poi_type]
            needed_poi_number = len(weight_table)
            
            buffer_400 = temp_geo_start.Buffer(400)
            buffer_400To1600 = temp_geo_start.Buffer(1600).Difference(buffer_400)
            buffer_1600To2400 = temp_geo_start.Buffer(2400).Difference(temp_geo_start.Buffer(1600))
            
            poi_points_geo_in_400buffer = SingleType_poi_points_geo.Intersection(buffer_400)
            count_in_400buffer = poi_points_geo_in_400buffer.GetGeometryCount()
            i = 0
            for i in range(min(count_in_400buffer, needed_poi_number)):
                value += weight_table[i]
                i += 1

            needed_poi_number = needed_poi_number - count_in_400buffer
            
            if needed_poi_number > 0:      
                poi_points_geo_in_400To1600buffer = SingleType_poi_points_geo.Intersection(buffer_400To1600)
                count_in_400To1600buffer = poi_points_geo_in_400To1600buffer.GetGeometryCount()
                for j in range(count_in_400To1600buffer):
                    temp_poi_point_geo = poi_points_geo_in_400To1600buffer.GetGeometryRef(j)
                    
                    distance = temp_geo_start.Distance(temp_poi_point_geo)
                    
                    distances.append(distance)
                distances.sort()
                k = 0
                for i in range(i, i + min(count_in_400To1600buffer, needed_poi_number)):
                    value += weight_table[i] * Attenuate(distances[k])
                    i += 1
                    k += 1
                poi_points_geo_in_400To1600buffer = SingleType_poi_points_geo.Intersection(buffer_400To1600)
                count_in_400To1600buffer = poi_points_geo_in_400To1600buffer.GetGeometryCount()
                
                needed_poi_number = needed_poi_number - count_in_400To1600buffer
            
            if needed_poi_number > 0:
                buffer_1600To2400 = temp_geo_start.Buffer(2400).Difference(temp_geo_start.Buffer(1600))
                poi_points_geo_in_1600To2400buffer = SingleType_poi_points_geo.Intersection(buffer_1600To2400)
                count_in_1600To2400buffer = poi_points_geo_in_1600To2400buffer.GetGeometryCount()
                for i in range(i, i + min(count_in_1600To2400buffer, needed_poi_number)):
                    value += weight_table[i] * 0.12
                    i += 1
        
        start_pointInfo.Update_Walkscore(value*100/15)
        end_time = time.time()
        print('步行指数：%f，用时：%f秒' % (value*100/15, end_time-start_time))
                    
