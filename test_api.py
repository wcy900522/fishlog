#!/usr/bin/env python3
"""
FishLog API 测试脚本
测试完整的用户流程：注册 -> 登录 -> 查看钓点 -> 创建记录 -> 查看记录 -> 删除记录
"""

import asyncio
import httpx
from datetime import datetime

BASE_URL = "http://localhost:8000"

async def test_fishlog():
    async with httpx.AsyncClient() as client:
        print("🎣 FishLog API 测试开始...\n")

        # 1. 测试首页
        print("1️⃣  测试首页...")
        response = await client.get(f"{BASE_URL}/")
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ 首页加载成功")
        else:
            print(f"   ❌ 首页加载失败: {response.text}")

        # 2. 注册新用户
        print("\n2️⃣  测试用户注册...")
        register_data = {
            "nickname": "测试钓手",
            "phone": "13800138000",
            "password": "test123456"
        }
        response = await client.post(f"{BASE_URL}/api/auth/register", json=register_data)
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ 注册成功")
            user_data = response.json()
            print(f"   用户ID: {user_data.get('id')}, 昵称: {user_data.get('nickname')}")
        else:
            print(f"   ❌ 注册失败: {response.text}")

        # 3. 登录
        print("\n3️⃣  测试用户登录...")
        login_data = {
            "phone": "13800138000",
            "password": "test123456"
        }
        response = await client.post(f"{BASE_URL}/api/auth/login", json=login_data)
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            token_data = response.json()
            token = token_data.get('access_token')
            print("   ✅ 登录成功")
            print(f"   Token: {token[:20]}...")
        else:
            print(f"   ❌ 登录失败: {response.text}")
            return

        # 4. 获取钓点列表
        print("\n4️⃣  获取钓点列表...")
        response = await client.get(f"{BASE_URL}/api/spots")
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            spots = response.json()
            print(f"   ✅ 成功获取 {len(spots)} 个钓点")
            if spots:
                first_spot = spots[0]
                print(f"   第一个钓点: {first_spot.get('name')} ({first_spot.get('city')})")
                spot_id = first_spot.get('id')
        else:
            print(f"   ❌ 获取失败: {response.text}")
            return

        # 5. 获取钓点详情和天气
        print(f"\n5️⃣  获取钓点详情和天气...")
        response = await client.get(f"{BASE_URL}/api/spots/{spot_id}")
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ 获取钓点详情成功")
        else:
            print(f"   ❌ 获取失败: {response.text}")

        response = await client.get(f"{BASE_URL}/api/spots/{spot_id}/weather")
        print(f"   天气 - 状态码: {response.status_code}")
        if response.status_code == 200:
            weather = response.json()
            print(f"   ✅ 天气数据: {weather.get('temperature')}°C, 风速{weather.get('wind_speed')}m/s")
        else:
            print(f"   ❌ 获取失败: {response.text}")

        # 6. 创建钓鱼记录
        print("\n6️⃣  创建钓鱼记录...")
        log_data = {
            "spot_id": spot_id,
            "fishing_at": datetime.now().isoformat(),
            "duration": 120,
            "species": "鲤鱼",
            "bait": "玉米粒",
            "quantity": 3,
            "note": "天气不错，收获不错！"
        }
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.post(f"{BASE_URL}/api/logs", json=log_data, headers=headers)
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            log = response.json()
            log_id = log.get('id')
            print("   ✅ 记录创建成功")
            print(f"   记录ID: {log_id}, 鱼种: {log.get('species')}, 数量: {log.get('quantity')}")
        else:
            print(f"   ❌ 创建失败: {response.text}")
            return

        # 7. 获取我的记录
        print("\n7️⃣  获取我的记录...")
        response = await client.get(f"{BASE_URL}/api/logs", headers=headers)
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            logs = response.json()
            print(f"   ✅ 成功获取 {len(logs)} 条记录")
            if logs:
                print(f"   最新记录: {logs[0].get('species')}, 渔获 {logs[0].get('quantity')} 条")
        else:
            print(f"   ❌ 获取失败: {response.text}")

        # 8. 更新记录
        print("\n8️⃣  更新记录...")
        update_data = {
            "quantity": 5,
            "note": "更新后的备注"
        }
        response = await client.put(f"{BASE_URL}/api/logs/{log_id}", json=update_data, headers=headers)
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ 记录更新成功")
        else:
            print(f"   ❌ 更新失败: {response.text}")

        # 9. 获取记录详情
        print("\n9️⃣  获取记录详情...")
        response = await client.get(f"{BASE_URL}/api/logs/{log_id}", headers=headers)
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            log = response.json()
            print("   ✅ 成功获取记录详情")
            print(f"   渔获数量: {log.get('quantity')}, 温度: {log.get('temperature')}°C")
        else:
            print(f"   ❌ 获取失败: {response.text}")

        # 10. 删除记录
        print("\n🔟 删除记录...")
        response = await client.delete(f"{BASE_URL}/api/logs/{log_id}", headers=headers)
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ 记录删除成功")
        else:
            print(f"   ❌ 删除失败: {response.text}")

        print("\n" + "="*50)
        print("✨ 测试流程完成！")
        print("="*50)

if __name__ == "__main__":
    asyncio.run(test_fishlog())
