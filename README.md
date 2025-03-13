

# google_map_agent

## Backend
```
cd .\backend\
python -m venv env
.\env\Scripts\activate
pip install -r requirements.txt
```

- ถ้าโหลดไรมาใน backend ให้เข้า env แล้วพิมตัวนี้
pip freeze > requirements.txt

**คำสั่งรัน**
```uvicorn main:app --host 127.0.0.1 --port 8000```


---

## Frontend
```
cd .\my-frontend\
npm install
```

**คำสั่งรัน** 
```npm start```





ที่ต้องทำ
- ปักหมุด สถานีบนลาดกระบัง
- กำหนดให้สุ่มใน ลาดกระบัง
- คำนวณ path ตาม backend
- ทำ route เพิ่ม by a* 
- ค่อยนำมาเทียบกัน



<!-- streamlit run app.py -->
env\Scripts\activate 
streamlit run app.py

# อธิบาย
folium → ใช้สร้างแผนที่
streamlit → ใช้ทำอินเทอร์เฟซแบบเว็บ
random → ใช้สุ่มตำแหน่งเริ่มต้นและปลายทาง
heapq → อาจใช้สำหรับ A* ในอนาคต (แต่ตอนนี้ไม่ได้ใช้)
json → แปลงตำแหน่งตัวแทนเป็น JSON สำหรับใช้ใน JavaScript
streamlit.components.v1 → ใช้ฝัง HTML และ JavaScript ลงใน Streamlit





# ปัญหา

## วิธีแก้ไขปัญหา มันโชว์หลายเฟรม
1. ใช้ JavaScript ใน Folium
- ใช้ folium.plugins.TimestampedGeoJson หรือ folium.plugins.MarkerCluster เพื่ออัปเดตตำแหน่งของ Marker แบบต่อเนื่อง
- ใช้ JavaScript เพื่อเคลื่อนย้าย Marker โดยไม่ต้องสร้างแผนที่ใหม่ทุกครั้ง

2. ใช้ Streamlit กับ HTML/JS Components
- ใช้ st.components.v1.html() เพื่อฝัง JavaScript ที่อัปเดตตำแหน่ง Marker ตามข้อมูลที่ส่งมาจาก Python


## วิธีแก้ปัญหา มันสร้าง Marker ใหม่เรื่อยๆ ให้เหมือนเป็นการเคลื่อนไหว real-time แต่มันไม่ลบ Marker เก่า
- ใช้ JavaScript เพื่ออัปเดตตำแหน่ง Marker ที่มีอยู่แทนการสร้างใหม่
- อัปเดตตำแหน่ง Marker โดยใช้ **setLatLng()** แทนการสร้าง Marker ใหม่
- เมื่อ Marker เคลื่อนที่ไปตำแหน่งใหม่ ตำแหน่งเก่าจะถูก**ลบอัตโนมัติ**
- ใช้ setTimeout() ใน JavaScript เพื่ออัปเดต Marker ทุก 500ms


---


- สถานี (Stations) ที่ fix ไว้
- Agent แต่ละคนที่มีเส้นทางเดิน (Route) โดยใช้ A* คำนวณระหว่างสถานี
- การ animate marker โดยอัปเดตตำแหน่งของ agent ในแต่ละ timestep บนแผนที่เดียว (เหมือนวิดีโอ)
- สุ่มตำแหน่งเริ่มต้นและปลายทางของ agent จากนั้นเลือกสถานีที่ใกล้ที่สุดเพื่อคำนวณเส้นทาง
- เส้นทางของ agent จะประกอบด้วย จุดเริ่มต้น, สถานีต้นทาง, เส้นทางจาก A* (ระหว่างสถานี), และจุดปลายทาง


# รอทำ 🫧𓇼𓏲*ੈ✩‧₊˚🎐
- เปรียบความสัมพันธ์ระหว่าง a* , cbs
- แก้โครงงาน


