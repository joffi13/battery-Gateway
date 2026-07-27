"""Tests for the universal CAN analyzer."""

from pathlib import Path
import tempfile
import unittest

from tools.can_analyzer import CANAnalyzer, CandumpParser, analyze_file


class CandumpParserTest(unittest.TestCase):
    """Parser tests for supported candump formats."""

    def setUp(self) -> None:
        self.parser = CandumpParser()

    def test_compact_candump_format(self) -> None:
        result = self.parser.parse_line(
            "(1780000000.000001) can0 351#4202E8039E07D001"
        )

        self.assertIsNotNone(result.frame)
        assert result.frame is not None
        self.assertEqual(result.frame.can_id, "351")
        self.assertEqual(result.frame.interface, "can0")
        self.assertEqual(result.frame.timestamp, "1780000000.000001")
        self.assertEqual(result.frame.data, bytes.fromhex("4202E8039E07D001"))

    def test_classic_candump_format(self) -> None:
        result = self.parser.parse_line(
            "can0 351 [8] 42 02 E8 03 9E 07 D0 01"
        )

        self.assertIsNotNone(result.frame)
        assert result.frame is not None
        self.assertEqual(result.frame.can_id, "351")
        self.assertEqual(result.frame.data, bytes.fromhex("4202E8039E07D001"))

    def test_invalid_line_is_skipped(self) -> None:
        result = self.parser.parse_line("not a candump line")

        self.assertIsNone(result.frame)
        self.assertTrue(result.skipped)


class CANAnalyzerTest(unittest.TestCase):
    """Analyzer tests for streaming statistics."""

    def test_empty_file_has_no_frames(self) -> None:
        report = CANAnalyzer().analyze_lines([])

        self.assertEqual(report.total_frames, 0)
        self.assertEqual(report.skipped_lines, 0)
        self.assertEqual(report.can_ids, ())

    def test_invalid_lines_do_not_crash(self) -> None:
        report = CANAnalyzer().analyze_lines([
            "garbage\n",
            "can0 351 [8] 42 02 XX 03 9E 07 D0 01\n",
            "can0 351 [7] 42 02 E8 03 9E 07 D0\n",
        ])

        self.assertEqual(report.total_frames, 0)
        self.assertEqual(report.skipped_lines, 3)
        self.assertEqual(report.can_ids, ())

    def test_mixed_files_are_grouped_by_can_id(self) -> None:
        report = CANAnalyzer().analyze_lines([
            "(1.0) can0 351#4202E8039E07D001\n",
            "can0 351 [8] 43 02 E8 03 9E 07 D0 01\n",
            "can0 123 [8] 00 00 00 00 00 00 00 00\n",
            "bad line\n",
        ])

        self.assertEqual(report.total_frames, 3)
        self.assertEqual(report.skipped_lines, 1)
        self.assertEqual([item.can_id for item in report.can_ids], ["123", "351"])

        report_351 = report.can_ids[1]
        self.assertEqual(report_351.frame_count, 2)
        self.assertEqual(report_351.variable_bytes, (0,))
        self.assertEqual(report_351.constant_bytes, (1, 2, 3, 4, 5, 6, 7))
        self.assertEqual(report_351.byte_stats[0].min_value, 0x42)
        self.assertEqual(report_351.byte_stats[0].max_value, 0x43)
        self.assertEqual(report_351.byte_stats[0].distinct_count, 2)

    def test_16_bit_statistics_are_calculated_for_all_interpretations(self) -> None:
        report = CANAnalyzer().analyze_lines([
            "can0 351 [8] 01 02 00 00 00 00 00 00\n",
            "can0 351 [8] FF FE 00 00 00 00 00 00\n",
        ])

        word_pair = report.can_ids[0].word_pairs[0]
        self.assertEqual(word_pair.offset, 0)
        self.assertEqual(word_pair.little_unsigned.min_value, 0x0201)
        self.assertEqual(word_pair.little_unsigned.max_value, 0xFEFF)
        self.assertEqual(word_pair.little_unsigned.distinct_count, 2)
        self.assertEqual(word_pair.little_signed.min_value, -257)
        self.assertEqual(word_pair.little_signed.max_value, 513)
        self.assertEqual(word_pair.big_unsigned.min_value, 0x0102)
        self.assertEqual(word_pair.big_unsigned.max_value, 0xFFFE)
        self.assertEqual(word_pair.big_signed.min_value, -2)
        self.assertEqual(word_pair.big_signed.max_value, 258)

    def test_analyze_file_helper(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.log"
            path.write_text("can0 351 [8] 42 02 E8 03 9E 07 D0 01\n")

            report = analyze_file(path)

        self.assertEqual(report.total_frames, 1)
        self.assertEqual(report.can_ids[0].can_id, "351")


if __name__ == "__main__":
    unittest.main()
