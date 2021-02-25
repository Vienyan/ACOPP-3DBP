import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import random
import copy

# #获得节点之间的距离
# wb =  pd.read_excel('dist.xlsx')
# data=wb.values
# distanceMat=np.zeros(shape=(11,11))
# for dis in data:
#     distanceMat[dis[0],dis[1]] = dis[2]
#     if dis[0]==0:
#         distanceMat[0,10] = 9999999999
#     distanceMat[dis[0],0] = 9999999999
#     distanceMat[10,:] = 9999999999   #终点到所有点都不可达

    

#输入城市数量已经距离矩阵，返回一条最短路径
def antLoad(numcity,distanceMat,antNum,itermax,mustFirstArr):

    # antNum = 20
    # numcity =  coordinates.shape[0]
    # numcity = 11    #包括起点和终点
    alpha = 1       # 信息素重要程度因子
    beta = 2         # 启发函数重要程度因子
    rho = 0.3       # 信息素的挥发速度
    Q = 1           # 完成率

    iter = 0       #迭代初始
    # itermax = 30  #迭代总数

    #初始化路上的信息素
    etatable = 1.0 / (distanceMat + np.diag([1e10] * numcity))      #初始化启发函数矩阵
    #diag(),将一维数组转化为方阵 启发函数矩阵，表示蚂蚁从城市i转移到城市j的期望程度
    pheromonetable = np.ones((numcity, numcity))            #信息素矩阵
    #路径记录表
    pathtable = np.zeros((antNum, numcity)).astype(int)
    lengthaver = np.zeros(itermax)  # 存放每次迭代后，路径的平均长度 
    lengthbest = np.zeros(itermax)  # 存放每次迭代后，最佳路径长度
    pathbest = np.zeros((itermax, numcity))  #存放每次迭代后，最佳路径城市的坐标
    #每只蚂蚁的最优
    everyAntBestPath = np.zeros((antNum, numcity))
    everyAntBestLength = np.zeros(antNum)

    while iter < itermax:
        #起点设置在0
        pathtable[:numcity, 0] = 0
        # pathtable[numcity:, 0] = np.random.permutation(range(numcity))[:antNum - numcity]
        length = np.zeros(antNum)

        #算出每只/第i只蚂蚁转移到下一个城市的概率
        for i in range(antNum):
            copy_frist =  copy.deepcopy(mustFirstArr)
            #如果有必须要优先送的点
            visiting = pathtable[i,0]  # 当前所在的城市
            unvisited = set(range(numcity))
            #删除访问过的
            unvisited.remove(visiting)
            #删除终点
            unvisited.remove(numcity-1)

            for j in range(1, numcity-1):
                
                listunvisited = list(unvisited)                 #未访问城市数,list
                probtrans = np.zeros(len(listunvisited))

                #如果存在必须先访问的
                if copy_frist:
                    index = random.randint(0,len(copy_frist)-1)
                    k = copy_frist[index]
                    copy_frist.remove(k)
                else:
                    # if mustFirstArr:
                    #     #所有的路线第一个点必须从mustFirstArr中取
                    #     visiting = random.randint(0,len(mustFirstArr)-1)
                    # else
                    #以下是计算转移概率
                    for k in range(len(listunvisited)):
                        probtrans[k] = np.power(pheromonetable[visiting][listunvisited[k]], alpha) \
                                    * np.power(etatable[visiting][listunvisited[k]], beta)
                    #eta-从城市i到城市j的启发因子 这是概率公式的分母   其中[visiting][listunvis[k]]是从本城市到k城市的信息素

                    #求出本只蚂蚁的转移到各个城市的概率斐波衲挈数列
                    # cumsumprobtrans = (probtrans / sum(probtrans)).cumsum()
                    cumsumprobtrans = (probtrans / sum(probtrans))
                    #生成下一个要访问的城市k
                    while True:
                        random_num = np.random.rand()
                        index_need = np.where(cumsumprobtrans > random_num)[0]
                        if len(index_need) > 0:
                            k = listunvisited[index_need[0]]
                            break
                pathtable[i, j] = k
                unvisited.remove(k)
                length[i] += distanceMat[visiting][k]
                visiting = k
            
            #加上到终点的距离
            pathtable[i, j+1] = numcity-1
            length[i] += distanceMat[visiting][numcity-1]

            #保留每只蚂蚁的最优
            if iter == 0:
                everyAntBestPath[i] = pathtable[i].copy().astype(int)
                everyAntBestLength[i] = length[i]
            else:
                if length[i]<everyAntBestLength[i]:
                    everyAntBestPath[i] = pathtable[i].copy().astype(int)
                    everyAntBestLength[i] = length[i]

                    
        #本次循环所有蚂蚁的平均路径长度
        lengthaver[iter] = length.mean()

        #记录下路径
        if iter == 0:
            lengthbest[iter] = length.min()
            pathbest[iter] = pathtable[length.argmin()].copy().astype(int)
        else:
            if length.min() > lengthbest[iter - 1]:
                lengthbest[iter] = lengthbest[iter - 1]
                pathbest[iter] = pathbest[iter - 1].copy().astype(int)
            else:
                lengthbest[iter] = length.min()
                pathbest[iter] = pathtable[length.argmin()].copy().astype(int)

        #更新信息素
        changepheromonetable = np.zeros((numcity, numcity))
        for i in range(antNum):
            for j in range(numcity - 1):
                changepheromonetable[pathtable[i, j]][pathtable[i, j + 1]] += Q / distanceMat[pathtable[i, j]][pathtable[i, j + 1]]
            # changepheromonetable[pathtable[i, j + 1]][pathtable[i, 0]] += Q / distanceMat[pathtable[i, j + 1]][pathtable[i, 0]]
        pheromonetable = (1 - rho) * pheromonetable + changepheromonetable
        iter += 1
        # print("this iteration end：",iter,"result:",lengthbest)

    res ={'path':everyAntBestPath.astype(int),'length':everyAntBestLength}

    return res


# #以下是做图部分
# #做出平均路径长度和最优路径长度
# fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(12, 10))
# axes[0].plot(lengthaver, 'k', marker='*')
# axes[0].set_title('Average Length')
# axes[0].set_xlabel(u'iteration')


# #线条颜色black
# axes[1].plot(lengthbest, 'k', marker='<')
# axes[1].set_title('Best Length')
# axes[1].set_xlabel(u'iteration')
# fig.savefig('Average_Best.png', dpi=500, bbox_inches='tight')
# fig.show()
# plt.close()

