import networkx as nx
from osgeo import ogr
import math
import time

def linear_distance(point_A_coord:tuple, point_B_coord:tuple):
    point_A_x = point_A_coord[0]
    point_A_y = point_A_coord[1]
    point_B_x = point_B_coord[0]
    point_B_y = point_B_coord[1]
    dis = math.sqrt((point_A_x-point_B_x)**2 + (point_A_y-point_B_y)**2)
    return dis
 
def read_shp_to_graph(path, simplify=True, geom_attrs=True, strict=True):
    
    net = nx.Graph()
    shp = ogr.Open(path)
    if shp is None:
        raise RuntimeError("Unable to open {}".format(path))
    for lyr in shp:
        fields = [x.GetName() for x in lyr.schema]
        for f in lyr:
            g = f.geometry()
            if g is None:
                if strict:
                    raise nx.NetworkXError("Bad data: feature missing geometry")
                else:
                    continue
            flddata = [f.GetField(f.GetFieldIndex(x)) for x in fields]
            attributes = dict(zip(fields, flddata))
            attributes["ShpName"] = lyr.GetName()
            # Note:  Using layer level geometry type
            if g.GetGeometryType() == ogr.wkbPoint:
                net.add_node((g.GetPoint_2D(0)), **attributes)
            elif g.GetGeometryType() in (ogr.wkbLineString,
                                         ogr.wkbMultiLineString):
                for edge in edges_from_line(g, attributes, simplify,
                                            geom_attrs):
                    e1, e2, attr = edge
                    dis = linear_distance(e1, e2)
                    e1_x = e1[0]
                    e1_y = e1[1]
                    e2_x = e2[0]
                    e2_y = e2[1]
                    mod_e1 = (int(e1_x), int(e1_y))
                    mod_e2 = (int(e2_x), int(e2_y))
                    
                    net.add_weighted_edges_from([(mod_e1, mod_e2, dis)])
                    net[mod_e1][mod_e2].update(attr)
            else:
                if strict:
                    raise nx.NetworkXError("GeometryType {} not supported".
                                           format(g.GetGeometryType()))

    return net

def edges_from_line(geom, attrs, simplify=True, geom_attrs=True):

    if geom.GetGeometryType() == ogr.wkbLineString:
        if simplify:
            edge_attrs = attrs.copy()
            last = geom.GetPointCount() - 1
            if geom_attrs:
                edge_attrs["Wkb"] = geom.ExportToWkb()
                edge_attrs["Wkt"] = geom.ExportToWkt()
                edge_attrs["Json"] = geom.ExportToJson()
            yield (geom.GetPoint_2D(0), geom.GetPoint_2D(last), edge_attrs)
        else:
            for i in range(0, geom.GetPointCount() - 1):
                pt1 = geom.GetPoint_2D(i)
                pt2 = geom.GetPoint_2D(i + 1)
                edge_attrs = attrs.copy()
                if geom_attrs:
                    segment = ogr.Geometry(ogr.wkbLineString)
                    segment.AddPoint_2D(pt1[0], pt1[1])
                    segment.AddPoint_2D(pt2[0], pt2[1])
                    edge_attrs["Wkb"] = segment.ExportToWkb()
                    edge_attrs["Wkt"] = segment.ExportToWkt()
                    edge_attrs["Json"] = segment.ExportToJson()
                    del segment
                yield (pt1, pt2, edge_attrs)

    elif geom.GetGeometryType() == ogr.wkbMultiLineString:
        for i in range(geom.GetGeometryCount()):
            geom_i = geom.GetGeometryRef(i)
            for edge in edges_from_line(geom_i, attrs, simplify, geom_attrs):
                yield edge
                
def read_shp_to_geo(path):
    dr = ogr.GetDriverByName('ESRI Shapefile')
    if dr is None:
        return False

    ds = dr.Open(path, 0)
    if ds is None:
        return False

    layer = ds.GetLayerByIndex(0)
    if layer is None:
        return False

    layer.ResetReading()    
    
    MultiRoads_geos = ogr.Geometry(ogr.wkbMultiLineString)
    temp_road = layer.GetNextFeature()
    while temp_road:
        temp_geo = temp_road.GetGeometryRef().Clone() 
        MultiRoads_geos.AddGeometry(temp_geo)
        temp_road = layer.GetNextFeature()
    
    ds.Destroy()
    return MultiRoads_geos
    
def distance(point_P, point_A, point_B):
    point_P_x = point_P[0]
    point_P_y = point_P[1]  
    
    point_A_x = point_A[0]    
    point_A_y = point_A[1]        
    
    point_B_x = point_B[0]    
    point_B_y = point_B[1]
    
    vector_AP = (point_P_x-point_A_x, point_P_y-point_A_y)
    vector_AB = (point_B_x-point_A_x, point_B_y-point_A_y)
    AB = math.sqrt((vector_AB[0]**2+vector_AB[1]**2))
    r = (vector_AP[0]*vector_AB[0] + vector_AP[1]*vector_AB[1]) / (AB**2)
    if r >= 1:
        dis = linear_distance(point_B, point_P)
        return dis
    elif r <= 0:
        dis = linear_distance(point_A, point_P)
        return dis
    else:
        AP = math.sqrt((vector_AP[0]**2+vector_AP[1]**2))
        cos = (vector_AP[0]*vector_AB[0] + vector_AP[1]*vector_AB[1]) / (AP*AB)
        sin = math.sqrt(1 - cos**2)
        dis = AP * sin
        return dis
                
def main():                
    G_direct = read_shp_to_graph('D:\\WalkScore\\networkx_test\\new_roads_for_network_cgcs2000.shp', simplify=False)
    MultiRoads_geos = read_shp_to_geo('D:\\WalkScore\\networkx_test\\new_roads_for_network_cgcs2000.shp')
#    G = G_direct.to_undirected()
    point = ogr.Geometry(ogr.wkbPoint)
    point.AddPoint_2D(20674347, 3549035)
    buffer = point.Buffer(200)
    interroads = buffer.Intersection(MultiRoads_geos)
    count = interroads.GetGeometryCount()
    point_dis = {}
#    a = time.time()
    for i in range(count):
        temp_road = interroads.GetGeometryRef(i)
        
        point_count = temp_road.GetPointCount()
        for j in range(point_count-1):
            point_A = temp_road.GetPoint_2D(j)
            point_B = temp_road.GetPoint_2D(j+1)
            point_P = (point.GetX(), point.GetY())
        
            dis = distance(point_P, point_A, point_B)
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
    
    
    

#    b = time.time()
#    print(point_index)
'''
    source = (20668929, 3546880)
    target = (20671264, 3548553)
    start = time.time()
    lujing = nx.dijkstra_path_length(G, source, target)
    end = time.time()
    print(lujing)
    print('\n')
    print(end-start)
'''    
if __name__ == '__main__':
    main()



