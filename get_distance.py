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
    '''在networkx的迪杰斯特拉算法的基础上小改了一下，原来到达cutoff后会报错，我改成了返回一个大值(1000000000)'''
    if source == target:
        return 0
    weight = _weight_function(G, weight)
    length = _dijkstra(G, source, weight, cutoff=cutoff, target=target)
    return length
        
  
def GetNetDistances(start_point:tuple, stop_points, pre_nex_points, road_points, G):
    '''计算路网距离'''
    a = time.time()
    net_distances = []

    tied_start_point_coord = tuple(integer(start_point))
    start_between_A = tuple(integer(pre_nex_points[0]))
    start_between_B = tuple(integer(pre_nex_points[1]))
    poi_to_road_dists = {}
    poi_and_tied_stop_point = {}
    for stop_point in stop_points:
        aaa = time.time()
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
    bbb = time.time()
    b = time.time()
    #print('all time: %.6f' % (b-a))
    return net_distances
