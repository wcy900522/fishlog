import unittest
from types import SimpleNamespace

from app.services.experience_service import ExperienceService
from app.services.level_service import LevelService


class LevelServiceTest(unittest.TestCase):
    def test_level_rules(self):
        cases = [
            (0, 1, "初学钓手", 100, 0),
            (100, 2, "钓鱼新人", 200, 0),
            (700, 4, "出钓达人", 800, 0),
            (51000, 10, "传奇钓圣", 0, 100),
        ]

        for xp, level, title, xp_to_next, progress in cases:
            with self.subTest(xp=xp):
                info = LevelService.get_level_info(xp)
                self.assertEqual(info.level, level)
                self.assertEqual(info.title, title)
                self.assertEqual(info.xp_to_next, xp_to_next)
                self.assertEqual(info.progress_percent, progress)

    def test_level_never_downgrades(self):
        user = SimpleNamespace(xp=50, level=4, title="出钓达人")

        info = LevelService.apply_level_to_user(user)

        self.assertEqual(info.level, 4)
        self.assertEqual(user.level, 4)
        self.assertEqual(user.title, "出钓达人")


class ExperienceServiceTest(unittest.TestCase):
    def test_catch_log_xp_cap(self):
        catch_log = SimpleNamespace(
            species="鲈鱼",
            quantity=3,
            temperature=20,
            pressure=1012,
            wind_speed=2,
            weather_snapshot={},
            image_count=2,
        )

        self.assertEqual(ExperienceService.calculate_catch_log_xp(catch_log), 40)

    def test_catch_log_xp_without_optional_fields(self):
        catch_log = SimpleNamespace(
            species=None,
            quantity=None,
            temperature=None,
            pressure=None,
            wind_speed=None,
            weather_snapshot={"error": "timeout"},
            image_count=0,
        )

        self.assertEqual(ExperienceService.calculate_catch_log_xp(catch_log), 20)

    def test_post_xp(self):
        self.assertEqual(ExperienceService.calculate_post_xp("技术分享"), 20)
        self.assertEqual(ExperienceService.calculate_post_xp("装备评测"), 20)
        self.assertEqual(ExperienceService.calculate_post_xp("钓点攻略"), 25)
        self.assertEqual(ExperienceService.calculate_post_xp("野钓"), 15)


if __name__ == "__main__":
    unittest.main()
