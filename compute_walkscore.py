from osgeo import ogr
from get_distance import GetNetDistances
import csv
import time
import math
import numba as nb
import numpy as np


def Attenuate(distance):
    '''距离衰减系数'''
    if distance <= 400:
        return 1
    elif 400 < distance <= 1600:
        return (-11/15000) * distance + (97/75)
    elif 1600 < distance <= 2400:
        return 0.12
    else:
        return 0
                       
def GetNeededPointsIndice_KDtree(start_point_coord, kdtree, needed_count, distance_upper_bound):
    query_result = kdtree.query(np.array(start_point_coord), k=needed_count, distance_upper_bound=distance_upper_bound)
    return query_result[1].tolist()

def Compute_Walkscore_Road(start_points_info:dict, weight_tables:dict, MultiType_poi_points:dict, road_points, G, kdtrees):          
    '''计算步行指数'''
    type_weights = {}
    for weights_types in weight_tables.values():
        type_weights[weights_types[1]] = weights_types[0]
    road_values = 0
    count = len(start_points_info)
    ws = dict.fromkeys([temp[1] for temp in weight_tables.values()], 0.0)
    for temp_start_point, pre_nex_points in start_points_info.items():    
        '''遍历一条道路上所有的出发点'''
        value = 0   #每一个出发点的步行指数
        #print(temp_start_point)
        for poi_type, poi_points in MultiType_poi_points.items():
            '''遍历每一个种类和对应的poi点'''

            temp_value = value
            needed_points = []
            weight_table = type_weights[poi_type]
            kdtree = kdtrees[poi_type] #这是poi点构成的树
            #print('points: ' + str(len(points)))
            #a = time.time()
            
            needed_points_indice = GetNeededPointsIndice_KDtree(temp_start_point, kdtree, len(weight_table)*2, 2400)
            for index in needed_points_indice:
                if index < len(poi_points):
                    needed_points.append(poi_points[index])
            #print(time.time()-a)
            #print('needed_points: ' + str(len(needed_points)))
            b = time.time()
            #print(needed_points)
            if len(needed_points) != 0:
                net_distances = GetNetDistances(temp_start_point, needed_points, pre_nex_points, road_points, G)
                net_distances.sort()
            else:
                net_distances = []
            #print('net_distances: ', net_distances)
            #print(time.time()-b)
            #print('')
            for i in range(min(len(weight_table), len(net_distances))):
                value += weight_table[i] * Attenuate(net_distances[i])
            ws[poi_type] = ws[poi_type] + value - temp_value
           
        road_values += value
    
    for poi_type in MultiType_poi_points.keys():
        ws[poi_type] = ws[poi_type] / count
    walkscore = road_values / count
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
            weight_tables = weight_tables[poi_type]
            needed_poi_number = len(weight_tables)
            
            buffer_400 = temp_geo_start.Buffer(400)
            

            
            poi_points_geo_in_400buffer = SingleType_poi_points_geo.Intersection(buffer_400)
            count_in_400buffer = poi_points_geo_in_400buffer.GetGeometryCount()
            i = 0
            for i in range(min(count_in_400buffer, needed_poi_number)):
                value += weight_tables[i]
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
                    value += weight_tables[i] * Attenuate(distances[k])
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
                    value += weight_tables[i] * 0.12
                    i += 1
        
        start_pointInfo.Update_Walkscore(value*100/15)
        end_time = time.time()
        print('步行指数：%f，用时：%f秒' % (value*100/15, end_time-start_time))