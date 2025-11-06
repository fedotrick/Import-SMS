from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

logger = logging.getLogger(__name__)


class ParserError(Exception):
    """Base exception for parser errors."""


class InvalidReportFormatError(ParserError):
    """Raised when the shift report format is invalid."""


@dataclass
class PlavkaRecord:
    id_plavka: int
    uchetny_nomer: str
    plavka_data: datetime
    nomer_plavki: str
    nomer_klastera: Optional[str]
    starshiy_smeny: str
    perviy_uchastnik: Optional[str]
    vtoroy_uchastnik: Optional[str]
    tretiy_uchastnik: Optional[str]
    chetvertyy_uchastnik: Optional[str]
    naimenovanie_otlivki: str
    tip_eksperementa: Optional[str]
    sektor_a_opoki: Optional[str]
    sektor_b_opoki: Optional[str]
    sektor_c_opoki: Optional[str]
    sektor_d_opoki: Optional[str]
    plavka_vremya_progreva_kovsha_a: Optional[str]
    plavka_vremya_peremesheniya_a: Optional[str]
    plavka_vremya_zalivki_a: Optional[str]
    plavka_temperatura_zalivki_a: Optional[float]
    plavka_vremya_progreva_kovsha_b: Optional[str]
    plavka_vremya_peremesheniya_b: Optional[str]
    plavka_vremya_zalivki_b: Optional[str]
    plavka_temperatura_zalivki_b: Optional[float]
    plavka_vremya_progreva_kovsha_c: Optional[str]
    plavka_vremya_peremesheniya_c: Optional[str]
    plavka_vremya_zalivki_c: Optional[str]
    plavka_temperatura_zalivki_c: Optional[float]
    plavka_vremya_progreva_kovsha_d: Optional[str]
    plavka_vremya_peremesheniya_d: Optional[str]
    plavka_vremya_zalivki_d: Optional[str]
    plavka_temperatura_zalivki_d: Optional[float]
    kommentariy: Optional[str]
    plavka_vremya_zalivki: Optional[str]

    def to_excel_row(self, row_id: int) -> List:
        return [
            self.id_plavka,
            self.uchetny_nomer,
            self.plavka_data,
            self.nomer_plavki,
            self.nomer_klastera,
            self.starshiy_smeny,
            self.perviy_uchastnik,
            self.vtoroy_uchastnik,
            self.tretiy_uchastnik,
            self.chetvertyy_uchastnik,
            self.naimenovanie_otlivki,
            self.tip_eksperementa,
            self.sektor_a_opoki,
            self.sektor_b_opoki,
            self.sektor_c_opoki,
            self.sektor_d_opoki,
            self.plavka_vremya_progreva_kovsha_a,
            self.plavka_vremya_peremesheniya_a,
            self.plavka_vremya_zalivki_a,
            self.plavka_temperatura_zalivki_a,
            self.plavka_vremya_progreva_kovsha_b,
            self.plavka_vremya_peremesheniya_b,
            self.plavka_vremya_zalivki_b,
            self.plavka_temperatura_zalivki_b,
            self.plavka_vremya_progreva_kovsha_c,
            self.plavka_vremya_peremesheniya_c,
            self.plavka_vremya_zalivki_c,
            self.plavka_temperatura_zalivki_c,
            self.plavka_vremya_progreva_kovsha_d,
            self.plavka_vremya_peremesheniya_d,
            self.plavka_vremya_zalivki_d,
            self.plavka_temperatura_zalivki_d,
            self.kommentariy,
            self.plavka_vremya_zalivki,
            row_id,
        ]


@dataclass
class ShiftReport:
    header: dict
    plavki: List[PlavkaRecord]
    total_plavok: int

    def validate(self) -> None:
        if len(self.plavki) != self.total_plavok:
            raise InvalidReportFormatError(
                f"Несоответствие количества плавок: ожидалось {self.total_plavok}, найдено {len(self.plavki)}"
            )
        
        required_header_fields = ["Дата", "Смена", "Старший_смены"]
        for field in required_header_fields:
            if field not in self.header or not self.header[field]:
                raise InvalidReportFormatError(f"Отсутствует обязательное поле заголовка: {field}")


def parse_shift_report(text: str) -> ShiftReport:
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    if not lines:
        raise InvalidReportFormatError("Пустой отчёт")
    
    header = {}
    plavki = []
    current_plavka_data = {}
    in_plavka_section = False
    total_plavok = 0
    
    for line in lines:
        if line.startswith("===") or line.startswith("---"):
            continue
        
        if line.upper().startswith("ОТЧЁТ О СМЕНЕ") or line.upper().startswith("SHIFT REPORT"):
            continue
        
        if ":" in line and not in_plavka_section:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            header[key] = value
            
            if key.lower() == "всего плавок":
                try:
                    total_plavok = int(value)
                except ValueError:
                    raise InvalidReportFormatError(f"Некорректное значение 'Всего плавок': {value}")
                in_plavka_section = True
                continue
        
        if in_plavka_section and line.startswith("Плавка"):
            if current_plavka_data:
                plavka = _create_plavka_record(current_plavka_data, header)
                plavki.append(plavka)
                current_plavka_data = {}
        
        if in_plavka_section and ":" in line:
            key, value = line.split(":", 1)
            current_plavka_data[key.strip()] = value.strip()
    
    if current_plavka_data:
        plavka = _create_plavka_record(current_plavka_data, header)
        plavki.append(plavka)
    
    report = ShiftReport(header=header, plavki=plavki, total_plavok=total_plavok)
    report.validate()
    
    return report


def _create_plavka_record(data: dict, header: dict) -> PlavkaRecord:
    try:
        date_str = header.get("Дата", "")
        plavka_date = datetime.strptime(date_str, "%d.%m.%Y") if date_str else datetime.now()
    except ValueError:
        plavka_date = datetime.now()
    
    nomer_plavki = data.get("Плавка №", data.get("Номер", ""))
    uchetny_nomer = data.get("Учетный номер", f"{plavka_date.day}-{nomer_plavki}/{plavka_date.year % 100}")
    
    id_plavka = int(f"{plavka_date.year}{plavka_date.month:02d}{int(nomer_plavki) if nomer_plavki.isdigit() else 0:03d}")
    
    return PlavkaRecord(
        id_plavka=id_plavka,
        uchetny_nomer=uchetny_nomer,
        plavka_data=plavka_date,
        nomer_plavki=nomer_plavki,
        nomer_klastera=data.get("Номер кластера"),
        starshiy_smeny=header.get("Старший_смены", data.get("Старший смены", "")),
        perviy_uchastnik=data.get("Участник 1"),
        vtoroy_uchastnik=data.get("Участник 2"),
        tretiy_uchastnik=data.get("Участник 3"),
        chetvertyy_uchastnik=data.get("Участник 4"),
        naimenovanie_otlivki=data.get("Наименование отливки", ""),
        tip_eksperementa=data.get("Тип эксперимента"),
        sektor_a_opoki=data.get("Сектор A"),
        sektor_b_opoki=data.get("Сектор B"),
        sektor_c_opoki=data.get("Сектор C"),
        sektor_d_opoki=data.get("Сектор D"),
        plavka_vremya_progreva_kovsha_a=data.get("Прогрев ковша A"),
        plavka_vremya_peremesheniya_a=data.get("Перемещение A"),
        plavka_vremya_zalivki_a=data.get("Заливка A"),
        plavka_temperatura_zalivki_a=_parse_float(data.get("Температура A")),
        plavka_vremya_progreva_kovsha_b=data.get("Прогрев ковша B"),
        plavka_vremya_peremesheniya_b=data.get("Перемещение B"),
        plavka_vremya_zalivki_b=data.get("Заливка B"),
        plavka_temperatura_zalivki_b=_parse_float(data.get("Температура B")),
        plavka_vremya_progreva_kovsha_c=data.get("Прогрев ковша C"),
        plavka_vremya_peremesheniya_c=data.get("Перемещение C"),
        plavka_vremya_zalivki_c=data.get("Заливка C"),
        plavka_temperatura_zalivki_c=_parse_float(data.get("Температура C")),
        plavka_vremya_progreva_kovsha_d=data.get("Прогрев ковша D"),
        plavka_vremya_peremesheniya_d=data.get("Перемещение D"),
        plavka_vremya_zalivki_d=data.get("Заливка D"),
        plavka_temperatura_zalivki_d=_parse_float(data.get("Температура D")),
        kommentariy=data.get("Комментарий"),
        plavka_vremya_zalivki=data.get("Время заливки"),
    )


def _parse_float(value: Optional[str]) -> Optional[float]:
    if not value:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None
