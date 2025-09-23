from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from datetime import datetime, timedelta
from ..database import get_database, Database

router = APIRouter()

@router.get("/ai-recommendations", response_model=List[Dict[str, Any]])
def get_ai_recommendations(db: Database = Depends(get_database)):
    """
    获取AI最有把握的投注推荐
    从ai_eval表中筛选：
    - 比赛是否推荐 = 1
    - 推荐指数前3条
    - 平均赔率不为空
    - 比赛时间：今天下午到明天24点
    """
    try:
        # 计算时间范围：今天下午12点到明天24点
        now = datetime.now()
        today_noon = now.replace(hour=12, minute=0, second=0, microsecond=0)
        tomorrow_end = (now + timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=999999)
        
        query = """
        SELECT 
            league_name,
            home_name,
            away_name,
            平均赔率,
            fixture_date,
            推荐指数,
            比赛预测及原因,
            预测结果
        FROM ai_eval 
        WHERE 比赛是否推荐 = 1 
        AND 平均赔率 IS NOT NULL 
        AND fixture_date >= %s
        AND fixture_date <= %s
        ORDER BY 推荐指数 DESC 
        LIMIT 3
        """
        
        results = db.fetch_all(query, (today_noon, tomorrow_end))
        
        if not results:
            return []
        
        # 格式化返回数据
        formatted_results = []
        for row in results:
            formatted_results.append({
                "id": f"{row['home_name']}-{row['away_name']}-{row['fixture_date']}",
                "league": row['league_name'],
                "home_team": row['home_name'],
                "away_team": row['away_name'],
                "odds": row['平均赔率'],
                "fixture_date": row['fixture_date'],
                "recommendation_index": float(row['推荐指数']) if row['推荐指数'] else 0.0,
                "analysis": row['比赛预测及原因'],
                "prediction_result": row['预测结果']
            })
        
        return formatted_results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/ai-recommendations/test")
def test_connection(db: Database = Depends(get_database)):
    """测试数据库连接"""
    try:
        # 测试简单查询
        result = db.fetch_one("SELECT 1 as test")
        return {"status": "success", "message": "Database connection successful", "test_result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")