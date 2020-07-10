# -*- coding: utf-8 -*-
"""
Created on Sat Sep 28 16:32:41 2019

@author: 张径舟
"""

from osgeo import ogr
import networkx as nx
from networkx_readshp import *
import math
import time
from scipy.spatial.distance import cdist
import numba as nb
import numpy as np
from heapq import heappush, heappop
import itertools

        
def run_time(func):
    def call_fun(*args, **kwargs):
        start_time = time.time()
        f = func(*args, **kwargs)
        end_time = time.time()
        print('%s() run time：%s ms' % (func.__name__, 1000*(end_time - start_time)))
        return f
    return call_fun

def integer(a_list):
    '''把列表(或元组)内每一个元素（必须是float）向下取整'''
    new_list = [int(i) for i in a_list]
    return new_list

@nb.jit(nopython=True)    
def linear_distance(point_A_coord:tuple, point_B_coord:tuple):
    '''两点间直线距离'''
    return math.sqrt((point_A_coord[0]-point_B_coord[0])**2 + (point_A_coord[1]-point_B_coord[1])**2)

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

def tie_point_on_road_start(point_coord, road_geo):
    '''将出发点绑定到道路上的一个点，由于出发点本来就在道路上，所以找到出发点前后在道路线要素上的点就行'''
    count = road_geo.GetPointCount()
    for i in range(count-1):
        point_A = road_geo.GetPoint_2D(i)
        point_B = road_geo.GetPoint_2D(i+1)
        if (point_A[0] <= point_coord[0] <= point_B[0] or point_B[0] <= point_coord[0] <= point_A[0]) and \
           (point_A[1] <= point_coord[1] <= point_B[1] or point_B[1] <= point_coord[1] <= point_A[1]):
            return [list(point_coord), list(point_A), list(point_B)] 
'''
def tie_point_on_road_stop(point_coord, MultiRoads_geos): 
    #将停止点绑定到道路上的一个点
    interroads = MultiRoads_geos
    count = interroads.GetGeometryCount()
    point_dis = {}
    
    for i in range(count):  #这个循环太慢了，准备改进算法或者用奇技淫巧
        temp_road = interroads.GetGeometryRef(i)
        point_count = temp_road.GetPointCount()
        
        for j in range(point_count-1):

            point_A = temp_road.GetPoint_2D(j)
            point_B = temp_road.GetPoint_2D(j+1)
            point_P = point_coord

            dis = point_to_segment_distance(point_P, point_A, point_B)
            if dis == -1:
                continue
            point_dis[(point_A, point_B)] = dis
    point_dis_order=sorted(point_dis.items(),key=lambda x:x[1],reverse=False)   
    point_on_road1_coord = point_dis_order[0][0][0]
    point_on_road2_coord = point_dis_order[0][0][1]
    shortest_dis = point_dis_order[0][1]
    
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
    return [list(tied_point_coord), list(point_on_road1_coord), list(point_on_road2_coord), shortest_dis]
'''
def tie_point_on_road_stop_discrete(point_coord:tuple, road_points:dict):  
    '''
    road_points[point_coord] = (绑定点:tuple, 前点:tuple, 后点:tuple, 距离)
    points_stop = [绑定点:list, 前点:list, 后点:list, 距离]
    '''
    points_stop = [] 
    for value in road_points[point_coord]:
        if type(value) == tuple:
            points_stop.append(list(value))
        else:
            points_stop.append(value)
    return points_stop
   
def GenerateRoadPoints(MultiType_poi_points:dict, layer, seg_length:float):
    pass

def _weight_function(G, weight):
    if callable(weight):
        return weight
    # If the weight keyword argument is not callable, we assume it is a
    # string representing the edge attribute containing the weight of
    # the edge.
    if G.is_multigraph():
        return lambda u, v, d: min(attr.get(weight, 1) for attr in d.values())
    return lambda u, v, data: data.get(weight, 1)

def _dijkstra(G, source, weight, pred=None, paths=None, cutoff=None,
              target=None):
    return _dijkstra_multisource(G, [source], weight, pred=pred, paths=paths,
                                 cutoff=cutoff, target=target)
    
def _dijkstra_multisource(G, sources, weight, pred=None, paths=None,
                          cutoff=None, target=None):
    G_succ = G._succ if G.is_directed() else G._adj

    push = heappush
    pop = heappop
    dist = {}  # dictionary of final distances
    seen = {}
    # fringe is heapq with 3-tuples (distance,c,node)
    # use the count c to avoid comparing nodes (may not be able to)
    c = itertools.count()
    fringe = []
    for source in sources:
        if source not in G:
            raise nx.NodeNotFound("Source {} not in G".format(source))
        seen[source] = 0
        push(fringe, (0, next(c), source))
    while fringe:
        (d, _, v) = pop(fringe)
        if v in dist:
            continue  # already searched this node.
        dist[v] = d
        if v == target:
            break
        for u, e in G_succ[v].items():
            cost = weight(v, u, e)
            if cost is None:
                continue
            vu_dist = dist[v] + cost
            if cutoff is not None:
                if vu_dist > cutoff:
                    continue
            if u in dist:
                if vu_dist < dist[u]:
                    raise ValueError('Contradictory paths found:',
                                     'negative weights?')
            elif u not in seen or vu_dist < seen[u]:
                seen[u] = vu_dist
                push(fringe, (vu_dist, next(c), u))
                if paths is not None:
                    paths[u] = paths[v] + [u]
                if pred is not None:
                    pred[u] = [v]
            elif vu_dist == seen[u]:
                if pred is not None:
                    pred[u].append(v)

    return dist


def my_dijkstra_path_length(G, source, target, cutoff=None, weight='weight'):
    if source == target:
        return 0
    weight = _weight_function(G, weight)
    length = _dijkstra(G, source, weight, cutoff=cutoff, target=target)
    return length
        

  
def GetNetDistances(start_point:tuple, stop_points, pre_nex_points, road_points, G):
    '''计算路网距离'''
    a = time.time()
    net_distances = []
    #points_start = tie_point_on_road_start(start_point, road_geo)
    tied_start_point_coord = tuple(integer(start_point))
    start_between_A = tuple(integer(pre_nex_points[0]))
    start_between_B = tuple(integer(pre_nex_points[1]))
    poi_to_road_dists = {}
    poi_and_tied_stop_point = {}
    for stop_point in stop_points:
        aaa = time.time()
        #points_stop = tie_point_on_road_stop(stop_point, MultiRoads_geos)    
        points_stop = tie_point_on_road_stop_discrete(stop_point, road_points)    
        
        tied_stop_point_coord = tuple(integer(points_stop[0]))
        stop_between_A = tuple(integer(points_stop[1]))
        stop_between_B = tuple(integer(points_stop[2]))
        poi_to_road_dis = points_stop[3]
        poi_to_road_dists[stop_point] = poi_to_road_dis
        G.remove_edges_from([(start_between_A, start_between_B),(stop_between_A, stop_between_B)])
        G.add_weighted_edges_from([(start_between_A, tied_start_point_coord, linear_distance(start_between_A, tied_start_point_coord)),
                                   (tied_start_point_coord, start_between_B, linear_distance(start_between_B, tied_start_point_coord)), 
                                   (stop_between_A, tied_stop_point_coord, linear_distance(stop_between_A, tied_stop_point_coord)),
                                   (tied_stop_point_coord, stop_between_B, linear_distance(stop_between_B, tied_stop_point_coord))])   
        poi_and_tied_stop_point[stop_point] = tied_stop_point_coord
    aaa = time.time()
    #print(aaa-a)
    dist = my_dijkstra_path_length(G, tied_start_point_coord, None, cutoff=2400)

    for stop_point in stop_points:
        tied_stop_point_coord = poi_and_tied_stop_point[stop_point]
        if dist.get(tied_stop_point_coord) is not None:
            temp_dist = dist[tied_stop_point_coord]
        else:
            temp_dist = 1000000000
        temp_dist = temp_dist + poi_to_road_dists[stop_point]
        if temp_dist < 2400:
            net_distances.append(temp_dist)
    '''
    try:
    #if nx.has_path(G, tied_start_point_coord, tied_stop_point_coord):
        aa = time.time()
        #注意：可能要写一个if来判断2400-poi_to_road_dis是正数还是负数
        dist = my_dijkstra_path_length(G, tied_start_point_coord, tied_stop_point_coord, cutoff=2400-poi_to_road_dis)+poi_to_road_dis
        #print(dist)
        if dist < 2400:
            net_distances.append(dist)
        bb = time.time()
        #print('net dist: %.6f' % (bb-aa))
        #print('路网距离计算成功')
    except:
    #else:
        aaaa = time.time()
        net_distances.append(linear_distance(start_point, stop_point))
        bbbb = time.time()
        #print('linear dist: %.6f' % (bbbb-aaaa))
        #print('路网距离计算失败，使用直线距离')
    '''
    bbb = time.time()
    #print('time: %.6f' % (bbb-aaa))
    #当路网距离无法进行计算时会消耗大量时间
    #可能需要在最后的时候把新添加的边删掉
    b = time.time()
    #print('all time: %.6f' % (b-a))
    return net_distances