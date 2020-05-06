# WalkScore
步行指数计算代码 2019年9月8日
作者：张径舟 2018级 南京师范大学地理科学学院

投影坐标系：CGCS2000 编码：GBK

POI的数据需要根据种类分为不同的文件夹，每一个文件夹中存放一种POI的shp文件。

可以计算道路的步行指数和面域的步行指数，面域的步行指数暂时用不上，所以没有更新。

2019年10月12日更新：
将直线距离更改为路网距离（但是计算耗时太长，实际上不可能计算出来），添加了一些注释，删除了少量不必要内容。

2020年05月06日更新：
  优化了POI文件的存储，现在POI文件中包括了所有种类的POI，计算时需要一张权重表来提供用到的POI种类和权重
  之前的计算瓶颈主要在于抓路，目前使用的方法是将道路离散化（50m），用scipy的kdtree获得POI最近的道路点，大大加快了抓路速度
  在networkx的迪杰斯特拉算法基础上进行了优化（其实就是把到达cutoff之后抛出错误改成返回一个非常大的值），加速了计算
