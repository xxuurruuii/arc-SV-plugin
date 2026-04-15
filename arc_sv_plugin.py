import traceback
try:
    import os
    #print("当前工作目录:", os.getcwd())
    #print("脚本所在目录:", os.path.dirname(os.path.abspath(__file__)))
    import bisect
    import re
    import math

    def format_aff_float(value):
        if abs(value)<1e-9:
            value=0.0
        s=f'{value:.6f}'.rstrip('0').rstrip('.')
        if '.' not in s:
            s+='.00'
        else:
            frac=s.split('.',1)[1]
            if len(frac)<2:
                s+='0'*(2-len(frac))
        return s

    def easing_progress(easing,ratio):
        ratio=max(0.0,min(1.0,ratio))
        if easing=='si':
            return math.sin(math.pi/2*ratio)
        if easing=='so':
            return 1-math.cos(math.pi/2*ratio)
        return ratio

    def split_easing_mode(easing):
        if easing in ('s','b','si','so'):
            return easing,easing
        if easing in ('sisi','siso','sosi','soso'):
            return easing[:2],easing[2:]
        return 's','s'

    def interpolate_arc(starttime,endtime,v1,v2,easing,t):
        if endtime==starttime:
            return v1
        ratio=(t-starttime)/(endtime-starttime)
        return v1+(v2-v1)*easing_progress(easing,ratio)

    def split_arc_line_by_timings(line,timing_points,timing_times=None,timing_bpms=None,drop_zero_bpm=False):
        pat=re.compile('arc\\(([^)]+)\\)(.*);')
        mat=pat.match(line)
        if mat is None:
            return [line]
        params=mat.group(1).split(',')
        if len(params)<10:
            return [line]
        try:
            starttime=int(params[0])
            endtime=int(params[1])
            x1=float(params[2])
            x2=float(params[3])
            easing=params[4]
            y1=float(params[5])
            y2=float(params[6])
            color=int(params[7])
            hitsound=params[8]
            arctype=params[9]
        except:
            return [line]
        if endtime<=starttime:
            return [line]
        cut_points=sorted({t for t in timing_points if starttime<t<endtime})
        if len(cut_points)==0:
            return [line]

        extra=mat.group(2).strip()
        arctaps=[]
        if extra!='':
            if not (extra.startswith('[') and extra.endswith(']')):
                return [line]
            raw_parts=extra[1:-1].split(',')
            for part in raw_parts:
                part=part.strip()
                if part=='':
                    continue
                arcpat=re.fullmatch('arctap\\((-?\\d+)\\)',part)
                if arcpat is None:
                    return [line]
                arctaps.append(int(arcpat.group(1)))

        xmode,ymode=split_easing_mode(easing)
        points=[starttime]+cut_points+[endtime]
        output=[]
        for i in range(len(points)-1):
            st=points[i]
            ed=points[i+1]
            if drop_zero_bpm and timing_times is not None and timing_bpms is not None and len(timing_times)>0:
                idx=bisect.bisect_right(timing_times,st)-1
                if idx>=0 and abs(timing_bpms[idx])<1e-9:
                    continue
            segx1=interpolate_arc(starttime,endtime,x1,x2,xmode,st)
            segx2=interpolate_arc(starttime,endtime,x1,x2,xmode,ed)
            segy1=interpolate_arc(starttime,endtime,y1,y2,ymode,st)
            segy2=interpolate_arc(starttime,endtime,y1,y2,ymode,ed)

            segment_taps=[]
            for tap in arctaps:
                if st<=tap<=ed and not (tap==st and i>0):
                    segment_taps.append(tap)
            segextra=''
            if len(segment_taps)>0:
                segextra='['+','.join([f'arctap({i})' for i in segment_taps])+']'

            output.append(
                f'arc({st},{ed},{format_aff_float(segx1)},{format_aff_float(segx2)},{easing},'
                f'{format_aff_float(segy1)},{format_aff_float(segy2)},{color},{hitsound},{arctype}){segextra};'
            )
        return output

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



    f=open(os.path.dirname(os.path.abspath(__file__))+"\\1.aff",'r')
    f2=open(os.path.dirname(os.path.abspath(__file__))+'\\0.aff','w')
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
        first_tg_noinput=('noinput' in tgstarters[0])
        hidegroup_controls=[]                   # 由起始y=0.5的绿线生成的hidegroup控制
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
                y1=a[6]
                y2=a[7]
                if abs(y1-1.0)<1e-6 or abs(y1-0.0)<1e-6:
                    if abs(y1-1.0)<1e-6:     #若绿色黑线满足y=1, 该瞬移发生在前1ms
                        starttime-=1
                    bpmaddlist[starttime]=60000*a[4]*2
                    timelist.append(starttime)
                    timelist.append(starttime+1)
                elif abs(y1-0.5)<1e-6:
                    if abs(y2-1.0)<1e-6 or abs(y2-0.0)<1e-6:
                        hidegroup_controls.append((a[1],int(round(y2))))
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
        generated_timing_entries=[]
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
                generated_timing_entries.append((t1,bpm1))
            lastbpm=bpm1
            t1=t2
        f2.write(f'{tgstarters.pop(0)}\n{output}')
        for t,hidevalue in hidegroup_controls:
            f2.write(f'scenecontrol({t},hidegroup,0.00,{hidevalue});\n')
        tgstarters.pop(0)
        generated_timing_points=[i[0] for i in generated_timing_entries]
        generated_timing_bpms=[i[1] for i in generated_timing_entries]
        first_group_content=originalaff.pop(0)
        for s in first_group_content.split('\n'):
            if 'timing(' in s:
                continue
            if first_tg_noinput and s.startswith('arc'):
                for seg in split_arc_line_by_timings(
                    s,
                    generated_timing_points,
                    generated_timing_points,
                    generated_timing_bpms,
                    True
                ):
                    f2.write(seg+'\n')
                continue
            f2.write(s+'\n')
        originalaff.pop(0)
        #print(output)
    f2.close()
except:
    print(traceback.format_exc())
    input()
