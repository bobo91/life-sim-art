import argparse
import struct
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest.mock import patch

from art_pipeline.cli import ROOT, build, main, normalize_png_metadata


def chunk(kind, value):
    return struct.pack(">I", len(value))+kind+value+struct.pack(">I", zlib.crc32(kind+value)&0xffffffff)


class CliTests(unittest.TestCase):
    def test_metadata_normalization_preserves_image_and_color_chunks(self):
        header = b"\x89PNG\r\n\x1a\n"
        ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", 1,1,8,6,0,0,0))
        pixels = chunk(b"IDAT", zlib.compress(b"\x00\xff\x00\x00\xff"))
        srgb = chunk(b"sRGB", b"\x00")
        end = chunk(b"IEND", b"")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"image.png"
            path.write_bytes(header+ihdr+srgb+chunk(b"tEXt", b"RenderTime\x001.2")+pixels+end)
            normalize_png_metadata(path)
            self.assertEqual(path.read_bytes(), header+ihdr+srgb+pixels+end)

    def test_refuses_overwriting_existing_output(self):
        with tempfile.TemporaryDirectory() as directory:
            sentinel = Path(directory)/"keep.txt"
            sentinel.write_text("existing evidence")
            args = argparse.Namespace(config=ROOT/"configs/streetlamp.json", output=directory, blender=__file__)
            with self.assertRaisesRegex(ValueError, "new or empty"):
                build(args)
            self.assertEqual(sentinel.read_text(), "existing evidence")

    def test_blender_failure_is_nonzero_and_leaves_diagnostic_log(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)/"failed"
            args = argparse.Namespace(config=ROOT/"configs/streetlamp.json", output=output, blender=__file__)
            with patch("art_pipeline.cli.source_identity", return_value=("a"*40,"b"*64,False)), \
                 patch("art_pipeline.cli.subprocess.run", return_value=argparse.Namespace(returncode=1,stdout="script error")):
                with self.assertRaisesRegex(ValueError, "Blender failed"):
                    build(args)
            self.assertEqual((output/"blender.log").read_text(), "script error")
            self.assertFalse((output/"manifest.json").exists())

    def test_missing_blender_is_actionable_nonzero(self):
        with patch("art_pipeline.cli.shutil.which", return_value=None), patch.dict("os.environ", {"BLENDER_BIN":""}):
            self.assertEqual(main(["audit"]), 1)


if __name__ == "__main__":
    unittest.main()
