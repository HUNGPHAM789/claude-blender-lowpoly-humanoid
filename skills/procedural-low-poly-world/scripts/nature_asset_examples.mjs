/** Original LPM nature example factory, geometry authored without CGTrader model data.
 * Three.js Y-up, meters, pivot root near ground. Rendering adapter uses THREE namespace.
 * Demo asset variants cover ALL publicly listed CGTrader nature pack categories;
 * they are independent examples, NOT one-to-one geometric reproductions.
 * Usage: import {makeAsset,toThree,audit,catalogue,grouping} from './nature_asset_examples.mjs';
 * const oak = toThree(THREE,makeAsset('tree',0,29)); scene.add(oak);
 * For distant scenery use instancing and LOD; toThree is a simple correctness demo.
 */

function rng(seed){let x=(seed|0)||1234567;return function(){x^=x<<13;x^=x>>>17;x^=x<<5;return (x>>>0)/4294967296;};}

function add(a,b){return [a[0]+b[0],a[1]+b[1],a[2]+b[2]];}

function sub(a,b){return [a[0]-b[0],a[1]-b[1],a[2]-b[2]];}

function mul(a,k){return [a[0]*k,a[1]*k,a[2]*k];}

function dot(a,b){return a[0]*b[0]+a[1]*b[1]+a[2]*b[2];}

function cross(a,b){return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];}

function norm(a){const d=Math.sqrt(dot(a,a));if(d<1e-9)throw Error("zero tangent");return mul(a,1/d);}

function lerp(a,b,t){return add(mul(a,1-t),mul(b,t));}

function bezier(p,t){const s=1-t;return [0,1,2].map(j=>s*s*s*p[0][j]+3*s*s*t*p[1][j]+3*s*t*t*p[2][j]+t*t*t*p[3][j]);}

function mesh(){return {triangles:[],materials:[]};}

function face(m,a,b,c,material){m.triangles.push([a,b,c]);m.materials.push(material);}

function quad(m,a,b,c,d,mat){face(m,a,b,c,mat);face(m,a,c,d,mat);}

function tube(m,path,radii,sides,mat){if(path.length<2||path.length!==radii.length||sides<3)throw Error("invalid tube");let prev=[1,0,0],rings=[];for(let i=0;i<path.length;i++){const tangent=norm(sub(path[Math.min(i+1,path.length-1)],path[Math.max(i-1,0)]));let u=sub(prev,mul(tangent,dot(prev,tangent)));if(dot(u,u)<1e-6){let guide=Math.abs(tangent[0])<.8?[1,0,0]:[0,0,1];u=sub(guide,mul(tangent,dot(guide,tangent)));}u=norm(u);const v=norm(cross(tangent,u));prev=u;const ring=[];for(let k=0;k<sides;k++){const a=Math.PI*2*k/sides;ring.push(add(path[i],mul(add(mul(u,Math.cos(a)),mul(v,Math.sin(a))),radii[i])));}rings.push(ring);}for(let i=0;i<rings.length-1;i++)for(let j=0;j<sides;j++){let k=(j+1)%sides;quad(m,rings[i][j],rings[i][k],rings[i+1][k],rings[i+1][j],mat);}for(let k=1;k<sides-1;k++){face(m,path[0],rings[0][k+1],rings[0][k],mat);face(m,path[path.length-1],rings[rings.length-1][k],rings[rings.length-1][k+1],mat);}return m;}

function curveTube(m,control,r0,r1,segments,sides,mat,flare=0){const path=[],radii=[];for(let i=0;i<=segments;i++){const t=i/segments;path.push(bezier(control,t));radii.push((r0*(1-t)+r1*t)*(1+flare*Math.max(0,1-t/.2)**2));}tube(m,path,radii,sides,mat);return path;}

function blob(m,center,rx,ry,rz,mat,seed=1,sides=7){const R=rng(seed),ring=[],bands=[-.68,.08,.64];for(let j=0;j<3;j++){const rr=j===1?1:.74;ring[j]=[];for(let k=0;k<sides;k++){const a=k*Math.PI*2/sides,fl=.88+.24*R();ring[j].push([center[0]+rx*rr*Math.cos(a)*fl,center[1]+ry*bands[j],center[2]+rz*rr*Math.sin(a)*fl]);}}for(let j=0;j<2;j++)for(let k=0;k<sides;k++)quad(m,ring[j][k],ring[j][(k+1)%sides],ring[j+1][(k+1)%sides],ring[j+1][k],mat);const bot=add(center,[0,-ry,0]),top=add(center,[0,ry,0]);for(let k=0;k<sides;k++){face(m,bot,ring[0][(k+1)%sides],ring[0][k],mat);face(m,top,ring[2][k],ring[2][(k+1)%sides],mat);}return m;}

function leaf(m,root,tip,width,mat){const dir=norm(sub(tip,root)),side=norm(cross(dir,Math.abs(dir[1])<.9?[0,1,0]:[0,0,1]));const mid=lerp(root,tip,.52);const lift=add(mid,[0,Math.min(.10,width*.45),0]);face(m,root,add(lift,mul(side,width)),tip,mat);face(m,root,tip,sub(lift,mul(side,width)),mat);}

function box(m,c,half,mat){const [x,y,z]=c,[a,b,d]=half;const v=[[x-a,y-b,z-d],[x+a,y-b,z-d],[x+a,y+b,z-d],[x-a,y+b,z-d],[x-a,y-b,z+d],[x+a,y-b,z+d],[x+a,y+b,z+d],[x-a,y+b,z+d]];for(const [i,j,k,l] of [[0,1,2,3],[4,7,6,5],[0,4,5,1],[3,2,6,7],[0,3,7,4],[1,5,6,2]])quad(m,v[i],v[j],v[k],v[l],mat);}

function makeTree(variant=0,seed=1){const m=mesh(),R=rng(seed+101*variant),kind=variant%6;const H=[6.2,7.1,5.7,6.0,5.3,2.8][kind],base=[.39,.24,.25,.42,.28,.14][kind];const theta=2*Math.PI*R(),lean=(kind===4?.19:.09+.09*R())*H;const tip=[Math.cos(theta)*lean,H,Math.sin(theta)*lean];const p=[[0,0,0],[tip[0]*.16,H*.28,tip[2]*.14],[tip[0]*.92,H*.74,tip[2]*.8],tip];curveTube(m,p,base,base*.19,10,7,kind===2?"birch":"bark",.25);const count=kind===1?6:kind===4?5:kind===5?2:4;for(let k=0;k<count;k++){const t=.4+k*.105+R()*.055,origin=bezier(p,Math.min(.94,t)),a=k*2.39996+R()*.35,length=(kind===4?1.7:kind===1?1.25:2.0)*(.75+.4*R())*(kind===5?.5:1);const end=add(origin,[Math.cos(a)*length,.48+.5*R(),Math.sin(a)*length]);const c=[origin,add(origin,[Math.cos(a)*length*.25,.2,Math.sin(a)*length*.25]),lerp(origin,end,.67),end];curveTube(m,c,base*.32,base*.055,4,5,kind===2?"birch":"bark");if(kind!==4&&kind!==1){blob(m,add(end,[0,.20,0]),length*.54,length*.38,length*.47,kind===2?"leafLight":"leaf",seed+k*13);}}if(kind===1){for(let k=0;k<6;k++){const t=.3+k*.105,cy=H*t,rad=(1-t)*1.45+.2;const angle=.6*k;const center=[bezier(p,t)[0]+Math.sin(angle)*.12,cy,bezier(p,t)[2]+Math.cos(angle)*.12];let prev=[];const sides=7;for(let j=0;j<sides;j++){const a=j*2*Math.PI/sides;prev.push(add(center,[rad*Math.cos(a),-.30,rad*Math.sin(a)]));}let apex=add(center,[0,.9,0]);for(let j=0;j<sides;j++)face(m,prev[j],prev[(j+1)%sides],apex,k%2?"leaf":"leafDark");}}if(kind===0||kind===3){blob(m,add(tip,[0,-.25,0]),1.38,1.06,1.26,"leaf",seed+99);}if(kind===2)blob(m,add(tip,[0,-.12,0]),.65,.75,.7,"leafLight",seed+31);if(kind===5)blob(m,add(tip,[0,.1,0]),.75,.65,.7,"leafLight",seed+31);return m;}

function makeBush(variant=0,seed=1){const m=mesh(),R=rng(seed+variant*71),type=variant%7;const H=[1.0,1.5,.95,1.05,1.15,.65,.9][type];for(let i=0;i<4+(type===1?2:0);i++){const a=i*2.399+.2*R(),l=(.6+.4*R()),c=[Math.cos(a)*.15,0,Math.sin(a)*.15],tip=[Math.cos(a)*l*.5,H*(.72+.25*R()),Math.sin(a)*l*.5];curveTube(m,[c,lerp(c,tip,.4),lerp(c,tip,.7),tip],.025,.008,3,5,"bark");if(type!==6)blob(m,tip,.32*l,.24*l,.31*l,i%2?"leaf":"leafLight",seed+i+11);if(type===0||type===3){for(let k=0;k<3;k++){const b=add(tip,[(R()-.5)*.35,(R()-.5)*.22,(R()-.5)*.35]);blob(m,b,.045,.045,.04,type===3?"flower":"berry",seed+k+100);}}}return m;}

function makeFlower(variant=0,seed=1){const m=mesh(),R=rng(seed+variant*21);for(let c=0;c<3;c++){const x=(c-1)*.21,z=(R()-.5)*.2,h=.45+R()*.25;const start=[x,0,z],tip=[x+.1*(R()-.5),h,z+.08*(R()-.5)];curveTube(m,[start,add(start,[0,h*.25,0]),add(tip,[-.03,-h*.2,0]),tip],.014,.006,4,5,"stem");if(variant%2===0){blob(m,tip,.07,.05,.07,"flowerCore",seed+c);for(let k=0;k<6;k++){let a=k*2*Math.PI/6;const out=add(tip,[Math.cos(a)*.23,.035,Math.sin(a)*.23]);leaf(m,tip,out,.064,k%2?"flower":"flowerLight");}}else{const center=add(tip,[0,-.09,0]);for(let k=0;k<5;k++){const a=k*2*Math.PI/5;leaf(m,tip,add(center,[Math.cos(a)*.16,-.14,Math.sin(a)*.16]),.065,k%2?"flower":"flowerLight");}blob(m,center,.035,.04,.035,"flowerCore",seed+c);}}return m;}

function makeMushroom(variant=0,seed=1){const m=mesh(),R=rng(seed+variant*19);const count=variant%4===3?4:1;for(let i=0;i<count;i++){const x=count===1?0:(i-1.5)*.13,z=count===1?0:(R()-.5)*.18,H=(.20+R()*.12)*(count===1?1:.8),r=.13+R()*.07;curveTube(m,[[x,0,z],[x+.01,H*.34,z],[x+.015,H*.67,z],[x+.02,H*.83,z]],.042,.029,4,6,"mushroomStem");const cy=H*.85,material=variant%4===0?"mushroomRed":variant%4===1?"mushroomBrown":"mushroomGold";const capHeight=variant%4===1?.20:variant%4===2?.055:.11;blob(m,[x,cy+capHeight*.23,z],r,capHeight,r,material,seed+i,7);if(variant%4===0)for(let j=0;j<3;j++){let a=j*2.399;blob(m,[x+Math.cos(a)*r*.62,cy+capHeight*.83,z+Math.sin(a)*r*.62],.018,.01,.018,"flowerCore",seed+j);}}return m;}

function makeStone(variant=0,seed=1){const m=mesh(),R=rng(seed+variant*137),type=variant%12;let w=.25+(type%4)*.32,h=.18+Math.floor(type/4)*.32;if(type===9)h=1.85;if(type===10)w=1.8;if(type===11){h=1.2;w=1.65;}const count=type===8?3:1;for(let i=0;i<count;i++){const x=i*.6,z=(R()-.5)*.3;blob(m,[x,h*.49,z],w*(.8+.3*R())/(count===3?2:1),h*.5,w*.72,(type===5||type===8)?"moss":"stone",seed+type*8+i,6+type%3);}return m;}

function makePlant(variant=0,seed=1){const m=mesh(),R=rng(seed+variant*29),type=variant%6;const N=[6,4,5,5,3,6][type];for(let k=0;k<N;k++){const a=k*2.399+R()*.35,r=(type===4?.2:.1)+.05*R(),root=[Math.cos(a)*r,0,Math.sin(a)*r];const h=(type===1?.65:type===4?.7:type===5?.12:.32)+.14*R();let tip=add(root,[Math.cos(a)*(type===1?.2:.23),h,Math.sin(a)*(type===1?.2:.23)]);if(type===1||type===4){curveTube(m,[root,add(root,[0,h*.3,0]),lerp(root,tip,.8),tip],.018,.007,3,5,"stem");if(type===4)blob(m,add(tip,[0,-.12,0]),.055,.15,.05,"reedHead",seed+k);}if(type===0||type===2||type===3||type===5){leaf(m,root,tip,type===3?.14:type===5?.11:.055,type===3?"leafLight":"leaf");}if(type===1){for(let j=1;j<=4;j++){const p=lerp(root,tip,j/5);leaf(m,p,add(p,[Math.cos(a+j*2)*.22,.06,Math.sin(a+j*2)*.22]),.055,"leaf");}}}return m;}

function makeCloud(variant=0,seed=1){const m=mesh(),R=rng(seed+variant*19);for(let k=0;k<3+variant%3;k++)blob(m,[(k-1)*.75,(R()-.5)*.25,0],.7,.34+.12*R(),.5,"cloud",seed+k);return m;}

function makeLog(seed=1,offset=[0,0,0]){const m=mesh();const R=rng(seed);const a=add(offset,[-.8,.15,0]),b=add(offset,[.8,.18,.08+(R()-.5)*.18]);curveTube(m,[a,lerp(a,b,.33),add(lerp(a,b,.66),[0,.04+R()*.08,0]),b],.18,.16,6,7,"bark");return m;}

function makeStump(seed=1){const m=mesh(),R=rng(seed);curveTube(m,[[0,0,0],[.04,.12,0],[.07,.30,.02],[.09,.45,.03]],.36,.26,5,8,"bark",.2);blob(m,[.09,.454,.03],.25,.015,.25,"sapwood",seed);return m;}

function makeLogPile(seed=1){const m=mesh();for(let i=0;i<5;i++){const log=makeLog(seed+i,[0,.2*(i>=3?1:0),i%3*.3]);for(let j=0;j<log.triangles.length;j++){m.triangles.push(log.triangles[j]);m.materials.push(log.materials[j]);}}return m;}

function makeTreeTrunk(seed=1){const m=mesh(),R=rng(seed),h=2.4+R()*.6,bend=(R()-.5)*.32;const stem=[[0,0,0],[bend*.3,h*.37,0],[bend*.8,h*.7,.09],[bend,h,.15]];curveTube(m,stem,.34,.13,8,7,"bark",.25);for(let k=0;k<2;k++){const a=k*2.4+R()*.3,base=bezier(stem,.45+k*.18),tip=add(base,[Math.cos(a)*(.65+.3*R()),.48,Math.sin(a)*(.65+.3*R())]);curveTube(m,[base,lerp(base,tip,.3),lerp(base,tip,.7),tip],.12,.035,4,5,"bark");}return m;}

function makeCliff(seed=1){const m=mesh();for(let i=0;i<3;i++)blob(m,[(i-1)*1.8,1.4+(i%2)*.8,0],1.35,1.8+(i%2)*.8,1.0,i===1?"stone":"stoneLight",seed+i,7);return m;}

function makeBridge(seed=1){const m=mesh(),R=rng(seed);for(let i=0;i<9;i++){const x=(i-4)*.4,y=.8+.12*Math.sin(i/8*Math.PI)+(R()-.5)*.04;box(m,[x,y,0],[.185,.07,.7],"wood");}for(let k of [-1,1])for(let x of [-1.5,1.5])box(m,[x,.45,k*.57],[.09,.45,.09],"bark");return m;}

function makeAsset(kind,variant=0,seed=1){const aliases={trees:"tree",bushes:"bush",flowers:"flower",mushrooms:"mushroom",stones:"stone",plants:"plant",clouds:"cloud",logs:"log",stumps:"stump",treetrunk:"treeTrunk",treeTrunks:"treeTrunk",logpiles:"logPile",cliffs:"cliff",bridges:"bridge"};kind=aliases[kind]||kind;switch(kind){case"tree":return makeTree(variant,seed);case"bush":return makeBush(variant,seed);case"flower":return makeFlower(variant,seed);case"mushroom":return makeMushroom(variant,seed);case"stone":return makeStone(variant,seed);case"plant":return makePlant(variant,seed);case"cloud":return makeCloud(variant,seed);case"log":return makeLog(seed);case"stump":return makeStump(seed);case"treeTrunk":return makeTreeTrunk(seed);case"logPile":return makeLogPile(seed);case"cliff":return makeCliff(seed);case"bridge":return makeBridge(seed);default:throw Error("Unknown nature kind: "+kind);}}

function grouping(variant=0,seed=1){const R=rng(seed+variant*471);const options=[["tree","bush","stone","plant"],["tree","tree","plant","flower"],["stone","stone","mushroom"],["log","stump","bush"],["tree","mushroom","plant"],["flower","flower","bush"],["tree","stone","stone"],["plant","plant","flower"],["tree","tree","bush"],["bush","stone","mushroom"],["cliff","stone","plant"],["bridge","plant","stone"]];return options[variant%12].map((kind,i)=>({kind,variant:(variant+i)%({tree:6,bush:7,stone:12,plant:6,flower:2,mushroom:4}[kind]||1),seed:seed+i*107,position:[(R()-.5)*5,0,(R()-.5)*4]}));}

function audit(m){if(m.triangles.length===0||m.triangles.length!==m.materials.length)throw Error("empty or missing materials");let xmin=Infinity,xmax=-Infinity,ymin=Infinity,ymax=-Infinity,zmin=Infinity,zmax=-Infinity;for(const T of m.triangles){const [a,b,c]=T;for(const p of T){if(!p.every(Number.isFinite))throw Error("nonfinite geometry");xmin=Math.min(xmin,p[0]);xmax=Math.max(xmax,p[0]);ymin=Math.min(ymin,p[1]);ymax=Math.max(ymax,p[1]);zmin=Math.min(zmin,p[2]);zmax=Math.max(zmax,p[2]);}const n=cross(sub(b,a),sub(c,a));if(dot(n,n)<1e-16)throw Error("degenerate face");}return {triangles:m.triangles.length,materials:new Set(m.materials).size,bounds:[xmin,ymin,zmin,xmax,ymax,zmax]};}

function toThree(THREE,m){const buckets=new Map();m.triangles.forEach((T,i)=>{const mat=m.materials[i];if(!buckets.has(mat))buckets.set(mat,[]);for(const v of T)buckets.get(mat).push(...v);});const g=new THREE.BufferGeometry(),positions=[],names=[...buckets.keys()];let idx=0;for(const name of names){const vals=buckets.get(name);positions.push(...vals);g.addGroup(idx,vals.length/3,names.indexOf(name));idx+=vals.length/3;}g.setAttribute("position",new THREE.Float32BufferAttribute(positions,3));g.computeVertexNormals();const materials=names.map(name=>new THREE.MeshLambertMaterial({color:PALETTE[name]||"#808080",flatShading:true,side:THREE.DoubleSide}));return new THREE.Mesh(g,materials);}

function toOBJ(m){const lines=["# Original LPM NatureAssetGrammar.v1; units meter; Y-up"],verts=[],buckets=new Map();for(let i=0;i<m.triangles.length;i++){let mat=m.materials[i];if(!buckets.has(mat))buckets.set(mat,[]);buckets.get(mat).push(m.triangles[i]);}let idx=1;for(const [mat,tris] of buckets){lines.push("g "+mat);lines.push("usemtl "+mat);for(const T of tris){for(const v of T)lines.push("v "+v.map(x=>x.toFixed(6)).join(" "));lines.push("f "+idx+" "+(idx+1)+" "+(idx+2));idx+=3;}}return lines.join("\n")+"\n";}

function catalogue(){return [["tree",6],["bush",7],["flower",2],["mushroom",4],["stone",12],["plant",6],["cloud",3],["log",1],["stump",1],["treeTrunk",1],["logPile",1],["cliff",1],["bridge",1]];}

const PALETTE = {
  "bark": "#68482e",
  "birch": "#d6c7a2",
  "wood": "#916e47",
  "sapwood": "#d5b681",
  "leaf": "#648a38",
  "leafLight": "#80a74c",
  "leafDark": "#3c622b",
  "berry": "#b63b3e",
  "stem": "#54703c",
  "flower": "#c76b9e",
  "flowerLight": "#f3abc2",
  "flowerCore": "#e3ad42",
  "mushroomStem": "#e2d5b1",
  "mushroomRed": "#b93e37",
  "mushroomBrown": "#977453",
  "mushroomGold": "#d7ac5f",
  "stone": "#807a70",
  "stoneLight": "#a9a294",
  "moss": "#59734a",
  "reedHead": "#9c7945",
  "cloud": "#f0f3ee"
};

export {makeAsset,toThree,toOBJ,catalogue,grouping,audit,PALETTE};
