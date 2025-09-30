from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
from ..database import get_database, Database

router = APIRouter()

@router.get("/ai-recommendations", response_model=List[Dict[str, Any]])
def get_ai_recommendations(
    locale: Optional[str] = Query(default="zh", description="用户语言设置"),
    db: Database = Depends(get_database)
):
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
            预测结果,
            reason_dict
        FROM ai_eval 
        WHERE 比赛是否推荐 = 1 
        AND 平均赔率 IS NOT NULL 
        AND fixture_date >= %s
        AND fixture_date <= %s
        AND reason_dict IS NOT NULL
        ORDER BY 推荐指数 DESC 
        LIMIT 3
        """
        
        results = db.fetch_all(query, (today_noon, tomorrow_end))
        
        if not results:
            return []
        
        # 格式化返回数据
        formatted_results = []
        for row in results:
            # 解析reason_dict JSON字段
            reason_dict = {}
            if row.get('reason_dict'):
                try:
                    # PostgreSQL的jsonb字段已经是dict类型，不需要json.loads
                    reason_dict = row['reason_dict'] if isinstance(row['reason_dict'], dict) else json.loads(row['reason_dict'])
                except (json.JSONDecodeError, TypeError):
                    reason_dict = {}
            
            # 根据locale获取对应语言的分析内容
            analysis_text = row['比赛预测及原因']  # 默认使用原始字段
            if reason_dict and locale in reason_dict:
                analysis_text = reason_dict[locale]
            elif reason_dict and 'zh' in reason_dict:
                # 如果没有对应语言，回退到中文
                analysis_text = reason_dict['zh']
            
            formatted_results.append({
                "id": f"{row['home_name']}-{row['away_name']}-{row['fixture_date']}",
                "league": row['league_name'],
                "home_team": row['home_name'],
                "away_team": row['away_name'],
                "odds": row['平均赔率'],
                "fixture_date": row['fixture_date'],
                "recommendation_index": float(row['推荐指数']) if row['推荐指数'] else 0.0,
                "analysis": analysis_text,
                "prediction_result": row['预测结果'],
                "reason_dict": reason_dict  # 也返回完整的reason_dict供前端使用
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