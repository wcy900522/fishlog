import unittest

from app.core.nickname_validator import (
    NICKNAME_INVALID_MESSAGE,
    NicknameValidationError,
    NicknameValidator,
)


class NicknameValidatorTest(unittest.TestCase):
    def test_valid_nicknames(self):
        valid_names = [
            "钓鱼达人",
            "夜钓大师",
            "FishLog",
            "CloudOps",
            "Jack",
            "Tom",
            "Sky",
            "奶茶大师",
            "爷青回",
        ]

        for nickname in valid_names:
            with self.subTest(nickname=nickname):
                self.assertTrue(NicknameValidator.is_valid(nickname))

    def test_invalid_nicknames(self):
        invalid_names = [
            "傻逼",
            "SB",
            "sb",
            "S B",
            "FUCK",
            "Fuck",
            "妈",
            "妈妈",
            "爸爸",
            "爷爷",
            "奶奶",
            "儿子",
            "cnm",
            "nmsl",
            "狗东西",
            "去死",
            "shabi",
            "sha bi",
            "f.u.c.k",
            "ｍａ",
            "ＭＡ",
            "妈妈做的饭",
            "爸爸带我去钓鱼",
            "妈🐶",
            "爸 爸",
            "ＳＢ",
            "ＦＵＣＫ",
            "s___b",
        ]

        for nickname in invalid_names:
            with self.subTest(nickname=nickname):
                self.assertFalse(NicknameValidator.is_valid(nickname))

    def test_validate_raises_generic_message(self):
        with self.assertRaises(NicknameValidationError) as context:
            NicknameValidator.validate("f.u.c.k")

        self.assertEqual(str(context.exception), NICKNAME_INVALID_MESSAGE)


if __name__ == "__main__":
    unittest.main()
