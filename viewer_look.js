// viewer_look.js - everything that makes the model look like a real object
// rather than a CAD drawing:
//
//   - studio lighting, reflections, soft shadows and ambient occlusion
//   - a material finish for every part (textured plastic, galvanised steel,
//     glass, clear lenses, printed PETG, rubber ...)
//   - a lit screen with a picture, and a backlight that glows
//   - cables drawn as bundles of round wires and flat ribbons
//   - a wall and a sideboard for the set to live in
//
// The picture on the screen and all textures are generated here in code. No
// image files are loaded.

import * as THREE from "three";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";
import { EffectComposer } from "three/addons/postprocessing/EffectComposer.js";
import { RenderPass } from "three/addons/postprocessing/RenderPass.js";
import { GTAOPass } from "three/addons/postprocessing/GTAOPass.js";
import { UnrealBloomPass } from "three/addons/postprocessing/UnrealBloomPass.js";
import { OutputPass } from "three/addons/postprocessing/OutputPass.js";

// ---- generated textures -------------------------------------------------------
// Small repeatable random number generator, so textures look the same every load.
function random(seed) {
  let s = seed;
  return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296);
}

function canvasTexture(size, draw, { repeat = true, colour = false } = {}) {
  const canvas = document.createElement("canvas");
  canvas.width = size[0]; canvas.height = size[1];
  draw(canvas.getContext("2d"), size[0], size[1]);
  const texture = new THREE.CanvasTexture(canvas);
  if (repeat) texture.wrapS = texture.wrapT = THREE.RepeatWrapping;
  if (colour) texture.colorSpace = THREE.SRGBColorSpace;
  texture.anisotropy = 8;
  return texture;
}

// Fine random grain: moulded-plastic texture, paint, rubber.
const grain = canvasTexture([256, 256], (c, w, h) => {
  const rnd = random(7), image = c.createImageData(w, h);
  for (let i = 0; i < w * h; i++) {
    const v = 110 + rnd() * 90;
    image.data.set([v, v, v, 255], i * 4);
  }
  c.putImageData(image, 0, 0);
});

// Streaks: rolled or brushed sheet metal.
const streaks = canvasTexture([256, 256], (c, w, h) => {
  const rnd = random(21);
  c.fillStyle = "#888"; c.fillRect(0, 0, w, h);
  for (let i = 0; i < 900; i++) {
    const v = 90 + rnd() * 110;
    c.fillStyle = `rgba(${v},${v},${v},0.35)`;
    c.fillRect(0, rnd() * h, w, 0.6 + rnd() * 1.4);
  }
});

// Blotches: the crystal pattern ("spangle") on galvanised steel.
const spangle = canvasTexture([256, 256], (c, w, h) => {
  const rnd = random(5);
  c.fillStyle = "#909090"; c.fillRect(0, 0, w, h);
  for (let i = 0; i < 260; i++) {
    const v = 105 + rnd() * 90, x = rnd() * w, y = rnd() * h, r = 6 + rnd() * 16;
    c.fillStyle = `rgba(${v},${v},${v},0.5)`;
    c.beginPath();
    for (let k = 0; k < 6; k++) c.lineTo(x + Math.cos(k + rnd()) * r, y + Math.sin(k + rnd()) * r);
    c.fill();
  }
});

// Layer lines: the surface of a 3D print.
const layers = canvasTexture([8, 64], (c, w, h) => {
  for (let y = 0; y < h; y++) {
    const v = 128 + Math.sin((y / h) * Math.PI * 2 * 8) * 90;
    c.fillStyle = `rgb(${v},${v},${v})`;
    c.fillRect(0, y, w, 1);
  }
});

// Wood grain for the sideboard.
const wood = canvasTexture([512, 512], (c, w, h) => {
  const rnd = random(33);
  c.fillStyle = "#6f4a2b"; c.fillRect(0, 0, w, h);
  for (let i = 0; i < 420; i++) {
    const y = rnd() * h, dark = rnd() > 0.5;
    c.strokeStyle = dark ? `rgba(48,28,12,${0.10 + rnd() * 0.22})` : `rgba(160,112,66,${0.08 + rnd() * 0.18})`;
    c.lineWidth = 0.6 + rnd() * 2.2;
    c.beginPath(); c.moveTo(0, y);
    for (let x = 0; x <= w; x += 32) c.lineTo(x, y + Math.sin(x / 70 + i) * 3 + (rnd() - 0.5) * 2);
    c.stroke();
  }
}, { colour: true });

// Conductor stripes for flat ribbon cables.
const ribbonStripes = canvasTexture([64, 8], (c, w, h) => {
  c.fillStyle = "#e9e9e4"; c.fillRect(0, 0, w, h);
  c.fillStyle = "#b9b9b2";
  for (let x = 0; x < w; x += 4) c.fillRect(x, 0, 2, h);
}, { colour: true });

// The picture shown on the screen: a generated sunset over mountains and water.
function screenPicture() {
  return canvasTexture([1920, 1080], (c, w, h) => {
    const rnd = random(11), horizon = h * 0.62;
    const sky = c.createLinearGradient(0, 0, 0, horizon);
    sky.addColorStop(0, "#0b1f4b"); sky.addColorStop(0.45, "#3d5fa8");
    sky.addColorStop(0.8, "#f08a4b"); sky.addColorStop(1, "#ffd08a");
    c.fillStyle = sky; c.fillRect(0, 0, w, horizon);
    const sun = c.createRadialGradient(w * 0.68, horizon - 20, 0, w * 0.68, horizon - 20, h * 0.5);
    sun.addColorStop(0, "rgba(255,244,214,1)"); sun.addColorStop(0.08, "rgba(255,214,140,0.9)");
    sun.addColorStop(1, "rgba(255,160,80,0)");
    c.fillStyle = sun; c.fillRect(0, 0, w, horizon);
    for (let i = 0; i < 9; i++) {                       // thin clouds
      const x = rnd() * w, y = h * (0.12 + rnd() * 0.3), len = 200 + rnd() * 500;
      const cloud = c.createLinearGradient(x, 0, x + len, 0);
      cloud.addColorStop(0, "rgba(255,200,170,0)"); cloud.addColorStop(0.5, "rgba(255,196,160,0.35)");
      cloud.addColorStop(1, "rgba(255,200,170,0)");
      c.fillStyle = cloud; c.fillRect(x, y, len, 6 + rnd() * 14);
    }
    const ranges = [["#5b5f8f", 0.30, 90], ["#3b3f6b", 0.20, 70], ["#1f2444", 0.12, 55], ["#0e1126", 0.05, 40]];
    for (const [colour, lift, rough] of ranges) {       // four mountain ranges, far to near
      c.fillStyle = colour; c.beginPath(); c.moveTo(0, horizon);
      let y = horizon - h * lift;
      for (let x = 0; x <= w; x += 12) { y += (rnd() - 0.5) * rough * 0.35; y = Math.min(horizon - 8, Math.max(horizon - h * (lift + 0.14), y)); c.lineTo(x, y); }
      c.lineTo(w, horizon); c.fill();
    }
    const water = c.createLinearGradient(0, horizon, 0, h);
    water.addColorStop(0, "#f2a35e"); water.addColorStop(0.25, "#7a5a78"); water.addColorStop(1, "#0a0f24");
    c.fillStyle = water; c.fillRect(0, horizon, w, h - horizon);
    for (let i = 0; i < 160; i++) {                     // glints on the water
      const y = horizon + Math.pow(rnd(), 1.8) * (h - horizon);
      const spread = (y - horizon) * 0.9 + 30;
      c.fillStyle = `rgba(255,224,170,${0.5 * (1 - (y - horizon) / (h - horizon))})`;
      c.fillRect(w * 0.68 + (rnd() - 0.5) * spread, y, 20 + rnd() * 60, 2);
    }
  }, { repeat: false, colour: true });
}

// ---- materials -------------------------------------------------------------------
const P = (colour, options = {}) => new THREE.MeshPhysicalMaterial({ color: colour, ...options });

function textured(map, repeatPerMm) {
  const texture = map.clone();
  texture.repeat.set(repeatPerMm, repeatPerMm);
  texture.needsUpdate = true;
  return texture;
}

// Each entry: a function that returns a fresh material. Looked up by item name
// first, then by group.
const FINISH = {
  // Enclosure
  rear_cover: () => P(0x161618, { roughness: 0.78, bumpMap: textured(grain, 0.09), bumpScale: 0.35 }),
  front_bezel: () => P(0x0a0a0b, { roughness: 0.3, clearcoat: 0.55, clearcoatRoughness: 0.25 }),
  brand_badge: () => P(0xdfe2e6, { metalness: 1, roughness: 0.18 }),
  ir_window: () => P(0x3a0508, { roughness: 0.08, transparent: true, opacity: 0.85, clearcoat: 1 }),
  cover_screws: () => P(0x9a9da3, { metalness: 1, roughness: 0.35 }),
  // Panel and backlight
  lcd_cell: () => P(0x050608, { roughness: 0.25, clearcoat: 0.6, clearcoatRoughness: 0.2, envMapIntensity: 0.2 }),
  mould_frame: () => P(0x1d1d20, { roughness: 0.7 }),
  prism_sheet_upper: () => P(0xe8f1ff, { roughness: 0.18, transparent: true, opacity: 0.4, iridescence: 1, iridescenceIOR: 1.6, side: THREE.DoubleSide }),
  prism_sheet_lower: () => P(0xe8f1ff, { roughness: 0.18, transparent: true, opacity: 0.4, iridescence: 1, iridescenceIOR: 1.6, side: THREE.DoubleSide }),
  diffuser_sheet: () => P(0xf6f6f4, { roughness: 0.75, transparent: true, opacity: 0.7, side: THREE.DoubleSide }),
  diffuser_plate: () => P(0xf7f7f4, { roughness: 0.9, transparent: true, opacity: 0.93 }),
  support_pins: () => P(0xf3f3ee, { roughness: 0.45 }),
  reflector_sheet: () => P(0xfbfbf8, { roughness: 0.95 }),
  led_lenses: () => P(0xffffff, { roughness: 0.04, transmission: 1, thickness: 4, ior: 1.49 }),
  led_chips: () => P(0xfff1b8, { roughness: 0.4 }),
  led_strips: () => P(0xf1f1ec, { roughness: 0.55 }),
  source_boards: () => P(0x0d5a2a, { roughness: 0.45, clearcoat: 0.4 }),
  source_sockets: () => P(0xe9e2cf, { roughness: 0.7 }),
  source_cofs: () => P(0xc9812a, { roughness: 0.3, transparent: true, opacity: 0.85, side: THREE.DoubleSide }),
  // Chassis
  back_chassis: () => P(0xa4a8ae, { metalness: 0.85, roughness: 0.68, envMapIntensity: 0.8, map: textured(spangle, 0.02), roughnessMap: textured(spangle, 0.02), bumpMap: textured(streaks, 0.03), bumpScale: 0.05 }),
  // Speakers and mains
  speakers: () => P(0x0f0f10, { roughness: 0.65, bumpMap: textured(grain, 0.12), bumpScale: 0.25 }),
  mains_inlet: () => P(0x0c0c0d, { roughness: 0.5 }),
  // Stand feet
  stand_feet: () => P(0x0b0b0c, { roughness: 0.32, clearcoat: 0.5 }),
  // Remote control
  remote_top_shell: () => P(0x101012, { roughness: 0.55, bumpMap: textured(grain, 0.2), bumpScale: 0.15 }),
  remote_bottom_shell: () => P(0x131315, { roughness: 0.6, bumpMap: textured(grain, 0.2), bumpScale: 0.15 }),
  remote_battery_door: () => P(0x151517, { roughness: 0.6, bumpMap: textured(grain, 0.2), bumpScale: 0.15 }),
  remote_keypad: () => P(0x2e3034, { roughness: 0.95 }),
  remote_electronics: () => P(0x0d5a2a, { roughness: 0.45, clearcoat: 0.4 }),
  remote_batteries: () => P(0xc79a2a, { metalness: 0.9, roughness: 0.3 }),
};
const GROUP_FINISH = {
  // 3D-printed PETG: slightly glossy, with visible layer lines.
  "Wall mount": () => P(0x121214, { roughness: 0.42, bumpMap: textured(layers, 0.6), bumpScale: 0.12 }),
};

export function materialFor(entry, fallbackColour) {
  const make = FINISH[entry.name] ?? GROUP_FINISH[entry.group];
  const material = make ? make() : P(fallbackColour, { roughness: 0.6 });
  if ((entry.opacity ?? 1) < 1 && !material.transmission) material.transparent = true;
  if (material.transparent) material.depthWrite = material.opacity > 0.9;
  return material;
}

// STL meshes carry no texture coordinates. Give each face coordinates from its
// own flat projection, in millimetres, so textures tile evenly over any part.
export function addBoxUVs(geometry) {
  const position = geometry.attributes.position, normal = geometry.attributes.normal;
  const uv = new Float32Array(position.count * 2);
  for (let i = 0; i < position.count; i++) {
    const ax = Math.abs(normal.getX(i)), ay = Math.abs(normal.getY(i)), az = Math.abs(normal.getZ(i));
    const x = position.getX(i), y = position.getY(i), z = position.getZ(i);
    if (ax >= ay && ax >= az) uv.set([y, z], i * 2);
    else if (ay >= az) uv.set([x, z], i * 2);
    else uv.set([x, y], i * 2);
  }
  geometry.setAttribute("uv", new THREE.BufferAttribute(uv, 2));
}

// ---- lighting, shadows and post-processing ----------------------------------------
export function setupRendering(renderer, scene, camera) {
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 0.72;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;

  // Soft studio reflections on every surface.
  const pmrem = new THREE.PMREMGenerator(renderer);
  // (The renderer is passed in so the environment's lamps use physical brightness.)
  scene.environment = pmrem.fromScene(new RoomEnvironment(renderer), 0.03).texture;

  // Main light: high, from the front left, casting the shadows.
  const sun = new THREE.DirectionalLight(0xfff4e6, 2.2);
  sun.position.set(-520, 900, 760);
  sun.target.position.set(0, 40, -40);
  sun.castShadow = true;
  sun.shadow.mapSize.set(4096, 4096);
  Object.assign(sun.shadow.camera, { left: -620, right: 620, top: 520, bottom: -520, near: 100, far: 2600 });
  sun.shadow.bias = -0.0004;
  sun.shadow.normalBias = 0.6;
  sun.shadow.radius = 5;
  scene.add(sun, sun.target);

  // Gentle fill from all round, so the shaded side is never black. (Not a
  // directional lamp: that would glare straight back off the glass screen.)
  const fill = new THREE.HemisphereLight(0xffffff, 0x8a8a90, 0.55);
  scene.add(fill);

  let composer = null, ambient = null;
  try {
    composer = new EffectComposer(renderer);
    composer.addPass(new RenderPass(scene, camera));
    ambient = new GTAOPass(scene, camera, 1, 1);          // darkens creases and contact points
    ambient.updateGtaoMaterial({ radius: 14, distanceExponent: 1.6, thickness: 4, scale: 1.1, samples: 16 });
    ambient.blendIntensity = 0.9;
    composer.addPass(ambient);
    composer.addPass(new UnrealBloomPass(new THREE.Vector2(1, 1), 0.12, 0.4, 1.6));   // glow on lit things
    composer.addPass(new OutputPass());
  } catch (err) {
    console.warn("Post-processing unavailable; using plain rendering.", err);
    composer = null;
  }

  return {
    quality: true,
    resize(width, height) {
      if (composer) composer.setSize(width, height);
    },
    render(target) {
      // Keep the shadow-casting light on the side you are looking from.
      sun.position.y = camera.position.y >= 0 ? 900 : -900;
      if (composer && this.quality) composer.render();
      else renderer.render(scene, camera);
    },
  };
}

export function enableShadows(object) {
  object.traverse((o) => {
    if (o.isMesh && !o.userData.halo) {
      o.castShadow = !(o.material.transparent && o.material.opacity < 0.6);
      o.receiveShadow = true;
    }
  });
}

// ---- the room -------------------------------------------------------------------
export function buildRoom(tableTopZ) {
  const room = new THREE.Group();
  // Painted wall at Y = 0. Single-sided, so it vanishes when you look from behind it.
  const wall = new THREE.Mesh(new THREE.PlaneGeometry(3600, 2400),
    P(0xb9b4aa, { roughness: 0.95, bumpMap: textured(grain, 12), bumpScale: 0.6, envMapIntensity: 0.45 }));
  wall.rotation.x = -Math.PI / 2;
  wall.rotation.z = Math.PI;
  wall.position.set(0, -0.2, 250);
  wall.receiveShadow = true;
  // Sideboard under the set: where the remote lies, and where the feet would stand.
  const top = new THREE.Mesh(new THREE.BoxGeometry(1500, 430, 28),
    P(0xffffff, { map: (() => { const t = wood.clone(); t.repeat.set(3, 1); t.needsUpdate = true; return t; })(), roughness: 0.38, clearcoat: 0.35, clearcoatRoughness: 0.4 }));
  top.position.set(0, 215, tableTopZ - 14);
  const body = new THREE.Mesh(new THREE.BoxGeometry(1460, 400, 420), P(0xcfcbc2, { roughness: 0.55, envMapIntensity: 0.6 }));
  body.position.set(0, 205, tableTopZ - 28 - 210);
  for (const mesh of [top, body]) { mesh.castShadow = true; mesh.receiveShadow = true; }
  const furniture = new THREE.Group();
  furniture.add(top, body);
  room.add(wall, furniture);
  room.userData.furniture = furniture;
  return room;
}

// ---- the screen and the backlight -----------------------------------------------
export function buildScreen(screen) {
  const { width: w, height: h, y, z } = screen;
  // Corners listed so the picture reads correctly from the room (+Y side).
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute([
    w / 2, y + 0.06, z + h / 2, -w / 2, y + 0.06, z + h / 2,
    -w / 2, y + 0.06, z - h / 2, w / 2, y + 0.06, z - h / 2], 3));
  geometry.setAttribute("uv", new THREE.Float32BufferAttribute([0, 1, 1, 1, 1, 0, 0, 0], 2));
  geometry.setIndex([0, 2, 1, 0, 3, 2]);
  geometry.computeVertexNormals();
  const picture = screenPicture();
  const material = P(0x000000, { emissive: 0xffffff, emissiveMap: picture, emissiveIntensity: 2.2,
                                 roughness: 0.3, clearcoat: 0.6, clearcoatRoughness: 0.25, envMapIntensity: 0.12,
                                 // drawn slightly "nearer" so it never flickers against the glass behind it
                                 polygonOffset: true, polygonOffsetFactor: -4, polygonOffsetUnits: -8 });
  const mesh = new THREE.Mesh(geometry, material);
  mesh.userData.setPower = (on) => { material.emissiveIntensity = on ? 2.2 : 0; };
  return mesh;
}

// ---- cables -----------------------------------------------------------------------
const WIRE_COLOURS = {
  cable_psu_to_main: [0xe2b100, 0xe2b100, 0xe2b100, 0x141414, 0x141414, 0x141414, 0xd22b2b, 0x2a6fd6, 0xeeeeea],
  cable_psu_to_led_driver: [0xd22b2b, 0xd22b2b, 0x141414, 0x141414, 0x2a6fd6, 0xeeeeea],
  cable_led_strips: [0xd22b2b, 0x141414, 0xd22b2b, 0x141414],
  cable_mains: [0x7a4a22, 0x2a6fd6],
  cable_speaker_right: [0xd22b2b, 0x141414],
  cable_speaker_left: [0xd22b2b, 0x141414],
  cable_ir_board: [0xd22b2b, 0xeeeeea, 0x2a9d3a, 0xe2b100, 0x141414],
  cable_wifi: [0xd22b2b, 0xeeeeea, 0x2a9d3a, 0x141414],
};

// A path that follows the route but rounds off every corner.
function roundedPath(points, radius) {
  const path = new THREE.CurvePath();
  let from = points[0].clone();
  for (let i = 1; i < points.length; i++) {
    const corner = points[i];
    if (i === points.length - 1) { path.add(new THREE.LineCurve3(from, corner.clone())); break; }
    const next = points[i + 1];
    const r = Math.min(radius, corner.distanceTo(from) / 2, corner.distanceTo(next) / 2);
    const before = corner.clone().add(from.clone().sub(corner).setLength(r));
    const after = corner.clone().add(next.clone().sub(corner).setLength(r));
    if (before.distanceTo(from) > 1e-3) path.add(new THREE.LineCurve3(from, before));
    path.add(new THREE.QuadraticBezierCurve3(before, corner.clone(), after));
    from = after;
  }
  return path;
}

export function buildCables(routes, stackDepth) {
  const groups = new Map();
  const world = ([x, z, w]) => new THREE.Vector3(x, stackDepth + w, z);

  for (const [name, route] of Object.entries(routes)) {
    const group = new THREE.Group();
    const points = route.points.map(world).filter((p, i, all) => i === 0 || p.distanceTo(all[i - 1]) > 1e-3);

    if (route.kind === "wire") {
      // A loose bundle of round insulated wires, each a copy of the route moved a little sideways.
      const colours = WIRE_COLOURS[name] ?? [0x141414];
      const radius = Math.min(0.85, route.thick * 0.36);
      const pitch = Math.min(radius * 2.05, route.width / colours.length);
      colours.forEach((colour, i) => {
        const side = (i - (colours.length - 1) / 2) * pitch * 0.72;
        const lift = ((i % 2) - 0.5) * Math.min(radius, route.thick * 0.2);
        const shifted = points.map((p) => p.clone().add(new THREE.Vector3(side, lift, side)));
        const path = roundedPath(shifted, 3.5);
        const tube = new THREE.Mesh(new THREE.TubeGeometry(path, Math.max(24, points.length * 28), radius, 8),
                                    P(colour, { roughness: 0.45 }));
        group.add(tube);
      });
    } else {
      // Flat flexible cable: thin white ribbon with conductor stripes and blue stiffened ends.
      const half = route.width / 2, t = route.thick;
      const strip = (a, b, material) => {
        const alongX = Math.abs(a.x - b.x) > 1e-3, alongZ = Math.abs(a.z - b.z) > 1e-3;
        const size = alongX ? [Math.abs(a.x - b.x) + route.width, t, route.width]
          : alongZ ? [route.width, t, Math.abs(a.z - b.z)]
          : [route.width, Math.abs(a.y - b.y) + t, t];
        const mesh = new THREE.Mesh(new THREE.BoxGeometry(...size), material);
        mesh.position.copy(a).add(b).multiplyScalar(0.5);
        return mesh;
      };
      for (let i = 0; i + 1 < points.length; i++) {
        const a = points[i], b = points[i + 1];
        const length = a.distanceTo(b);
        const map = ribbonStripes.clone();
        const alongX = Math.abs(a.x - b.x) > 1e-3;
        map.repeat.set(alongX ? 1 : half / 2, alongX ? half / 2 : 1);
        map.rotation = alongX ? Math.PI / 2 : 0;
        map.needsUpdate = true;
        group.add(strip(a, b, P(0xffffff, { map, roughness: 0.5, side: THREE.DoubleSide })));
        if (length < 0.01) continue;
      }
      // Blue stiffeners where the ribbon enters its sockets.
      for (const [end, toward] of [[points[0], points[1]], [points[points.length - 1], points[points.length - 2]]]) {
        const tip = end.clone().add(toward.clone().sub(end).setLength(Math.min(5, end.distanceTo(toward))));
        const mesh = strip(end, tip, P(0x2356b8, { roughness: 0.5 }));
        mesh.scale.set(1.002, 1.6, 1.002);
        group.add(mesh);
      }
    }
    groups.set(name, group);
  }
  return groups;
}
