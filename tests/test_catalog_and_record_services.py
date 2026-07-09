import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch


try:
    import app.services.catalog_service as catalog_module
    import app.services.record_service as record_module
    from app.services.catalog_service import CatalogService
    from app.services.record_service import RecordService
    from app.repositories import CatchLogRepository
except ModuleNotFoundError:
    catalog_module = None
    record_module = None
    CatalogService = None
    RecordService = None
    CatchLogRepository = None


class CatalogServiceTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        if CatalogService is None:
            self.skipTest("SQLAlchemy dependencies are not installed in this environment")

    async def test_update_species_returns_none_when_missing(self):
        with patch.object(catalog_module.FishSpeciesRepository, "get_by_id", new=AsyncMock(return_value=None)), \
             patch.object(catalog_module.FishSpeciesRepository, "update", new=AsyncMock()) as update_mock:
            result = await CatalogService.update_species(object(), 404, SimpleNamespace())

        self.assertIsNone(result)
        update_mock.assert_not_called()

    async def test_update_species_delegates_to_repository(self):
        session = object()
        species = SimpleNamespace(id=1, name="鲈鱼")
        payload = SimpleNamespace(name="海鲈")
        updated = SimpleNamespace(id=1, name="海鲈")

        with patch.object(catalog_module.FishSpeciesRepository, "get_by_id", new=AsyncMock(return_value=species)), \
             patch.object(catalog_module.FishSpeciesRepository, "update", new=AsyncMock(return_value=updated)) as update_mock:
            result = await CatalogService.update_species(session, 1, payload)

        self.assertIs(result, updated)
        update_mock.assert_awaited_once_with(session, species, payload)

    async def test_equipment_permission_scope_uses_user_id_for_non_admin(self):
        session = object()
        user = SimpleNamespace(id=9, is_admin=False)
        equipment = SimpleNamespace(id=3, user_id=9)

        with patch.object(catalog_module, "is_admin_user", return_value=False), \
             patch.object(catalog_module.EquipmentRepository, "get_by_id", new=AsyncMock(return_value=equipment)) as get_mock:
            result = await CatalogService.get_equipment(session, user, 3)

        self.assertIs(result, equipment)
        get_mock.assert_awaited_once_with(session, 3, 9)

    async def test_delete_bait_returns_false_when_missing(self):
        with patch.object(catalog_module.BaitRepository, "get_by_id", new=AsyncMock(return_value=None)), \
             patch.object(catalog_module.BaitRepository, "delete", new=AsyncMock()) as delete_mock:
            result = await CatalogService.delete_bait(object(), 404)

        self.assertFalse(result)
        delete_mock.assert_not_called()


class RecordServiceTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        if RecordService is None:
            self.skipTest("SQLAlchemy dependencies are not installed in this environment")

    async def test_list_records_admin_uses_all_logs_with_filters(self):
        session = object()
        user = SimpleNamespace(id=7, is_admin=True)
        date_from = datetime(2026, 1, 1)
        date_to = datetime(2026, 1, 31)

        with patch.object(record_module, "is_admin_user", return_value=True), \
             patch.object(record_module.CatchLogRepository, "get_all_logs", new=AsyncMock(return_value=["row"])) as get_all:
            result = await RecordService.list_records(
                session,
                user,
                spot_id=2,
                species="鲈鱼",
                bait="米诺",
                date_from=date_from,
                date_to=date_to,
            )

        self.assertEqual(result, ["row"])
        get_all.assert_awaited_once_with(
            session,
            spot_id=2,
            species="鲈鱼",
            bait="米诺",
            date_from=date_from,
            date_to=date_to,
        )

    async def test_list_records_user_scopes_to_user_id(self):
        session = object()
        user = SimpleNamespace(id=7, is_admin=False)

        with patch.object(record_module, "is_admin_user", return_value=False), \
             patch.object(record_module.CatchLogRepository, "get_logs_by_user", new=AsyncMock(return_value=["mine"])) as get_user:
            result = await RecordService.list_records(session, user, species="白鲳")

        self.assertEqual(result, ["mine"])
        get_user.assert_awaited_once_with(
            session,
            7,
            spot_id=None,
            species="白鲳",
            bait=None,
            date_from=None,
            date_to=None,
        )

    async def test_create_record_raises_when_spot_missing(self):
        record_data = SimpleNamespace(spot_id=404)

        with patch.object(record_module.FishingSpotRepository, "get_spot_by_id", new=AsyncMock(return_value=None)), \
             patch.object(record_module.WeatherService, "get_current_weather", new=AsyncMock()) as weather_mock, \
             patch.object(record_module.CatchLogRepository, "create_log", new=AsyncMock()) as create_mock:
            with self.assertRaisesRegex(ValueError, "Spot not found"):
                await RecordService.create_record(object(), SimpleNamespace(id=1), record_data)

        weather_mock.assert_not_called()
        create_mock.assert_not_called()

    async def test_create_record_persists_weather_snapshot(self):
        session = object()
        user = SimpleNamespace(id=1)
        record_data = SimpleNamespace(spot_id=2)
        spot = SimpleNamespace(latitude=30.1, longitude=120.2)
        weather = {
            "temperature": 21.5,
            "pressure": 1011.2,
            "wind_speed": 3.4,
            "raw_json": {"source": "test"},
        }
        created = SimpleNamespace(id=9)

        with patch.object(record_module.FishingSpotRepository, "get_spot_by_id", new=AsyncMock(return_value=spot)), \
             patch.object(record_module.WeatherService, "get_current_weather", new=AsyncMock(return_value=weather)) as weather_mock, \
             patch.object(record_module.CatchLogRepository, "create_log", new=AsyncMock(return_value=created)) as create_mock, \
             patch.object(record_module.ExperienceService, "award_catch_log", new=AsyncMock()), \
             patch.object(record_module.BadgeService, "unlock_eligible_badges", new=AsyncMock()):
            result = await RecordService.create_record(session, user, record_data)

        self.assertIs(result, created)
        weather_mock.assert_awaited_once_with(30.1, 120.2)
        create_mock.assert_awaited_once_with(session, 1, record_data, weather)

    async def test_update_record_uses_payload_spot_for_weather(self):
        session = object()
        user = SimpleNamespace(id=1, is_admin=False)
        record = SimpleNamespace(id=8, spot_id=1)
        record_data = SimpleNamespace(spot_id=2)
        spot = SimpleNamespace(latitude=30.1, longitude=120.2)
        weather = {"temperature": 22}
        updated = SimpleNamespace(id=8, spot_id=2)

        with patch.object(record_module.RecordService, "get_record", new=AsyncMock(return_value=record)), \
             patch.object(record_module.FishingSpotRepository, "get_spot_by_id", new=AsyncMock(return_value=spot)) as spot_mock, \
             patch.object(record_module.WeatherService, "get_current_weather", new=AsyncMock(return_value=weather)) as weather_mock, \
             patch.object(record_module.CatchLogRepository, "update_log", new=AsyncMock(return_value=updated)) as update_mock:
            result = await RecordService.update_record(session, user, 8, record_data)

        self.assertIs(result, updated)
        spot_mock.assert_awaited_once_with(session, 2)
        weather_mock.assert_awaited_once_with(30.1, 120.2)
        update_mock.assert_awaited_once_with(session, record, record_data, weather)

    async def test_log_datetime_is_normalized_to_naive_utc(self):
        aware = datetime(2026, 7, 9, 10, 2, tzinfo=timezone.utc)

        normalized = CatchLogRepository._naive_utc(aware)

        self.assertEqual(normalized, datetime(2026, 7, 9, 10, 2))
        self.assertIsNone(normalized.tzinfo)


if __name__ == "__main__":
    unittest.main()
