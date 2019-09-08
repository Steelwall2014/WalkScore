from attenuator import Attenuate
from osgeo import ogr
import csv
import time

def Compute_Walkscore_Road(start_points_info, weight_tables:dict, MultiType_poi_points_geo:dict, road_geo):          
    '''计算步行指数'''
    road_values = 0
    count = len(start_points_info)
    ws = dict.fromkeys(['grocery_stores', 
                        'restaurants_and_bars', 
                        'shops', 
                        'cafes', 
                        'banks', 
                        'parks', 
                        'schools', 
                        'bookstores', 
                        'entertain'], 0)
    buffer_2400 = road_geo.Buffer(2400)
    buffer_2600 = road_geo.Buffer(2600)
    poi_points_geo_in_buffer = {}
    for poi_type, SingleType_poi_points_geo in MultiType_poi_points_geo.items():
        if poi_type == 'parks':
            poi_points_geo_in_buffer[poi_type] = SingleType_poi_points_geo.Intersection(buffer_2600)
        else:
            poi_points_geo_in_buffer[poi_type] = SingleType_poi_points_geo.Intersection(buffer_2400)
    for start_pointInfo in start_points_info:    
        '''遍历一条道路上所有的出发点'''
        value = 0   #每一个出发点的步行指数
        temp_geo_start = start_pointInfo.point_geo

        for poi_type in MultiType_poi_points_geo.keys():
            '''遍历每一个种类和对应的poi点'''
            temp_value = value
            distances = []
            weight_table = weight_tables[poi_type]
            count_in_buffer = poi_points_geo_in_buffer[poi_type].GetGeometryCount()
            if count_in_buffer == 0:
                continue
            
            for i in range(count_in_buffer):
                temp_geo = poi_points_geo_in_buffer[poi_type].GetGeometryRef(i)
                distance = temp_geo.Distance(temp_geo_start)
                distances.append(distance)
            distances.sort()
            for i in range(min(len(weight_table), len(distances))):
                if poi_type == 'parks':
                    value += weight_table[i] * Attenuate(distances[i]-200)
                else:
                    value += weight_table[i] * Attenuate(distances[i])
            ws[poi_type] = ws[poi_type] + value - temp_value
        road_values += value
    for poi_type in MultiType_poi_points_geo.keys():
        ws[poi_type] = ws[poi_type] / count * 100/15
    walkscore = road_values / count * 100/15
    ws['main'] = walkscore
    return ws

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
            

            
            poi_points_geo_in_400buffer = SingleType_poi_points_geo.Intersection(buffer_400)
            count_in_400buffer = poi_points_geo_in_400buffer.GetGeometryCount()
            i = 0
            for i in range(min(count_in_400buffer, needed_poi_number)):
                value += weight_table[i]
                i += 1

            needed_poi_number = needed_poi_number - count_in_400buffer
            
            if needed_poi_number > 0:      
                buffer_400To1600 = temp_geo_start.Buffer(1600).Difference(buffer_400)
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
                    
