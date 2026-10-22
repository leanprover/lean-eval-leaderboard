const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

class Element {
  constructor(tag, text = '') { this.tag = tag; this.nodeType = 1; this.children = []; this.attributes = {}; this.listeners = {}; this.text = text; }
  set textContent(value) { this.text = String(value); this.children = []; }
  get textContent() { return this.text + this.children.map(child => child.textContent).join(''); }
  setAttribute(key, value) { this.attributes[key] = value; }
  appendChild(child) { this.children.push(child); return child; }
  replaceChildren(...children) { this.text = ''; this.children = children; }
  addEventListener(name, listener) { this.listeners[name] = listener; }
}
const document = { readyState: 'complete', querySelector: () => null, createElement: tag => new Element(tag), createTextNode: text => new Element('#text', text) };
const context = vm.createContext({ document, URL, location: { href: 'https://lean-lang.org/eval/problems/example/' } });
const code = fs.readFileSync('static/lifecycle-preview.js', 'utf8').replace('  function run() {', '  globalThis.compute = { preferredMeasurement, compareCells, measuredSummary, comparisonViews };\n  function run() {');
vm.runInContext(code, context);
const compute = context.compute;
function nodes(root, predicate) { return [root, ...root.children.flatMap(child => nodes(child, predicate))].filter(predicate); }
function solution(id, metadata = {}) { return { result_id: id, canonical_credit: { label: id }, submitter: 'alice', statement_revision: 1, measurements: [], metadata, replay: { status: 'unavailable', reason: 'not-enqueued' } }; }

test('prefers the acceptance measurement, then newest successful attempt rather than fastest', () => {
  const s = solution('a');
  const replay = { kind: 'checker-replay', status: 'available', replay_status: 'accepted', updated_at: '2026-10-22', attempt: 1, build_wall_time_ms: 1 };
  const accepted = { kind: 'acceptance-build', status: 'available', measured_at: '2026-10-21', attempt: 1, build_wall_time_ms: 1000 };
  s.measurements = [replay, accepted, { ...accepted, measured_at: '2026-10-23', status: 'failed' }];
  assert.equal(compute.preferredMeasurement(s), accepted);
  s.measurements.push({ ...accepted, measured_at: '2026-10-22', build_wall_time_ms: 2000 });
  assert.equal(compute.preferredMeasurement(s).build_wall_time_ms, 2000);
});

test('missing values sort last in both directions while zero remains numeric', () => {
  for (const direction of [1, -1]) {
    assert.equal(compute.compareCells(null, 0, direction), 1);
    assert.equal(compute.compareCells(0, null, direction), -1);
  }
  assert.ok(compute.compareCells(2, 10, 1) < 0);
});

test('cards explain noisy time and unavailable counters', () => {
  const s = solution('a');
  s.measurements = [{ kind: 'acceptance-build', status: 'available', build_wall_time_ms: 0, build_retired_instructions: null, build_retired_instructions_unavailable_reason: 'counter_permission_denied', checker_wall_time_ms: 10, checker_retired_instructions: 5 }];
  const text = compute.measuredSummary(s).textContent;
  assert.match(text, /very noisy/);
  assert.match(text, /0 seconds/);
  assert.match(text, /Runner does not allow instruction counters/);
});

test('production table sorts actual numeric totals and keeps unknown values last', () => {
  const solutions = [solution('ten', { input_tokens: { value: 10 } }), solution('unknown'), solution('zero', { input_tokens: { value: 0 } })];
  const view = compute.comparisonViews(solutions);
  const production = nodes(view, e => e.tag === 'button' && e.textContent.startsWith('Production information'))[0];
  production.listeners.click();
  const inputHeader = nodes(view, e => e.tag === 'button' && e.textContent === 'Input tokens')[0];
  inputHeader.listeners.click();
  let rows = nodes(view, e => e.tag === 'tbody')[0].children;
  assert.equal(rows[0].children[0].textContent, 'zero');
  assert.equal(rows[0].children[4].textContent, '0');
  assert.equal(rows[2].children[0].textContent, 'unknown');
  nodes(view, e => e.tag === 'button' && e.textContent.startsWith('Input tokens'))[0].listeners.click();
  rows = nodes(view, e => e.tag === 'tbody')[0].children;
  assert.equal(rows[0].children[0].textContent, 'ten');
  assert.equal(rows[2].children[0].textContent, 'unknown');
});
