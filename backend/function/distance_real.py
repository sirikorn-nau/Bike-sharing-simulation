
import streamlit as st
import streamlit.components.v1 as components
from geopy.distance import geodesic 



# -----------------------------------------------------------------------------
# ฟังก์ชันใหม่สำหรับคำนวณ timeline ของ agent โดยใช้ระยะทางจริง
def compute_segment_boundaries(path, t_per_meter, simulation_time_step):
    """
    - ฟังก์ชันนี้ใช้คำนวณจุดแบ่งเวลา (time boundaries) สำหรับแต่ละส่วน (segment) ของเส้นทาง 
    - แปลงระยะทางจริงให้เป็นจำนวน time steps ในการจำลอง
    path: เส้นทางที่เป็นชุดของพิกัด
    t_per_meter: เวลาที่ใช้ในการเดินทางต่อระยะทาง 1 เมตร (หน่วย: time step ต่อเมตร)
    simulation_time_step: ขนาดของ time step ในการจำลอง
    """
    # t_per_meter = 0.1           # เวลาที่ใช้เดิน 1 เมตร (วินาที)
    # simulation_time_step = 1    # 1 วินาทีต่อ time step

    boundaries = [0]
    total_steps = 0
    for i in range(len(path)-1):
        d = geodesic(path[i], path[i+1]).meters #  สำหรับแต่ละ segment คำนวณระยะทางจริงระหว่างจุดด้วย geodesic().meters
        
        seg_time = d * t_per_meter # คำนวณเวลาที่ใช้สำหรับ segment นั้น

        seg_steps = max(1, int(round(seg_time / simulation_time_step))) # แปลงเวลาเป็นจำนวน time steps โดยปัดเศษและกำหนดให้มีอย่างน้อย 1 step
        total_steps += seg_steps # เก็บสะสมจำนวน steps ทั้งหมดไว้ใน total_steps

        boundaries.append(total_steps) 

    return boundaries
    # คืนค่า list boundaries ที่เก็บค่าสะสมของ time steps ณ จุดสิ้นสุดของแต่ละ segment
    # ตัวอย่างเช่น [0, 5, 12, 18] หมายถึง segment แรกใช้ 5 steps, segment ที่สองใช้ 7 steps, และ segment ที่สามใช้ 6 steps
# -----------------------------------------------------------------------------

    







def interpolate_position(start, end, fraction):
    """คำนวณตำแหน่งระหว่าง start กับ end ตาม fraction (0-1)
       คืนค่าเป็น [lat, lon]"""
    return [
        start[0] + (end[0] - start[0]) * fraction,
        start[1] + (end[1] - start[1]) * fraction
    ]





# def compute_agent_timeline(path, t_per_meter, simulation_time_step, max_time_steps):
#     """
#     คำนวณ timeline ของ agent ตาม path ที่ให้
#       - ใช้ geodesic distance ในการคำนวณเวลาเดินแต่ละ segment
#       - simulation_time_step คือความยาวของ time step (วินาที)
#       - max_time_steps คือจำนวน time step สูงสุดที่ agent จะเดิน (เมื่อครบแล้วจะหยุด)
#     คืนค่า timeline เป็น list ของตำแหน่ง [lat, lon] สำหรับแต่ละ time step
#     """
#     timeline = []
#     total_steps = 0
#     for i in range(len(path)-1):
#         start = path[i]
#         end = path[i+1]
#         d = geodesic(start, end).meters
#         seg_time = d * t_per_meter  # เวลาเดินในหน่วยวินาที
#         seg_steps = max(1, int(round(seg_time / simulation_time_step)))
#         for step in range(seg_steps):
#             # หากจำนวน time steps รวมเกิน max_time_steps ให้หยุดทันที
#             if total_steps >= max_time_steps:
#                 return timeline[:max_time_steps]
#             fraction = step / seg_steps
#             timeline.append(interpolate_position(start, end, fraction))
#             total_steps += 1
#     # เติมตำแหน่งสุดท้าย (จุดหมายปลายทาง) ถ้ายังไม่ครบ max_time_steps
#     while len(timeline) < max_time_steps:
#         timeline.append(path[-1])
#     return timeline[:max_time_steps]





def compute_agent_timeline(path, t_per_meter, simulation_time_step, max_time_step):
    """
    ปัญหา: ฟังก์ชัน compute_agent_timeline อาจเกิดข้อผิดพลาดหากเส้นทาง (path) ไม่ถูกต้องหรือมีค่าว่าง
    แก้ไข: ตรวจสอบเส้นทางก่อนคำนวณ timeline
    """
    timeline = {}
    if not path or len(path) < 2:
        return {t: path[0] for t in range(max_time_step)}
    
    # คำนวณระยะทางทั้งหมดตามเส้นทาง
    total_distance = 0
    for i in range(1, len(path)):
        try:
            segment_distance = geodesic(path[i-1], path[i]).meters
            total_distance += segment_distance
        except Exception as e:
            print(f"Error calculating distance: {e}")
            segment_distance = 0.001  # ค่าเริ่มต้นเล็กๆ เพื่อป้องกันการหารด้วยศูนย์
            total_distance += segment_distance
    
    total_time = total_distance * t_per_meter
    
    # ถ้าเวลาทั้งหมดเป็น 0 กำหนดค่าเริ่มต้น
    if total_time <= 0:
        total_time = 1
    
    # สร้าง timeline
    for t in range(max_time_step):
        real_time = t * simulation_time_step
        if real_time >= total_time:
            timeline[t] = path[-1]  # ถึงจุดหมายแล้ว
        else:
            # คำนวณตำแหน่งตามเวลา
            progress_ratio = real_time / total_time
            
            # หาตำแหน่งในเส้นทาง
            cumulative_distance = 0
            for i in range(1, len(path)):
                segment_distance = geodesic(path[i-1], path[i]).meters
                new_cumulative = cumulative_distance + segment_distance
                
                if cumulative_distance / total_distance <= progress_ratio <= new_cumulative / total_distance:
                    # คำนวณตำแหน่งระหว่างจุดสองจุด
                    segment_progress = (progress_ratio - cumulative_distance / total_distance) / (segment_distance / total_distance)
                    lat1, lon1 = path[i-1]
                    lat2, lon2 = path[i]
                    interpolated_pos = (
                        lat1 + segment_progress * (lat2 - lat1),
                        lon1 + segment_progress * (lon2 - lon1)
                    )
                    timeline[t] = interpolated_pos
                    break
                
                cumulative_distance = new_cumulative
            
            # ถ้าไม่ได้กำหนดตำแหน่ง ให้ใช้ตำแหน่งสุดท้าย
            if t not in timeline:
                timeline[t] = path[-1]
    
    return timeline