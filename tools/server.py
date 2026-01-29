from fastapi import FastAPI
app = FastAPI()

@app.get("/")
def home():
    return {"message": "ALU/Tool Server Online"}

@app.get("/hello")
def hello():
    return {"value": 90, "status": "success"}

@app.get("/health")
def health_check():
    # This is the "Heartbeat" signal for the Control Unit
    return {"status": "ok"}