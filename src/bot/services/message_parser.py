"""Service for parsing shift report messages."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum

import logging

logger = logging.getLogger(__name__)


class MeltStatus(Enum):
    """Status of a melt."""
    COMPLETED = "✅"
    IN_PROGRESS = "🔄"
    UNKNOWN = "❓"


@dataclass
class ShiftHeader:
    """Parsed shift header information."""
    shift_number: Optional[str] = None
    date: Optional[str] = None
    time_range: Optional[str] = None
    duration: Optional[str] = None
    supervisor: Optional[str] = None
    total_melts: Optional[int] = None
    participants: List[str] = None

    def __post_init__(self):
        if self.participants is None:
            self.participants = []


@dataclass
class MeltDetail:
    """Parsed melt detail information."""
    status: MeltStatus
    number: int
    route_card: Optional[str] = None
    cluster: Optional[str] = None
    casting: Optional[str] = None
    gating_system: Optional[str] = None
    molds: Optional[str] = None
    temperature: Optional[float] = None
    pour_time: Optional[str] = None
    created: Optional[str] = None


@dataclass
class ParsedShiftReport:
    """Complete parsed shift report."""
    header: ShiftHeader
    melts: List[MeltDetail]

    def __post_init__(self):
        if self.melts is None:
            self.melts = []


class MessageParseError(Exception):
    """Raised when message parsing fails."""


class MessageParser:
    """Parser for shift report messages."""

    # Header patterns
    HEADER_PATTERNS = {
        'shift': re.compile(r'Смена\s*[:\s]\s*(\d+|[IVX]+)', re.IGNORECASE),
        'date': re.compile(r'Дата\s*[:\s]\s*([0-9]{1,2}\.[0-9]{1,2}\.[0-9]{4})', re.IGNORECASE),
        'time': re.compile(r'Время\s*[:\s]\s*([0-9]{1,2}:[0-9]{2}\s*-\s*[0-9]{1,2}:[0-9]{2})', re.IGNORECASE),
        'duration': re.compile(r'Длительность\s*[:\s]\s*([0-9]+)\s*ч', re.IGNORECASE),
        'supervisor': re.compile(r'Старший\s*[:\s]\s*([^\n]+)', re.IGNORECASE),
        'total_melts': re.compile(r'Всего\s+плавок\s*[:\s]\s*(\d+)', re.IGNORECASE),
        'participants': re.compile(r'Участники\s*[:\s]\s*([^\n]+)', re.IGNORECASE),
    }

    # Melt detail pattern - matches lines like: ✅ 1 РК-001 кластер-1 отливка-123 литник-456 опоки-789 t=1250°C 14:30 Создана
    MELT_PATTERN = re.compile(
        r'([✅🔄❓])\s*'  # Status emoji (group 1)
        r'(\d+)\s*'    # Melt number (group 2)
        r'(?:РК[-\s]?(\S+))?\s*'  # Route card (group 3, optional)
        r'(?:кластер[-\s]?(\S+))?\s*'  # Cluster (group 4, optional)
        r'(?:отливка[-\s]?(\S+))?\s*'  # Casting (group 5, optional)
        r'(?:литник[-\s]?(\S+))?\s*'  # Gating system (group 6, optional)
        r'(?:опоки[-\s]?(\S+))?\s*'  # Molds (group 7, optional)
        r'(?:t\s*=\s*(\d+(?:[.,]\d+)?)\s*°?C?)?\s*'  # Temperature (group 8, optional)
        r'([0-9]{1,2}:[0-9]{2})?\s*'  # Pour time (group 9, optional)
        r'(\S+)?\s*'  # Created status (group 10, optional)
        r'.*$',  # Match rest of line to be more permissive
        re.IGNORECASE
    )

    def parse_message(self, message_text: str) -> ParsedShiftReport:
        """Parse a complete shift report message."""
        try:
            lines = [line.strip() for line in message_text.strip().split('\n') if line.strip()]
            
            if not lines:
                raise MessageParseError("Empty message")
            
            header = self._parse_header(lines)
            melts = self._parse_melts(lines)
            
            # Validate that total melts matches parsed melts
            if header.total_melts is not None and header.total_melts != len(melts):
                logger.warning(
                    "Total melts count mismatch: header says %d, parsed %d melts",
                    header.total_melts, len(melts)
                )
            
            return ParsedShiftReport(header=header, melts=melts)
            
        except Exception as exc:
            raise MessageParseError(f"Failed to parse shift report: {exc}") from exc

    def _parse_header(self, lines: List[str]) -> ShiftHeader:
        """Parse header information from message lines."""
        header = ShiftHeader()
        
        # Find header section (before "ДЕТАЛИ ПЛАВОК")
        header_lines = []
        for line in lines:
            # Normalize whitespace and check for "ДЕТАЛИ ПЛАВОК"
            normalized_line = re.sub(r'\s+', ' ', line.upper().strip())
            if normalized_line.startswith('ДЕТАЛИ ПЛАВОК'):
                break
            header_lines.append(line)
        
        # Extract header fields
        header_text = '\n'.join(header_lines)
        
        for field_name, pattern in self.HEADER_PATTERNS.items():
            match = pattern.search(header_text)
            if match:
                value = match.group(1).strip()
                
                if field_name == 'shift':
                    header.shift_number = value
                elif field_name == 'date':
                    header.date = value
                elif field_name == 'time':
                    header.time_range = value
                elif field_name == 'duration':
                    header.duration = f"{value} ч"
                elif field_name == 'supervisor':
                    header.supervisor = value
                elif field_name == 'total_melts':
                    try:
                        header.total_melts = int(value)
                    except ValueError:
                        logger.warning("Invalid total melts value: %s", value)
                elif field_name == 'participants':
                    # Split by comma and clean up
                    participants = [p.strip() for p in value.split(',')]
                    header.participants = [p for p in participants if p]
        
        return header

    def _parse_melts(self, lines: List[str]) -> List[MeltDetail]:
        """Parse melt details from message lines."""
        melts = []
        
        # Find melt details section (after "ДЕТАЛИ ПЛАВОК")
        in_melts_section = False
        
        for line in lines:
            # Normalize whitespace and check for "ДЕТАЛИ ПЛАВОК"
            normalized_line = re.sub(r'\s+', ' ', line.upper().strip())
            if normalized_line.startswith('ДЕТАЛИ ПЛАВОК'):
                in_melts_section = True
                continue
            
            if not in_melts_section:
                continue
            
            # Try to parse as melt detail
            match = self.MELT_PATTERN.match(line)
            if match:
                try:
                    melt = self._create_melt_from_match(match)
                    melts.append(melt)
                except Exception as exc:
                    logger.warning("Failed to parse melt line '%s': %s", line, exc)
        
        return melts

    def _create_melt_from_match(self, match: re.Match) -> MeltDetail:
        """Create MeltDetail from regex match."""
        status_emoji = match.group(1)
        number = int(match.group(2))
        
        # Map emoji to status
        if status_emoji == "✅":
            status = MeltStatus.COMPLETED
        elif status_emoji == "🔄":
            status = MeltStatus.IN_PROGRESS
        else:
            status = MeltStatus.UNKNOWN
        
        # Parse temperature (handle comma as decimal separator)
        temp_str = match.group(8)
        temperature = None
        if temp_str:
            temp_str = temp_str.replace(',', '.')
            try:
                temperature = float(temp_str)
            except ValueError:
                logger.warning("Invalid temperature value: %s", temp_str)
        
        return MeltDetail(
            status=status,
            number=number,
            route_card=match.group(3),
            cluster=match.group(4),
            casting=match.group(5),
            gating_system=match.group(6),
            molds=match.group(7),
            temperature=temperature,
            pour_time=match.group(9),
            created=match.group(10)
        )

    def validate_report(self, report: ParsedShiftReport) -> List[str]:
        """Validate parsed report and return list of issues."""
        issues = []
        
        # Check for required header fields
        if not report.header.shift_number:
            issues.append("Missing shift number")
        
        if not report.header.date:
            issues.append("Missing shift date")
        
        if not report.header.supervisor:
            issues.append("Missing supervisor")
        
        # Check melts
        if not report.melts:
            issues.append("No melts found")
        
        # Validate melt numbers are sequential
        if report.melts:
            expected_numbers = list(range(1, len(report.melts) + 1))
            actual_numbers = [melt.number for melt in report.melts]
            if actual_numbers != expected_numbers:
                issues.append(f"Melt numbers are not sequential: expected {expected_numbers}, got {actual_numbers}")
        
        # Check total melts count
        if report.header.total_melts is not None and report.header.total_melts != len(report.melts):
            issues.append(
                f"Total melts count mismatch: header says {report.header.total_melts}, "
                f"found {len(report.melts)} melts"
            )
        
        return issues