import unittest
from unittest.mock import patch

from core.dependencies import resolve_cookies_args
from core.downloader import build_command, clip_section_range, playlist_items_range


class PlaylistItemsRangeTests(unittest.TestCase):
    def test_empty_range_is_unrestricted(self):
        self.assertIsNone(playlist_items_range("", ""))

    def test_start_and_end_are_normalized(self):
        self.assertEqual(playlist_items_range("2", "8"), "2:8")

    def test_end_without_start_starts_at_first_item(self):
        self.assertEqual(playlist_items_range("", "8"), "1:8")

    def test_rejects_non_numeric_or_reversed_ranges(self):
        for start, end in (("x", ""), ("1", "x"), ("0", ""), ("8", "2")):
            with self.subTest(start=start, end=end):
                with self.assertRaises(ValueError):
                    playlist_items_range(start, end)


class BuildCommandTests(unittest.TestCase):
    @patch("core.downloader.get_ytdlp_cmd", return_value=["yt-dlp"])
    @patch("core.downloader.get_ffmpeg_dir", return_value=None)
    def test_playlist_range_and_configured_options_are_applied(self, *_mocks):
        command = build_command(
            "https://example.com/playlist",
            "C:\\Downloads",
            {
                "mode": "playlist",
                "media_type": "video",
                "format": "mp4",
                "quality": "Best Quality (En İyi)",
                "playlist_start": "2",
                "playlist_end": "5",
                "concurrent_fragments": 8,
                "speed_limit": "2M",
                "proxy": "http://127.0.0.1:8080",
            },
        )

        self.assertIn("2:5", command)
        self.assertIn("8", command)
        self.assertIn("2M", command)
        self.assertIn("http://127.0.0.1:8080", command)
        self.assertIn("--yes-playlist", command)

    @patch("core.downloader.get_ytdlp_cmd", return_value=["yt-dlp"])
    @patch("core.downloader.get_ffmpeg_dir", return_value=None)
    def test_rejects_out_of_range_fragment_count(self, *_mocks):
        with self.assertRaises(ValueError):
            build_command(
                "https://example.com/video",
                "C:\\Downloads",
                {"concurrent_fragments": 17},
            )

    @patch("core.downloader.get_ytdlp_cmd", return_value=["yt-dlp"])
    @patch("core.downloader.get_ffmpeg_dir", return_value=None)
    def test_rejects_invalid_playlist_range(self, *_mocks):
        with self.assertRaises(ValueError):
            build_command(
                "https://example.com/playlist",
                "C:\\Downloads",
                {
                    "mode": "playlist",
                    "playlist_start": "5",
                    "playlist_end": "2",
                },
            )

    @patch("core.downloader.get_ytdlp_cmd", return_value=["yt-dlp"])
    @patch("core.downloader.get_ffmpeg_dir", return_value=None)
    def test_ignore_errors_is_only_enabled_for_playlists(self, *_mocks):
        single_command = build_command(
            "https://example.com/video",
            "C:\\Downloads",
            {"mode": "single", "ignore_errors": True},
        )
        playlist_command = build_command(
            "https://example.com/playlist",
            "C:\\Downloads",
            {"mode": "playlist", "ignore_errors": True},
        )

        self.assertNotIn("--ignore-errors", single_command)
        self.assertIn("--ignore-errors", playlist_command)

    @patch("core.downloader.get_ytdlp_cmd", return_value=["yt-dlp"])
    @patch("core.downloader.get_ffmpeg_dir", return_value=None)
    def test_wav_and_webm_skip_embed_thumbnail_to_prevent_ytdlp_error(self, *_mocks):
        wav_cmd = build_command(
            "https://example.com/audio",
            "C:\\Downloads",
            {"media_type": "audio", "format": "wav", "embed_thumbnail": True},
        )
        mp3_cmd = build_command(
            "https://example.com/audio",
            "C:\\Downloads",
            {"media_type": "audio", "format": "mp3", "embed_thumbnail": True},
        )
        self.assertNotIn("--embed-thumbnail", wav_cmd)
        self.assertIn("--embed-thumbnail", mp3_cmd)
        self.assertIn("after_move:[FINAL_PATH] %(filepath)s", mp3_cmd)

    @patch("core.downloader.get_ytdlp_cmd", return_value=["yt-dlp"])
    @patch("core.downloader.get_ffmpeg_dir", return_value=None)
    def test_archive_clip_and_sponsorblock_flags_are_applied(self, *_mocks):
        cmd = build_command(
            "https://example.com/video",
            "C:\\Downloads",
            {
                "mode": "single",
                "use_download_archive": True,
                "archive_file": "C:\\Downloads\\archive.txt",
                "sponsorblock_remove": True,
                "sponsorblock_cats": "sponsor,intro,outro",
                "clip_start": "01:20",
                "clip_end": "03:45",
            },
        )
        self.assertIn("--download-archive", cmd)
        self.assertIn("C:\\Downloads\\archive.txt", cmd)
        self.assertIn("--sponsorblock-remove", cmd)
        self.assertIn("sponsor,intro,outro", cmd)
        self.assertIn("--download-sections", cmd)
        self.assertIn("*01:20-03:45", cmd)

    def test_clip_section_range_validation(self):
        self.assertIsNone(clip_section_range("", ""))
        self.assertEqual(clip_section_range("01:20", "03:45"), "*01:20-03:45")
        self.assertEqual(clip_section_range("01:20", ""), "*01:20-inf")
        self.assertEqual(clip_section_range("", "03:45"), "*00:00-03:45")
        with self.assertRaises(ValueError):
            clip_section_range("05:00", "02:00")
        with self.assertRaises(ValueError):
            clip_section_range("abc", "02:00")


class CookieResolutionTests(unittest.TestCase):
    def test_missing_cookie_file_is_reported(self):
        with self.assertRaises(FileNotFoundError):
            resolve_cookies_args("file", cookies_file="missing-cookies.txt")

    def test_default_placeholder_cookie_file_is_rejected(self):
        with self.assertRaises(FileNotFoundError):
            resolve_cookies_args("file", cookies_file="Seçilmedi")


if __name__ == "__main__":
    unittest.main()
