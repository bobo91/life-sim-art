"""Reference provenance and preflight regressions; no Blender import needed."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'scripts/neighborhood_references.py'


def functions(*names,**namespace):
    tree=ast.parse(SOURCE.read_text())
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
    if {n.name for n in nodes}!=set(names):raise AssertionError('Missing actual reference helper')
    scope={'hashlib':hashlib,'json':json,'Path':Path,**namespace}
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(SOURCE),'exec'),scope)
    return scope


class NeighborhoodReferenceTests(unittest.TestCase):
    def test_pinned_original_sources_and_configs_are_present_and_unchanged(self):
        lock=json.loads((ROOT/'configs/neighborhood-reference-locks.json').read_text())
        self.assertEqual(set(lock['pullRequests']),{'34','35','36','37'})
        for pr in lock['pullRequests'].values():
            self.assertFalse(pr['merged'])
            self.assertEqual(pr['state'],'open')
            self.assertRegex(pr['head'],r'^[0-9a-f]{40}$')
        for name,digest in lock['sourceFilesSHA256'].items():
            path=(ROOT/name).resolve()
            path.relative_to(ROOT)
            with self.subTest(source=name):
                self.assertTrue(path.is_file())
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),digest)
        for entry in lock['references'].values():
            self.assertIn(entry['config'],lock['sourceFilesSHA256'])

    def test_signed_zero_does_not_change_approved_geometry_fingerprint(self):
        fingerprint=functions('geometry_fingerprint',b=SimpleNamespace(signature=copy.deepcopy))['geometry_fingerprint']
        a={'positions':[(-0.0,1.2,0.0),(2.0,0.0,3.0)],'triangles':12}
        b={'positions':[(0.0,1.2,-0.0),(2.0,-0.0,3.0)],'triangles':12}
        self.assertEqual(fingerprint(a),fingerprint(b))
        self.assertNotEqual(fingerprint(a),fingerprint(dict(b,triangles=14)))
        self.assertNotEqual(fingerprint(a),fingerprint({'positions':[(0.0,1.3,0.0),(2.0,0.0,3.0)],'triangles':12}))

    def preflight(self,root,lock):
        file=root/'reference-locks.json';file.write_text(json.dumps(lock))
        f=functions('sha','build_references',ROOT=root,LOCK_PATH=file)
        return f['build_references']

    def test_changed_original_source_is_rejected_before_cache_writes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();original=root/'original.py';original.write_text('modified source')
            lock={'sourceFilesSHA256':{'original.py':hashlib.sha256(b'approved source').hexdigest()},'references':{}}
            build=self.preflight(root,lock)
            with self.assertRaisesRegex(ValueError,'Pinned original source/config changed'):
                build(root/'output')
            self.assertFalse((root/'output/reference').exists())

    def test_missing_approved_house_fingerprint_is_rejected_before_cache_writes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve()
            lock={'sourceFilesSHA256':{},'references':{'walter-house':{'kind':'house','expectedWorldGeometrySHA256':None}}}
            build=self.preflight(root,lock)
            with self.assertRaisesRegex(ValueError,'Record approved world geometry fingerprint'):
                build(root/'output')
            self.assertFalse((root/'output/reference').exists())


if __name__=='__main__':unittest.main()
