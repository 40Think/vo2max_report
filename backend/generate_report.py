#!/usr/bin/env python3
"""
Generate reports with template selection.

Usage:
    python3 generate_report.py                    # Default report
    python3 generate_report.py --template detailed_report   # Detailed report
    python3 generate_report.py --list             # List available templates
"""
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.reports import create_sample_report
from core.reports.generator import ReportGenerator


def create_detailed_report_data() -> dict:
    """Create sample data for detailed report format (variant 2)."""
    return {
        'client': {
            'name': 'ИмяФамилия',
            'weight': 74,
        },
        'test': {
            'sport': 'велоспорт',
            'date': '2 ноября 2019',
            'equipment': 'Elite Drivo 2',
            'cadence': 80,
            'notes': 'Замеры лактата были из капель крови, взятых за 5-10 секунд до окончания ступени.',
            'date_1': '4 августа',
            'date_2': '2 ноября',
        },
        'data_rows': [
            {'time': '2:00', 'power': 120, 'hr': 129.47, 'lactate': '', 'vo2': 1777.33, 've': 40.51, 'tv': 3.72, 'rf': 10.99},
            {'time': '4:00', 'power': 120, 'hr': 133.27, 'lactate': '', 'vo2': 1432.67, 've': 43.71, 'tv': 2.62, 'rf': 16.82},
            {'time': '6:05', 'power': 140, 'hr': 140.73, 'lactate': 1.2, 'vo2': 1808, 've': 50.43, 'tv': 2.07, 'rf': 24.89},
            {'time': '8:00', 'power': 160, 'hr': 145.83, 'lactate': 1.5, 'vo2': 2223.11, 've': 60.49, 'tv': 3.09, 'rf': 19.83},
            {'time': '10:00', 'power': 180, 'hr': 151.83, 'lactate': 1.5, 'vo2': 2277.08, 've': 55.92, 'tv': 2.35, 'rf': 24.06},
            {'time': '12:00', 'power': 200, 'hr': 162.43, 'lactate': 2.3, 'vo2': 2412.42, 've': 64.24, 'tv': 2.58, 'rf': 25.08},
            {'time': '14:00', 'power': 220, 'hr': 171.8, 'lactate': 3.6, 'vo2': 2766.08, 've': 74.48, 'tv': 2.64, 'rf': 28.55},
            {'time': '16:00', 'power': 240, 'hr': 178.07, 'lactate': 4.6, 'vo2': 3067, 've': 86.42, 'tv': 2.67, 'rf': 32.69},
            {'time': '18:00', 'power': 260, 'hr': 182.4, 'lactate': 7.1, 'vo2': 3149.26, 've': 99.35, 'tv': 2.55, 'rf': 39.21},
            {'time': '20:00', 'power': 280, 'hr': 188.37, 'lactate': 9.6, 'vo2': 3249, 've': 120.9, 'tv': 2.54, 'rf': 47.84},
        ],
        'hr_comparison': [
            {'power': 120, 'hr_1': 124, 'hr_2': 129.47},
            {'power': 140, 'hr_1': 142, 'hr_2': 140.73},
            {'power': 160, 'hr_1': 151, 'hr_2': 145.83},
            {'power': 180, 'hr_1': 163, 'hr_2': 151.83},
            {'power': 200, 'hr_1': 169, 'hr_2': 162.43},
            {'power': 220, 'hr_1': 176, 'hr_2': 171.8},
            {'power': 240, 'hr_1': 182, 'hr_2': 178.07},
        ],
        've_comparison': [
            {'power': 120, 've_1': 35, 've_2': 40.51},
            {'power': 140, 've_1': 49, 've_2': 50.43},
            {'power': 160, 've_1': 55, 've_2': 60.49},
            {'power': 180, 've_1': 68, 've_2': 55.92},
            {'power': 200, 've_1': 81, 've_2': 64.24},
            {'power': 220, 've_1': 98, 've_2': 74.48},
            {'power': 240, 've_1': 121, 've_2': 86.42},
        ],
        'vo2_comparison': [
            {'power': 120, 'vo2_1': 1552, 'vo2_2': 1777.33},
            {'power': 140, 'vo2_1': 2124, 'vo2_2': 1808},
            {'power': 160, 'vo2_1': 2128, 'vo2_2': 2223.11},
            {'power': 180, 'vo2_1': 2454, 'vo2_2': 2277.08},
            {'power': 200, 'vo2_1': 2603, 'vo2_2': 2412.42},
            {'power': 220, 'vo2_1': 2792, 'vo2_2': 2766.08},
            {'power': 240, 'vo2_1': 2765, 'vo2_2': 3067},
        ],
        'lactate_comparison': [
            {'power': 120, 'la_1': 1.2, 'la_2': 1.4},
            {'power': 140, 'la_1': '', 'la_2': 1.2},
            {'power': 160, 'la_1': 2.6, 'la_2': 1.5},
            {'power': 180, 'la_1': 3.7, 'la_2': 1.5},
            {'power': 200, 'la_1': 5.7, 'la_2': 2.3},
            {'power': 220, 'la_1': 8.4, 'la_2': 3.6},
            {'power': 240, 'la_1': 11.2, 'la_2': 4.6},
        ],
        'skills': [
            {'name': 'Мышечная Сила (МАМ)', 'your_value': 1000, 'your_level': 6, 'level_1': 200, 'level_2': 400, 'level_3': 500, 'level_4': 700, 'level_5': 800, 'level_6': 1000, 'world_best': '1000-1400+'},
            {'name': 'АэП - окисление жиров', 'your_value': 180, 'your_level': 3, 'level_1': 0, 'level_2': 50, 'level_3': 100, 'level_4': 200, 'level_5': 300, 'level_6': 350, 'world_best': '400'},
            {'name': 'Мышечная выносливость (АнП)', 'your_value': 220, 'your_level': 3, 'level_1': 50, 'level_2': 100, 'level_3': 200, 'level_4': 300, 'level_5': 350, 'level_6': 400, 'world_best': '450+'},
            {'name': 'Доставка O2 (ДО2)', 'your_value': 400, 'your_level': 5, 'level_1': 150, 'level_2': 200, 'level_3': 250, 'level_4': 300, 'level_5': 400, 'level_6': 500, 'world_best': '600-800'},
        ],
        'examples': [
            'Крис Фрум – АэП 350 ватт, АнП 420 ватт, МАМ 1400 ватт, ДО2 600 ватт',
            'Лэнс Армстронг в начале карьеры – МАМ 1000 ватт, АнП 350 ватт',
            'Лучшие лыжники и гребцы – 1000-1500 ватт МАМ',
            'Трековые спринтеры – МАМ 2000-3500 ватт',
        ],
        'conclusion': 'На основании проведённого тестирования рекомендуется развивать мышечную выносливость через работу в зоне АнП.',
    }


def main():
    parser = argparse.ArgumentParser(description='VO2max Report Generator')
    parser.add_argument('--template', '-t', default='default_report', help='Template name')
    parser.add_argument('--list', '-l', action='store_true', help='List available templates')
    parser.add_argument('--output', '-o', default=None, help='Output filename')
    args = parser.parse_args()
    
    generator = ReportGenerator()
    
    if args.list:
        print("Available templates:")
        for tpl in generator.list_templates():
            print(f"  - {tpl}")
        return
    
    print("=" * 60)
    print(f"VO2max Report Generator — Template: {args.template}")
    print("=" * 60)
    
    # Select data based on template
    if args.template == 'detailed_report':
        data = create_detailed_report_data()
        print(f"\nClient: {data['client']['name']}")
        print(f"Sport: {data['test']['sport']}")
        print(f"Data rows: {len(data['data_rows'])}")
        print(f"Skills: {len(data['skills'])}")
    else:
        report_data = create_sample_report()
        data = report_data.to_dict()
        print(f"\nClient: {data['client']['name'] or 'Not specified'}")
        print(f"Sport: {data['test']['sport']}")
        print(f"Thresholds: {len(data['thresholds'])}")
    
    # Generate HTML
    output_file = args.output or f"{args.template}.html"
    output_path = Path(__file__).parent / output_file
    
    generator.generate_html_file(
        data=data,
        template=args.template,
        output_path=str(output_path)
    )
    
    print(f"\n✅ Report generated: {output_path}")
    print("   Open in browser to preview")


if __name__ == "__main__":
    main()
