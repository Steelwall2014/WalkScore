from walkscore_calculator import WalkscoreCalculator
import time

def main():
    poi_types = ['grocery_stores', 
                 'restaurants_and_bars', 
                 'shops', 
                 'cafes', 
                 'banks', 
                 'parks', 
                 'schools', 
                 'bookstores', 
                 'entertain']
    #后面再加种类  
    weight_tables = {'grocery_stores': [3], 
                     'restaurants_and_bars': [0.75,0.45,0.25,0.25,0.225,0.225,0.225,0.225,0.2,0.2], 
                     'shops': [0.5,0.45,0.4,0.35,0.3], 
                     'cafes': [1.25,0.75], 
                     'banks': [1], 
                     'parks': [1], 
                     'schools': [1], 
                     'bookstores': [1], 
                     'entertain': [1]}   
    #后面再加种类     
    WS_cal = WalkscoreCalculator(poi_types, weight_tables)
    WS_cal.Set_Road_Linedata('D:\\WalkScore\\jiangdu\\roads\\roads_cgcs2000_special.shp')
    WS_cal.Set_POI_Pointdata('D:\\WalkScore\\jiangdu\\')

    WS_cal.Prepare_POIinfo()    
    first_point_coord = [20733766, 3620680] 
    last_point_coord =  [20767706, 3582231] 
    seg_length = 200
    density = 500
    region_walkscore_filepath = 'D:\\WalkScore\\jiangdu\\Region\\points_'+str(density)+'m.shp'
#    flag = input('按1开始计算街道的步行指数，按2开始计算面域步行指数\n')
    flag='1' #测试的时候懒得输了，直接赋个值
    if flag == '1':
        start_time = time.time()
        WS_cal.Compute_Road_Walkscore(seg_length)
        end_time = time.time()
        print('完成! 一共用时：%f秒' % (end_time-start_time))        
    elif flag == '2':
        start_time = time.time()
        WS_cal.Compute_Region_Walkscore(first_point_coord, last_point_coord, density, region_walkscore_filepath)
        end_time = time.time()
        print('完成! 一共用时：%f秒' % (end_time-start_time))
if __name__ == "__main__":
    main()