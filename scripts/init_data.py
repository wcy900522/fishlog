import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from app.models import FishingSpot
from app.core.config import settings, Base

SAMPLE_SPOTS = [
    {"name": "东疆港", "province": "天津", "city": "天津", "latitude": 39.0061, "longitude": 117.9166, "water_type": "sea", "description": "天津港口区，海钓胜地"},
    {"name": "大神堂", "province": "天津", "city": "天津", "latitude": 39.1333, "longitude": 117.2500, "water_type": "river", "description": "海河支流，鲤鱼和草鱼丰富"},
    {"name": "中新生态城", "province": "天津", "city": "天津", "latitude": 39.0030, "longitude": 117.7486, "water_type": "lake", "description": "人工湖泊，环境优美"},
    {"name": "团泊湖", "province": "天津", "city": "天津", "latitude": 39.0667, "longitude": 117.0333, "water_type": "lake", "description": "天津最大淡水湖，各种鱼类资源丰富"},
    {"name": "于桥水库", "province": "天津", "city": "天津", "latitude": 39.0833, "longitude": 117.6500, "water_type": "reservoir", "description": "供水水库，环境保护良好"},
    {"name": "官厅水库", "province": "河北", "city": "张家口", "latitude": 40.4500, "longitude": 115.3500, "water_type": "reservoir", "description": "华北地区最大水库，产鱼量大"},
    {"name": "密云水库", "province": "北京", "city": "北京", "latitude": 40.6167, "longitude": 116.8500, "water_type": "reservoir", "description": "北京重要水源地，清水鱼多"},
    {"name": "怀柔水库", "province": "北京", "city": "北京", "latitude": 40.3833, "longitude": 116.6333, "water_type": "reservoir", "description": "环境优美，四季皆宜"},
    {"name": "雍和宫外河", "province": "北京", "city": "北京", "latitude": 39.9833, "longitude": 116.4167, "water_type": "river", "description": "京城内河，便利的钓点"},
    {"name": "北运河", "province": "北京", "city": "北京", "latitude": 40.0167, "longitude": 116.4000, "water_type": "river", "description": "生态治理后改善明显"},
    {"name": "大清河", "province": "河北", "city": "保定", "latitude": 38.8833, "longitude": 115.5000, "water_type": "river", "description": "华北重要河流，鱼种多样"},
    {"name": "白洋淀", "province": "河北", "city": "保定", "latitude": 38.7333, "longitude": 115.8333, "water_type": "lake", "description": "华北最大淡水湖，芦苇荡钓鱼"},
    {"name": "南水北调中线", "province": "河南", "city": "南阳", "latitude": 32.9500, "longitude": 112.6000, "water_type": "river", "description": "大型调水工程，水清鱼肥"},
    {"name": "丹江口水库", "province": "湖北", "city": "十堰", "latitude": 32.8333, "longitude": 110.7500, "water_type": "reservoir", "description": "南水北调水源地，环境一流"},
    {"name": "洱海", "province": "云南", "city": "大理", "latitude": 25.9667, "longitude": 100.1833, "water_type": "lake", "description": "高原湖泊，风景秀丽"},
    {"name": "滇池", "province": "云南", "city": "昆明", "latitude": 24.8833, "longitude": 102.7333, "water_type": "lake", "description": "云南最大湖泊，四季可钓"},
    {"name": "鄱阳湖", "province": "江西", "city": "九江", "latitude": 28.9667, "longitude": 116.1333, "water_type": "lake", "description": "长江流域最大淡水湖"},
    {"name": "千岛湖", "province": "浙江", "city": "杭州", "latitude": 29.4500, "longitude": 118.9667, "water_type": "lake", "description": "浙江知名水库，风景优美"},
    {"name": "西湖", "province": "浙江", "city": "杭州", "latitude": 30.2500, "longitude": 120.1333, "water_type": "lake", "description": "著名景区，市内休闲钓点"},
    {"name": "太湖", "province": "江苏", "city": "无锡", "latitude": 31.2500, "longitude": 120.6333, "water_type": "lake", "description": "中国第二大湖，鱼类资源丰富"},
    {"name": "滴水湖", "province": "上海", "city": "上海", "latitude": 30.9000, "longitude": 121.9250, "water_type": "lake", "description": "临港新城人工湖，水面开阔，适合城市休闲垂钓"},
    {"name": "淀山湖", "province": "上海", "city": "上海", "latitude": 31.1000, "longitude": 120.9500, "water_type": "lake", "description": "沪苏交界大型湖泊，鲫鱼、鲤鱼等淡水鱼资源较多"},
    {"name": "东平国家森林公园水域", "province": "上海", "city": "上海", "latitude": 31.6760, "longitude": 121.4790, "water_type": "lake", "description": "崇明岛生态水域，环境安静，适合周末休闲钓"},
    {"name": "海鸥岛", "province": "广东", "city": "广州", "latitude": 22.9750, "longitude": 113.4920, "water_type": "river", "description": "珠江口河网区域，常见罗非、鲫鱼和鲤鱼"},
    {"name": "万绿湖", "province": "广东", "city": "河源", "latitude": 23.7700, "longitude": 114.5700, "water_type": "reservoir", "description": "新丰江水库，水质清澈，湖库钓点众多"},
    {"name": "大梅沙海滨", "province": "广东", "city": "深圳", "latitude": 22.5950, "longitude": 114.3060, "water_type": "sea", "description": "深圳东部海滨区域，适合岸边海钓体验"},
    {"name": "厦门五缘湾", "province": "福建", "city": "厦门", "latitude": 24.5290, "longitude": 118.1780, "water_type": "sea", "description": "厦门岛内海湾水域，交通便利，适合轻量海钓"},
    {"name": "闽江口", "province": "福建", "city": "福州", "latitude": 26.0500, "longitude": 119.6500, "water_type": "river", "description": "江海交汇区域，鱼种丰富，潮汐影响明显"},
    {"name": "青岛栈桥海域", "province": "山东", "city": "青岛", "latitude": 36.0610, "longitude": 120.3190, "water_type": "sea", "description": "市区经典海钓点，适合岸钓和短时体验"},
    {"name": "微山湖", "province": "山东", "city": "济宁", "latitude": 34.7500, "longitude": 117.1500, "water_type": "lake", "description": "鲁南大型淡水湖，芦苇水域多，适合传统钓和台钓"},
    {"name": "三岔湖", "province": "四川", "city": "成都", "latitude": 30.2780, "longitude": 104.2760, "water_type": "reservoir", "description": "成都近郊大型水库，常见鲫鱼、鲤鱼和翘嘴"},
    {"name": "升钟湖", "province": "四川", "city": "南充", "latitude": 31.5600, "longitude": 105.8000, "water_type": "reservoir", "description": "川东北湖库钓场，水域宽广，适合长时间守钓"},
    {"name": "嘉陵江北碚段", "province": "重庆", "city": "重庆", "latitude": 29.8250, "longitude": 106.4330, "water_type": "river", "description": "嘉陵江城市河段，水流变化明显，适合江钓"},
    {"name": "洞庭湖", "province": "湖南", "city": "岳阳", "latitude": 29.3100, "longitude": 112.9500, "water_type": "lake", "description": "长江中游大型湖泊，鱼类资源丰富，湖区钓点多"},
    {"name": "巢湖", "province": "安徽", "city": "合肥", "latitude": 31.6000, "longitude": 117.5000, "water_type": "lake", "description": "安徽大型淡水湖，岸线长，适合近郊休闲垂钓"},
    {"name": "万泉河", "province": "海南", "city": "琼海", "latitude": 19.2350, "longitude": 110.4700, "water_type": "river", "description": "海南东部河流，水质较好，适合溪流和河道垂钓"},
]

async def init_db():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        created_count = 0
        skipped_count = 0

        for spot_data in SAMPLE_SPOTS:
            result = await session.execute(
                select(FishingSpot).where(
                    FishingSpot.name == spot_data["name"],
                    FishingSpot.province == spot_data["province"],
                    FishingSpot.city == spot_data["city"],
                )
            )
            if result.scalars().first():
                skipped_count += 1
                continue

            spot = FishingSpot(**spot_data)
            session.add(spot)
            created_count += 1

        await session.commit()
        print(
            f"Initialized {created_count} sample fishing spots "
            f"({skipped_count} already existed, {len(SAMPLE_SPOTS)} total)"
        )

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(init_db())
