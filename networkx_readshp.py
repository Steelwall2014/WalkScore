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
          
                


