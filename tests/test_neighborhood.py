"""Offline checks of locked reuse and the actual neighborhood handoff layout."""
import hashlib
import copy
import json
import math
from pathlib import Path,PurePosixPath
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]


def load(name):
    return json.loads((ROOT/'configs'/name).read_text(encoding='utf-8'))


def inside(point,rectangle,tolerance=1e-7):
    return (rectangle[0]-tolerance<=point[0]<=rectangle[2]+tolerance
            and rectangle[1]-tolerance<=point[1]<=rectangle[3]+tolerance)


def segment_distance(point,a,b):
    direction=[b[i]-a[i] for i in range(2)]
    length=sum(x*x for x in direction)
    t=max(0,min(1,sum((point[i]-a[i])*direction[i] for i in range(2))/length))
    return math.dist(point[:2],[a[i]+t*direction[i] for i in range(2)])


def prop_route_conflicts(layout,references):
    """Screen actual oriented prop envelopes against the reserved corridor.

    Use the locked prop configurations, not a copied list of guessed radii.
    The parasol uses its explicit weighted-base proposal, allowing its crown
    to overhang the path. Other listed props use conservative mesh XY bounds.
    This is an art placement screen, not a physics/NavMesh simulation.
    """
    checked={'prop_cafe_table_001','prop_cafe_chair_001','prop_mailbox_001',
        'prop_porch_bench_001','prop_streetlamp_pipeline_001','prop_cafe_parasol_001',
        'prop_wooden_crate_001','prop_flower_pot_001','prop_flower_pot_002',
        'prop_old_watering_can_001','prop_porch_rocking_chair_001',
        'prop_wooden_fence_001','prop_fence_post_001'}
    conflicts=[]
    for item in layout['instances']:
        asset=item['assetId']
        if asset not in checked:continue
        cfg=json.loads((ROOT/references[asset]['config']).read_text())
        size=cfg['dimensionsMeters'];width,height,depth=size
        centre=(0,0,height/2)
        if asset=='prop_cafe_parasol_001':
            base=cfg['collisionProposal']['base']
            width,height,depth=base['sizeXYZ']
            centre=(base['centerXYZ'][0],-base['centerXYZ'][2],base['centerXYZ'][1])
        # Body-only pot/watering-can proposals are descriptive strings rather
        # than numeric boxes. Their full configured envelopes conservatively
        # contain those bodies; do not silently omit them or invent a smaller box.
        rx,ry=[math.radians(item.get('rotation'+axis+'Degrees',0)) for axis in 'XY']
        cx,sx,cy,sy=math.cos(rx),math.sin(rx),math.cos(ry),math.sin(ry)
        corners=[]
        for dx in (-width/2,width/2):
            for dy in (-depth/2,depth/2):
                for dz in (-height/2,height/2):
                    x,y,z=centre[0]+dx,centre[1]+dy,centre[2]+dz
                    y1,z1=cx*y-sx*z,sx*y+cx*z
                    corners.append((cy*x+sy*z1,y1))
        lower=[min(p[i] for p in corners) for i in range(2)]
        upper=[max(p[i] for p in corners) for i in range(2)]
        offset=[(a+b)/2 for a,b in zip(lower,upper)]
        width,depth=[b-a for a,b in zip(lower,upper)]
        angle=math.radians(item['rotationZDegrees']);co,si=math.cos(angle),math.sin(angle)
        scale=item['uniformScale'];origin=item['positionSourceXYZ']
        for route in layout['routes']:
            nearest=float('inf')
            for a,b in zip(route['pointsSourceXYZ'],route['pointsSourceXYZ'][1:]):
                steps=max(1,math.ceil(math.dist(a[:2],b[:2])/.025))
                for step in range(steps+1):
                    t=step/steps
                    x=(a[0]+(b[0]-a[0])*t-origin[0])/scale
                    y=(a[1]+(b[1]-a[1])*t-origin[1])/scale
                    local=(co*x+si*y-offset[0],-si*x+co*y-offset[1])
                    distance=math.hypot(max(abs(local[0])-width/2,0),max(abs(local[1])-depth/2,0))*scale
                    nearest=min(nearest,distance)
            # A 25 mm sample step can overestimate the true nearest distance by
            # at most12.5 mm. Reserve that margin instead of silently missing it.
            if nearest<route['widthMeters']/2+.0125:
                conflicts.append((item['instanceId'],route['routeId'],round(nearest,5)))
    return conflicts


class NeighborhoodTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.layout=load('neighborhood-layout.json')
        cls.config=load('neighborhood-assets.json')
        cls.locks=load('neighborhood-reference-locks.json')
        cls.assets={a['assetId']:a for a in cls.config['assets']}

    def test_approved_references_are_commit_and_source_locked(self):
        self.assertRegex(self.locks['baseMainCommit'],r'^[0-9a-f]{40}$')
        self.assertIn('No purchased',self.locks['provenance'])
        for path,digest in self.locks['sourceFilesSHA256'].items():
            with self.subTest(source=path):
                self.assertRegex(digest,r'^[0-9a-f]{64}$')
                self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),digest)
        for asset,ref in self.locks['references'].items():
            with self.subTest(reference=asset):
                self.assertRegex(ref['sourceCommit'],r'^[0-9a-f]{40}$')
                if ref['sourcePR'] is not None:
                    self.assertEqual(ref['sourceCommit'],self.locks['pullRequests'][str(ref['sourcePR'])]['head'])
                    self.assertRegex(ref['approvedGLBSHA256'],r'^[0-9a-f]{64}$')
                if ref['kind']=='house':
                    self.assertRegex(ref['expectedWorldGeometrySHA256'] or '',r'^[0-9a-f]{64}$')
                self.assertTrue((ROOT/ref['config']).is_file())
        # A local bootstrap path is never required to run these offline checks.

    def test_bounded_inventory_and_authored_bounds(self):
        expected={'env_ground_400_001','env_road_600_001','env_sidewalk_200_001',
            'env_curb_200_001','env_sidewalk_corner_001','env_crosswalk_001',
            'env_curb_ramp_001','env_soil_bed_001','prop_street_name_001','env_deciduous_tree_001',
            'env_small_tree_001','env_shrub_001','env_shrub_002',
            'bld_cafe_storefront_200_001','bld_cafe_fascia_200_001','prop_cafe_sign_001'}
        self.assertEqual(set(self.assets),expected)
        self.assertEqual(len(self.config['assets']),len(expected))
        self.assertFalse(set(self.assets)&set(self.locks['references']))
        for asset in self.assets.values():
            span=[b-a for a,b in zip(asset['expectedBounds']['min'],asset['expectedBounds']['max'])]
            self.assertTrue(all(math.isfinite(v) and v>0 for v in span))
            for a,b in zip(span,asset['dimensionsMeters']):self.assertAlmostEqual(a,b,places=6)

    def test_instances_use_known_roots_and_finite_positive_transforms(self):
        instances=self.layout['instances'];ids=[i['instanceId'] for i in instances]
        self.assertEqual(len(ids),len(set(ids)))
        known=set(self.assets)|set(self.locks['references'])|{'cafe-building'}
        for item in instances:
            with self.subTest(instance=item['instanceId']):
                self.assertIn(item['assetId'],known)
                self.assertEqual(len(item['positionSourceXYZ']),3)
                self.assertTrue(all(math.isfinite(v) for v in item['positionSourceXYZ']))
                self.assertTrue(math.isfinite(item['rotationZDegrees']))
                self.assertTrue(math.isfinite(item['uniformScale']) and item['uniformScale']>0)
                self.assertIsInstance(item['static'],bool)
                self.assertTrue(item['group'])
                if not item['static']:self.assertTrue(item.get('futureInteraction'))

    def test_catalog_paths_and_exported_poses_are_unambiguous(self):
        catalog=self.layout['assetCatalog']
        self.assertTrue(set(self.assets)<=set(catalog))
        for asset,entry in catalog.items():
            path=PurePosixPath(entry['file'])
            self.assertFalse(path.is_absolute())
            self.assertNotIn('..',path.parts)
            self.assertEqual(path.suffix,'.glb');self.assertEqual(path.stem,asset)
        for item in self.layout['instances']:
            self.assertIn(item['assetId'],catalog)
            x,y,z=item['positionSourceXYZ']
            for a,b in zip(item['positionGlTFXYZ'],(x,z,-y)):self.assertAlmostEqual(a,b,places=9)
            q=item['rotationGlTFXYZW'];self.assertEqual(len(q),4)
            # Source Euler XYZ includes the explicitly upturned crate. Transform
            # the source quaternion vector through the X/Z/-Y export basis.
            x,y,z=[math.radians(item.get('rotation'+axis+'Degrees',0))/2 for axis in 'XYZ']
            sx,cx,sy,cy,sz,cz=math.sin(x),math.cos(x),math.sin(y),math.cos(y),math.sin(z),math.cos(z)
            source=(sx*cy*cz-cx*sy*sz,cx*sy*cz+sx*cy*sz,
                    cx*cy*sz-sx*sy*cz,cx*cy*cz+sx*sy*sz)
            expected=(source[0],source[2],-source[1],source[3])
            self.assertAlmostEqual(sum(v*v for v in q),1,places=9)
            self.assertAlmostEqual(abs(sum(a*b for a,b in zip(q,expected))),1,places=9,
                msg='Source orientation must use the glTF export basis; q and -q are equivalent')

    def test_route_endpoints_and_full_width_use_connected_walk_surfaces(self):
        surfaces=self.layout['walkableSurfaces']
        entrances=self.layout['entrances']
        route=next(r for r in self.layout['routes'] if r['routeId']=='walter-to-cafe')
        points=route['pointsSourceXYZ']
        self.assertEqual(points[0],entrances['entry_walter']['positionSourceXYZ'])
        self.assertEqual(points[-1],entrances['entry_cafe']['positionSourceXYZ'])
        self.assertGreaterEqual(route['widthMeters'],.9)
        length=0
        for a,b in zip(points,points[1:]):
            distance=math.dist(a[:2],b[:2]);self.assertGreater(distance,0);length+=distance
            normal=(-(b[1]-a[1])/distance,(b[0]-a[0])/distance)
            steps=max(1,math.ceil(distance/.10))
            for step in range(steps+1):
                t=step/steps
                for side in (-.5,0,.5):
                    sample=[a[i]+(b[i]-a[i])*t+normal[i]*route['widthMeters']*side for i in range(2)]
                    self.assertTrue(any(inside(sample,s['boundsSourceXY']) for s in surfaces),
                        f'Unsupported route width at {sample}')
        self.assertLess(length,70,'First block should stay compact and walkable')

    def test_planting_leaves_reserved_route_clear(self):
        # Conservative XY screening: entire low shrub envelope; tree root
        # envelope only, since elevated crown overhang is intentionally allowed.
        for item in self.layout['instances']:
            asset=item['assetId']
            if asset not in {'env_shrub_001','env_shrub_002','env_deciduous_tree_001','env_small_tree_001'}:continue
            if asset.startswith('env_shrub_'):
                dimensions=self.assets[asset]['dimensionsMeters']
                radius=math.hypot(dimensions[0],dimensions[2])/2*item['uniformScale']
            else:radius=.25*item['uniformScale']
            for route in self.layout['routes']:
                points=route['pointsSourceXYZ']
                distance=min(segment_distance(item['positionSourceXYZ'],a,b) for a,b in zip(points,points[1:]))
                self.assertGreaterEqual(distance+1e-6,radius+route['widthMeters']/2,item['instanceId'])
            self.assertFalse(any(inside(item['positionSourceXYZ'],f['boundsSourceXY'])
                                 for f in self.layout['buildingFootprints']),item['instanceId'])

    def test_tables_chairs_and_street_furniture_leave_route_clear(self):
        self.assertEqual(prop_route_conflicts(self.layout,self.locks['references']),[])

    def test_clearance_check_detects_a_table_blocking_cafe_approach(self):
        blocked=copy.deepcopy(self.layout)
        table=next(i for i in blocked['instances'] if i['assetId']=='prop_cafe_table_001')
        table['positionSourceXYZ']=[10,-6,.11]
        conflicts=prop_route_conflicts(blocked,self.locks['references'])
        self.assertTrue(any(c[0]==table['instanceId'] for c in conflicts),
            'A full-width table across the entry route must be rejected')

    def test_clearance_check_detects_original_crate_and_pot_intrusion(self):
        for asset in ('prop_wooden_crate_001','prop_flower_pot_002'):
            blocked=copy.deepcopy(self.layout)
            item=next(i for i in blocked['instances']
                      if i['assetId']==asset and i['group']=='walter.props')
            item['positionSourceXYZ'][0]=-10.38
            conflicts=prop_route_conflicts(blocked,self.locks['references'])
            self.assertTrue(any(c[0]==item['instanceId'] for c in conflicts),asset)

    def test_units_grade_and_camera_remain_explicit_proposals(self):
        c=self.layout['coordinateSystem']
        self.assertEqual(c['units'],'meters');self.assertEqual(c['sourceUp'],'+Z')
        self.assertEqual(c['glTFUp'],'+Y');self.assertIn('Open',c['unityImporterHandedness'])
        self.assertEqual(self.assets['env_ground_400_001']['expectedBounds']['max'][1],0)
        self.assertEqual(self.assets['env_road_600_001']['expectedBounds']['max'][1],.02)
        self.assertEqual(self.assets['env_sidewalk_200_001']['expectedBounds']['max'][1],.12)
        camera=self.layout['cameras']['game16m']
        self.assertEqual((camera['distanceMeters'],camera['pitchDegrees'],camera['verticalFovDegrees']),(16,50,40))
        self.assertIn('proxy',self.layout['cameras']['scope'].lower())
        self.assertFalse(self.layout['gameRepositoryChanged']);self.assertFalse(self.layout['mergeAuthorized'])
        self.assertEqual(load('modular-building.json')['roofSpanMeters'],6)


if __name__=='__main__':unittest.main()
