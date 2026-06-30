import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
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
]

async def init_db():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        for spot_data in SAMPLE_SPOTS:
            spot = FishingSpot(**spot_data)
            session.add(spot)

        await session.commit()
        print(f"Initialized {len(SAMPLE_SPOTS)} sample fishing spots")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(init_db())
