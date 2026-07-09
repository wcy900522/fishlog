import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

try:
    from fastapi import HTTPException
    from app.api.users import update_my_profile
    from app.schemas import UserProfileUpdate
except ModuleNotFoundError:
    HTTPException = None
    update_my_profile = None
    UserProfileUpdate = None


class UserProfileApiTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        if update_my_profile is None:
            self.skipTest("FastAPI dependencies are not installed in this environment")

    async def test_update_nickname_saves_valid_name(self):
        user = SimpleNamespace(id=8, nickname="旧昵称", phone=None)
        session = SimpleNamespace(commit=AsyncMock(), refresh=AsyncMock())

        result = await update_my_profile(UserProfileUpdate(nickname=" 新钓友 "), user, session)

        self.assertIs(result, user)
        self.assertEqual(user.nickname, "新钓友")
        session.commit.assert_awaited_once()
        session.refresh.assert_awaited_once_with(user)

    async def test_update_nickname_rejects_sensitive_words(self):
        user = SimpleNamespace(id=8, nickname="旧昵称", phone=None)
        session = SimpleNamespace(commit=AsyncMock(), refresh=AsyncMock())

        with self.assertRaises(HTTPException) as context:
            await update_my_profile(UserProfileUpdate(nickname="f.u.c.k"), user, session)

        self.assertEqual(context.exception.status_code, 400)
        session.commit.assert_not_awaited()

    async def test_update_nickname_rejects_reserved_admin_name(self):
        user = SimpleNamespace(id=8, nickname="普通钓友", phone=None)
        session = SimpleNamespace(commit=AsyncMock(), refresh=AsyncMock())

        with self.assertRaises(HTTPException) as context:
            await update_my_profile(UserProfileUpdate(nickname="wang_77"), user, session)

        self.assertEqual(context.exception.status_code, 400)
        session.commit.assert_not_awaited()

    async def test_protected_admin_cannot_change_nickname(self):
        user = SimpleNamespace(id=2, nickname="wang_77", phone=None)
        session = SimpleNamespace(commit=AsyncMock(), refresh=AsyncMock())

        with self.assertRaises(HTTPException) as context:
            await update_my_profile(UserProfileUpdate(nickname="日常管理员"), user, session)

        self.assertEqual(context.exception.status_code, 400)
        session.commit.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
