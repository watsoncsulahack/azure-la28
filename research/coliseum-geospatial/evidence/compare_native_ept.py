"""Check two distributions of the same survey; this is not venue-accuracy validation."""
from pathlib import Path
import json
import numpy as np
from pyproj import CRS,Transformer
from scipy.spatial import cKDTree
import acquire

ROOT=Path(__file__).resolve().parent


def stats(v):
    v=np.asarray(v)
    return {'count':len(v),'rmse_m':float(np.sqrt(np.mean(v*v))),
        'median_signed_m':float(np.median(v)),'median_absolute_m':float(np.median(abs(v))),
        'p95_absolute_m':float(np.percentile(abs(v),95)),'maximum_absolute_m':float(np.max(abs(v)))}


def main():
    info=json.loads((ROOT/'reports/native-extraction.json').read_text())
    systems=[CRS.from_wkt(t['crs_wkt'])for t in info['tiles']]
    horizontal=[c.sub_crs_list[0]if c.is_compound else c for c in systems]
    if not all(c.equals(horizontal[0])for c in horizontal):
        raise ValueError('Native tiles use different horizontal reference systems')
    native=np.load(ROOT/'derived/native-aoi.npz')['points']
    ept=np.load(ROOT/'derived/lidar-aoi.npz')['points']
    rng=np.random.default_rng(699)
    pool=rng.choice(len(native),size=min(len(native),100000),replace=False)
    good=np.isin(native[pool,3],[1,2])&(native[pool,6]==0)
    ids=pool[good][:50000]
    if not len(ids):raise ValueError('No usable native sample points')
    transform=Transformer.from_crs(3857,horizontal[0],always_xy=True)
    x,y=transform.transform(ept[:,0],ept[:,1])
    comparison=np.column_stack((x,y,ept[:,2]))
    tree=cKDTree(comparison)
    distance,index=tree.query(native[ids,:3],workers=2)
    difference=native[ids,:3]-comparison[index]
    report={'purpose':'Encoding/distribution consistency for the same USGS acquisition; not independent physical validation of survey or model.',
        'native_aoi_points':len(native),'ept_aoi_points':len(ept),'sample_seed':699,'sample_points':len(ids),
        'sample_scope':'Uniform random native AOI points, classes 1/2, withheld excluded. At most 50,000; all EPT points used for 3D nearest-neighbor association.',
        'horizontal_crs':horizontal[0].to_string(),'ept_to_native_operation':transform.description,
        'operation_nominal_accuracy_m':transform.accuracy,'vertical_coordinate_transform_applied':False,
        'nearest_3d_distance_m':stats(distance),
        'horizontal_distance_m':stats(np.hypot(difference[:,0],difference[:,1])),
        'native_minus_ept_z_m':stats(difference[:,2]),
        'within_0_02m_fraction':float(np.mean(distance<=.02)),
        'within_0_05m_fraction':float(np.mean(distance<=.05)),
        'comparison_threshold_scope':'0.02/0.05 m describe correspondence at source coordinate quantization; they are not feature acceptance tolerances.',
        'classification_equal_fraction':float(np.mean(native[ids,3]==ept[index,3])),
        'physical_accuracy_verified':False,'geographic_model_registration_approved':False,
        'limitations':['Same underlying acquisition is not independent validation.',
            'Nearest coordinates are inferred point associations; not source point-ID matches.',
            'Absolute horizontal/vertical survey accuracy and model-origin correspondence remain separate.']}
    # Investigate count differences where source quantization can change crop inclusion.
    bounds=json.loads((ROOT/'reports/lidar-selection.json').read_text())['crop_native']
    nx,ny=Transformer.from_crs(horizontal[0],3857,always_xy=True).transform(native[:,0],native[:,1])
    def near(x,y,width):
        w,s,e,n=bounds
        return (abs(x-w)<width)|(abs(x-e)<width)|(abs(y-s)<width)|(abs(y-n)<width)
    ni=np.flatnonzero(near(nx,ny,.1));ei=np.flatnonzero(near(ept[:,0],ept[:,1],.1))
    native_candidates=np.flatnonzero(near(nx,ny,.2))
    forward,_=tree.query(native[ni,:3],workers=2)
    reverse,_=cKDTree(native[native_candidates,:3]).query(comparison[ei],workers=2)
    missing_native=int(np.sum(forward>.02));missing_ept=int(np.sum(reverse>.02))
    report['crop_boundary_check']={'band_width_projected_m':.1,'matching_distance_m':.02,
        'native_boundary_points_checked':len(ni),'ept_boundary_points_checked':len(ei),
        'native_points_without_ept_match':missing_native,'ept_points_without_native_match':missing_ept,
        'net_unmatched_native_minus_ept':missing_native-missing_ept,
        'total_count_native_minus_ept':len(native)-len(ept),
        'interpretation':'Near-boundary nearest-coordinate associations check whether crop/quantization differences account for the count delta. Source point IDs are not available in the derived arrays.'}
    acquire.dump(ROOT/'reports/native-ept-consistency.json',report)
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
