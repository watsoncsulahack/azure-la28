"""A failed/resumed native transfer must never become a completed raw source."""
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock,patch
from urllib.error import HTTPError

SOURCE=Path(__file__).resolve().parents[1]/'evidence/native_transfer.py'
spec=importlib.util.spec_from_file_location('native_transfer',SOURCE)
native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)


class NativeTransferTests(unittest.TestCase):
    def test_error_page_etag_does_not_replace_source_validator(self):
        with tempfile.TemporaryDirectory()as directory:
            path=Path(directory)/'tile.laz';partial=path.with_suffix('.laz.part')
            partial.write_bytes(b'LASF')
            response=MagicMock();response.status=206
            response.headers={'Content-Range':'bytes 0-3/12','ETag':'"native-source"'}
            response.read.return_value=b'LASF';response.__enter__.return_value=response
            error=HTTPError('https://example.invalid/tile.laz',429,'rate limited',
                            {'ETag':'"error-page"'},io.BytesIO(b'Rate limited'))
            with patch.object(native,'urlopen',side_effect=[response,error]):
                with self.assertRaises(HTTPError):
                    native.fetch_native(path,'https://example.invalid/tile.laz',12)
            receipt=json.loads(partial.with_suffix('.part.receipt.json').read_text())
            self.assertEqual(receipt['validator'],'"native-source"')
            self.assertFalse(path.exists());self.assertEqual(partial.read_bytes(),b'LASF')

    def test_wrong_prefix_is_preserved_and_never_resumed(self):
        with tempfile.TemporaryDirectory()as directory:
            path=Path(directory)/'tile.laz';partial=path.with_suffix('.laz.part')
            partial.write_bytes(b'LASF')
            response=MagicMock();response.status=206;response.headers={'Content-Range':'bytes 0-3/12'}
            response.read.return_value=b'nope';response.__enter__.return_value=response
            with patch.object(native,'urlopen',return_value=response)as start:
                with self.assertRaisesRegex(ValueError,'Partial prefix differs'):
                    native.fetch_native(path,'https://example.invalid/tile.laz',12)
                self.assertEqual(start.call_count,1)
            self.assertEqual(partial.read_bytes(),b'LASF');self.assertFalse(path.exists())

    def test_wrong_cached_size_is_rejected_without_network(self):
        with tempfile.TemporaryDirectory()as directory:
            path=Path(directory)/'tile.laz';path.write_bytes(b'LASF')
            with patch.object(native,'urlopen')as fetch:
                with self.assertRaisesRegex(ValueError,'unexpected size'):
                    native.fetch_native(path,'https://example.invalid/tile.laz',12)
                fetch.assert_not_called()


if __name__=='__main__':unittest.main()
