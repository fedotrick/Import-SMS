"""Unit tests for message parser service."""

from __future__ import annotations

import pytest

from src.bot.services.message_parser import (
    MessageParser,
    ParsedShiftReport,
    ShiftHeader,
    MeltDetail,
    MeltStatus,
    MessageParseError,
)


class TestMessageParser:
    """Test cases for MessageParser."""

    @pytest.fixture
    def parser(self) -> MessageParser:
        """Create parser instance."""
        return MessageParser()

    def test_parse_complete_message(self, parser: MessageParser, sample_shift_message: str):
        """Test parsing a complete shift message."""
        result = parser.parse_message(sample_shift_message)
        
        assert isinstance(result, ParsedShiftReport)
        assert result.header.shift_number == "1"
        assert result.header.date == "15.11.2024"
        assert result.header.time_range == "08:00-20:00"
        assert result.header.duration == "12 ч"
        assert result.header.supervisor == "Иванов И.И."
        assert result.header.total_melts == 5
        assert len(result.header.participants) == 2
        assert "Петров П.П." in result.header.participants
        assert "Сидоров С.С." in result.header.participants
        
        assert len(result.melts) == 3
        
        # Check first melt
        first_melt = result.melts[0]
        assert first_melt.status == MeltStatus.COMPLETED
        assert first_melt.number == 1
        assert first_melt.route_card == "001"
        assert first_melt.cluster == "1"
        assert first_melt.casting == "123"
        assert first_melt.gating_system == "456"
        assert first_melt.molds == "789"
        assert first_melt.temperature == 1250.0
        assert first_melt.pour_time == "14:30"
        assert first_melt.created == "Создана"
        
        # Check second melt (in progress)
        second_melt = result.melts[1]
        assert second_melt.status == MeltStatus.IN_PROGRESS
        assert second_melt.number == 2

    def test_parse_minimal_message(self, parser: MessageParser):
        """Test parsing a minimal shift message."""
        message = """Смена: 2
Дата: 16.11.2024
Старший: Тестовый Т.Т.

ДЕТАЛИ ПЛАВОК:
✅ 1 РК-100"""
        
        result = parser.parse_message(message)
        
        assert result.header.shift_number == "2"
        assert result.header.date == "16.11.2024"
        assert result.header.supervisor == "Тестовый Т.Т."
        assert result.header.total_melts is None
        
        assert len(result.melts) == 1
        melt = result.melts[0]
        assert melt.status == MeltStatus.COMPLETED
        assert melt.number == 1
        assert melt.route_card == "100"

    def test_parse_message_with_alternative_formats(self, parser: MessageParser):
        """Test parsing with alternative field formats."""
        message = """Смена: III
Дата: 01/12/2024
Время: 09-15
Длительность: 6 ч
Старший: Админ А.А.
Всего плавок: 2
Участники: Оператор1, Оператор2

ДЕТАЛИ ПЛАВОК:
✅ 1 РК-АБВ кластер-А t=1250,5°C 09:15 Готова
🔄 2 РК-ГДЕ t=1260,0°C 10:30 В работе"""
        
        result = parser.parse_message(message)
        
        assert result.header.shift_number == "III"
        assert result.header.duration == "6 ч"
        assert result.header.total_melts == 2
        assert len(result.header.participants) == 2
        
        assert len(result.melts) == 2
        
        # Check temperature parsing with comma
        first_melt = result.melts[0]
        assert first_melt.temperature == 1250.5
        
        second_melt = result.melts[1]
        assert second_melt.temperature == 1260.0

    def test_parse_message_with_missing_fields(self, parser: MessageParser):
        """Test parsing message with missing optional fields."""
        message = """Смена: 1
Дата: 15.11.2024

ДЕТАЛИ ПЛАВОК:
✅ 1
🔄 2"""
        
        result = parser.parse_message(message)
        
        assert result.header.shift_number == "1"
        assert result.header.date == "15.11.2024"
        assert result.header.supervisor is None
        assert result.header.total_melts is None
        
        assert len(result.melts) == 2
        assert result.melts[0].number == 1
        assert result.melts[1].number == 2

    def test_parse_empty_message(self, parser: MessageParser):
        """Test parsing empty message."""
        with pytest.raises(MessageParseError):
            parser.parse_message("")

    def test_parse_message_only_header(self, parser: MessageParser):
        """Test parsing message with only header."""
        message = """Смена: 1
Дата: 15.11.2024
Старший: Иванов И.И."""
        
        result = parser.parse_message(message)
        
        assert result.header.shift_number == "1"
        assert len(result.melts) == 0

    def test_parse_message_with_extra_whitespace(self, parser: MessageParser):
        """Test parsing message with irregular whitespace."""
        message = """   Смена:    1   
   Дата:   15.11.2024   
   Старший:   Иванов   И.И.   

   ДЕТАЛИ   ПЛАВОК:   
   ✅   1   РК-001   кластер-1   t=1250°C   14:30   Создана   """
        
        result = parser.parse_message(message)
        
        assert result.header.shift_number == "1"
        assert result.header.supervisor == "Иванов   И.И."
        assert len(result.melts) == 1

    def test_validate_perfect_report(self, parser: MessageParser, sample_shift_message: str):
        """Test validation of a perfect report."""
        result = parser.parse_message(sample_shift_message)
        issues = parser.validate_report(result)
        
        # Should have one issue: total melts mismatch (5 declared, 3 found)
        assert len(issues) == 1
        assert "Total melts count mismatch" in issues[0]

    def test_validate_report_with_missing_fields(self, parser: MessageParser):
        """Test validation of report with missing required fields."""
        result = ParsedShiftReport(
            header=ShiftHeader(),
            melts=[]
        )
        
        issues = parser.validate_report(result)
        
        assert len(issues) >= 4  # shift, date, supervisor, melts
        assert "Missing shift number" in issues
        assert "Missing shift date" in issues
        assert "Missing supervisor" in issues
        assert "No melts found" in issues

    def test_validate_non_sequential_melts(self, parser: MessageParser):
        """Test validation with non-sequential melt numbers."""
        result = ParsedShiftReport(
            header=ShiftHeader(
                shift_number="1",
                date="15.11.2024",
                supervisor="Иванов И.И.",
                total_melts=2
            ),
            melts=[
                MeltDetail(status=MeltStatus.COMPLETED, number=1),
                MeltDetail(status=MeltStatus.IN_PROGRESS, number=3),  # Missing 2
            ]
        )
        
        issues = parser.validate_report(result)
        
        assert any("not sequential" in issue for issue in issues)

    def test_parse_melt_with_various_status_emojis(self, parser: MessageParser):
        """Test parsing melts with different status emojis."""
        messages = [
            "✅ 1 РК-001",
            "🔄 2 РК-002",
            "❓ 3 РК-003",  # Unknown status
        ]
        
        for msg in messages:
            full_msg = f"Смена: 1\nДата: 15.11.2024\n\nДЕТАЛИ ПЛАВОК:\n{msg}"
            result = parser.parse_message(full_msg)
            
            assert len(result.melts) == 1
            if "✅" in msg:
                assert result.melts[0].status == MeltStatus.COMPLETED
            elif "🔄" in msg:
                assert result.melts[0].status == MeltStatus.IN_PROGRESS
            else:
                assert result.melts[0].status == MeltStatus.UNKNOWN

    def test_parse_temperature_with_various_formats(self, parser: MessageParser):
        """Test parsing temperature in different formats."""
        test_cases = [
            ("t=1250°C", 1250.0),
            ("t=1250,5°C", 1250.5),
            ("t=1250.0", 1250.0),
            ("t=1250", 1250.0),
        ]
        
        for temp_str, expected_temp in test_cases:
            message = f"""Смена: 1
Дата: 15.11.2024

ДЕТАЛИ ПЛАВОК:
✅ 1 РК-001 {temp_str}"""
            
            result = parser.parse_message(message)
            assert len(result.melts) == 1
            assert result.melts[0].temperature == expected_temp

    def test_parse_message_with_cyrillic_directory_path(self, parser: MessageParser):
        """Test that parser handles Cyrillic text correctly."""
        message = """Смена: 1
Дата: 15.11.2024
Старший: Иванов Иван Иванович

ДЕТАЛИ ПЛАВОК:
✅ 1 РК-001 кластер-АБВ отливка-ГДЕ"""
        
        result = parser.parse_message(message)
        
        assert result.header.supervisor == "Иванов Иван Иванович"
        assert result.melts[0].cluster == "АБВ"
        assert result.melts[0].casting == "ГДЕ"