#!/usr/bin/env python3
"""Test script for shift report parser."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.bot.services.parser import parse_shift_report, InvalidReportFormatError


def test_valid_report():
    print("Test 1: Valid shift report")
    report_text = """
===================================
ОТЧЁТ О СМЕНЕ
===================================

Дата: 06.11.2024
Смена: Дневная
Старший_смены: Иванов Иван Иванович
Всего плавок: 2

-----------------------------------

Плавка № 1
Номер: 11-1
Учетный номер: 11-1/24
Наименование отливки: Держатель ригеля
Участник 1: Петров Петр Петрович
Температура A: 1520.5

Плавка № 2
Номер: 11-2
Учетный номер: 11-2/24
Наименование отливки: Адаптер
Участник 1: Петров Петр Петрович
Температура A: 1535.0
    """
    
    try:
        report = parse_shift_report(report_text)
        print(f"✓ Parsed {len(report.plavki)} plavok")
        print(f"  Header: {report.header}")
        print(f"  Total plavok: {report.total_plavok}")
        for i, plavka in enumerate(report.plavki, 1):
            print(f"  Plavka {i}: {plavka.nomer_plavki} - {plavka.naimenovanie_otlivki}")
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


def test_mismatch_count():
    print("\nTest 2: Mismatch between declared and actual plavok count")
    report_text = """
Дата: 06.11.2024
Старший_смены: Иванов Иван Иванович
Всего плавок: 5

Плавка № 1
Номер: 11-1
Наименование отливки: Держатель ригеля
    """
    
    try:
        report = parse_shift_report(report_text)
        report.validate()
        print(f"✗ Should have failed validation")
        return False
    except InvalidReportFormatError as e:
        print(f"✓ Correctly caught error: {e}")
        return True
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


def test_missing_header():
    print("\nTest 3: Missing required header field")
    report_text = """
Дата: 06.11.2024
Всего плавок: 1

Плавка № 1
Номер: 11-1
Наименование отливки: Держатель ригеля
    """
    
    try:
        report = parse_shift_report(report_text)
        report.validate()
        print(f"✗ Should have failed validation")
        return False
    except InvalidReportFormatError as e:
        print(f"✓ Correctly caught error: {e}")
        return True
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


def test_empty_report():
    print("\nTest 4: Empty report")
    report_text = ""
    
    try:
        report = parse_shift_report(report_text)
        print(f"✗ Should have failed")
        return False
    except InvalidReportFormatError as e:
        print(f"✓ Correctly caught error: {e}")
        return True
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


def main():
    print("=" * 60)
    print("SHIFT REPORT PARSER TEST SUITE")
    print("=" * 60)
    
    tests = [
        test_valid_report,
        test_mismatch_count,
        test_missing_header,
        test_empty_report,
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 60)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)
    
    return all(results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
