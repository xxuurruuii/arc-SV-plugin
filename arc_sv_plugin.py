import re
import math
import os

def parse_aff_file(content):
    originalaff = []
    tg = -1
    output = []
    currenttg = []
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
            if not mat:
                continue
            params1 = mat.group(1).split(',')
            params1[0] = int(params1[0])
            params1[1] = int(params1[1])
            params1[2] = float(params1[2])
            params1[3] = float(params1[3])
            params1[4] = params1[4].strip()
            params1[5] = float(params1[5])
            params1[6] = float(params1[6])
            params1[7] = int(params1[7])
            params1[8] = params1[8].strip()
            params1[9] = params1[9].strip().lower() == 'true'
            params2 = mat.group(2)
            if params2 != '':
                params2 = params2[1:-1].split(',')
                params2 = [int(i[7:-1]) for i in params2 if i.startswith('arctap(')]
            else:
                params2 = []
            params1 = ['arc'] + params1 + [params2]
            currenttg.append(params1)
            continue
        if s.startswith('timing('):
            pat = re.compile('timing\(([^)]+)\);')
            mat = pat.match(s)
            if not mat:
                continue
            params1 = mat.group(1).split(',')
            params1[0] = int(params1[0])
            params1[1] = float(params1[1])
            params1[2] = params1[2].strip()
            params1 = ['timing'] + params1
            currenttg.append(params1)
            continue
        if s.startswith('('):
            pat = re.compile('\(([^)]+)\);')
            mat = pat.match(s)
            if not mat:
                continue
            params1 = mat.group(1).split(',')
            params1[0] = int(params1[0])
            params1[1] = int(params1[1])
            params1 = ['tap'] + params1
            currenttg.append(params1)
            continue
        if s == '};' and tg >= 0:
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
            
            # 文件头
            for s in content.split('\n'):
                if s.startswith('timinggroup'):
                    break
                if s.strip() != '':
                    f2.write(s + '\n')
            
            # 基础BPM
            base_bpm = 100.0
            for s in content.split('\n'):
                if s.startswith('timing('):
                    pat = re.compile('timing\(([^)]+)\);')
                    mat = pat.match(s)
                    if mat:
                        params1 = mat.group(1).split(',')
                        base_bpm = float(params1[1])
                        break
            
            parsed_data, originalaff = parse_aff_file(content)
            
            while len(parsed_data) >= 2:
                list1 = parsed_data.pop(0)
                list2 = parsed_data.pop(0)
                
                maxtime = 0
                for event in list1 + list2:
                    if event[0] == 'arc':
                        maxtime = max(maxtime, event[1], event[2])
                    else:
                        maxtime = max(maxtime, event[1])
                maxtime += 100
                
                poslist = [0.0] * (maxtime + 1)
                timelist = []
                bpmlist = [base_bpm] * (maxtime + 1)
                bpmmodify = [1.0] * (maxtime + 1)
                zerolist = []
                
                # 处理第一个tg
                bpm1 = base_bpm
                bpm1time = 0
                for a in list1:
                    if a[0] == 'timing':
                        bpm2 = a[2]
                        bpm2time = a[1]
                        for i in range(bpm1time, bpm2time + 1):
                            if i < len(bpmlist):
                                bpmlist[i] = bpm1
                        bpm1, bpm1time = bpm2, bpm2time
                        timelist.append(a[1])
                        continue
                    zerolist.append(a[1])
                
                # 剩下的BPM
                for i in range(bpm1time, min(maxtime + 1, len(bpmlist))):
                    bpmlist[i] = bpm1
                
                for a in list2:
                    if a[0] == 'timing':
                        continue
                    if a[0] != 'arc':
                        continue
                    
                    starttime = a[1]
                    endtime = a[2]
                    x1 = a[3]
                    x2 = a[4]
                    easing = a[5]
                    arc_type = a[8]
                    
                    # 位置变化
                    if arc_type == '0':
                        for t in range(starttime, min(endtime + 1, len(poslist))):
                            ratio = (t - starttime) / max(1, (endtime - starttime))
                            if easing == 's':
                                poslist[t] = x1 + (x2 - x1) * ratio
                            elif easing == 'si':
                                poslist[t] = x1 + (x2 - x1) * math.sin(math.pi / 2 * ratio)
                            elif easing == 'so':
                                poslist[t] = x1 + (x2 - x1) * (1 - math.cos(math.pi / 2 * ratio))
                        timelist.extend([starttime - 1, starttime, endtime, endtime + 1])
                    
                    elif arc_type == '1':
                        for t in range(starttime, min(endtime + 1, len(bpmmodify))):
                            ratio = (t - starttime) / max(1, (endtime - starttime))
                            if easing == 's':
                                bpmmodify[t] = x1 + (x2 - x1) * ratio
                            elif easing == 'si':
                                bpmmodify[t] = x1 + (x2 - x1) * math.sin(math.pi / 2 * ratio)
                            elif easing == 'so':
                                bpmmodify[t] = x1 + (x2 - x1) * (1 - math.cos(math.pi / 2 * ratio))
                        timelist.extend([starttime, endtime])
                
                for t in zerolist:
                    if t < len(poslist):
                        poslist[t] = 0
                
                for i in range(min(len(bpmlist), len(bpmmodify))):
                    bpmlist[i] *= bpmmodify[i]
                
                # 生成时间点列表
                timelist = sorted(set(t for t in timelist if 0 <= t < len(poslist)))
                
                # 生成新的timing
                t1, t2 = 0, 0
                output_lines = []
                
                while t2 < maxtime and timelist:
                    if t2 >= timelist[0]:
                        t2 = timelist.pop(0)
                    else:
                        t2 += deltat
                    
                    if t2 >= maxtime or t2 >= len(poslist):
                        break
                    
                    # 计算平均BPM
                    if t2 > t1:
                        total_bpm = 0.0
                        count = 0
                        for t in range(t1, t2 + 1):
                            if t < len(bpmlist):
                                total_bpm += bpmlist[t]
                                count += 1
                        if count > 0:
                            avg_bpm = total_bpm / count
                            output_lines.append(f'timing({t1},{avg_bpm},4);\n')
                    t1 = t2
                
                # 写入新的tg
                f2.write(f'timinggroup(){{\n')
                for line in output_lines:
                    f2.write(line)
                
                if originalaff:
                    aff_content = originalaff.pop(0)
                    for s in aff_content.split('\n'):
                        if 'timing(' not in s:
                            f2.write(s + '\n')
                
                if originalaff:
                    originalaff.pop(0)
                
                f2.write('};\n')
        
        print(f"转换完成！aff路径： {output_file}")
    
    except Exception as e:
        import traceback
        print(f"转换失败！ {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    main()