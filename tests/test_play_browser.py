"""Request-order checks for the real frontend, without WebGL or a browser."""
from pathlib import Path
import shutil
import subprocess

import pytest


@pytest.mark.parametrize("scenario", ["selection", "render", "edit"])
def test_download_follows_only_the_current_completed_preview(scenario):
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is needed for the frontend request-order check")
    source = Path(__file__).resolve().parents[1] / "src/mm_mcp/play/static/app.js"
    harness = r'''
const fs = require('fs'), vm = require('vm'), assert = require('node:assert/strict');
const fields = new Map(), pending = [];
const field = () => ({hidden:false, disabled:false, value:'', textContent:'',
  children:[], appendChild(child) {this.children.push(child);}});
const context = {
  scenario:process.argv[2], console, URLSearchParams,
  window:{location:''}, document:{getElementById(id) {
    if (!fields.has(id)) fields.set(id, field());
    return fields.get(id);
  }, createElement:field},
  setTimeout() {return 1;}, clearTimeout() {},
  fetch:async url => url === '/api/materials'
    ? {json:async () => ({ok:true, materials:[]})}
    : new Promise(resolve => pending.push(out => resolve({json:async () => out})))
};
vm.createContext(context);
vm.runInContext(fs.readFileSync(process.argv[1], 'utf8'), context);
const material = name => ({ok:true, name, sliders:[{id:'group/param0', value:1}]});
const rendered = id => ({ok:true, path:'headless', preview_id:id, maps:[]});
(async () => {
  if (context.scenario === 'selection') {
    const first = vm.runInContext("loadMaterial('first')", context);
    const second = vm.runInContext("loadMaterial('second')", context);
    pending[1](material('second')); await second;
    pending[0](material('first')); await first;
    assert.equal(vm.runInContext('current.name', context), 'second');
    return;
  }
  const selection = vm.runInContext("loadMaterial('first')", context);
  pending.shift()(material('first')); await selection;
  const first = vm.runInContext('doRender(256)', context);
  if (context.scenario === 'edit') {
    const row = fields.get('sliders').children.find(x => x.className === 'slider-row');
    const input = row.children.find(x => x.type === 'range');
    input.value = '2'; input.oninput();
    pending.shift()(rendered('old')); await first;
    assert.equal(fields.get('download').disabled, true);
    fields.get('download').onclick();
    assert.equal(context.window.location, '');
    return;
  }
  const second = vm.runInContext('doRender(1024)', context);
  pending[1](rendered('new')); await second;
  pending[0](rendered('old')); await first;
  assert.equal(fields.get('download').disabled, false);
  fields.get('download').onclick();
  assert.equal(context.window.location, '/api/export?preview_id=new');
})().catch(error => {console.error(error); process.exitCode = 1;});
'''
    result = subprocess.run([node, "-e", harness, str(source), scenario],
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stdout + result.stderr
