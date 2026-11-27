import unittest

from stream_parser import rewrite_playlist


class RewritePlaylistTests(unittest.TestCase):
    def test_rewrites_relative_segments(self):
        text = "\n".join(
            [
                "#EXTM3U",
                "#EXT-X-TARGETDURATION:4",
                "#EXTINF:4.000,",
                "seg-1-f1-v1-a1.m4s",
                "#EXT-X-ENDLIST",
            ]
        )
        base = "https://cdn.example.com/path/master.m3u8"
        result = rewrite_playlist(
            text,
            base,
            "/stream/manifest?url={url}",
            "/stream/segment?url={url}",
        )
        self.assertIn("/stream/segment?url=", result)
        self.assertIn("https%3A%2F%2Fcdn.example.com%2Fpath%2Fseg-1-f1-v1-a1.m4s", result)

    def test_rewrites_variant_playlists_to_manifest_proxy(self):
        text = "\n".join(
            [
                "#EXTM3U",
                "#EXT-X-STREAM-INF:BANDWIDTH=1284621,RESOLUTION=854x462",
                "index-f1-v1-a1.m3u8",
                "#EXT-X-ENDLIST",
            ]
        )
        base = "https://cdn.example.com/master.m3u8"
        result = rewrite_playlist(
            text,
            base,
            "/stream/manifest?url={url}",
            "/stream/segment?url={url}",
        )
        self.assertIn(
            "/stream/manifest?url=https%3A%2F%2Fcdn.example.com%2Findex-f1-v1-a1.m3u8",
            result,
        )

    def test_rewrites_absolute_urls(self):
        text = "\n".join(
            [
                "#EXTM3U",
                "#EXT-X-STREAM-INF:BANDWIDTH=1284621,RESOLUTION=854x462",
                "https://other.example.com/variant/index.m3u8",
                "#EXT-X-ENDLIST",
            ]
        )
        base = "https://cdn.example.com/master.m3u8"
        result = rewrite_playlist(
            text,
            base,
            "/stream/manifest?url={url}",
            "/stream/segment?url={url}",
        )
        self.assertIn("https%3A%2F%2Fother.example.com%2Fvariant%2Findex.m3u8", result)

    def test_rewrites_init_map_uri(self):
        text = "\n".join(
            [
                "#EXTM3U",
                '#EXT-X-MAP:URI="init-c1-f1-v1-a1.mp4"',
                "#EXT-X-ENDLIST",
            ]
        )
        base = "https://cdn.example.com/media/index.m3u8"
        result = rewrite_playlist(
            text,
            base,
            "/stream/manifest?url={url}",
            "/stream/segment?url={url}",
        )
        self.assertIn('URI="/stream/segment?url=https%3A%2F%2Fcdn.example.com%2Fmedia%2Finit-c1-f1-v1-a1.mp4"', result)

    def test_preserves_comments_without_uris(self):
        text = "\n".join(
            [
                "#EXTM3U",
                "#EXT-X-PLAYLIST-TYPE:VOD",
                "#EXT-X-ENDLIST",
            ]
        )
        base = "https://cdn.example.com/master.m3u8"
        result = rewrite_playlist(
            text,
            base,
            "/stream/manifest?url={url}",
            "/stream/segment?url={url}",
        )
        self.assertIn("#EXTM3U", result)
        self.assertIn("#EXT-X-ENDLIST", result)
        self.assertNotIn("/stream/segment?url=", result)


if __name__ == "__main__":
    unittest.main()
