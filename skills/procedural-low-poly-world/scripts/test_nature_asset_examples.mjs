import assert from "node:assert/strict";
import {makeAsset,catalogue,grouping,audit,toOBJ} from "./nature_asset_examples.mjs";
let variants=0;
for(const [kind,count] of catalogue()){
  for(let i=0;i<count;i++){
    const a=makeAsset(kind,i,29),metrics=audit(a);
    assert.ok(metrics.triangles>0 && metrics.triangles<=1800,kind+" triangle count");
    assert.deepEqual(a,makeAsset(kind,i,29),kind+" deterministic seed");
    assert.notDeepEqual(a,makeAsset(kind,i,31),kind+" distinct seed");
    assert.ok(toOBJ(a).includes("\nf "),"OBJ mesh export");
    variants++;
  }
}
for(let n=0;n<12;n++){
  const a=grouping(n,29);
  assert.ok(a.length>=3);
  assert.deepEqual(a,grouping(n,29));
}
const sample=audit(makeAsset("tree",0,29));
assert.ok(sample.bounds[4]>=5.7 && sample.bounds[4]<8);
console.log("PASS "+variants+" original example meshes + 12 groupings; tree audit",sample);
