import os
import time
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
import requests

app = FastAPI()

# --- CORS CONFIGURATION ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CONFIGURATION ---
lh_url = os.getenv("LH_DB_URL")   # WarehousePG / Lakehouse Connection
pgd_url = os.getenv("PGD_DB_URL") # EDB Postgres Distributed Connection
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Spark Connect URLs (Defaults provided, but can be overridden via .env)
SPARK_CPU_URL = os.getenv("SPARK_CPU_URL", "sc://spark-connect:15002")
SPARK_GPU_URL = os.getenv("SPARK_GPU_URL", "sc://spark-gpu:15002")

# --- GLOBAL DEMO STATE ---
# Tracks the currently selected PGAA execution engine (seafowl, spark_cpu, spark_gpu)
CURRENT_ENGINE = "seafowl"

# --- DATA MODELS ---
class GeminiRequest(BaseModel):
    prompt: str
    system_instruction: str = ""

class EngineSwitchRequest(BaseModel):
    engine: str

# --- HELPER: ENGINE GUC INJECTOR ---
def apply_engine_gucs(cur):
    """Injects the correct PGAA configuration into the current session."""
    if CURRENT_ENGINE == "seafowl":
        cur.execute("SET pgaa.executor_engine = 'seafowl';")
    elif CURRENT_ENGINE == "spark_cpu":
        cur.execute("SET pgaa.executor_engine = 'spark_connect';")
        cur.execute(f"SET pgaa.spark_connect_url = '{SPARK_CPU_URL}';")
    elif CURRENT_ENGINE == "spark_gpu":
        cur.execute("SET pgaa.executor_engine = 'spark_connect';")
        cur.execute(f"SET pgaa.spark_connect_url = '{SPARK_GPU_URL}';")


# ==========================================
# ENGINE SWITCH API
# ==========================================

@app.post("/api/engine/switch")
def switch_engine(req: EngineSwitchRequest):
    global CURRENT_ENGINE
    if req.engine not in ["seafowl", "spark_cpu", "spark_gpu"]:
        raise HTTPException(status_code=400, detail="Invalid engine specified")
    CURRENT_ENGINE = req.engine
    return {"status": "success", "current_engine": CURRENT_ENGINE}


# ==========================================
# WHPG / LAKEHOUSE ENDPOINTS (ANALYTICS)
# ==========================================

@app.get("/api/dashboard/summary")
def get_dashboard_summary():
    try:
        with psycopg2.connect(lh_url) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                apply_engine_gucs(cur)
                cur.execute("""
                    SELECT
                        COUNT(DISTINCT lo.id) AS total_orders,
                        COALESCE(SUM(lo.quantity * i.price), 0) AS real_time_revenue
                    FROM demo.live_orders lo
                    JOIN demo.items i ON lo.item_id = i.id
                    WHERE lo.order_timestamp >= CURRENT_DATE;
                """)
                return cur.fetchone()
    except Exception as e:
        print(f"Database Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch summary metrics.")

@app.get("/api/dashboard/velocity")
def get_order_velocity():
    try:
        with psycopg2.connect(lh_url) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                apply_engine_gucs(cur)
                cur.execute("""
                    SELECT
                        DATE_TRUNC('minute', time_spine) AS minute_bucket,
                        COUNT(lo.id) AS orders_per_minute,
                        COALESCE(SUM(lo.quantity * i.price), 0) AS revenue_per_minute
                    FROM generate_series(
                        DATE_TRUNC('minute', NOW()) - INTERVAL '60 minutes',
                        DATE_TRUNC('minute', NOW()),
                        INTERVAL '1 minute'
                    ) AS time_spine
                    LEFT JOIN demo.live_orders lo 
                        ON DATE_TRUNC('minute', lo.order_timestamp) = DATE_TRUNC('minute', time_spine)
                    LEFT JOIN demo.items i ON lo.item_id = i.id
                    GROUP BY 1
                    ORDER BY 1 ASC;
                """)
                return cur.fetchall()
    except Exception as e:
        print(f"Database Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch velocity metrics.")

@app.get("/api/dashboard/baseline")
def get_baseline_comparison():
    try:
        with psycopg2.connect(lh_url) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                apply_engine_gucs(cur)
                
                # Start the execution timer
                start_time = time.time()
                
                cur.execute("""
                    WITH live_metrics AS (
                        SELECT
                            EXTRACT(DOW FROM order_timestamp) AS day_of_week,
                            EXTRACT(HOUR FROM order_timestamp) AS hour_of_day,
                            CAST(SUM(lo.quantity * i.price) AS NUMERIC) AS current_revenue
                        FROM demo.live_orders lo
                        JOIN demo.items i ON lo.item_id = i.id
                        WHERE DATE_TRUNC('hour', order_timestamp) = DATE_TRUNC('hour', NOW())
                        GROUP BY 1, 2
                    ),
                    historical_baseline AS (
                        SELECT
                            EXTRACT(DOW FROM sale_timestamp) AS day_of_week,
                            EXTRACT(HOUR FROM sale_timestamp) AS hour_of_day,
                            CAST(SUM(hs.quantity * i.price) / COUNT(DISTINCT DATE_TRUNC('day', sale_timestamp)) AS NUMERIC) AS avg_historical_revenue
                        FROM demo.historical_sales hs
                        JOIN demo.items i ON hs.item_id = i.id
                        WHERE sale_timestamp >= NOW() - INTERVAL '90 days'
                        GROUP BY 1, 2
                    )
                    SELECT
                        COALESCE(lm.current_revenue, CAST(0 AS NUMERIC)) AS current_revenue,
                        COALESCE(hb.avg_historical_revenue, CAST(0 AS NUMERIC)) AS avg_historical_revenue,
                        CASE 
                            -- Use ANSI CAST instead of ::NUMERIC for Spark compatibility
                            WHEN hb.avg_historical_revenue > CAST(0 AS NUMERIC) THEN 
                                ROUND(CAST(((COALESCE(lm.current_revenue, CAST(0 AS NUMERIC)) - hb.avg_historical_revenue) / hb.avg_historical_revenue) * 100 AS NUMERIC), 2)
                            ELSE CAST(0 AS NUMERIC) 
                        END AS percent_difference
                    FROM historical_baseline hb
                    LEFT JOIN live_metrics lm 
                        ON lm.day_of_week = hb.day_of_week AND lm.hour_of_day = hb.hour_of_day;
                """)
                result = dict(cur.fetchone() or {"current_revenue": 0, "avg_historical_revenue": 0, "percent_difference": 0})
                
                # Calculate execution time in milliseconds
                exec_time_ms = int((time.time() - start_time) * 1000)
                result["execution_time_ms"] = exec_time_ms
                
                return result
    except Exception as e:
        print(f"Database Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch baseline metrics.")

@app.get("/api/dashboard/campaigns")
def get_campaign_attribution():
    try:
        with psycopg2.connect(lh_url) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                apply_engine_gucs(cur)
                cur.execute("""
                    SELECT
                        COALESCE(c.name, 'Organic / No Campaign') AS campaign_name,
                        COUNT(lo.id) AS total_orders,
                        SUM(lo.quantity * i.price) AS generated_revenue
                    FROM demo.live_orders lo
                    JOIN demo.items i ON lo.item_id = i.id
                    LEFT JOIN demo.campaigns c ON lo.campaign_id = c.id
                    WHERE lo.order_timestamp >= CURRENT_DATE
                    GROUP BY 1
                    ORDER BY generated_revenue DESC;
                """)
                return cur.fetchall()
    except Exception as e:
        print(f"Database Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch campaign attribution.")


# ==========================================
# PGD ENDPOINTS (TRANSACTIONAL / LIVE)
# ==========================================

@app.post("/api/trigger-target-customer")
def trigger_target_customer():
    try:
        with psycopg2.connect(pgd_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO demo.live_orders 
                    (store_id, customer_id, item_id, campaign_id, quantity) 
                    VALUES ('MV-01', 123, 1, 'SPRING_LATTE_PROMO', 1)
                    RETURNING id;
                """)
                order_id = cur.fetchone()[0]
                
                cur.execute("""
                    UPDATE demo.customers 
                    SET propensity_score = LEAST(propensity_score + 0.15, 1.00) 
                    WHERE id = 123
                    RETURNING propensity_score, first_name;
                """)
                result = cur.fetchone()
                conn.commit()
                
        return {
            "status": "success", 
            "message": f"Order processed for {result[1]}.", 
            "order_id": order_id,
            "new_propensity_score": float(result[0])
        }
    except Exception as e:
        print(f"Database Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger target customer order.")


# ==========================================
# AI / UTILITY ENDPOINTS
# ==========================================

@app.post("/api/generate")
async def generate_text(request: GeminiRequest):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Server missing API Key")
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": request.prompt}]}],
        "systemInstruction": {"parts": [{"text": request.system_instruction}]}
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        text = data['candidates'][0]['content']['parts'][0]['text']
        return {"text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))