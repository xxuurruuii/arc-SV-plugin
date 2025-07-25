import re
import math

def parse_aff_file(content):
    global maxtime
    tg=-1
    output=[]
    for s in content.split('\n'):
        s=s.strip()
        if s.startswith('timinggroup'):
            tg+=1
            tgstarters.append(s)
            originalaff.append('')
            currenttg=[]
            continue
        if tg<0:continue
        originalaff[-1]+=s+'\n'
        if s.startswith('arc'):
            pat=re.compile('arc\(([^)]+)\)(.*);')
            mat=pat.match(s)
            params1=mat.group(1).split(',')
            params1[0]=int(params1[0])      #starttime
            params1[1]=int(params1[1])      #endtime
            if params1[1]>maxtime:maxtime=params1[1]
            params1[2]=float(params1[2])    #x1
            params1[3]=float(params1[3])    #x2
            params1[4]=params1[4]           #easing
            params1[5]=float(params1[5])    #y1
            params1[6]=float(params1[6])    #y2
            params1[7]=int(params1[7])      #color
            params1[8]=params1[8]               #hitsound 
            params1[9]=bool(params1[9])     #arctype
            params2=mat.group(2)
            if params2!='':
                params2=params2[1:-1].split(',')
                params2=[int(i[7:-1]) for i in params2]
            else:params2=[]
            params1=['arc']+params1+[params2]
            currenttg.append(params1)
            continue
        if s.startswith('timing('):
            pat=re.compile('timing\(([^)]+)\);')
            mat=pat.match(s)
            params1=mat.group(1).split(',')
            params1[0]=int(params1[0])      #starttime
            if params1[0]>maxtime:maxtime=params1[0]
            params1[1]=float(params1[1])    #bpm
            params1[2]=params1[2]               #beats
            params1=['timing']+params1
            currenttg.append(params1)
            continue
        if s.startswith('('):
            pat=re.compile('\(([^)]+)\);')
            mat=pat.match(s)
            params1=mat.group(1).split(',')
            params1[0]=int(params1[0])      #starttime
            if params1[0]>maxtime:maxtime=params1[0]
            params1[1]=int(params1[1])      #x
            params1=['tap']+params1
            currenttg.append(params1)
            continue
        if s=='};':
            output.append(currenttg)
    return output



f=open("1.aff",'r')
f2=open('0.aff','w')
content = f.read()
deltat=30
for s in content.split('\n'):
    if s.startswith('timinggroup'):
        break
    f2.write(s+'\n')
for s in content.split('\n'):
    if s.startswith('timing'):
        pat=re.compile('timing\(([^)]+)\);')
        mat=pat.match(s)
        params1=mat.group(1).split(',')
        bpm=float(params1[1])
        break
k=60000*2/2

maxtime=0
originalaff=[]
tgstarters=[]
parsed_data = parse_aff_file(content)
maxtime+=100
#print(parsed_data)

while len(parsed_data)>=2:
    list1=parsed_data.pop(0)
    list2=parsed_data.pop(0)
    a=list2.pop(0)
    bpm1=a[2]
    bpm1time=0
    #maxtime=max(list1[-1][1],list2[-1][2])+100
    poslist=[0 for _ in range(maxtime)]     #每个时刻判定线的位置
    timelist=[]                             #必须要切断的时刻
    bpmlist=[0 for _ in range(maxtime)]     #每个时刻bpm的数值
    bpmaddlist=[0 for _ in range(maxtime)]  #绿蛇的bpm增量
    bpmmodify=[0.5 for _ in range(maxtime)] #bpm修改，默认0.5不修改
    zerolist=[]                             #暂存判定线需要置0的时刻
    for a in list1:             # 从原谱读取已有bpm和切断时刻
        if a[0]=='timing':
            bpm2=a[2]
            bpm2time=a[1]
            for i in range(bpm1time,bpm2time):bpmlist[i]=bpm1
            bpm1,bpm1time=bpm2,bpm2time
            timelist.append(a[1])
            continue
        timelist.append(a[1]-1)
        timelist.append(a[1])
        timelist.append(a[1]+1)
        zerolist.append(a[1])
    for i in range(bpm1time,maxtime):bpmlist[i]=bpm1
    for a in list2:             # 读取判定线位置和bpm修正
        if a[0]=='timing':
            continue
        starttime=a[1]
        endtime=a[2]
        x1=a[3]
        x2=a[4]
        easing=a[5]
        if a[8]==0:     #蓝色黑线；调整判定线位置
            for t in range(starttime,endtime+1):
                if easing=='s':
                    poslist[t]=x1+(x2-x1)*(t-starttime)/(endtime-starttime)
                if easing=='si':
                    poslist[t]=x1+(x2-x1)*math.sin(math.pi/2*(t-starttime)/(endtime-starttime))
                if easing=='so':
                    poslist[t]=x1+(x2-x1)*(1-math.cos(math.pi/2*(t-starttime)/(endtime-starttime)))
            timelist.append(starttime-1)
            timelist.append(starttime)
            timelist.append(endtime)
            timelist.append(endtime+1)
        if a[8]==1:     #红色黑线；调整bpm数值
            for t in range(starttime,endtime):
                if easing=='s':
                    bpmmodify[t]=x1+(x2-x1)*(t-starttime)/(endtime-starttime)
                if easing=='si':
                    bpmmodify[t]=x1+(x2-x1)*math.sin(math.pi/2*(t-starttime)/(endtime-starttime))
                if easing=='so':
                    bpmmodify[t]=x1+(x2-x1)*(1-math.cos(math.pi/2*(t-starttime)/(endtime-starttime)))
            timelist.append(starttime)
            timelist.append(endtime)
        if a[8]==2:     #绿色黑线；以蛇尾位置瞬移谱面
            bpmaddlist[starttime]=60000*a[4]*2
            timelist.append(starttime)
            timelist.append(starttime+1)
    for i in zerolist:
        poslist[i]=0
    for i in range(maxtime):
        bpmlist[i]*=bpmmodify[i]*2
        bpmlist[i]+=bpmaddlist[i]
    timelist.append(maxtime-1)
    timelist=sorted(set(timelist))
    while timelist[0]<=0:timelist.pop(0)
    t1,t2=0,0
    output=''
    lastbpm=0.00001
    while t2<maxtime-1 and len(timelist)>0:
        t2+=deltat
        if t2>=timelist[0]:
            t2=timelist.pop(0)
        if t2>=maxtime:break
        bpm1=(sum(bpmlist[t1:t2])-k*(poslist[t2]-poslist[t1]))/(t2-t1)
        bpm1=round(bpm1,4)
        if bpm1!=lastbpm:
            output+=f'timing({t1},{bpm1},4);\n'
        lastbpm=bpm1
        t1=t2
    f2.write(f'{tgstarters.pop(0)}\n{output}')
    tgstarters.pop(0)
    for s in originalaff.pop(0).split('\n'):
        if not 'timing(' in s:f2.write(s+'\n')
    originalaff.pop(0)
    #print(output)
f2.close()