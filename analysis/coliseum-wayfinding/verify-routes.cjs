// Run only the uploaded demo's pure graph/data section, not its browser UI.
// Usage: node verify-routes.cjs > route-verification.json
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const crypto = require('node:crypto');
const source = fs.readFileSync(path.join(__dirname, 'source-demo.html'), 'utf8');
const begin = source.indexOf('const NODES =');
const end = source.indexOf('const SPEED_PRESETS =');
if (begin < 0 || end <= begin) throw Error('Expected source markers missing');
const api = vm.runInNewContext(
  source.slice(begin, end) + '\n;({NODES, EDGES_RAW, ADJ, computeDijkstraRoute});',
  {}, {timeout: 2000, contextCodeGeneration: {strings: false, wasm: false}}
);
const starts = ['sw-dropoff', 'east-peristyle', 'north-gate14'];
const destinations = ['sec-109a', 'sec-308', 'club-1923', 'sensory-room', 'ada-restroom'];
const results = [];
for (const start of starts) for (const destination of destinations) {
  for (const stepFreeOnly of [true, false]) for (const avoidLoudCrowds of [false, true]) for (const maxShade of [false, true]) {
    const options = {stepFreeOnly, avoidLoudCrowds, maxShade};
    const route = api.computeDijkstraRoute(start, destination, options);
    if (!route) throw Error('Missing route: ' + JSON.stringify({start, destination, options}));
    if (stepFreeOnly && route.edges.some(e => e.hasStairs || e.maxSlopePct > 8.33)) throw Error('Step-free exclusion violated');
    if (route.nodes[0] !== start || route.nodes.at(-1) !== destination) throw Error('Incorrect endpoints');
    results.push({start, destination, ...options, nodes: route.nodes, meters: route.totalMeters,
      maxGradePct: route.maxGradePct, stairEdges: route.stairsCount,
      elevatorRuns: route.elevatorCount, shadePct: route.shadePct, modeledAvgDb: route.avgNoiseDb});
  }
}
const pick = (start, destination, opts = {}) => results.find(r => r.start === start && r.destination === destination &&
  r.stepFreeOnly === (opts.stepFreeOnly ?? true) && r.avoidLoudCrowds === (opts.avoidLoudCrowds ?? false) && r.maxShade === (opts.maxShade ?? false));
const normal = pick('north-gate14', 'sec-109a');
const calm = pick('north-gate14', 'sec-109a', {avoidLoudCrowds: true});
const standard = pick('sw-dropoff', 'sec-308', {stepFreeOnly: false});
const stepFree = pick('sw-dropoff', 'sec-308');
const output = {
  sourceSha256: crypto.createHash('sha256').update(source).digest('hex'),
  method: 'Executed unchanged pure graph section in Node VM; browser, external libraries and device APIs were not executed.',
  graphNodes: Object.keys(api.NODES).length,
  undirectedEdges: api.EDGES_RAW.length,
  routeConfigurationsExecuted: results.length,
  stepFreeConfigurationsWithNoStairsAndNoEdgesOver833Percent: results.filter(r => r.stepFreeOnly).length,
  defaultStepFree: stepFree, defaultStandard: standard,
  builtinVC2ActualPredicate: stepFree.stairEdges === 0 && standard.stairEdges > 0 && stepFree.elevatorRuns >= 1,
  lowSensoryExample: {normal, calm, pathActuallyChanged: normal.nodes.join('|') !== calm.nodes.join('|')},
  maxShadePathsChanged: results.filter(r => r.maxShade).filter(r => {
    const comparison = pick(r.start, r.destination, {stepFreeOnly:r.stepFreeOnly,avoidLoudCrowds:r.avoidLoudCrowds});
    return comparison.nodes.join('|') !== r.nodes.join('|');
  }).length,
  invalidEndpointReturnsNull: api.computeDijkstraRoute('not-a-node', 'sec-308') === null,
  routes: results
};
process.stdout.write(JSON.stringify(output, null, 2) + '\n');
