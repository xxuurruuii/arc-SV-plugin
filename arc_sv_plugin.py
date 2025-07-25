import re
import math
import os

def parse_aff_file(content):
    originalaff = []
    tg = -1
    output = []
    for s in content.split('\n'):
        s = s.strip()
        if s.startswith('timinggroup'):
            tg += 1
            originalaff.append('')
            currenttg = []
            continue
        if tg < 0:
            continue
        originalaff[-1] += s + '\n'
        if s.startswith('arc'):
            pat = re.compile('arc\(([^)]+)\)(.*);')
            mat = pat.match(s)
            params1 = mat.group(1).split(',')
            params1[0] = int(params1[0])
            params1[1] = int(params1[1])
            params1[2] = float(params1[2])
            params1[3] = float(params1[3])
            params1[4] = params1[4]
            params1[5] = float(params1[5])
            params1[6] = float(params1[6])
            params1[7] = int(params1[7])
            params1[8] = params1[8]
            params1[9] = bool(params1[9])
            params2 = mat.group(2)
            if params2 != '':
                params2 = params2[1:-1].split(',')
                params2 = [int(i[7:-1]) for i in params2]
            else:
                params2 = []
            params1 = ['arc'] + params1 + [params2]
            currenttg.append(params1)
            continue
        if s.startswith('timing('):
            pat = re.compile('timing\(([^)]+)\);')
            mat = pat.match(s)
            params1 = mat.group(1).split(',')
            params1[0] = int(params1[0])
            params1[1] = float(params1[1])
            params1[2] = params1[2]
            params1 = ['timing'] + params1
            currenttg.append(params1)
            continue
        if s.startswith('('):
            pat = re.compile('\(([^)]+)\);')
            mat = pat.match(s)
            params1 = mat.group(1).split(',')
            params1[0] = int(params1[0])
            params1[1] = int(params1[1])
            params1 = ['tap'] + params1
            currenttg.append(params1)
            continue
        if s == '};':
            output.append(currenttg)
    return output, originalaff

def main():
    print("arc谱面文件转换器")
    input_file = input("请输入aff文件路径（可以直接将aff文件拖进来）: ").strip()
    
    if not os.path.exists(input_file):
        print(f"此arc谱面文件不存在！")
        return
    
    base_name = os.path.splitext(input_file)[0]
    output_file = f"{base_name}_converted.aff"
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"此arc谱面文件无法读取哦 {input_file}: {e}")
        return
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f2:
            deltat = 30
            
            for s in content.split('\n'):
                if s.startswith('timinggroup'):
                    break
                f2.write(s + '\n')
            
            for s in content.split('\n'):
                if s.startswith('timing'):
                    pat = re.compile('timing\(([^)]+)\);')
                    mat = pat.match(s)
                    params1 = mat.group(1).split(',')
                    bpm = float(params1[1])
                    break
            
            k = 60000 * 2 / 2
            
            parsed_data, originalaff = parse_aff_file(content)
            
            while len(parsed_data) >= 2:
                list1 = parsed_data.pop(0)
                list2 = parsed_data.pop(0)
                a = list2.pop(0)
                bpm1 = a[2]
                bpm1time = 0
                maxtime = max(list1[-1][1], list2[-1][2]) + 100
                poslist = [0 for _ in range(maxtime)]
                timelist = []
                bpmlist = [0 for _ in range(maxtime)]
                bpmmodify = [0.5 for _ in range(maxtime)]
                zerolist = []
                
                for a in list1:
                    if a[0] == 'timing':
                        bpm2 = a[2]
                        bpm2time = a[1]
                        for i in range(bpm1time, bpm2time):
                            bpmlist[i] = bpm1
                        bpm1, bpm1time = bpm2, bpm2time
                        timelist.append(a[1])
                        continue
                    timelist.append(a[1] - 1)
                    timelist.append(a[1])
                    timelist.append(a[1] + 1)
                    zerolist.append(a[1])
                
                for i in range(bpm1time, maxtime):
                    bpmlist[i] = bpm1
                
                for a in list2:
                    if a[0] == 'timing':
                        continue
                    starttime = a[1]
                    endtime = a[2]
                    x1 = a[3]
                    x2 = a[4]
                    easing = a[5]
                    
                    if a[8] == 0:
                        for t in range(starttime, endtime + 1):
                            if easing == 's':
                                poslist[t] = x1 + (x2 - x1) * (t - starttime) / (endtime - starttime)
                            if easing == 'si':
                                poslist[t] = x1 + (x2 - x1) * math.sin(math.pi / 2 * (t - starttime) / (endtime - starttime))
                            if easing == 'so':
                                poslist[t] = x1 + (x2 - x1) * (1 - math.cos(math.pi / 2 * (t - starttime) / (endtime - starttime)))
                        timelist.append(starttime - 1)
                        timelist.append(starttime)
                        timelist.append(endtime)
                        timelist.append(endtime + 1)
                    
                    if a[8] == 1:
                        for t in range(starttime, endtime):
                            if easing == 's':
                                bpmmodify[t] = x1 + (x2 - x1) * (t - starttime) / (endtime - starttime)
                            if easing == 'si':
                                bpmmodify[t] = x1 + (x2 - x1) * math.sin(math.pi / 2 * (t - starttime) / (endtime - starttime))
                            if easing == 'so':
                                bpmmodify[t] = x1 + (x2 - x1) * (1 - math.cos(math.pi / 2 * (t - starttime) / (endtime - starttime)))
                        timelist.append(starttime)
                        timelist.append(endtime)
                    
                    if a[8] == 2:
                        bpmlist[starttime] = 60000 * a[4] * 2
                        timelist.append(starttime)
                        timelist.append(starttime + 1)
                
                for i in zerolist:
                    poslist[i] = 0
                
                for i in range(maxtime):
                    bpmlist[i] *= bpmmodify[i] * 2
                
                timelist.append(maxtime - 1)
                timelist = sorted(set(timelist))
                
                while timelist[0] <= 0:
                    timelist.pop(0)
                
                t1, t2 = 0, 0
                output = ''
                
                while t2 < maxtime - 1 and len(timelist) > 0:
                    t2 += deltat
                    if t2 >= timelist[0]:
                        t2 = timelist.pop(0)
                    if t2 >= maxtime:
                        break
                    bpm1 = (sum(bpmlist[t1:t2]) - k * (poslist[t2] - poslist[t1])) / (t2 - t1)
                    output += f'timing({t1},{bpm1},4);\n'
                    t1 = t2
                
                f2.write(f'timinggroup(){{\n{output}')
                
                for s in originalaff.pop(0).split('\n'):
                    if not 'timing(' in s:
                        f2.write(s + '\n')
                
                originalaff.pop(0)
        
        print(f"转换完成！aff路径： {output_file}")
    
    except Exception as e:
        print(f"转换失败！ {e}")

if __name__ == "__main__":
    main()