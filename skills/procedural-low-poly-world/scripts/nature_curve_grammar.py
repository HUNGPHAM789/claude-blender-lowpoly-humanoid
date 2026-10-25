"""Original low-poly nature tube reference; no third-party model data.
Run: python3 nature_curve_grammar.py --test
Output: Z-up meter-space vertices/faces; transform to glTF Y-up on export.
"""
import math
import random
import argparse

def bezier(points, t):
    if len(points) != 4: raise ValueError("Need four cubic control points")
    u = 1 - t
    return tuple(u**3*points[0][j] + 3*u*u*t*points[1][j] +
                 3*u*t*t*points[2][j] + t**3*points[3][j] for j in range(3))

def sub(a,b): return tuple(x-y for x,y in zip(a,b))
def add(a,b): return tuple(x+y for x,y in zip(a,b))
def scale(a,s): return tuple(x*s for x in a)
def dot(a,b): return sum(x*y for x,y in zip(a,b))
def cross(a,b): return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def norm(v):
    n=math.sqrt(dot(v,v))
    if n < 1e-10: raise ValueError("Degenerate vector")
    return scale(v,1/n)

def transport(prev, tangent):
    n=sub(prev,scale(tangent,dot(prev,tangent)))
    if dot(n,n)<1e-8:
        pick=(1.,0.,0.) if abs(tangent[0])<.8 else (0.,1.,0.)
        n=sub(pick,scale(tangent,dot(pick,tangent)))
    return norm(n)

def tube(points,base_radius=.4,tip_ratio=.23,root_flare=.28,sides=7,samples=11,cap=True):
    """Sweep faceted rings along cubic Bézier; coherent frames; closed caps."""
    if sides<3 or samples<2 or base_radius<=0 or not 0<tip_ratio<=1 or root_flare<0:
        raise ValueError("Invalid tube parameters")
    vertices=[]; faces=[]; prev_normal=(1.,0.,0.)
    for i in range(samples):
        t=i/(samples-1)
        c=bezier(points,t)
        delta=max(1e-5,1/(samples*500))
        tangent=norm(sub(bezier(points,min(1,t+delta)),bezier(points,max(0,t-delta))))
        normal=transport(prev_normal,tangent)
        binormal=norm(cross(tangent,normal))
        prev_normal=normal
        radius=base_radius*(1-t*(1-tip_ratio))*(1+root_flare*max(0,1-t/.18)**2)
        for k in range(sides):
            angle=2*math.pi*k/sides
            v=add(c,scale(add(scale(normal,math.cos(angle)),scale(binormal,math.sin(angle))),radius))
            vertices.append(v)
    for i in range(samples-1):
        for k in range(sides):
            a=i*sides+k; b=i*sides+(k+1)%sides
            d=(i+1)*sides+k; e=(i+1)*sides+(k+1)%sides
            faces.extend(((a,b,d),(b,e,d)))
    if cap:
        bottom=len(vertices); vertices.append(bezier(points,0))
        top=len(vertices); vertices.append(bezier(points,1))
        for k in range(sides):
            faces.append((bottom,(k+1)%sides,k))
            a=(samples-1)*sides+k; b=(samples-1)*sides+(k+1)%sides
            faces.append((top,a,b))
    return {"vertices":vertices,"triangles":faces,"rings":samples,"sides":sides}

def oak_trunk(seed=29,height=6.2,radius=.41):
    """Preserve silhouette family while changing curvature deterministically."""
    rng=random.Random(seed)
    angle=rng.uniform(0,2*math.pi)
    lean=rng.uniform(.07,.15)*height
    dx=math.cos(angle)*lean
    dy=math.sin(angle)*lean
    curve=[(0.,0.,0.),(dx*.12,dy*.25,height*.32),
           (dx*.87,dy*.62,height*.72),(dx,dy,height)]
    return tube(curve,base_radius=radius)

def validate(mesh):
    vertices=mesh["vertices"]; faces=mesh["triangles"]
    if any(not math.isfinite(v) for p in vertices for v in p): raise AssertionError("nonfinite coordinate")
    for a,b,c in faces:
        assert len({a,b,c})==3 and min(a,b,c)>=0 and max(a,b,c)<len(vertices)
        area=dot(cross(sub(vertices[b],vertices[a]),sub(vertices[c],vertices[a])),cross(sub(vertices[b],vertices[a]),sub(vertices[c],vertices[a])))
        assert area>1e-16,"zero area face"
    counts={}
    for a,b,c in faces:
        for p,q in ((a,b),(b,c),(c,a)):
            edge=tuple(sorted((p,q))); counts[edge]=counts.get(edge,0)+1
    assert all(count==2 for count in counts.values()),"non-manifold edge"
    return {"vertices":len(vertices),"triangles":len(faces),"edges":len(counts)}

def run_tests():
    first=oak_trunk(29)
    assert first==oak_trunk(29),"non-deterministic output"
    assert first!=oak_trunk(11),"seeds did not vary"
    metrics=validate(first)
    assert metrics["triangles"]<350
    centers=[tuple(sum(first["vertices"][i*7+k][j] for k in range(7))/7 for j in range(3))
             for i in range(first["rings"])]
    assert math.dist(centers[0][:2],centers[-1][:2])>.05*6.2,"curvature too small"
    # near each ring, radius tapers overall despite root flare
    radii=[math.dist(first["vertices"][i*7],centers[i]) for i in range(first["rings"])]
    assert radii[0]>radii[1]>radii[-1]>0
    print("PASS",metrics,"base radius",round(radii[0],3),"tip radius",round(radii[-1],3))
    return True

if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--test",action="store_true");args=parser.parse_args()
    if args.test:run_tests()
    else:print(validate(oak_trunk()))
