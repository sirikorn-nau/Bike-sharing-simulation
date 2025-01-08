

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
