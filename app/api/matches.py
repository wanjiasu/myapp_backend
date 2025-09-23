from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from datetime import datetime, timedelta
from ..database import get_database, Database

router = APIRouter()

@router.get("/matches", response_model=List[Dict[str, Any]])
def get_matches(db: Database = Depends(get_database)):
    """
    获取所有比赛数据
    从ai_eval表中筛选：
    - 平均赔率不为空
    - 比赛时间：今天下午到明天24点
    返回格式：日期、时间、联赛、对阵、主胜、平、客胜、AI、操作
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
            比赛是否推荐
        FROM ai_eval 
        WHERE 平均赔率 IS NOT NULL 
        AND fixture_date >= %s
        AND fixture_date <= %s
        ORDER BY fixture_date ASC
        """
        
        results = db.fetch_all(query, (today_noon, tomorrow_end))
        
        if not results:
            return []
        
        # 格式化返回数据
        formatted_results = []
        for row in results:
            # 解析平均赔率JSON
            odds_data = row['平均赔率']
            home_odds = odds_data.get('home_avg', 0) if odds_data else 0
            draw_odds = odds_data.get('draw_avg', 0) if odds_data else 0
            away_odds = odds_data.get('away_avg', 0) if odds_data else 0
            
            # 格式化日期和时间
            fixture_datetime = row['fixture_date']
            match_date = fixture_datetime.strftime('%m-%d') if fixture_datetime else ''
            match_time = fixture_datetime.strftime('%H:%M') if fixture_datetime else ''
            
            # AI预测信息
            ai_prediction = ""
            if row['预测结果']:
                prediction_map = {
                    'home': '主胜',
                    'away': '客胜', 
                    'draw': '平局'
                }
                ai_prediction = prediction_map.get(row['预测结果'], row['预测结果'])
                
                # 如果有推荐指数，添加到AI预测中
                if row['推荐指数']:
                    confidence = float(row['推荐指数']) * 100
                    ai_prediction += f" {confidence:.0f}%"
            
            formatted_results.append({
                "id": f"{row['home_name']}-{row['away_name']}-{row['fixture_date']}",
                "date": match_date,
                "time": match_time,
                "league": row['league_name'],
                "home_team": row['home_name'],
                "away_team": row['away_name'],
                "home_odds": round(home_odds, 2) if home_odds else 0,
                "draw_odds": round(draw_odds, 2) if draw_odds else 0,
                "away_odds": round(away_odds, 2) if away_odds else 0,
                "ai_prediction": ai_prediction,
                "is_recommended": bool(row['比赛是否推荐']),
                "analysis": row['比赛预测及原因'],
                "fixture_date": row['fixture_date'],
                "recommendation_index": float(row['推荐指数']) if row['推荐指数'] else 0.0
            })
        
        return formatted_results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/matches/test")
def test_matches_connection(db: Database = Depends(get_database)):
    """测试matches API连接"""
    try:
        # 测试查询
        result = db.fetch_one("SELECT COUNT(*) as count FROM ai_eval WHERE 平均赔率 IS NOT NULL")
        return {"status": "success", "message": "Matches API connection successful", "total_matches": result['count'] if result else 0}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")