#!/usr/bin/env python3
"""Original LPM primal stone axe, faceted procedural mesh from composition study.

Authoring frame (meters): +Z handle from butt to head; +X chopping side;
+Y front/back. Origin: grip center. Export GLB in Y-up, handle = +Y.
No external meshes or textures are imported.
"""
import json, math, argparse
from pathlib import Path
import numpy as np
import trimesh
from scipy.spatial import ConvexHull

PARTS=[]
COLORS={
 'WOOD':(201,154,93,255),'WOOD_DARK':(166,118,66,255),
 'OBSIDIAN':(58,60,63,255),'OBSIDIAN_HILITE':(90,94,97,255),
 'LEATHER':(96,63,49,255),'LEATHER_LIGHT':(124,81,61,255),
 'BONE':(220,203,166,255),'BONE_DARK':(176,157,120,255)
}

def add_part(name, v, faces, material, face_colors=None):
    v=np.asarray(v,float); f=np.asarray(faces,int)
    m=trimesh.Trimesh(vertices=v,faces=f,process=False)
    m.fix_normals()
    if face_colors is None:
        m.visual.face_colors=np.repeat(np.array([COLORS[material]],dtype=np.uint8),len(f),axis=0)
    else:
        m.visual.face_colors=np.asarray(face_colors,np.uint8)
    PARTS.append((name,material,m))
    return m

def sweep_handle():
    # 0.94m curved tapered haft; center near origin is gripped by LPM tool socket
    pts=np.array([[-.016,0,-.425],[-.011,0,-.285],[-.004,0,-.090],[.003,0,.000],[.010,0,.120],
                  [.014,0,.260],[.016,0,.385],[.012,0,.600]],float)
    radius=np.array([.020,.024,.021,.016,.022,.036,.044,.030])
    sides=9; V=[];F=[]; FC=[]
    for i,p in enumerate(pts):
        tangent=pts[min(i+1,len(pts)-1)]-pts[max(i-1,0)]
        tangent/=np.linalg.norm(tangent)
        a=np.array([0.,1.,0.]); a-=np.dot(a,tangent)*tangent; a/=np.linalg.norm(a)
        b=np.cross(tangent,a)
        for k in range(sides):
            theta=(k+.15)*2*math.pi/sides
            ellipse=1.0+0.055*math.sin(3*theta+i*.52)
            V.append(p+radius[i]*ellipse*(a*math.cos(theta)+b*.84*math.sin(theta)))
    for i in range(len(pts)-1):
      for k in range(sides):
        a=i*sides+k;b=i*sides+(k+1)%sides;c=(i+1)*sides+k;d=(i+1)*sides+(k+1)%sides
        F.extend([[a,c,d],[a,d,b]])
        color=COLORS['WOOD_DARK'] if (k+2*i)%9==0 else COLORS['WOOD']
        FC.extend([color,color])
    V.append(pts[0]);bottom=len(V)-1;V.append(pts[-1]);top=len(V)-1
    for k in range(sides):
        F.append([bottom,k,(k+1)%sides]);FC.append(COLORS['WOOD'])
        base=(len(pts)-1)*sides;F.append([top,base+(k+1)%sides,base+k]);FC.append(COLORS['WOOD'])
    return add_part('WOOD_CURVED_SHAFT',V,F,'WOOD',FC)

def axe_head(variant="stone"):
    # Asymmetric faceted stone blade. Rear mass shorter, chopping side +X.
    outline=np.array([
      [-.135,.465],[-.155,.417],[-.154,.359],[-.110,.304],[-.035,.289],
      [.087,.302],[.192,.293],[.345,.260],[.405,.286],[.432,.366],
      [.435,.470],[.408,.529],[.345,.550],[.251,.518],[.128,.515],[-.010,.505]
    ],float)
    # Normalized silhouette study: head/overall-height ~0.43, vs image reference ~0.43.
    outline[:,0]=.016+(outline[:,0]-.016)*.74
    center=np.mean(outline,axis=0); n=len(outline)
    V=[]
    # bevel ring outside, two inset face rings and two center points. thickness tapers toward sharpened edge.
    for side in [-1,1]:
      for inner in [0,1]:
        for i,(x,z) in enumerate(outline):
          at_edge=np.clip((x-.26)/.20,0,1)
          depth=(.045*(1-.78*at_edge))*(.56 if inner==0 else 1.0)
          p=center+(np.array([x,z])-center)*(.81 if inner else 1)
          V.append([p[0],side*(depth +(.004*np.sin(i*2.3) if inner else 0)),p[1]])
    V.extend([[center[0],-.061,center[1]],[center[0],+.061,center[1]]])
    # Stone seats BEHIND the handle; front wood/X binding remains visible.
    V=[[x,y+.070,z] for x,y,z in V]
    F=[];FC=[]
    bone = (variant == 'bone')
    for sideIndex in range(2):
      base=sideIndex*2*n; internal=base+n
      # annular faceted chamfer
      for i in range(n):
        k=(i+1)%n
        for f in ([base+i,internal+i,internal+k],[base+i,internal+k,base+k]):
          F.append(f);FC.append((181+(i*19)%33,168+(i*17)%28,132+(i*13)%29,255) if bone else (66+(i*19)%27,69+(i*17)%25,73+(i*13)%22,255))
      c=4*n+sideIndex
      for i in range(n):
        F.append([internal+i,c,internal+(i+1)%n]);v=58+((i*7+sideIndex*11)%26)
        FC.append((194+(i*7)%32,180+(i*9)%30,145+(i*5)%25,255) if bone else (v,v+1,v+3,255))
    for i in range(n):
      F.extend([[i,(i+1)%n,2*n+(i+1)%n],[i,2*n+(i+1)%n,2*n+i]])
      FC.extend([COLORS['BONE_DARK'] if bone else COLORS['OBSIDIAN']]*2)
    return add_part('BONE_CHIPPED_HEAD' if bone else 'STONE_CHIPPED_BLADE',V,F,'BONE' if bone else 'OBSIDIAN',FC)

def band_polyline(name,points,width=.029,depth=.005,material='LEATHER'):
    """Small segmented ribbon with volume; each element a closed convex hull of 8 corners.
    Local normal = +/-Y; compatible with robust flat-shaded lashing."""
    for i,(a,b) in enumerate(zip(points[:-1],points[1:])):
        a=np.array(a,float);b=np.array(b,float)
        v=b-a;v=v/np.linalg.norm(v)
        n=np.array([0.,1.,0.]);n-=np.dot(n,v)*v;n/=np.linalg.norm(n)
        side=np.cross(v,n);side/=np.linalg.norm(side)
        corners=[p+s*width*.5*side+d*depth*.5*n for p in [a,b] for s in [-1,1] for d in [-1,1]]
        hull=ConvexHull(corners)
        add_part(f'{name}_{i:02d}',corners,hull.simplices,material)

def lashing():
    # Wide X straps across the exposed shaft; darker than wood and blade.
    # Stone front is y=-.045 and back +.045; leather stands slightly above it.
    for sign,sideName in [(-1,'FRONT'),(1,'BACK')]:
      y=-.087 if sign==-1 else .142
      band_polyline(f'X_LASH_{sideName}_A', [(-.029,y,.477),(.006,y,.405),(.039,y,.326)],.031,.006,'LEATHER')
      band_polyline(f'X_LASH_{sideName}_B', [(.039,y,.477),(.008,y,.404),(-.026,y,.320)],.031,.006,'LEATHER_LIGHT')
    # Circumferential bands and diagonal winding around the bent haft.
    for step,(z,h) in enumerate([(.495,.025),(.283,.03),(.245,.028),(.202,.027)]):
      center=np.array([.016 if z>.25 else .012,0,z])
      radius=.052 if z>.28 else (.043 if z>.24 else .034)
      pts=[]
      for k in range(13):
        a=2*math.pi*k/12
        pts.append(center+[radius*math.cos(a),radius*.78*math.sin(a),h*(k/12-.5)])
      band_polyline(f'WRAP_{step}',pts,.025,.005,'LEATHER' if step%2==0 else 'LEATHER_LIGHT')

def validate_and_export(out,variant="stone"):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    R=trimesh.transformations.rotation_matrix(-math.pi/2,[1,0,0])  # authoring Z-up -> glTF Y-up
    scene=trimesh.Scene();reports=[];materials={}
    for name,material,mesh in PARTS:
        assert mesh.is_watertight,f'{name}: mesh not closed'
        assert len(mesh.faces)<700,f'{name}: unexpected mesh budget'
        assert np.isfinite(mesh.vertices).all()
        assert np.isfinite(mesh.area) and mesh.area>0
        # Put geometry in Y-up scene for browser Three.js; +X unchanged.
        render_mesh=mesh.copy();render_mesh.apply_transform(R)
        materials.setdefault(material,[]).append(render_mesh)
        bounds=mesh.bounds.round(5).tolist()
        reports.append({'name':name,'material':material,'vertices':len(mesh.vertices),
                        'triangles':len(mesh.faces),'watertight':bool(mesh.is_watertight),'bounds_authoring_Zup_m':bounds})
    for material, meshes in materials.items():
        # One draw-call group per material; individual watertight pieces are already audited.
        batched=trimesh.util.concatenate(meshes)
        scene.add_geometry(batched,node_name=f'BATCH_{material}',geom_name=f'BATCH_{material}')
    glb=scene.export(file_type='glb')
    base='primal_bone_axe' if variant=='bone' else 'primal_stone_axe'
    (out/f'{base}.glb').write_bytes(glb)
    # Combine all parts into single OBJ for Blender import (trimesh scene export).
    (out/f'{base}.obj').write_text(scene.export(file_type='obj'),encoding='utf8')
    meta={'asset':'LPM.PrimalBoneAxe.v1' if variant=='bone' else 'LPM.PrimalStoneAxe.v1','design':'Original low-poly reconstruction based on user-supplied visual reference',
     'source_policies':'No third-party mesh used; geometry procedural',
     'reference':'user supplied stone axe image, handle wooden curved, dark chipped stone, X leather lashing',
     'variant':variant,'version':'1.0.0','unit':'meter','authoring_axes':'Z up, X blade, Y front','glb_axes':'Y up, X blade, -Z front',
     'socket_compatibility':{'LPM_socket':'SOCKET_cam_L/R','handle_radius_at_grip_m':.016,
         'grip_authoring_Zup_m':[0,0,0],'grip_export_Yup_m':[0,0,0],
         'length_axis_authoring':[0,0,1],'length_axis_GLTF':[0,1,0],
         'attach':'align exported local +Y with socket len, +X chopping side away from body'},
     'gameplay':{'job':'woodcutter','requires_tool':True,'durability_max':55,'durability_loss_per_chop':1,
       'rack_slots_per_type_starter':2,'on_zero':'destroy_and_release_job_and_tool_reservation'},
     'parts':reports,'total_triangles':sum(p['triangles'] for p in reports),'render_batches':len(materials),
     'image_comparison_status':'silhouette and materials analyzed visually; no original 3D mesh available',
     'measured_limits':{'triangles_max':3000,'watertight_per_component':True}}
    (out/f'{base}.json').write_text(json.dumps(meta,indent=2,ensure_ascii=False),encoding='utf8')
    assert meta['total_triangles']<=3000,f'Triangle budget {meta["total_triangles"]}'
    print(json.dumps({'exported':str(out),'triangles':meta['total_triangles'],'parts':len(reports),'render_batches':len(materials),
         'glb_bytes':len(glb)},ensure_ascii=False))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--out',default='out/primal_axe');
    a.add_argument('--variant',choices=['stone','bone','both'],default='both');args=a.parse_args()
    for variant in (['stone','bone'] if args.variant=='both' else [args.variant]):
        PARTS.clear()
        sweep_handle();axe_head(variant);lashing();validate_and_export(args.out,variant)