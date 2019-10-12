# -*- coding: utf-8 -*-
"""
Created on Sat Sep 28 16:32:41 2019

@author: DELL
"""

from osgeo import ogr
import networkx as nx
from networkx_readshp import *
import math
import time

def integer(a_list):
    '''把列表内每一个元素（必须是float）向下取整'''
    count = len(a_list)
    new_list = []
    for i in range(count):
        new_list.append(int(a_list[i]))
    return new_list
    
def linear_distance(point_A_coord:tuple, point_B_coord:tuple):
    '''两点间直线距离'''
    point_A_x = point_A_coord[0]
    point_A_y = point_A_coord[1]
    point_B_x = point_B_coord[0]
    point_B_y = point_B_coord[1]
    dis = math.sqrt((point_A_x-point_B_x)**2 + (point_A_y-point_B_y)**2)
    return dis

def point_to_segment_distance(point_P, point_A, point_B):
    '''点到线段距离'''
    point_P_x = point_P[0]
    point_P_y = point_P[1]  
    
    point_A_x = point_A[0]    
    point_A_y = point_A[1]        
    
    point_B_x = point_B[0]    
    point_B_y = point_B[1]
    
    vector_AP = (point_P_x-point_A_x, point_P_y-point_A_y)
    vector_AB = (point_B_x-point_A_x, point_B_y-point_A_y)
    AB = math.sqrt((vector_AB[0]**2+vector_AB[1]**2))
    if AB == 0:
        return -1
    r = (vector_AP[0]*vector_AB[0] + vector_AP[1]*vector_AB[1]) / (AB**2)
    if r >= 1:
        dis = linear_distance(point_B, point_P)
    elif r <= 0:
        dis = linear_distance(point_A, point_P)
    else:
        AP = math.sqrt((vector_AP[0]**2+vector_AP[1]**2))
        cos = (vector_AP[0]*vector_AB[0] + vector_AP[1]*vector_AB[1]) / (AP*AB)
        try:
            sin = math.sqrt(1 - cos**2)
        except:
            sin = 0
        dis = AP * sin
    return dis

def tie_point_on_road_start(point:ogr.Geometry, road_geo):
    '''将出发点绑定到道路上的一个点，由于出发点本来就在道路上，所以找到出发点前后在道路线要素上的点就行'''
    count = road_geo.GetPointCount()
    point_coord = (point.GetX(), point.GetY())
    for i in range(count-1):
        point_A = road_geo.GetPoint_2D(i)
        point_B = road_geo.GetPoint_2D(i+1)
        if (point_A[0] <= point_coord[0] <= point_B[0] or point_B[0] <= point_coord[0] <= point_A[0]) and \
           (point_A[1] <= point_coord[1] <= point_B[1] or point_B[1] <= point_coord[1] <= point_A[1]):
            return [list(point_coord), list(point_A), list(point_B)] 

def tie_point_on_road_stop(point:ogr.Geometry, MultiRoads_geos): 
    '''将停止点绑定到道路上的一个点'''
    interroads = MultiRoads_geos
    count = interroads.GetGeometryCount()
    point_dis = {}
    
    for i in range(count):  #这个循环太慢了，准备改进算法或者用奇技淫巧
        temp_road = interroads.GetGeometryRef(i)
        point_count = temp_road.GetPointCount()
        
        for j in range(point_count-1):

            point_A = temp_road.GetPoint_2D(j)
            point_B = temp_road.GetPoint_2D(j+1)
            point_P = (point.GetX(), point.GetY())

            dis = point_to_segment_distance(point_P, point_A, point_B)
            if dis == -1:
                continue
            point_dis[(point_A, point_B)] = dis
    point_dis_order=sorted(point_dis.items(),key=lambda x:x[1],reverse=False)   
    point_on_road1_coord = point_dis_order[0][0][0]
    point_on_road2_coord = point_dis_order[0][0][1]
    shortest_dis = point_dis_order[0][1]
    point_coord = point.GetPoint_2D(0)
    
    dis_1 = linear_distance(point_coord, point_on_road1_coord)
    dis_2 = linear_distance(point_coord, point_on_road2_coord)
    if abs(shortest_dis-dis_1) <= 0.01:
        tied_point_coord = point_on_road1_coord
    elif abs(shortest_dis-dis_2) <= 0.01:
        tied_point_coord = point_on_road2_coord
    else:
        k = (point_on_road2_coord[1]-point_on_road1_coord[1])/ \
            (point_on_road2_coord[0]-point_on_road1_coord[0])
        b = point_on_road1_coord[1] - k*point_on_road1_coord[0]
        tied_point_x = (k*(point_coord[1]-b) + point_coord[0])/ \
                       (k**2 + 1)
        tied_point_y = k*tied_point_x + b
        tied_point_coord = (tied_point_x, tied_point_y)
    return [list(tied_point_coord), list(point_on_road1_coord), list(point_on_road2_coord)]
        
def net_Distance(G, road_geo, MultiRoads_geos, start_point_geo, stop_point_geo):
    '''计算路网距离'''
    net_distance = 0
    points_start = tie_point_on_road_start(start_point_geo, road_geo)
    points_stop = tie_point_on_road_stop(stop_point_geo, MultiRoads_geos)
    tied_start_point_coord = tuple(integer(points_start[0]))
    tied_stop_point_coord = tuple(integer(points_stop[0]))

    start_between_A = tuple(integer(points_start[1]))
    start_between_B = tuple(integer(points_start[2]))
    
    stop_between_A = tuple(integer(points_stop[1]))
    stop_between_B = tuple(integer(points_stop[2]))
    
    G.remove_edges_from([(start_between_A, start_between_B),(stop_between_A, stop_between_B)])
    G.add_weighted_edges_from([(start_between_A, tied_start_point_coord, linear_distance(start_between_A, tied_start_point_coord)),\
                               (tied_start_point_coord, start_between_B, linear_distance(start_between_B, tied_start_point_coord))])   
    G.add_weighted_edges_from([(stop_between_A, tied_stop_point_coord, linear_distance(stop_between_A, tied_stop_point_coord)),\
                               (tied_stop_point_coord, stop_between_B, linear_distance(stop_between_B, tied_stop_point_coord))])   
    nodelist = G.nodes()
    if tied_stop_point_coord in nodelist:
        print(1)
    try:
        net_distance = nx.dijkstra_path_length(G, tied_start_point_coord, tied_stop_point_coord)
#        print('路网距离计算成功')
    except:
        net_distance = start_point_geo.Distance(stop_point_geo)
#        print('路网距离计算失败，使用直线距离')
    return net_distance