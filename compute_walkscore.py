from osgeo import ogr
from get_distance import GetNetDistances
import csv
import time
import math
import numba as nb
import numpy as np

def run_time(func):
    def call_fun(*args, **kwargs):
        start_time = time.time()
        f = func(*args, **kwargs)
        end_time = time.time()
        print('%s() run time：%s ms' % (func.__name__, 1000*(end_time - start_time)))
        return f
    return call_fun


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
                     
def GetNeededPointsIndice_KDtree(start_point_coord, kdtree, k, distance_upper_bound):
    '''获取距离出发点最近的k个POI点，距离上限是distance_upper_bound'''
    query_result = kdtree.query(np.array(start_point_coord), k=k, distance_upper_bound=distance_upper_bound)
    if k is None:
        return query_result[1]
    else:
        return query_result[1].tolist()

def Compute_Walkscore_Road(start_points_info:dict, weight_tables:dict, MultiType_poi_points:dict, road_points, G, kdtrees, poi_num, scale):          
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
            kdtree = kdtrees[poi_type] #这是poi点构成的kdtree
            #print('points: ' + str(len(points)))
            #a = time.time()
            
            #poi_num用来限制去计算路网距离的POI数目，要不然计算所有在2400m直线距离内的POI的话太耗时了
            needed_points_indice = GetNeededPointsIndice_KDtree(temp_start_point, kdtree, poi_num, 2400) 
            
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

            for i in range(min(len(weight_table), len(net_distances))):
                value += weight_table[i] * Attenuate(net_distances[i])
            ws[poi_type] = ws[poi_type] + value - temp_value
           
        road_values += value
    
    for poi_type in MultiType_poi_points.keys():
        ws[poi_type] = ws[poi_type] / count * scale
    walkscore = road_values / count * scale
    ws['main'] = walkscore
    return ws
