#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

const UA_DIR = '/home/the-goated-mufasa/Flutter Projects/Fladder/.ua';
const INPUT_PATH = path.join(UA_DIR, 'intermediate/assembled-graph.json');
const OUTPUT_PATH = path.join(UA_DIR, 'tmp/ua-arch-input.json');
const LAYERS_PATH = path.join(UA_DIR, 'intermediate/layers.json');

// Load assembled graph
const graph = JSON.parse(fs.readFileSync(INPUT_PATH, 'utf8'));

// Extract file-level nodes
const fileNodes = graph.nodes.filter(n => n.type === 'file');

// Extract import edges
const importEdges = graph.edges.filter(e => e.type === 'imports');

// Build adjacency info
const importsFrom = {};
const importsTo = {};
importEdges.forEach(e => {
  if (!importsFrom[e.source]) importsFrom[e.source] = [];
  importsFrom[e.source].push(e.target);
  if (!importsTo[e.target]) importsTo[e.target] = [];
  importsTo[e.target].push(e.source);
});

// === DIRECTORY GROUPING ===
const directoryGroups = {};
fileNodes.forEach(n => {
  const parts = n.filePath.split('/');
  const group = parts[0];
  if (!directoryGroups[group]) directoryGroups[group] = [];
  directoryGroups[group].push(n.id);
});

// === NODE TYPE GROUPING ===
const nodeTypeGroups = {};
fileNodes.forEach(n => {
  if (!nodeTypeGroups[n.type]) nodeTypeGroups[n.type] = [];
  nodeTypeGroups[n.type].push(n.id);
});

// === CROSS-CATEGORY DEPENDENCY ANALYSIS ===
function getTopDir(filePath) {
  return filePath.split('/')[0];
}

function getLayer(filePath) {
  return assignLayer(filePath, '', {});
}

const crossCategoryDeps = {};
importEdges.forEach(e => {
  const srcNode = fileNodes.find(n => n.id === e.source);
  const tgtNode = fileNodes.find(n => n.id === e.target);
  if (srcNode && tgtNode) {
    const srcDir = getTopDir(srcNode.filePath);
    const tgtDir = getTopDir(tgtNode.filePath);
    const key = `${srcDir} -> ${tgtDir}`;
    if (srcDir !== tgtDir) {
      crossCategoryDeps[key] = (crossCategoryDeps[key] || 0) + 1;
    }
  }
});

// === INTER-GROUP IMPORT FREQUENCY ===
function getInterGroupKey(srcFilePath, tgtFilePath) {
  const srcGroup = srcFilePath.split('/')[0];
  const tgtGroup = tgtFilePath.split('/')[0];
  if (srcGroup === tgtGroup && srcGroup === 'lib') {
    const srcSub = srcFilePath.split('/')[1] || 'root';
    const tgtSub = tgtFilePath.split('/')[1] || 'root';
    if (srcSub !== tgtSub) return `lib/${srcSub} -> lib/${tgtSub}`;
  }
  if (srcGroup !== tgtGroup) return `${srcGroup} -> ${tgtGroup}`;
  return null;
}

const interGroupFreq = {};
importEdges.forEach(e => {
  const srcNode = fileNodes.find(n => n.id === e.source);
  const tgtNode = fileNodes.find(n => n.id === e.target);
  if (srcNode && tgtNode) {
    const key = getInterGroupKey(srcNode.filePath, tgtNode.filePath);
    if (key) interGroupFreq[key] = (interGroupFreq[key] || 0) + 1;
  }
});

// Write analysis input
const analysisInput = {
  fileNodes: fileNodes.map(n => ({ id: n.id, filePath: n.filePath, name: n.name, tags: n.tags, summary: n.summary })),
  importEdges: importEdges.map(e => ({ source: e.source, target: e.target, confidence: e.confidence })),
  directoryGroups,
  nodeTypeGroups,
  crossCategoryDeps,
  interGroupFrequency: interGroupFreq
};

fs.writeFileSync(OUTPUT_PATH, JSON.stringify(analysisInput, null, 2));
console.log(`Wrote analysis input to ${OUTPUT_PATH}`);
console.log(`  File nodes: ${fileNodes.length}`);
console.log(`  Import edges: ${importEdges.length}`);
console.log(`  Directory groups: ${Object.keys(directoryGroups).length}`);

// === LAYER ASSIGNMENT ===
function assignLayer(filePath, name, tags) {
  // Platform Layer - platform-specific directories
  if (/^(android|ios|linux|macos|windows|web)\/(.*)$/.test(filePath)) {
    return 'platform';
  }
  
  // Config & Build - infrastructure files
  const infraFiles = [
    'pubspec.yaml', 'pubspec.lock', 'analysis_options.yaml', 'build.yaml',
    'l10n.yaml', '.fvmrc', '.metadata', '.gitmodules',
    'Dockerfile', 'Dockerfile-rootless', 'docker-compose.yml', '.dockerignore',
    'docker-entrypoint.sh', 'AppImageBuilder.yml', 'altstore.json',
    'devtools_options.yaml', 'icons_launcher-development.yaml',
    'icons_launcher-production.yaml'
  ];
  if (infraFiles.some(f => filePath.endsWith(f) || filePath === f)) {
    return 'infrastructure';
  }
  
  // Infrastructure - docs and config directories
  if (/^(scripts|config|fastlane|snap|flatpak|swagger|pigeons)\//.test(filePath)) {
    return 'infrastructure';
  }
  if (/^(CODE_OF_CONDUCT|CONTRIBUTING|DEVELOPEMENT|INSTALL|README)\.md$/.test(filePath)) {
    return 'infrastructure';
  }
  if (/^\.github\//.test(filePath)) {
    return 'infrastructure';
  }
  
  // Test Layer
  if (/^test\//.test(filePath)) {
    return 'test';
  }
  
  // Assets Layer
  if (/^assets\//.test(filePath)) {
    return 'assets';
  }
  
  // lib/ directory - main application code
  if (filePath.startsWith('lib/')) {
    const parts = filePath.split('/');
    const libSub = parts[1] || 'root';
    
    // Presentation Layer - screens, widgets, theme
    if (libSub === 'screens' || libSub === 'widgets') {
      return 'presentation';
    }
    if (libSub === 'theme.dart' || libSub === 'theme') {
      return 'presentation';
    }
    
    // Business Logic Layer - providers, services, background, logic
    if (libSub === 'providers' || libSub === 'services' || libSub === 'background' || libSub === 'logic') {
      return 'business-logic';
    }
    
    // Data Layer - models, jellyfin API, seerr API, l10n, generated pigeon code
    if (libSub === 'models' || libSub === 'jellyfin' || libSub === 'seerr' || libSub === 'l10n' || libSub === 'src') {
      return 'data';
    }
    
    // Infrastructure Layer - util, bootstrap, routes, profiles, stubs, wrappers, fake, main.dart, localization_delegates
    if (['util', 'bootstrap', 'routes', 'profiles', 'stubs', 'wrappers', 'fake'].includes(libSub)) {
      return 'infrastructure';
    }
    if (libSub === 'main.dart' || libSub === 'localization_delegates.dart' || libSub === 'shaders') {
      return 'infrastructure';
    }
    
    // Default for anything else in lib/
    return 'infrastructure';
  }
  
  // Default fallback
  return 'infrastructure';
}

// Assign layers
const layerMap = {
  presentation: [],
  'business-logic': [],
  data: [],
  infrastructure: [],
  platform: [],
  test: [],
  assets: []
};

const layerDescriptions = {
  presentation: 'UI components, screens, widgets, and theme',
  'business-logic': 'State management, providers, services, and background tasks',
  data: 'Models, API clients, generated code, and localization resources',
  infrastructure: 'Utilities, bootstrap, routing, profiles, configuration, and build files',
  platform: 'Platform-specific native code (Android, iOS, Linux, macOS, Windows, Web)',
  test: 'Unit tests and widget tests',
  assets: 'Static assets (images, fonts, etc.)'
};

fileNodes.forEach(n => {
  const layer = assignLayer(n.filePath, n.name, n.tags || []);
  if (layerMap[layer]) {
    layerMap[layer].push(n.id);
  }
});

// Build layers.json
const layers = Object.keys(layerMap).filter(k => layerMap[k].length > 0).map(key => ({
  id: `layer:${key}`,
  name: key === 'business-logic' ? 'Business Logic Layer' :
        key === 'presentation' ? 'Presentation Layer' :
        key === 'data' ? 'Data Layer' :
        key === 'infrastructure' ? 'Infrastructure Layer' :
        key === 'platform' ? 'Platform Layer' :
        key === 'test' ? 'Test Layer' :
        'Assets Layer',
  description: layerDescriptions[key],
  nodeIds: layerMap[key]
}));

fs.writeFileSync(LAYERS_PATH, JSON.stringify(layers, null, 2));

console.log(`\nWrote layers to ${LAYERS_PATH}`);
console.log(`\nLayer summary:`);
layers.forEach(l => console.log(`  ${l.name}: ${l.nodeIds.length} files`));
console.log(`\nTotal files assigned: ${layers.reduce((s, l) => s + l.nodeIds.length, 0)}`);
