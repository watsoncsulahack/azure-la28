#!/usr/bin/env python3
"""Measure acquired evidence, and publish explicitly conditional geometry diagnostics.

This does not approve geographic registration or a physical acceptance tolerance.
County roof/courtyard boundaries and airborne returns are not accessible-route surveys.
"""
import csv
import json
import math
import os
from pathlib import Path
import numpy as np
from pyproj import Transformer
from scipy.stats import binned_statistic_2d
from shapely.geometry import shape
import shapely
import rasterio

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
OUT = REPO/'analysis/coliseum-model/evidence-iteration'
os.environ.setdefault('MPLCONFIGDIR', str(REPO/'work/matplotlib'))
os.environ.setdefault('XDG_CACHE_HOME', str(REPO/'work/cache'))


def dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, allow_nan=False)+'\n')


def stats(values):
    values = np.asarray(values)
    values = values[np.isfinite(values)]
    if not len(values):
        return {'count': 0, 'status': 'UNOBSERVED'}
    return {'count': len(values), 'mean_m': float(np.mean(values)), 'rmse_m': float(np.sqrt(np.mean(values**2))),
            'median_signed_m': float(np.median(values)), 'median_absolute_m': float(np.median(abs(values))),
            'p95_absolute_m': float(np.percentile(abs(values),95)), 'maximum_absolute_m': float(np.max(abs(values))),
            'min_signed_m': float(values.min()), 'max_signed_m': float(values.max())}


def rectangle_axes(poly):
    rect = np.array(poly.minimum_rotated_rectangle.exterior.coords)[:4]
    edges = np.roll(rect,-1,axis=0)-rect
    i = np.argmax(np.linalg.norm(edges,axis=1))
    direction = edges[i]/np.linalg.norm(edges[i])
    if direction[0] < 0:
        direction *= -1
    return rect.mean(axis=0), math.atan2(direction[1],direction[0]), sorted(np.linalg.norm(edges,axis=1).tolist())[::2]


def main():
    spec = json.loads((REPO/'apps/coliseum-mvp/dist/data/venue.json').read_text())
    p = spec['parameters']
    fc = json.loads((ROOT/'derived/buildings.geojson').read_text())
    to_utm = Transformer.from_crs(4326,6340,always_xy=True)
    polys = {int(f['properties']['OBJECTID']): shapely.transform(shape(f['geometry']),to_utm.transform,interleaved=False) for f in fc['features']}
    stadium, courtyard = polys[1325059], polys[1282840]
    origin, angle, dims = rectangle_axes(courtyard)
    co, si = math.cos(angle), math.sin(angle)
    R = np.array([[co,-si],[si,co]])
    raw = np.load(ROOT/'derived/lidar-aoi.npz')['points']
    tx = Transformer.from_crs(3857,6340,always_xy=True)
    ex, ny = tx.transform(raw[:,0], raw[:,1])
    xy = np.column_stack((ex,ny))
    local = (xy-origin) @ R
    z = raw[:,2]
    usable = np.isin(raw[:,3],[1,2])&(raw[:,5]==0)&((raw[:,6].astype(int)&4)==0)
    # Align vertical translation with one half of a small field-interior patch only.
    # Validation uses the other half; these are not independent horizontal control points.
    patch = (abs(local[:,0])<35)&(abs(local[:,1])<12)&usable&(raw[:,4]==1)
    calibration = patch & (local[:,0]<0)
    holdout = patch & (local[:,0]>=0)
    z0 = float(np.median(z[calibration]))
    lon,lat = Transformer.from_crs(6340,4326,always_xy=True).transform(*origin)
    # CAD [x,north,z_up] and Three.js [x,up,south] mappings kept explicit.
    matrix = [[co,0,si,float(origin[0])],[si,0,-co,float(origin[1])],[0,1,0,z0],[0,0,0,1]]
    alignment = {'status':'PROVISIONAL_DIAGNOSTIC_ONLY', 'approved_for_model':False,
      'horizontal_crs':'EPSG:6340 NAD83(2011) / UTM zone 11N',
      'vertical_reference':'EPT Z presumed unchanged NAVD88/GEOID18 from original project; native check recorded separately.',
      'horizontal_method':'Center and major axis of minimum rotated rectangle of county courtyard OBJECTID 1282840. 2008 stereo-derived boundary; correspondence to current chosen model origin is unverified.',
      'vertical_method':'Median usable first-return Z in west half of local field-interior box (x −35 to 0 m; north −12 to 12 m). East half withheld. These field returns are class 1, not class 2. No height-based rejection.',
      'origin_epsg6340_m':origin.tolist(), 'origin_lon_lat_approx':[lon,lat],
      'grid_rotation_radians':angle, 'grid_rotation_degrees':math.degrees(angle),
      'grid_rotation_is_true_bearing':False,'field_reference_z_m':z0,
      'horizontal_transform_operation':tx.description,
      'horizontal_transform_nominal_accuracy_m':tx.accuracy,
      'datum_limit':'PROJ operation reports 2 m nominal accuracy for EPT/WGS84 to NAD83(2011). This is not site-measured uncertainty. No vertical coordinate transformation performed.',
      'scale':1, 'threejs_to_utm_matrix_row_major':matrix,
      'cad_to_utm':'E=E0+cos(theta)*x-sin(theta)*y; N=N0+sin(theta)*x+cos(theta)*y; H=H0+z',
      'uncertainty':{'horizontal_m':None,'vertical_registration_m':None,'model_origin_correspondence_m':None},
      'required_control':'Current surveyed field corners/centerline, perimeter points and a NAVD88 benchmark, with withheld controls. No accepted external site control available.'}
    dump(ROOT/'reports/candidate-registration.json',alignment)
    # Raster observations are medians of first returns, 1 m square cells in projected CRS.
    select = usable & (raw[:,4]==1) & (abs(local[:,0])<190)&(abs(local[:,1])<145)
    edgesx,edgesy = np.arange(-190,191),np.arange(-145,146)
    surface = binned_statistic_2d(local[select,0],local[select,1],z[select],statistic='median',bins=[edgesx,edgesy]).statistic
    counts = np.histogram2d(local[select,0],local[select,1],bins=[edgesx,edgesy])[0]
    xx,yy = np.meshgrid((edgesx[1:]+edgesx[:-1])/2,(edgesy[1:]+edgesy[:-1])/2,indexing='ij')
    observed = counts>=3
    a = p['innerBowlLength']/2; b = p['innerBowlWidth']/2
    ar = p['bowlLength']/2-3.8; br = p['bowlWidth']/2-3.8
    lo,hi = np.zeros_like(xx),np.ones_like(xx)
    for _ in range(45):
        t = (lo+hi)/2
        outside = (xx/(a+(ar-a)*t))**2+(yy/(b+(br-b)*t))**2>1
        lo = np.where(outside,t,lo);hi=np.where(outside,hi,t)
    t=(lo+hi)/2
    az = np.mod(np.arctan2(-yy/(b+(br-b)*t),xx/(a+(ar-a)*t)),2*np.pi)
    bowl = ((xx/a)**2+(yy/b)**2>=1)&((xx/ar)**2+(yy/br)**2<=1)
    bowl &= np.cos(az)<=np.cos(p['peristyleOpeningHalfAngle'])
    bowl &= ~((t>.36)&(az>1)&(az<2.14))
    model_height = np.ceil(t*p['visualRows'])/p['visualRows']*p['rimHeight']
    residual = surface-z0-model_height
    sampled = bowl&observed
    classes, number = np.unique(raw[:,3],return_counts=True)
    inside_stadium = shapely.contains_xy(stadium,ex,ny)
    metrics = {'source':'USGS CA_LosAngeles_1_B23 EPT all-depth AOI extraction',
      'aoi_points_all_returns_including_noise':len(raw),
      'classification_counts':dict(zip(map(lambda c:str(int(c)),classes),map(int,number))),
      'withheld_points_excluded':int((raw[:,5]!=0).sum()),
      'classification_assessment':'Only classes 1,2,7,18 occur here. Roofs, seats, walls and vegetation are not semantically classified. Local classification accuracy not independently measured.',
      'stadium_reference_polygon_objectid':1325059,'stadium_reference_vintage':2008,
      'stadium_polygon_area_m2':float(stadium.area),
      'stadium_all_return_points':int(inside_stadium.sum()),
      'stadium_all_return_density_per_m2':float(inside_stadium.sum()/stadium.area),
      'stadium_usable_first_return_density_per_m2':float((inside_stadium&usable&(raw[:,4]==1)).sum()/stadium.area),
      'field_calibration_points':int(calibration.sum()),
      'field_holdout_vertical_residual_m':stats(z[holdout]-z0),
      'field_holdout_scope':'Usable first returns in east interior half-box (class 1, unclassified); conditional on presumed EPT vertical datum and candidate pose. No height-based rejection. Not an independent absolute-elevation check or full field-shape validation.',
      'bowl_conditional_vertical_residual_m':stats(residual[sampled]),
      'bowl_grid_cells':int(bowl.sum()),'bowl_observed_cells_at_least_3_first_returns':int(sampled.sum()),
      'bowl_missing_cells':int((bowl&~observed).sum()),
      'bowl_observed_fraction':float(sampled.sum()/bowl.sum()),
      'bowl_metric_scope':'Observed first-return cell median minus generated terrace top at cell center; vertical difference only, not nearest point-to-mesh/3D positional error. Returns may hit seats/people/fixtures. Candidate horizontal pose not accepted. No geometry acceptance decision.',
      'occlusion':'2D occupancy does not observe under-stand interiors, door clearances, stair risers or hidden surfaces. An occupied cell is not complete 3D coverage.',
      'independent_physical_acceptance_checks':0,'ready_for_accessibility_or_crowd_simulation':False}
    dump(ROOT/'reports/independent-diagnostics.json',metrics)
    # Preserve explicit missing-observation masks; never interpolate holes for validation.
    np.savez_compressed(ROOT/'derived/coverage-and-residuals.npz',x_edges=edgesx,y_edges=edgesy,
        first_return_counts=counts,observed=observed,bowl_mask=bowl,median_source_z=surface,
        bowl_vertical_residual_m=np.where(sampled,residual,np.nan))
    # County data chronology and boundary diagnostics, without asserting a field match.
    from collections import Counter
    county = {'feature_count':len(fc['features']), 'vintage_counts':dict(Counter(f['properties']['DATE_'] for f in fc['features'])),
      'code_counts':dict(Counter(f['properties']['CODE'] for f in fc['features'])),
      'stadium':{'objectid':1325059,'properties':next(f['properties']for f in fc['features']if f['properties']['OBJECTID']==1325059),
        'bounds_epsg6340':list(stadium.bounds),'projected_polygon_area_m2':float(stadium.area),'interior_rings':len(stadium.interiors),
        'limitation':'Stadium record DATE_=2008 SOURCE=LARIAC2 STATUS=Unchanged. Does not certify the post-2019 tower or current bowl boundary.'},
      'courtyard':{'objectid':1282840,'area_m2':float(courtyard.area),'mrr_spans_m':dims,
        'difference_from_guide_area_m2':float(courtyard.area-135837*.3048**2),
        'boundary_equivalence_to_2024_playing_field':False,'boundary_equivalence_to_model_field':False},
      'height_and_elevation_units':'Unverified in retrieved service field metadata. Values retained without conversion or use as control.',
      'outline_interpretation':'Item describes stereo imagery roof-line capture; polygons are not automatically wall footprints.'}
    dump(ROOT/'reports/building-assessment.json',county)
    # DEM comparison at held-out field points is same-survey consistency, not independent.
    with rasterio.open(ROOT/'derived/dem-aoi.tif') as src:
        demxy=Transformer.from_crs(6340,src.crs,always_xy=True).transform(ex[holdout][::30],ny[holdout][::30])
        values=np.array([v[0]for v in src.sample(zip(*demxy))]);valid=values!=src.nodata
        exterior=usable&(raw[:,3]==2)&(raw[:,4]==1)&~shapely.contains_xy(shapely.Polygon(stadium.exterior),ex,ny)
        ix=np.flatnonzero(exterior)[::500]
        dex,dny=Transformer.from_crs(6340,src.crs,always_xy=True).transform(ex[ix],ny[ix])
        dv=np.array([v[0]for v in src.sample(zip(dex,dny))]);ok=dv!=src.nodata
        demreport={'resolution_m':list(src.res),'crs':str(src.crs),'same_survey_as_lidar':True,
          'field_dem_minus_lidar_m':stats(values[valid]-z[holdout][::30][valid]),
          'exterior_class2_dem_minus_lidar_m':stats(dv[ok]-z[ix][ok]),
          'field_status':'DO_NOT_USE_DEM_AS_FIELD_ELEVATION_CONTROL',
          'interpretation':'A large field-only difference can result from ground-class exclusion and bare-earth interpolation across the stadium excavation. This is an engineering inference, not a verified production-history explanation. Do not apply a global vertical offset from the field residual.',
          'scope':'Nearest DEM cells at field patch and exterior class-2 first returns. This checks derivative consistency only.',
          'not_suitable_for':'Bare-earth interpolation cannot supply seats, ramps, concourses, curb edges, treads or under-stand floors.'}
    dump(ROOT/'reports/dem-assessment.json',demreport)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(13,5),constrained_layout=True)
    extent=[edgesx[0],edgesx[-1],edgesy[0],edgesy[-1]]
    im=axes[0].imshow(np.where(observed,surface-z0,np.nan).T,origin='lower',extent=extent,cmap='terrain',vmin=0,vmax=52)
    axes[0].set_title('Observed surface: 1 m first-return medians')
    fig.colorbar(im,ax=axes[0],label='Source Z minus fitted field reference (m)')
    im=axes[1].imshow(np.where(sampled,residual,np.nan).T,origin='lower',extent=extent,cmap='RdBu_r',vmin=-10,vmax=10)
    axes[1].set_title('Bowl vertical residual; candidate pose only')
    fig.colorbar(im,ax=axes[1],label='Observed minus generated terrace height (m)')
    for ax in axes:
        ax.set(xlabel='Candidate local X (m)',ylabel='Candidate local north (m)',aspect='equal');ax.set_facecolor('#dddddd')
    fig.savefig(ROOT/'reports/surface-diagnostics.png',dpi=160)
    print(json.dumps({'points':len(raw),'field_holdout':metrics['field_holdout_vertical_residual_m'],
      'bowl_conditional':metrics['bowl_conditional_vertical_residual_m'],'observed_fraction':metrics['bowl_observed_fraction']},indent=2))


if __name__=='__main__':
    main()
