# -*- coding: utf-8 -*-
"""
Created on Tue Apr  7 16:06:28 2020

@author: 张径舟
将POI点绑定到道路点上，kdtree，效果拔群，从1个小时加速到35秒
"""
from osgeo import ogr
import csv
import numba as nb
import math
import time
from scipy import spatial
import numpy as np


cities = {'石家庄':32650, '太原':32649, '呼和浩特':32649, '沈阳':32651, '长春':32651, '哈尔滨':32652, '南京':32650,
          '杭州':32650, '合肥':32650, '福州':32650, '南昌':32650, '济南':32650, '郑州':32649, '武汉':32650, '长沙':32649, 
          '广州':32649, '南宁':32649, '海口':32649, '成都':32648, '贵阳':32648, '昆明':32648, '拉萨':32646, '西安':32649, 
          '兰州':32648, '西宁':32647, '银川':32648, '乌鲁木齐':32645, '北京':32650, 
          '上海':32651, '天津':32650, '重庆':32648}

def Make_Discre_Road_Points(road_geo:ogr.Geometry, 
                           start_points:dict, 
                           seg_length:float):
    '''
    在road_geo上每隔seg_length取一个出发点（魔改版）
    start_point将会是一个元组而不是Startpoint对象
    (离散道路点, 前点, 后点)
    '''

     
    count = road_geo.GetPointCount()
    total_length = road_geo.Length()
    
    '''如果是在递归中seg_length比路的全长还要长，那就把路的最后一个点作为出发点'''
    if seg_length >= total_length:
        start_point_coord = road_geo.GetPoint_2D(count-1)
        point_A_coord = road_geo.GetPoint_2D(count-2)
        point_B_coord = road_geo.GetPoint_2D(count-1)
        start_points[start_point_coord] = (point_A_coord, point_B_coord)
        return 
    
    first_to_current_length = 0
    temp_length = 0
    temp_x1 = None
    temp_y1 = None
    temp_x2 = None
    temp_y2 = None
    
    '''计算当前线段的长度和累计长度'''
    for index in range(count-1):
        temp_x1 = road_geo.GetX(index)              
        temp_y1 = road_geo.GetY(index)  
        temp_x2 = road_geo.GetX(index+1)
        temp_y2 = road_geo.GetY(index+1)
        temp_length = math.sqrt( (temp_x1-temp_x2)**2 + (temp_y1-temp_y2)**2 )
        first_to_current_length = first_to_current_length + temp_length
        if seg_length < first_to_current_length:
            break
    '''这时从第零个点到第index+1个点的距离大于seg_length了'''

    '''算出发点的坐标'''
    len1 = seg_length - (first_to_current_length - temp_length)
    start_point_x = (len1 / temp_length) * (temp_x2 - temp_x1) + temp_x1
    start_point_y = (len1 / temp_length) * (temp_y2 - temp_y1) + temp_y1
    if temp_x1 == 0:
        print([temp_x1, temp_y1])
    start_points[(start_point_x, start_point_y)] = ((temp_x1, temp_y1), (temp_x2, temp_y2))
    
    '''给出发点后面的点做一个线的几何体，用来进行下一个递归'''
    temp_road_geo = ogr.Geometry(ogr.wkbLineString)
    temp_road_geo.AddPoint(start_point_x, start_point_y)
    for i in range(index+1, count):
        temp_x = road_geo.GetX(i)                   
        temp_y = road_geo.GetY(i)        
        temp_road_geo.AddPoint(temp_x, temp_y)
     
    Make_Discre_Road_Points(temp_road_geo, start_points, seg_length)

def Set_POI_Pointdata(filepath:str):
    all_poi_points = []
    with open(filepath, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        lines = list(reader)
        del lines[0]
        for line in lines:
            all_poi_points.append( (float(line[6]), float(line[7])) )
    return all_poi_points

def GenerateRoadPoints(all_poi_points:list, road_linedata_filename, seg_length:float):
    '''
    生成road_points字典:{POI点:tuple:[道路点:tuple, 前点:tuple, 后点:tuple, 距离]} 这边点都是tuple而不是list是因为numba加速的时候tuple比list快10倍
    点都是精准的、小数一大堆的点
    法二思路见：https://blog.csdn.net/hengcall/article/details/82807946
    '''
    
    dr = ogr.GetDriverByName('ESRI Shapefile')
    if dr is None:
        print('注册道路的驱动失败...')
        return False
    print('注册道路的驱动成功...')
    ds = dr.Open(road_linedata_filename, 1)
    if ds is None:
        print('打开道路的shp文件失败...')
        return False
    print('打开道路的shp文件成功...')
    '''读取图层'''
    layer = ds.GetLayerByIndex(0)
    if layer is None:
        print('获取道路的图层失败...')
        return False
    print('获取道路的图层成功...')
    layer.ResetReading() 

    poi_points = all_poi_points

    road_points = dict.fromkeys(poi_points)   
    temp_road = layer.GetNextFeature()
    
    start_points = {}    #[离散道路点: (前点, 后点), 离散道路点: (前点, 后点)...] 
    print("正在读取道路并生成道路离散点")
    while temp_road:
        temp_geo = temp_road.GetGeometryRef().Clone()
        if temp_geo.GetGeometryName() == 'MULTILINESTRING':
            roads_count = temp_geo.GetGeometryCount()
            for index in range(roads_count):
                temp_road_geo = temp_geo.GetGeometryRef(index)
                Make_Discre_Road_Points(temp_road_geo, start_points, seg_length)
        elif temp_geo.GetGeometryName() == 'LINESTRING':
            Make_Discre_Road_Points(temp_geo, start_points, seg_length)
        temp_road = layer.GetNextFeature()
    print('将道路离散化为%d个点' % len(start_points))
    print('正在生成绑定道路点 kdtree')
    

    length = len(poi_points)
    start_road_points = list(start_points.keys())
    tree = spatial.KDTree(start_road_points)
    start = time.time()
    tree.query(np.array(poi_points[:1000]))
    end = time.time()
    print((end-start) / 1000 * length)
    query_result = tree.query(np.array(poi_points))    
    distances = query_result[0].tolist()
    indices = query_result[1].tolist()

    for i in range(len(distances)):
        poi_point = poi_points[i]
        min_dist = distances[i]
        lisan_road_point = start_road_points[indices[i]]
        pre_point, next_point = start_points[lisan_road_point]
        road_points[poi_point] = [lisan_road_point, pre_point, next_point, min_dist]
    print('一共%.6f秒' % (time.time()-start))
    return road_points


def to_tuple(s):
    coord = s.split(', ')
    x = float(coord[0][1:])
    y = float(coord[1][:-1])
    return (x, y)

def main(city, poi_path, road_path, newcsv_path, error_path, seg_length):
    
    
    all_poi_points = Set_POI_Pointdata(poi_path)
    print('一共有%d个POI点' % len(all_poi_points))
    road_points = GenerateRoadPoints(all_poi_points, road_path, seg_length)
    error = []
    '''
    road_points = {}
    with open(newcsv_path, 'r') as file:
        reader = csv.reader(file)
        lines = list(reader)
        del lines[0]
        for line in lines:
            if len(line) != 16:
                continue
            coord = (float(line[5]), float(line[6]))
            road_point = to_tuple(line[12])
            pre_point = to_tuple(line[13])
            next_point = to_tuple(line[14])
            dist = float(line[15])
            road_points[coord] = [road_point, pre_point, next_point, dist]
    print(len(road_points))
    '''
    with open(poi_path, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        new_lines = []
        lines = list(reader)
        del lines[0]
        for line in lines:
            new_line = []
            new_line.extend(line)
            coord = (float(line[6]), float(line[7]))
            if road_points.get(coord) is not None:
                road_point = road_points[coord][0]
                pre_point = road_points[coord][1]
                next_point = road_points[coord][2]
                dist = road_points[coord][3]
                new_line.extend([road_point, pre_point, next_point, dist])
            else:
                error.append(new_line)
            new_lines.append(new_line)
    
    with open(newcsv_path, 'w', newline='', encoding='gbk') as file:
        head = ['', 'id', 'parent', 'poi_code', 'poi_type', 'name', 'lng', 'lat', 'entr_lng', 'entr_lat', 'city', 'district', 'address', '道路点', '前点', '后点', '距离']
        writer = csv.writer(file)
        print('正在将POI点和对应最近道路点的字典写入文件')
        writer.writerow(head)
        writer.writerows(new_lines)
        
    with open(error_path, 'w', newline='', encoding='gbk') as file:
        writer = csv.writer(file)
        print('正在写入没绑定成功的点')
        writer.writerows(error)
    
city = '南京'        
poi_path = '../POI信息_新版/' + city + '_' + '.csv'
#test_poi_path = '../POI信息_投影/test.csv'
#road_path = '../高德路网_final/' + city + '.shp'
road_path = '../OSM路网_投影_改/' + city + '.shp'
newcsv_path = '../Road_Points_新版/' + city + '.csv'
error_path = '../Road_Points_新版/' + city + '错误.csv'     
seg_length = 50
main(city, 
     poi_path, 
     road_path, 
     newcsv_path, 
     error_path,
     seg_length) 
