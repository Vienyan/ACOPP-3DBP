
import os
import sys
import numpy as np
import re
import random
import copy
import json

from time import *
from pack import Pack
from antAlgorithm import antLoad
from NDSort import NDSort



def main(argv):
    # input_dir = argv[1]
    input_dir = 'data/inputs'
    # output_dir = argv[2]
    output_dir = 'data/outputs'
    antNum = 20  #蚂蚁数量，有多少只蚂蚁就会返回多少个路径
    # iterTime = 30

    for file_name in os.listdir(input_dir):
        pack_time = 0   #调用pack的次数
        #代表一个实例
        begin_time = time()
        end_time = time()
        solution = []       #存放所有非支配解
        resultArray = []        #存放所有解的目标值
        gen = 0                 #迭代次数
        input_path = os.path.join(input_dir, file_name)
        with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
            message_str = f.read()
        pack = Pack(message_str,output_path=output_dir)
        pack_time += 1
        #数据中的节点数量
        numOfNode = len(pack.data['algorithmBaseParamDto']['platformDtoList'])
        #数据中的卡车
        truck = pack.data['algorithmBaseParamDto']['truckTypeDtoList']
        truckOfNum = len(truck)

        distanceInfo = handleDist(pack.data['algorithmBaseParamDto']['distanceMap'],numOfNode)
        distanceMat = distanceInfo['distanceMat']
        platformOrder = distanceInfo['platformOrder']
        allBox = copy.deepcopy(pack.box_list)      #获取需要装箱的盒子

        #track1
        # while pack_time<2000 and (end_time - begin_time)<420:

        #track2
        while (end_time - begin_time)<130:
            
            #确认是否有需要优先的平台,不确定是否有几个
            needFirst = []
            for item in pack.data['algorithmBaseParamDto']['platformDtoList']:
                if item['mustFirst'] == True:
                    needFirst.append(platformOrder.index(int(re.findall("\d+",item['platformCode'])[0])))

            updataPath = 0
            #每隔10代重新求一次路径,返回的是platformOrder的索引节点
            if gen<30 and gen%5 == 0:
                bestPath = antLoad(numOfNode+2,distanceMat,antNum,gen%5+1,needFirst)
                updataPath = 1
            elif gen%20 == 0:
                #返回多条路径，但是很可能包含相同,path表示路径，length表示长度
                bestPath = antLoad(numOfNode+2,distanceMat,antNum,random.randint(10,30),needFirst)
                updataPath = 1

            if updataPath == 1:
                #将path组转成参数所需要的格式 ['platform04','platform05']
                routes = []
                for k in range(len(bestPath['path'])):
                    oneAnt = []
                    for j in range(len(bestPath['path'][k])-1):
                        if j!=0:
                            if platformOrder[bestPath['path'][k,j]]<10:
                                platform = 'platform0' + str(platformOrder[bestPath['path'][k,j]])
                            else:
                                platform = 'platform' + str(platformOrder[bestPath['path'][k,j]])
                            oneAnt.append(platform)
                    routes.append(oneAnt)

            #还未装载的盒子,这里需要使用深度拷贝
            restBox = copy.deepcopy(allBox)
            res = []
            while  len(restBox)!=0:
                
                #所有能使用的车辆编号,range不包括最后truckOfNum
                canUseTruck = list(range(truckOfNum))
                #随机选择一种类型的卡车
                chose_truck = random.randint(0,truckOfNum - 1)
                #随机选择一条路径
                chose_path = random.randint(0,len(routes) - 1)

                old_path = copy.deepcopy(routes[chose_path])


                #如果货物中已经有盒子超过了货车的大小，则不能再选择此种货车
                box_id = []
                for box in restBox:
                    box_id.append(box.box_id)

                onePack = Pack(message_str,spu_ids=box_id,truck_code=truck[chose_truck]['truckTypeCode'],route=[routes[chose_path]],output_path=output_dir)
                one = onePack.run()
                pack_time += 1

                #如果打包成功
                if one:
                    #检查一下路径是否符合要求
                    if needFirst:
                        for node in range(len(one['platformArray'])):
                            if node != 0:
                                if platformOrder.index(int(re.findall("\d+",one['platformArray'][node])[0])) in needFirst:
                                    #去掉不符合规则的那个平台，然后重新计算
                                    old_path.remove(one['platformArray'][node])
                                    onePack = Pack(message_str,spu_ids=box_id,truck_code=truck[chose_truck]['truckTypeCode'],route=[old_path],output_path=output_dir)
                                    one = onePack.run()
                                    pack_time += 1
                            break

                    res.append(one)
                    #去掉已经装载的箱子
                    for loadBox in one['spuArray']:
                        for box in restBox:
                            if box.box_id == loadBox['spuId']:
                                restBox.remove(box)


            #计算这个方案的装载率和运输距离
            result = calResult(res,distanceMat,numOfNode+2,platformOrder)
            resultArray.append(result)
            solution.append(res)
            gen +=1
            end_time = time()
            print('result:',result)
        
        #迭代完成之后去掉一些重复解
        new_resultArr = []
        new_solution = []
        for no_repeat in resultArray:
            if no_repeat not in new_resultArr:
                new_resultArr.append(no_repeat)
                new_solution.append(solution[resultArray.index(no_repeat)])


        #迭代完成之后去掉一些支配解
        obj_arr = np.array(new_resultArr)
        paretoIndex = NDSort(obj_arr.shape[0], obj_arr)
        paretoIndex.fast_non_dominate_sort()
        paretoIndex.crowd_distance()

        #保存第一层的解
        temp_solution =  []
        temp_obj   = []
        for i in paretoIndex.f[0]:
            temp_solution.append(new_solution[i])
            temp_obj.append(obj_arr[i])

        print('finally result:',temp_obj)

        estimateCode = pack.data['estimateCode']
        reserveResult(output_dir,estimateCode,temp_solution,file_name)

#将结果输出到文件
def reserveResult(output_path,estimateCode,solution,file_name):
    res = {"estimateCode": estimateCode, "solutionArray": solution}
    if output_path is not None:
        if not os.path.exists(output_path):
            os.mkdir(output_path)
        output_file = os.path.join(output_path, file_name)
        with open(
                output_file, 'w', encoding='utf-8', errors='ignore') as f:
            json.dump(res, f, ensure_ascii=False)

#计算方案的装载率和运输距离
def calResult(res,distanceMap,nodeNum,order):
    radio = np.zeros((len(res),1))
    carNum = len(res)
    for item in range(carNum):
        #计算体积装载率
        CarVolume = res[item]['innerLength']*res[item]['innerWidth']*res[item]['innerHeight']
        vRadio = res[item]['volume']/CarVolume
        #重量装载率
        wRadio = res[item]['weight']/res[item]['maxLoad']
        radio[item] = max(vRadio,wRadio)

    f1 = (1 - sum(radio)/carNum)[0]         #第一个目标函数
 
    #计算汽车运输总距离
    totalDistance = 0
    for item in range(len(res)):
        for k in range(len(res[item]['platformArray'])):
            temp = res[item]['platformArray']
            i = order.index(int(re.findall("\d+",temp[k])[0]))   #当前遍历的节点
            if k == 0:
                totalDistance += distanceMap[0,i]
            else:
                j = order.index(int(re.findall("\d+",temp[k-1])[0]))     #上一个节点
                totalDistance += distanceMap[j,i]
            if k == len(temp)-1:                  #最后一个节点要加上到终点的距离
                totalDistance += distanceMap[i,nodeNum-1]

    # result = {'f1':f1,'f2':totalDistance}
    result = [f1,totalDistance]
    return result


#把数据中的距离变成距离矩阵
def handleDist(information,node_num):

    #先规定平台的顺序
    platformOrder = []
    for item in information.items():
        node_arr = item[0].split('+')
        if node_arr[0] !='end_point' and node_arr[0] !='start_point':
            temp_num = int(re.findall("\d+",node_arr[0])[0])
            if temp_num not in platformOrder:
                platformOrder.append(int(re.findall("\d+",node_arr[0])[0]))
    platformOrder.insert(0,0)       #插入起点
    platformOrder.append(-1)        #插入终点

    #加上起点和终点
    distanceMat=np.zeros(shape=(len(platformOrder),len(platformOrder)))
    for item in information.items():
        i = 0
        j = 0
        node_arr = item[0].split('+')
        if node_arr[0] =='end_point':
            i = node_num + 1
        elif node_arr[0] =='start_point':
            i = 0
        else:
            #数字节点
            i = platformOrder.index(int(re.findall("\d+",node_arr[0])[0]))

        if node_arr[1] =='end_point':
            j = node_num + 1
        elif node_arr[1] =='start_point':
            j = 0
        else:
            #数字节点
            j = platformOrder.index(int(re.findall("\d+",node_arr[1])[0]))
        
        distanceMat[i,j] = item[1]
        distanceMat[:,0] = 99999999999
        distanceMat[0,node_num + 1] = 99999999999
        distanceMat[node_num + 1,:] = 99999999999   #终点到所有点都不可达
    
    distanceInfo = {'platformOrder':platformOrder,'distanceMat':distanceMat}
    return distanceInfo

if __name__ == "__main__":
    main(sys.argv)

