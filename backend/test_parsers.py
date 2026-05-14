#!/usr/bin/env python3
"""
Standalone test script for VO2max Report parsers.

Tests the complete parsing workflow without Django/database.
Run from backend directory: python test_parsers.py
"""
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from core.parsers import ParserFactory, CsvParser, JsonParser


def test_csv_parser():
    """Test OMNIA CSV parsing."""
    print("=" * 60)
    print("CSV Parser Test (OMNIA Format)")
    print("=" * 60)
    
    file_path = Path(__file__).parent.parent / "doc" / "исходные.csv"
    
    parser = CsvParser()
    result = parser.parse(str(file_path))
    
    print(f"File: {file_path.name}")
    print(f"Format: {result.source_format}")
    print(f"Items: {len(result.items)}")
    print()
    
    if result.items:
        print("First 5 data points:")
        print("-" * 60)
        print(f"{'Time':>8} {'VO2/kg':>10} {'VO2':>10} {'HR':>6} {'Power':>8}")
        print("-" * 60)
        for item in result.items[:5]:
            vo2kg = f"{item.vo2_ml_kg_min:.2f}" if item.vo2_ml_kg_min else "N/A"
            vo2 = f"{item.vo2_ml_min:.0f}" if item.vo2_ml_min else "N/A"
            hr = f"{item.hr}" if item.hr else "N/A"
            power = f"{item.power:.1f}" if item.power else "N/A"
            print(f"{item.time_sec:>8.0f} {vo2kg:>10} {vo2:>10} {hr:>6} {power:>8}")
        
        print()
        print("Peak values:")
        max_vo2kg = max(i.vo2_ml_kg_min for i in result.items if i.vo2_ml_kg_min)
        max_hr = max(i.hr for i in result.items if i.hr)
        max_power = max(i.power for i in result.items if i.power)
        print(f"  VO2max: {max_vo2kg:.1f} mL/kg/min")
        print(f"  HRmax: {max_hr} bpm")
        print(f"  Peak Power: {max_power:.0f} W")
    
    return result


def test_json_parser():
    """Test custom JSON parsing."""
    print()
    print("=" * 60)
    print("JSON Parser Test (Custom Format)")
    print("=" * 60)
    
    file_path = Path(__file__).parent.parent / "doc" / "девайсы" / "T 20191110111405PDLGA001 Фетисова Ирина.json"
    
    parser = JsonParser()
    result = parser.parse(str(file_path))
    
    print(f"File: {file_path.name}")
    print(f"Format: {result.source_format}")
    print(f"Test ID: {result.test_id}")
    print()
    
    print("Client Info:")
    print(f"  Name: {result.client_name}")
    print(f"  Gender: {result.client_gender}, Age: {result.client_age}")
    print(f"  Weight: {result.client_weight} kg, Height: {result.client_height} cm")
    print()
    
    print(f"Items: {len(result.items)}")
    
    if result.items:
        print()
        print("First 5 data points:")
        print("-" * 70)
        print(f"{'Time':>6} {'VO2':>8} {'VCO2':>8} {'HR':>5} {'Power':>6} {'RER':>5} {'HRV':>5}")
        print("-" * 70)
        for item in result.items[:5]:
            vo2 = f"{item.vo2_ml_min:.0f}" if item.vo2_ml_min else "N/A"
            vco2 = f"{item.vco2_ml_min:.0f}" if item.vco2_ml_min else "N/A"
            hr = f"{item.hr}" if item.hr else "N/A"
            power = f"{item.power:.0f}" if item.power else "N/A"
            r = f"{item.r:.2f}" if item.r else "N/A"
            hrv = f"{item.hrv}" if item.hrv else "N/A"
            print(f"{item.time_sec:>6.0f} {vo2:>8} {vco2:>8} {hr:>5} {power:>6} {r:>5} {hrv:>5}")
        
        print()
        print("Peak values:")
        max_vo2 = max(i.vo2_ml_min for i in result.items if i.vo2_ml_min)
        max_hr = max(i.hr for i in result.items if i.hr)
        max_power = max(i.power for i in result.items if i.power)
        
        # Calculate VO2/kg using weight from setup
        vo2_kg = max_vo2 / result.client_weight if result.client_weight else 0
        
        print(f"  VO2max: {max_vo2:.0f} mL/min ({vo2_kg:.1f} mL/kg/min)")
        print(f"  HRmax: {max_hr} bpm")
        print(f"  Peak Power: {max_power:.0f} W")
    
    return result


def test_factory():
    """Test ParserFactory auto-detection."""
    print()
    print("=" * 60)
    print("ParserFactory Auto-Detection Test")
    print("=" * 60)
    
    csv_path = Path(__file__).parent.parent / "doc" / "исходные.csv"
    json_path = Path(__file__).parent.parent / "doc" / "девайсы" / "T 20191110111405PDLGA001 Фетисова Ирина.json"
    
    # Test CSV detection
    csv_result = ParserFactory.parse(str(csv_path))
    print(f"✓ CSV detected and parsed: {len(csv_result.items)} items")
    
    # Test JSON detection
    json_result = ParserFactory.parse(str(json_path))
    print(f"✓ JSON detected and parsed: {len(json_result.items)} items, client={json_result.client_name}")
    
    print()
    print("All factory tests passed!")


def detect_protocol(items):
    """Detect protocol parameters from power data."""
    powers = []
    for item in items:
        if item.power is not None and item.power > 0:
            rounded = round(item.power / 5) * 5
            if rounded not in powers:
                powers.append(int(rounded))
    
    if len(powers) < 2:
        return powers[0] if powers else 0, 0
    
    deltas = [powers[i] - powers[i-1] for i in range(1, len(powers))]
    positive_deltas = [d for d in deltas if d > 0]
    
    if not positive_deltas:
        return powers[0], 0
    
    from collections import Counter
    step = Counter(positive_deltas).most_common(1)[0][0]
    
    return powers[0], step


def test_protocol_detection():
    """Test protocol parameter auto-detection."""
    print()
    print("=" * 60)
    print("Protocol Detection Test")
    print("=" * 60)
    
    # Test on CSV
    csv_path = Path(__file__).parent.parent / "doc" / "исходные.csv"
    csv_result = ParserFactory.parse(str(csv_path))
    start, step = detect_protocol(csv_result.items)
    print(f"CSV Protocol: Start={start}W, Step={step}W")
    
    # Test on JSON
    json_path = Path(__file__).parent.parent / "doc" / "девайсы" / "T 20191110111405PDLGA001 Фетисова Ирина.json"
    json_result = ParserFactory.parse(str(json_path))
    start, step = detect_protocol(json_result.items)
    print(f"JSON Protocol: Start={start}W, Step={step}W")


if __name__ == "__main__":
    print()
    print("🧪 VO2max Report Parser Test Suite")
    print("=" * 60)
    
    csv_result = test_csv_parser()
    json_result = test_json_parser()
    test_factory()
    test_protocol_detection()
    
    print()
    print("=" * 60)
    print("✅ All tests completed successfully!")
    print("=" * 60)
