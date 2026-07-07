from __future__ import annotations

import re
import unicodedata
from pathlib import Path


NICKNAME_INVALID_MESSAGE = "昵称包含违规内容，请重新设置。"


class NicknameValidationError(ValueError):
    pass


class NicknameValidator:
    _loaded = False
    _bad_words: set[str] = set()
    _short_exact_words: set[str] = set()
    _family_exact_words: set[str] = set()
    _family_contains_words: set[str] = set()

    # Single-character kinship words are too broad for substring matching.
    _family_single_exact_source = {"妈", "爸", "爷", "奶"}
    _word_file = Path(__file__).resolve().parents[1] / "data" / "bad_words.txt"
    _ascii_short_pattern = re.compile(r"^[a-z0-9]{1,2}$")

    @classmethod
    def load(cls, force: bool = False) -> None:
        if cls._loaded and not force:
            return

        bad_words: set[str] = set()
        short_exact_words: set[str] = set()
        family_exact_words: set[str] = set()
        family_contains_words: set[str] = set()

        for raw_line in cls._word_file.read_text(encoding="utf-8").splitlines():
            raw_word = raw_line.strip()
            if not raw_word or raw_word.startswith("#"):
                continue

            normalized_word = cls._normalize(raw_word, collapse_repeats=False)
            collapsed_word = cls._collapse_repeats(normalized_word)
            if not normalized_word:
                continue

            if raw_word in cls._family_single_exact_source:
                family_exact_words.add(normalized_word)
                family_exact_words.add(collapsed_word)
                continue

            if cls._is_family_word(raw_word):
                family_contains_words.add(normalized_word)
                if collapsed_word not in cls._family_single_exact_source:
                    family_contains_words.add(collapsed_word)
                continue

            if cls._ascii_short_pattern.fullmatch(normalized_word):
                short_exact_words.add(normalized_word)
                short_exact_words.add(collapsed_word)
                continue

            bad_words.add(normalized_word)
            bad_words.add(collapsed_word)

        cls._bad_words = bad_words
        cls._short_exact_words = short_exact_words
        cls._family_exact_words = family_exact_words
        cls._family_contains_words = family_contains_words
        cls._loaded = True

    @classmethod
    def is_valid(cls, nickname: str) -> bool:
        cls.load()
        compact = cls._normalize(nickname, collapse_repeats=False)
        collapsed = cls._collapse_repeats(compact)
        if not compact:
            return False

        return not cls._contains_bad_word(compact, collapsed)

    @classmethod
    def validate(cls, nickname: str) -> None:
        if not cls.is_valid(nickname):
            raise NicknameValidationError(NICKNAME_INVALID_MESSAGE)

    @staticmethod
    def fallback_nickname(user_id: int | None = None) -> str:
        if user_id is None:
            return "钓友"
        return f"钓友{user_id}"

    @classmethod
    def _contains_bad_word(cls, compact: str, collapsed: str) -> bool:
        variants = {compact, collapsed}

        if variants & cls._family_exact_words:
            return True

        for word in cls._short_exact_words:
            if word in variants:
                return True

        for word in cls._family_contains_words:
            if any(word and word in value for value in variants):
                return True

        for word in cls._bad_words:
            if any(word and word in value for value in variants):
                return True

        return False

    @classmethod
    def _normalize(cls, value: str, collapse_repeats: bool = True) -> str:
        normalized = unicodedata.normalize("NFKC", value or "").casefold()
        stripped = "".join(
            char for char in normalized
            if cls._is_allowed_content_char(char)
        )
        if collapse_repeats:
            return cls._collapse_repeats(stripped)
        return stripped

    @staticmethod
    def _collapse_repeats(value: str) -> str:
        if not value:
            return value

        chars = [value[0]]
        for char in value[1:]:
            if char != chars[-1]:
                chars.append(char)
        return "".join(chars)

    @staticmethod
    def _is_allowed_content_char(char: str) -> bool:
        category = unicodedata.category(char)
        return category[0] in {"L", "N"}

    @staticmethod
    def _is_family_word(raw_word: str) -> bool:
        return raw_word in {
            "妈妈", "老妈", "妈咪",
            "爸爸", "老爸",
            "爷爷", "奶奶",
            "姥姥", "外婆", "外公", "祖宗",
            "儿子", "孙子", "孙女", "女儿",
            "父亲", "母亲", "老婆", "老公", "媳妇", "岳父", "岳母",
            "麻麻", "粑粑",
        }
