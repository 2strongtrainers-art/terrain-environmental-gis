/**
 * Alan Kaplan's Fishing Escape -- visual helpers v22.
 *
 * This module deliberately has no imports. Every public factory accepts the
 * caller's THREE namespace so the game keeps a single Three.js runtime and the
 * helpers remain compatible with a static GitHub Pages deployment.
 */

export const VISUALS_V22_VERSION = 'REALISTIC_VISUALS_V22';

const TAU = Math.PI * 2;

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function smoothstep(edge0, edge1, value) {
  const t = clamp((value - edge0) / Math.max(1e-8, edge1 - edge0), 0, 1);
  return t * t * (3 - 2 * t);
}

function seedNumber(value) {
  if (Number.isFinite(value)) return Number(value) >>> 0;
  const text = String(value ?? 'alan-v22');
  let hash = 2166136261;
  for (let i = 0; i < text.length; i += 1) {
    hash ^= text.charCodeAt(i);
    hash = Math.imul(hash, 16777619);
  }
  return hash >>> 0;
}

function randomFactory(seed) {
  let state = seedNumber(seed) || 0x6d2b79f5;
  return () => {
    state += 0x6d2b79f5;
    let value = state;
    value = Math.imul(value ^ (value >>> 15), value | 1);
    value ^= value + Math.imul(value ^ (value >>> 7), value | 61);
    return ((value ^ (value >>> 14)) >>> 0) / 4294967296;
  };
}

function positiveModulo(value, divisor) {
  return ((value % divisor) + divisor) % divisor;
}

function hash2D(x, y, seed, period) {
  const px = positiveModulo(x, period);
  const py = positiveModulo(y, period);
  let value = seedNumber(seed);
  value ^= Math.imul(px + 0x9e3779b9, 0x85ebca6b);
  value ^= Math.imul(py + 0xc2b2ae35, 0x27d4eb2d);
  value ^= value >>> 15;
  value = Math.imul(value, 0x2c1b3c6d);
  value ^= value >>> 12;
  value = Math.imul(value, 0x297a2d39);
  value ^= value >>> 15;
  return (value >>> 0) / 4294967295;
}

function periodicValueNoise(u, v, seed, period) {
  const x = u * period;
  const y = v * period;
  const x0 = Math.floor(x);
  const y0 = Math.floor(y);
  const tx = x - x0;
  const ty = y - y0;
  const sx = tx * tx * (3 - 2 * tx);
  const sy = ty * ty * (3 - 2 * ty);
  const a = hash2D(x0, y0, seed, period);
  const b = hash2D(x0 + 1, y0, seed, period);
  const c = hash2D(x0, y0 + 1, seed, period);
  const d = hash2D(x0 + 1, y0 + 1, seed, period);
  const ab = a + (b - a) * sx;
  const cd = c + (d - c) * sx;
  return ab + (cd - ab) * sy;
}

function periodicFbm(u, v, seed, basePeriod = 4, octaves = 4) {
  let total = 0;
  let amplitude = 0.55;
  let normalizer = 0;
  let period = basePeriod;
  for (let octave = 0; octave < octaves; octave += 1) {
    total += periodicValueNoise(u, v, seed + octave * 1013, period) * amplitude;
    normalizer += amplitude;
    amplitude *= 0.5;
    period *= 2;
  }
  return total / normalizer;
}

function makeCanvas(size) {
  if (typeof document !== 'undefined' && document.createElement) {
    const canvas = document.createElement('canvas');
    canvas.width = size;
    canvas.height = size;
    return canvas;
  }
  if (typeof OffscreenCanvas !== 'undefined') return new OffscreenCanvas(size, size);
  throw new Error('visuals-v22 texture generation requires Canvas or OffscreenCanvas');
}

function normalizedTextureSize(options) {
  const requested = Number(options.size);
  if (Number.isFinite(requested)) return clamp(Math.round(requested), 128, 1024);
  return options.mobile ? 256 : 512;
}

function configureTexture(THREE, canvas, options) {
  const texture = new THREE.CanvasTexture(canvas);
  texture.name = options.name;
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.RepeatWrapping;
  texture.repeat.set(options.repeat[0], options.repeat[1]);
  texture.generateMipmaps = true;
  texture.minFilter = THREE.LinearMipmapLinearFilter;
  texture.magFilter = THREE.LinearFilter;
  texture.anisotropy = Math.max(1, Math.floor(options.anisotropy || 1));
  if (options.color) {
    if ('colorSpace' in texture && THREE.SRGBColorSpace) texture.colorSpace = THREE.SRGBColorSpace;
    else if ('encoding' in texture && THREE.sRGBEncoding) texture.encoding = THREE.sRGBEncoding;
  } else if ('colorSpace' in texture && THREE.NoColorSpace) {
    texture.colorSpace = THREE.NoColorSpace;
  }
  texture.needsUpdate = true;
  return texture;
}

function surfacePixel(kind, u, v, x, y, seed) {
  const macro = periodicFbm(u, v, seed, 4, 4);
  const detail = periodicFbm(u, v, seed + 719, 16, 3);
  const grit = hash2D(x, y, seed + 1301, 65521);
  let height;
  let red;
  let green;
  let blue;

  if (kind === 'terrain') {
    const worn = smoothstep(0.2, 0.82, macro * 0.75 + detail * 0.25);
    const dry = smoothstep(0.68, 0.94, detail + (grit - 0.5) * 0.2);
    height = clamp(macro * 0.62 + detail * 0.3 + grit * 0.08, 0, 1);
    red = 62 + worn * 56 + dry * 21;
    green = 78 + worn * 61 + dry * 10;
    blue = 47 + worn * 37 + dry * 7;
  } else if (kind === 'shore') {
    const pebble = Math.pow(grit, 10);
    const mineral = periodicFbm(u, v, seed + 1877, 9, 3);
    height = clamp(detail * 0.42 + macro * 0.25 + pebble * 0.55, 0, 1);
    red = 112 + mineral * 52 + pebble * 26;
    green = 96 + mineral * 45 + pebble * 22;
    blue = 67 + mineral * 34 + pebble * 18;
  } else if (kind === 'rock') {
    const vein = Math.pow(Math.abs(Math.sin((u * 3.0 + v * 1.35 + macro * 0.38) * TAU)), 14);
    const lichen = smoothstep(0.73, 0.9, detail * 0.75 + macro * 0.25);
    height = clamp(macro * 0.54 + detail * 0.31 + vein * 0.19, 0, 1);
    red = 70 + macro * 50 + vein * 24 + lichen * 8;
    green = 74 + macro * 49 + vein * 21 + lichen * 20;
    blue = 69 + macro * 45 + vein * 18 + lichen * 9;
  } else {
    const warp = (macro - 0.5) * 0.09 + (detail - 0.5) * 0.025;
    const grainWave = 0.5 + 0.5 * Math.sin((v + warp) * TAU * 17 + Math.sin(u * TAU * 2) * 0.45);
    const fineGrain = 0.5 + 0.5 * Math.sin((v + warp * 0.35) * TAU * 53);
    const knotX = positiveModulo(u - 0.28, 1) - 0.5;
    const knotY = positiveModulo(v - 0.61, 1) - 0.5;
    const knotRadius = Math.sqrt(knotX * knotX * 2.4 + knotY * knotY * 18);
    const knot = Math.exp(-knotRadius * 14) * (0.5 + 0.5 * Math.sin(knotRadius * 58));
    height = clamp(grainWave * 0.31 + fineGrain * 0.09 + macro * 0.35 + knot * 0.3, 0, 1);
    red = 74 + macro * 54 + grainWave * 25 - knot * 28;
    green = 45 + macro * 37 + grainWave * 17 - knot * 18;
    blue = 27 + macro * 24 + grainWave * 10 - knot * 10;
  }

  return [height, red, green, blue];
}

function createSurfaceTexturePair(THREE, kind, options) {
  const size = options.size;
  const seed = seedNumber(options.seed);
  const colorCanvas = makeCanvas(size);
  const normalCanvas = makeCanvas(size);
  const colorContext = colorCanvas.getContext('2d', { alpha: false });
  const normalContext = normalCanvas.getContext('2d', { alpha: false });
  if (!colorContext || !normalContext) throw new Error('visuals-v22 could not create a 2D canvas context');

  const colorImage = colorContext.createImageData(size, size);
  const normalImage = normalContext.createImageData(size, size);
  const heights = new Float32Array(size * size);

  for (let y = 0; y < size; y += 1) {
    const v = y / size;
    for (let x = 0; x < size; x += 1) {
      const u = x / size;
      const index = y * size + x;
      const pixel = surfacePixel(kind, u, v, x, y, seed);
      heights[index] = pixel[0];
      const offset = index * 4;
      colorImage.data[offset] = clamp(Math.round(pixel[1]), 0, 255);
      colorImage.data[offset + 1] = clamp(Math.round(pixel[2]), 0, 255);
      colorImage.data[offset + 2] = clamp(Math.round(pixel[3]), 0, 255);
      colorImage.data[offset + 3] = 255;
    }
  }

  const normalStrength = options.normalStrength;
  for (let y = 0; y < size; y += 1) {
    const previousY = positiveModulo(y - 1, size);
    const nextY = (y + 1) % size;
    for (let x = 0; x < size; x += 1) {
      const previousX = positiveModulo(x - 1, size);
      const nextX = (x + 1) % size;
      const left = heights[y * size + previousX];
      const right = heights[y * size + nextX];
      const down = heights[previousY * size + x];
      const up = heights[nextY * size + x];
      let nx = (left - right) * normalStrength;
      let ny = (down - up) * normalStrength;
      let nz = 1;
      const inverseLength = 1 / Math.sqrt(nx * nx + ny * ny + nz * nz);
      nx *= inverseLength;
      ny *= inverseLength;
      nz *= inverseLength;
      const offset = (y * size + x) * 4;
      normalImage.data[offset] = Math.round((nx * 0.5 + 0.5) * 255);
      normalImage.data[offset + 1] = Math.round((ny * 0.5 + 0.5) * 255);
      normalImage.data[offset + 2] = Math.round((nz * 0.5 + 0.5) * 255);
      normalImage.data[offset + 3] = 255;
    }
  }

  colorContext.putImageData(colorImage, 0, 0);
  normalContext.putImageData(normalImage, 0, 0);
  const map = configureTexture(THREE, colorCanvas, {
    name: `alan-v22-${kind}-color`,
    repeat: options.repeat,
    anisotropy: options.anisotropy,
    color: true
  });
  const normalMap = configureTexture(THREE, normalCanvas, {
    name: `alan-v22-${kind}-normal`,
    repeat: options.repeat,
    anisotropy: options.anisotropy,
    color: false
  });

  return { map, normalMap };
}

/**
 * Create a deterministic, seamless texture kit for the main environment.
 *
 * Each entry exposes `map`, `normalMap`, and a `material` object that can be
 * spread directly into MeshStandardMaterial/MeshPhysicalMaterial options.
 * Defaults are 256px on mobile and 512px elsewhere (eight RGBA textures total).
 */
export function createProceduralTextureKit(THREE, options = {}) {
  if (!THREE || !THREE.CanvasTexture) throw new TypeError('createProceduralTextureKit requires THREE');
  const mobile = Boolean(options.mobile);
  const size = normalizedTextureSize({ ...options, mobile });
  const rootSeed = seedNumber(options.seed ?? 2209);
  const anisotropy = clamp(Number(options.anisotropy) || (mobile ? 2 : 6), 1, 16);
  const definitions = {
    terrain: { repeat: [12, 12], normalStrength: 3.0, roughness: 0.91, normalScale: mobile ? 0.52 : 0.68 },
    shore: { repeat: [10, 22], normalStrength: 4.6, roughness: 0.78, normalScale: mobile ? 0.58 : 0.76 },
    rock: { repeat: [3, 3], normalStrength: 5.8, roughness: 0.86, normalScale: mobile ? 0.62 : 0.82 },
    wood: { repeat: [3, 1], normalStrength: 4.0, roughness: 0.72, normalScale: mobile ? 0.48 : 0.64 }
  };

  const kit = { size, mobile, seed: rootSeed };
  const textures = [];
  Object.entries(definitions).forEach(([kind, definition], index) => {
    const pair = createSurfaceTexturePair(THREE, kind, {
      size,
      seed: rootSeed + index * 4099,
      anisotropy,
      repeat: definition.repeat,
      normalStrength: definition.normalStrength
    });
    textures.push(pair.map, pair.normalMap);
    kit[kind] = {
      ...pair,
      material: {
        map: pair.map,
        normalMap: pair.normalMap,
        normalScale: new THREE.Vector2(definition.normalScale, definition.normalScale),
        roughness: definition.roughness,
        metalness: 0
      }
    };
  });
  kit.dispose = () => textures.forEach((texture) => texture.dispose());
  return kit;
}

/**
 * Build a wave-ready lake disc with concentric subdivisions. `edgeScale` can
 * optionally return a shoreline multiplier for an angle in radians. The custom
 * `lakeDistance` vertex attribute is 0 at the centre and 1 at the shoreline.
 */
export function createLakeGeometry(THREE, options = {}) {
  if (!THREE || !THREE.BufferGeometry) throw new TypeError('createLakeGeometry requires THREE');
  const mobile = Boolean(options.mobile);
  const radius = Math.max(1, Number(options.radius) || 40);
  const radialSegments = clamp(Math.round(Number(options.radialSegments) || (mobile ? 24 : 40)), 8, 96);
  const angularSegments = clamp(Math.round(Number(options.angularSegments) || (mobile ? 96 : 144)), 24, 256);
  const irregularity = clamp(Number(options.irregularity) || 0, 0, 0.12);
  const phase = Number(options.phase) || 0;
  const edgeScale = typeof options.edgeScale === 'function' ? options.edgeScale : null;
  const positions = [0, 0, 0];
  const normals = [0, 1, 0];
  const uvs = [0.5, 0.5];
  const lakeDistances = [0];
  const indices = [];
  const uvExtent = radius * (1 + irregularity * 1.8);

  for (let ring = 1; ring <= radialSegments; ring += 1) {
    const lakeDistance = ring / radialSegments;
    for (let segment = 0; segment <= angularSegments; segment += 1) {
      const angle = (segment / angularSegments) * TAU;
      const harmonic = Math.sin(angle * 3 + phase) * 0.52
        + Math.sin(angle * 7 - phase * 0.71) * 0.31
        + Math.sin(angle * 13 + phase * 1.37) * 0.17;
      const proceduralEdge = 1 + harmonic * irregularity;
      const customEdge = edgeScale ? clamp(Number(edgeScale(angle)) || 1, 0.72, 1.28) : 1;
      const shorelineScale = proceduralEdge * customEdge;
      const localRadius = radius * lakeDistance * (1 + (shorelineScale - 1) * lakeDistance * lakeDistance);
      const x = Math.cos(angle) * localRadius;
      const z = Math.sin(angle) * localRadius;
      positions.push(x, 0, z);
      normals.push(0, 1, 0);
      uvs.push(0.5 + x / (uvExtent * 2), 0.5 + z / (uvExtent * 2));
      lakeDistances.push(lakeDistance);
    }
  }

  const ringStride = angularSegments + 1;
  for (let segment = 0; segment < angularSegments; segment += 1) {
    const current = 1 + segment;
    const next = current + 1;
    indices.push(0, next, current);
  }
  for (let ring = 1; ring < radialSegments; ring += 1) {
    const inner = 1 + (ring - 1) * ringStride;
    const outer = inner + ringStride;
    for (let segment = 0; segment < angularSegments; segment += 1) {
      const innerCurrent = inner + segment;
      const innerNext = innerCurrent + 1;
      const outerCurrent = outer + segment;
      const outerNext = outerCurrent + 1;
      indices.push(innerCurrent, outerNext, outerCurrent);
      indices.push(innerCurrent, innerNext, outerNext);
    }
  }

  const geometry = new THREE.BufferGeometry();
  geometry.name = 'alan-v22-subdivided-lake';
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geometry.setAttribute('normal', new THREE.Float32BufferAttribute(normals, 3));
  geometry.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2));
  geometry.setAttribute('lakeDistance', new THREE.Float32BufferAttribute(lakeDistances, 1));
  geometry.setIndex(indices);
  geometry.computeBoundingBox();
  geometry.computeBoundingSphere();
  geometry.userData.v22 = {
    kind: 'lake',
    radius,
    radialSegments,
    angularSegments,
    triangles: indices.length / 3
  };
  return geometry;
}

/**
 * Physically inspired opaque water: four analytic wave bands, Schlick Fresnel,
 * a broad/tight sun reflection path, shoreline foam, and explicit distance haze.
 * It uses GLSL 1 constructs only, so it remains valid on WebGL1/iOS.
 */
export function createWaterMaterial(THREE, options = {}) {
  if (!THREE || !THREE.ShaderMaterial) throw new TypeError('createWaterMaterial requires THREE');
  const mobile = Boolean(options.mobile);
  const uniforms = {
    uTime: { value: Number(options.time) || 0 },
    uWaveAmplitude: { value: Number(options.waveAmplitude) || (mobile ? 0.14 : 0.17) },
    uWaveFrequency: { value: Number(options.waveFrequency) || 0.82 },
    uWindSpeed: { value: Number(options.windSpeed) || 0.78 },
    uWindDirection: { value: new THREE.Vector2(...(options.windDirection || [0.88, 0.34])).normalize() },
    uSunDirection: { value: new THREE.Vector3(...(options.sunDirection || [-0.48, 0.38, -0.79])).normalize() },
    uDeepColor: { value: new THREE.Color(options.deepColor ?? 0x073b46) },
    uMidColor: { value: new THREE.Color(options.midColor ?? 0x176a72) },
    uShallowColor: { value: new THREE.Color(options.shallowColor ?? 0x4b9287) },
    uSkyZenithColor: { value: new THREE.Color(options.skyZenithColor ?? 0x315d78) },
    uHorizonColor: { value: new THREE.Color(options.horizonColor ?? 0xd4a67a) },
    uSunColor: { value: new THREE.Color(options.sunColor ?? 0xffcf8a) },
    uFoamColor: { value: new THREE.Color(options.foamColor ?? 0xdbe7d8) },
    uHazeColor: { value: new THREE.Color(options.hazeColor ?? 0xaab8ad) },
    uFoamWidth: { value: clamp(Number(options.foamWidth) || 0.055, 0.01, 0.2) },
    uHazeDensity: { value: Math.max(0, Number(options.hazeDensity) || (mobile ? 0.011 : 0.008)) },
    uSunPathStrength: { value: Math.max(0, Number(options.sunPathStrength) || 1.25) },
    uSparkleStrength: { value: Math.max(0, Number(options.sparkleStrength) || (mobile ? 0.16 : 0.28)) },
    uOpacity: { value: clamp(Number.isFinite(options.opacity) ? Number(options.opacity) : 1, 0, 1) }
  };

  const vertexShader = `
    uniform float uTime;
    uniform float uWaveAmplitude;
    uniform float uWaveFrequency;
    uniform float uWindSpeed;
    uniform vec2 uWindDirection;
    attribute float lakeDistance;
    varying vec3 vWorldPosition;
    varying vec3 vWorldNormal;
    varying float vLakeDistance;
    varying float vWaveHeight;

    void addWave(
      vec2 point,
      vec2 direction,
      float frequency,
      float amplitude,
      float speed,
      inout float height,
      inout float derivativeX,
      inout float derivativeZ
    ) {
      float phase = dot(point, direction) * frequency + uTime * speed;
      float sineValue = sin(phase);
      float cosineValue = cos(phase);
      height += sineValue * amplitude;
      derivativeX += cosineValue * amplitude * frequency * direction.x;
      derivativeZ += cosineValue * amplitude * frequency * direction.y;
    }

    void main() {
      vec3 displaced = position;
      vec2 wind = normalize(uWindDirection + vec2(0.0001, 0.0));
      vec2 crossWind = vec2(-wind.y, wind.x);
      vec2 diagonalA = normalize(wind * 0.78 + crossWind * 0.62);
      vec2 diagonalB = normalize(wind * 0.91 - crossWind * 0.41);
      float height = 0.0;
      float derivativeX = 0.0;
      float derivativeZ = 0.0;
      float frequency = uWaveFrequency;
      addWave(displaced.xz, wind, frequency, uWaveAmplitude * 0.52, uWindSpeed * 1.00, height, derivativeX, derivativeZ);
      addWave(displaced.xz, diagonalA, frequency * 1.73, uWaveAmplitude * 0.25, -uWindSpeed * 1.31, height, derivativeX, derivativeZ);
      addWave(displaced.xz, diagonalB, frequency * 3.10, uWaveAmplitude * 0.14, uWindSpeed * 1.87, height, derivativeX, derivativeZ);
      addWave(displaced.xz, crossWind, frequency * 5.35, uWaveAmplitude * 0.065, -uWindSpeed * 2.42, height, derivativeX, derivativeZ);
      float shoreFade = mix(1.0, 0.22, smoothstep(0.88, 1.0, lakeDistance));
      height *= shoreFade;
      derivativeX *= shoreFade;
      derivativeZ *= shoreFade;
      displaced.y += height;
      vec3 localNormal = normalize(vec3(-derivativeX, 1.0, -derivativeZ));
      vec4 worldPosition = modelMatrix * vec4(displaced, 1.0);
      vWorldPosition = worldPosition.xyz;
      vWorldNormal = normalize(mat3(modelMatrix) * localNormal);
      vLakeDistance = lakeDistance;
      vWaveHeight = height / max(0.001, uWaveAmplitude);
      gl_Position = projectionMatrix * viewMatrix * worldPosition;
    }
  `;

  const fragmentShader = `
    uniform float uTime;
    uniform vec3 uSunDirection;
    uniform vec3 uDeepColor;
    uniform vec3 uMidColor;
    uniform vec3 uShallowColor;
    uniform vec3 uSkyZenithColor;
    uniform vec3 uHorizonColor;
    uniform vec3 uSunColor;
    uniform vec3 uFoamColor;
    uniform vec3 uHazeColor;
    uniform float uFoamWidth;
    uniform float uHazeDensity;
    uniform float uSunPathStrength;
    uniform float uSparkleStrength;
    uniform float uOpacity;
    varying vec3 vWorldPosition;
    varying vec3 vWorldNormal;
    varying float vLakeDistance;
    varying float vWaveHeight;

    float hash21(vec2 point) {
      point = fract(point * vec2(123.34, 456.21));
      point += dot(point, point + 45.32);
      return fract(point.x * point.y);
    }

    void main() {
      vec3 normal = normalize(vWorldNormal);
      vec3 viewDirection = normalize(cameraPosition - vWorldPosition);
      vec3 sunDirection = normalize(uSunDirection);
      float normalView = clamp(dot(normal, viewDirection), 0.0, 1.0);
      float fresnel = 0.02 + 0.98 * pow(1.0 - normalView, 5.0);

      float centerDepth = pow(clamp(1.0 - vLakeDistance, 0.0, 1.0), 0.58);
      vec3 waterBody = mix(uShallowColor, uMidColor, smoothstep(0.0, 0.58, centerDepth));
      waterBody = mix(waterBody, uDeepColor, smoothstep(0.34, 1.0, centerDepth) * 0.78);
      waterBody *= 0.84 + max(normal.y, 0.0) * 0.16;

      vec3 reflectedDirection = reflect(-viewDirection, normal);
      float reflectedHeight = clamp(reflectedDirection.y * 0.5 + 0.5, 0.0, 1.0);
      vec3 reflectedSky = mix(uHorizonColor, uSkyZenithColor, smoothstep(0.28, 0.86, reflectedHeight));
      vec3 color = mix(waterBody, reflectedSky, clamp(fresnel * 0.86 + 0.06, 0.0, 0.94));

      vec3 sunReflection = reflect(-sunDirection, normal);
      float sunAlignment = max(dot(sunReflection, viewDirection), 0.0);
      float broadGlint = pow(sunAlignment, 24.0) * 0.22;
      float tightGlint = pow(sunAlignment, 150.0);
      float sparkleCell = hash21(floor((vWorldPosition.xz + vec2(uTime * 0.18, -uTime * 0.11)) * 3.2));
      float sparkle = smoothstep(0.82, 0.995, sparkleCell + abs(vWaveHeight) * 0.12);
      float sunPath = (broadGlint + tightGlint * (0.72 + sparkle * uSparkleStrength)) * uSunPathStrength;
      color += uSunColor * sunPath;

      float shoreBand = smoothstep(1.0 - uFoamWidth, 1.0, vLakeDistance);
      float foamWave = 0.5 + 0.5 * sin(vLakeDistance * 184.0 - uTime * 1.55
        + sin(vWorldPosition.x * 1.73 + vWorldPosition.z * 2.17));
      float brokenFoam = smoothstep(0.46, 0.78, foamWave + abs(vWaveHeight) * 0.2);
      float foam = shoreBand * brokenFoam * (0.54 + sparkleCell * 0.46);
      color = mix(color, uFoamColor, clamp(foam * 0.72, 0.0, 0.78));

      float cameraDistance = length(cameraPosition - vWorldPosition);
      float haze = 1.0 - exp(-cameraDistance * uHazeDensity);
      color = mix(color, uHazeColor, clamp(haze * 0.58, 0.0, 0.72));
      gl_FragColor = vec4(color, uOpacity);
      #include <tonemapping_fragment>
      #include <colorspace_fragment>
    }
  `;

  const material = new THREE.ShaderMaterial({
    name: 'alan-v22-physical-water',
    uniforms,
    vertexShader,
    fragmentShader,
    transparent: uniforms.uOpacity.value < 1,
    depthWrite: uniforms.uOpacity.value >= 1,
    depthTest: true,
    side: THREE.FrontSide,
    fog: false,
    toneMapped: true,
    precision: mobile ? 'mediump' : 'highp'
  });
  material.userData.v22Water = true;
  return material;
}

/** Convenience factory returning a Mesh with matched v22 lake geometry/material. */
export function createLakeSurface(THREE, options = {}) {
  const geometry = createLakeGeometry(THREE, options);
  const material = createWaterMaterial(THREE, options);
  const mesh = new THREE.Mesh(geometry, material);
  mesh.name = options.name || 'alan-v22-lake-surface';
  mesh.frustumCulled = true;
  mesh.receiveShadow = Boolean(options.receiveShadow);
  return mesh;
}

/** Update animated water values without allocating new uniforms each frame. */
export function updateWaterUniforms(material, elapsedSeconds, values = {}) {
  if (!material || !material.uniforms || !material.userData.v22Water) return material;
  const uniforms = material.uniforms;
  if (Number.isFinite(elapsedSeconds)) uniforms.uTime.value = elapsedSeconds;
  if (values.sunDirection && uniforms.uSunDirection) uniforms.uSunDirection.value.copy(values.sunDirection).normalize();
  if (values.windDirection && uniforms.uWindDirection) uniforms.uWindDirection.value.copy(values.windDirection).normalize();
  if (Number.isFinite(values.waveAmplitude)) uniforms.uWaveAmplitude.value = Math.max(0, values.waveAmplitude);
  if (Number.isFinite(values.windSpeed)) uniforms.uWindSpeed.value = values.windSpeed;
  if (Number.isFinite(values.hazeDensity)) uniforms.uHazeDensity.value = Math.max(0, values.hazeDensity);
  if (Number.isFinite(values.sunPathStrength)) uniforms.uSunPathStrength.value = Math.max(0, values.sunPathStrength);
  return material;
}

function pushKite(positions, colors, uvs, indices, vertices, vertexColors) {
  const start = positions.length / 3;
  vertices.forEach((vertex, index) => {
    positions.push(vertex[0], vertex[1], vertex[2]);
    const color = vertexColors[index];
    colors.push(color.r, color.g, color.b);
  });
  uvs.push(0, 0.5, 0.47, 1, 1, 0.5, 0.47, 0);
  indices.push(start, start + 1, start + 2, start, start + 2, start + 3);
}

/**
 * Build branch-whorl pine foliage for InstancedMesh. The crossed, drooping
 * branch kites form an open silhouette instead of three unmistakable cones.
 */
export function createPineFoliageGeometry(THREE, options = {}) {
  if (!THREE || !THREE.BufferGeometry) throw new TypeError('createPineFoliageGeometry requires THREE');
  const mobile = Boolean(options.mobile);
  const height = Math.max(1, Number(options.height) || 6.5);
  const baseRadius = Math.max(0.25, Number(options.radius) || 2.05);
  const levels = clamp(Math.round(Number(options.levels) || (mobile ? 7 : 9)), 4, 14);
  const branchesPerLevel = clamp(Math.round(Number(options.branchesPerLevel) || (mobile ? 7 : 9)), 5, 14);
  const random = randomFactory(options.seed ?? 2267);
  const positions = [];
  const colors = [];
  const uvs = [];
  const indices = [];
  const deepColor = new THREE.Color(options.baseColor ?? 0x123723);
  const freshColor = new THREE.Color(options.tipColor ?? 0x3b6b42);

  for (let level = 0; level < levels; level += 1) {
    const t = level / Math.max(1, levels - 1);
    const y = height * (0.12 + t * 0.78);
    const levelRadius = baseRadius * Math.pow(1 - t, 0.69) * (0.88 + random() * 0.2) + baseRadius * 0.055;
    const phase = random() * TAU + level * 0.39;
    for (let branch = 0; branch < branchesPerLevel; branch += 1) {
      const angle = phase + (branch / branchesPerLevel) * TAU + (random() - 0.5) * 0.18;
      const directionX = Math.cos(angle);
      const directionZ = Math.sin(angle);
      const perpendicularX = -directionZ;
      const perpendicularZ = directionX;
      const length = levelRadius * (0.8 + random() * 0.28);
      const width = length * (0.255 + random() * 0.085);
      const droop = length * (0.08 + (1 - t) * 0.075 + random() * 0.035);
      const rootRadius = baseRadius * 0.045;
      const root = [directionX * rootRadius, y, directionZ * rootRadius];
      const left = [
        directionX * length * 0.5 + perpendicularX * width,
        y - droop * 0.38 + length * 0.035,
        directionZ * length * 0.5 + perpendicularZ * width
      ];
      const tip = [directionX * length, y - droop, directionZ * length];
      const right = [
        directionX * length * 0.5 - perpendicularX * width,
        y - droop * 0.42 - length * 0.025,
        directionZ * length * 0.5 - perpendicularZ * width
      ];
      const baseMix = clamp(t * 0.38 + random() * 0.08, 0, 1);
      const tipMix = clamp(0.34 + t * 0.48 + random() * 0.12, 0, 1);
      const rootColor = deepColor.clone().lerp(freshColor, baseMix);
      const midColor = deepColor.clone().lerp(freshColor, (baseMix + tipMix) * 0.5);
      const tipColor = deepColor.clone().lerp(freshColor, tipMix);
      pushKite(positions, colors, uvs, indices, [root, left, tip, right], [rootColor, midColor, tipColor, midColor]);

      const upper = [directionX * length * 0.52, y + width * 0.86 - droop * 0.25, directionZ * length * 0.52];
      const lower = [directionX * length * 0.52, y - width * 0.94 - droop * 0.45, directionZ * length * 0.52];
      const verticalRoot = [directionX * rootRadius, y + width * 0.08, directionZ * rootRadius];
      pushKite(
        positions,
        colors,
        uvs,
        indices,
        [verticalRoot, upper, tip, lower],
        [rootColor, midColor, tipColor, midColor]
      );
    }
  }

  const crownBranches = mobile ? 5 : 7;
  for (let branch = 0; branch < crownBranches; branch += 1) {
    const angle = (branch / crownBranches) * TAU + random() * 0.34;
    const dx = Math.cos(angle);
    const dz = Math.sin(angle);
    const sideX = -dz;
    const sideZ = dx;
    const crownWidth = baseRadius * 0.1;
    const root = [dx * baseRadius * 0.03, height * 0.76, dz * baseRadius * 0.03];
    const left = [dx * baseRadius * 0.13 + sideX * crownWidth, height * 0.9, dz * baseRadius * 0.13 + sideZ * crownWidth];
    const tip = [dx * baseRadius * 0.05, height, dz * baseRadius * 0.05];
    const right = [dx * baseRadius * 0.13 - sideX * crownWidth, height * 0.9, dz * baseRadius * 0.13 - sideZ * crownWidth];
    const crownColor = deepColor.clone().lerp(freshColor, 0.82);
    const midColor = deepColor.clone().lerp(freshColor, 0.62);
    pushKite(positions, colors, uvs, indices, [root, left, tip, right], [midColor, crownColor, crownColor, crownColor]);
  }

  const geometry = new THREE.BufferGeometry();
  geometry.name = 'alan-v22-pine-branch-whorls';
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
  geometry.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2));
  geometry.setIndex(indices);
  geometry.computeVertexNormals();
  geometry.computeBoundingBox();
  geometry.computeBoundingSphere();
  geometry.userData.v22 = {
    kind: 'pine-foliage',
    height,
    radius: baseRadius,
    levels,
    branchesPerLevel,
    triangles: indices.length / 3
  };
  return geometry;
}

/**
 * Standard PBR foliage material with a very small vertex-only wind patch.
 * The patch supports both Mesh and InstancedMesh and requires no GLSL3 APIs.
 */
export function createPineFoliageMaterial(THREE, options = {}) {
  if (!THREE || !THREE.MeshStandardMaterial) throw new TypeError('createPineFoliageMaterial requires THREE');
  const windUniforms = {
    uFoliageTime: { value: Number(options.time) || 0 },
    uFoliageWind: { value: Number.isFinite(options.windStrength) ? Number(options.windStrength) : 0.045 },
    uFoliageHeight: { value: Math.max(0.1, Number(options.height) || 6.5) }
  };
  const material = new THREE.MeshStandardMaterial({
    name: 'alan-v22-pine-pbr',
    color: options.color ?? 0xffffff,
    roughness: Number.isFinite(options.roughness) ? Number(options.roughness) : 0.88,
    metalness: 0,
    vertexColors: true,
    side: THREE.DoubleSide,
    map: options.map || null,
    normalMap: options.normalMap || null,
    alphaTest: Number(options.alphaTest) || 0,
    transparent: false,
    dithering: true
  });
  material.userData.v22Foliage = true;
  material.userData.v22WindUniforms = windUniforms;
  material.onBeforeCompile = (shader) => {
    shader.uniforms.uFoliageTime = windUniforms.uFoliageTime;
    shader.uniforms.uFoliageWind = windUniforms.uFoliageWind;
    shader.uniforms.uFoliageHeight = windUniforms.uFoliageHeight;
    shader.vertexShader = shader.vertexShader.replace(
      '#include <common>',
      `#include <common>\n      uniform float uFoliageTime;\n      uniform float uFoliageWind;\n      uniform float uFoliageHeight;`
    );
    shader.vertexShader = shader.vertexShader.replace(
      '#include <begin_vertex>',
      `vec3 transformed = vec3(position);\n      float foliagePhase = 0.0;\n      #ifdef USE_INSTANCING\n        foliagePhase = instanceMatrix[3][0] * 0.061 + instanceMatrix[3][2] * 0.043;\n      #endif\n      float foliageHeight = clamp(transformed.y / max(0.1, uFoliageHeight), 0.0, 1.0);\n      float foliageBend = foliageHeight * foliageHeight * uFoliageWind;\n      transformed.x += sin(uFoliageTime * 0.73 + foliagePhase + transformed.y * 0.41) * foliageBend;\n      transformed.z += cos(uFoliageTime * 0.57 + foliagePhase * 1.37 + transformed.y * 0.29) * foliageBend * 0.62;`
    );
    material.userData.v22CompiledShader = shader;
  };
  material.customProgramCacheKey = () => 'alan-v22-pine-wind-glsl1';
  return material;
}

/** Update foliage wind time/strength; safe to call before shader compilation. */
export function updatePineFoliageUniforms(material, elapsedSeconds, windStrength) {
  const uniforms = material?.userData?.v22WindUniforms;
  if (!uniforms) return material;
  if (Number.isFinite(elapsedSeconds)) uniforms.uFoliageTime.value = elapsedSeconds;
  if (Number.isFinite(windStrength)) uniforms.uFoliageWind.value = Math.max(0, windStrength);
  return material;
}

/**
 * Create a deterministic, asymmetric high-detail boulder. Detail 1 is a good
 * mobile LOD (80 source faces); detail 2 is the desktop default (320 faces).
 */
export function createRockGeometry(THREE, options = {}) {
  if (!THREE || !THREE.IcosahedronGeometry) throw new TypeError('createRockGeometry requires THREE');
  const mobile = Boolean(options.mobile);
  const radius = Math.max(0.05, Number(options.radius) || 1);
  const detail = clamp(Math.round(Number.isFinite(options.detail) ? options.detail : (mobile ? 1 : 2)), 0, 3);
  const roughness = clamp(Number.isFinite(options.roughness) ? options.roughness : 0.2, 0, 0.42);
  const flattenBottom = clamp(Number.isFinite(options.flattenBottom) ? options.flattenBottom : 0.82, 0, 1);
  const scaleOption = options.scale || [1, 0.78, 1.08];
  const scaleX = Math.max(0.05, Number(scaleOption[0]) || 1);
  const scaleY = Math.max(0.05, Number(scaleOption[1]) || 0.78);
  const scaleZ = Math.max(0.05, Number(scaleOption[2]) || 1.08);
  const phase = (seedNumber(options.seed ?? 2293) / 4294967295) * TAU;
  const geometry = new THREE.IcosahedronGeometry(radius, detail);
  geometry.name = 'alan-v22-deformed-rock';
  const position = geometry.attributes.position;

  for (let index = 0; index < position.count; index += 1) {
    let x = position.getX(index);
    let y = position.getY(index);
    let z = position.getZ(index);
    const inverseLength = 1 / Math.max(1e-8, Math.sqrt(x * x + y * y + z * z));
    const dx = x * inverseLength;
    const dy = y * inverseLength;
    const dz = z * inverseLength;
    const broad = Math.sin(dx * 3.71 + dy * 5.13 + dz * 2.89 + phase) * 0.52
      + Math.sin(dx * 7.91 - dy * 3.47 + dz * 6.23 - phase * 0.71) * 0.31
      + Math.sin((dx + dy - dz) * 13.7 + phase * 1.83) * 0.17;
    const radial = radius * (1 + broad * roughness);
    x = dx * radial * scaleX;
    y = dy * radial * scaleY;
    z = dz * radial * scaleZ;
    x += y * Math.sin(phase * 1.7) * 0.055;
    z += y * Math.cos(phase * 1.3) * 0.045;
    const floorY = -radius * scaleY * 0.7;
    if (y < floorY) y = floorY + (y - floorY) * (1 - flattenBottom);
    position.setXYZ(index, x, y, z);
  }

  position.needsUpdate = true;
  geometry.computeVertexNormals();
  geometry.computeBoundingBox();
  geometry.computeBoundingSphere();
  geometry.userData.v22 = {
    kind: 'rock',
    detail,
    radius,
    roughness,
    triangles: geometry.index ? geometry.index.count / 3 : position.count / 3
  };
  return geometry;
}
