import unittest
from types import SimpleNamespace

try:
    from fastapi import HTTPException
    from app.api.admin import _assert_can_manage_target, _visible_user_condition
    from app.core.deps import can_view_root_admin_user, is_root_admin_user, is_super_admin_user
except ModuleNotFoundError:
    HTTPException = None
    _assert_can_manage_target = None
    _visible_user_condition = None
    can_view_root_admin_user = None
    is_root_admin_user = None
    is_super_admin_user = None



class AdminProtectionTest(unittest.TestCase):
    def setUp(self):
        if is_super_admin_user is None:
            self.skipTest("FastAPI dependencies are not installed in this environment")

    def test_wang_77_is_super_admin(self):
        user = SimpleNamespace(id=2, nickname="wang_77", phone=None)

        self.assertTrue(is_super_admin_user(user))
        self.assertFalse(is_root_admin_user(user))
        self.assertTrue(can_view_root_admin_user(user))

    def test_demo_is_root_admin(self):
        user = SimpleNamespace(id=1, nickname="Demo用户", phone="18610137321")

        self.assertTrue(is_root_admin_user(user))
        self.assertTrue(is_super_admin_user(user))

    def test_other_admin_cannot_manage_wang_77(self):
        admin = SimpleNamespace(id=1, nickname="普通管理员", phone="13900000000")
        target = SimpleNamespace(id=2, nickname="wang_77", phone=None)

        with self.assertRaises(HTTPException) as context:
            _assert_can_manage_target(admin, target)

        self.assertEqual(context.exception.status_code, 403)

    def test_super_admin_can_manage_self(self):
        admin = SimpleNamespace(id=2, nickname="wang_77", phone=None)

        _assert_can_manage_target(admin, admin)

    def test_wang_77_cannot_manage_demo(self):
        admin = SimpleNamespace(id=2, nickname="wang_77", phone=None)
        target = SimpleNamespace(id=1, nickname="Demo用户", phone="18610137321")

        with self.assertRaises(HTTPException) as context:
            _assert_can_manage_target(admin, target)

        self.assertEqual(context.exception.status_code, 403)

    def test_demo_can_manage_wang_77(self):
        admin = SimpleNamespace(id=1, nickname="Demo用户", phone="18610137321")
        target = SimpleNamespace(id=2, nickname="wang_77", phone=None)

        _assert_can_manage_target(admin, target)

    def test_only_wang_77_can_view_demo_in_user_list(self):
        wang = SimpleNamespace(id=2, nickname="wang_77", phone=None)
        regular_admin = SimpleNamespace(id=3, nickname="普通管理员", phone="13900000000")

        self.assertIsNone(_visible_user_condition(wang))
        self.assertIsNotNone(_visible_user_condition(regular_admin))


if __name__ == "__main__":
    unittest.main()
