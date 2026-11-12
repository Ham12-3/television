// viewer_boards.js - draws the circuit boards in detail from output/stl/boards.json.
//
// Each component is built from simple shapes chosen by its package type
// (chip with legs, electrolytic capacitor, HDMI socket ...), so it looks like
// the real kind of part and can be clicked on its own. Each board also gets
// painted artwork: solder mask, copper traces that follow the net list,
// vias, silkscreen outlines and reference labels.
//
// Local frame used by every builder:  x = along the board (u),
// y = up the board (v), z = height above the board surface.

import * as THREE from "three";

// ---- materials (shared) ----------------------------------------------------
const M = (colour, rough = 0.6, metal = 0.0, extra = {}) =>
  new THREE.MeshStandardMaterial({ color: colour, roughness: rough, metalness: metal, ...extra });

const MAT = {
  ic: M(0x141416, 0.55),
  tin: M(0xc9ccd1, 0.35, 0.85),
  gold: M(0xd4a938, 0.35, 0.9),
  steel: M(0xb9bcc2, 0.4, 0.85),
  alu: M(0xd3d6da, 0.45, 0.8),
  ferrite: M(0x2a2b2e, 0.8),
  copper: M(0xb86a2c, 0.45, 0.7),
  cream: M(0xe9e2cf, 0.7),
  brown: M(0x4a3524, 0.7),
  black: M(0x0c0c0d, 0.7),
  dark: M(0x050506, 0.9),
  white: M(0xf2f2ee, 0.6),
  yellow: M(0xe3b21c, 0.6),
  yellowTape: M(0xd9a514, 0.5),
  sleeve: M(0x1b2a5c, 0.5),
  sleeveBlack: M(0x16171a, 0.5),
  blueDisc: M(0x2c5fa8, 0.6),
  greenDisc: M(0x23432c, 0.7),
  tan: M(0xb99b6b, 0.7),
  red: M(0xc8261f, 0.5),
  redGlow: M(0xff3b30, 0.3, 0, { emissive: 0x7a0c08, transparent: true, opacity: 0.9 }),
  glass: M(0xdfeaf0, 0.1, 0, { transparent: true, opacity: 0.35 }),
  rcaYellow: M(0xe9c21a, 0.5), rcaWhite: M(0xf0f0ec, 0.5), rcaRed: M(0xcf2a22, 0.5),
  green: M(0x2fbf4a, 0.4, 0, { emissive: 0x0b3d14 }),
  amber: M(0xf0a020, 0.4, 0, { emissive: 0x4a2c00 }),
};

// ---- small shape helpers ---------------------------------------------------
function box(sx, sy, sz, material, x = 0, y = 0, z = 0) {
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(sx, sy, sz), material);
  mesh.position.set(x, y, z);
  return mesh;
}

// Cylinder with its axis along "x", "y" or "z" (three.js cylinders start along y).
function cyl(radius, length, material, axis = "z", x = 0, y = 0, z = 0, segments = 24) {
  const mesh = new THREE.Mesh(new THREE.CylinderGeometry(radius, radius, length, segments), material);
  if (axis === "z") mesh.rotation.x = Math.PI / 2;
  if (axis === "x") mesh.rotation.z = Math.PI / 2;
  mesh.position.set(x, y, z);
  return mesh;
}

function textTexture(lines, { size = 128, bg = "#151517", fg = "#b9bcc2", dot = true } = {}) {
  const canvas = document.createElement("canvas");
  canvas.width = canvas.height = size;
  const c = canvas.getContext("2d");
  c.fillStyle = bg;
  c.fillRect(0, 0, size, size);
  c.fillStyle = fg;
  c.textAlign = "center";
  c.textBaseline = "middle";
  const fontSize = size / (lines.length + 2.2);
  c.font = `600 ${fontSize}px system-ui, sans-serif`;
  lines.forEach((line, i) => c.fillText(line, size / 2, size / 2 + (i - (lines.length - 1) / 2) * fontSize * 1.15, size * 0.9));
  if (dot) { c.beginPath(); c.arc(size * 0.12, size * 0.88, size * 0.045, 0, 6.3); c.fill(); }
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}

// A flat label lying on top of a part (chip marking).
function marking(sx, sy, z, lines) {
  const material = new THREE.MeshStandardMaterial({ map: textTexture(lines), roughness: 0.6 });
  const mesh = new THREE.Mesh(new THREE.PlaneGeometry(sx, sy), material);
  mesh.position.z = z + 0.01;
  return mesh;
}

// Rows of legs along the sides of a chip. sides: "long" (two rows) or "all".
function legs(group, su, sv, sides, pitch = 1.27) {
  const add = (alongX, edge) => {
    const length = alongX ? su : sv;
    const count = Math.max(2, Math.min(16, Math.floor((length - 0.6) / pitch)));
    for (let i = 0; i < count; i++) {
      const t = (i - (count - 1) / 2) * pitch;
      group.add(alongX ? box(0.42, 0.9, 0.22, MAT.tin, t, edge, 0.11)
                       : box(0.9, 0.42, 0.22, MAT.tin, edge, t, 0.11));
    }
  };
  const longX = su >= sv;
  if (sides === "all" || longX) { add(true, sv / 2 - 0.3); add(true, -sv / 2 + 0.3); }
  if (sides === "all" || !longX) { add(false, su / 2 - 0.3); add(false, -su / 2 + 0.3); }
}

const shortName = (p) => p.desc.split(/[,(]/)[0].trim().split(" ").slice(0, 2).join(" ");

// ---- component builders, one per package type -------------------------------
const BUILD = {
  box: (p, g) => g.add(box(p.su, p.sv, p.h, MAT.ic, 0, 0, p.h / 2)),

  bga: (p, g) => {
    g.add(box(p.su, p.sv, p.h, MAT.ic, 0, 0, p.h / 2));
    g.add(marking(p.su * 0.92, p.sv * 0.92, p.h, [p.ref, shortName(p)]));
  },
  qfn: (p, g) => BUILD.bga(p, g),
  soic: (p, g) => {
    const longX = p.su >= p.sv;
    const bx = longX ? p.su : p.su - 1.4, by = longX ? p.sv - 1.4 : p.sv;
    g.add(box(bx, by, p.h, MAT.ic, 0, 0, p.h / 2 + 0.05));
    legs(g, p.su, p.sv, "long", Math.max(0.65, Math.min(1.27, (longX ? p.su : p.sv) / 6)));
    g.add(marking(bx * 0.9, by * 0.9, p.h + 0.05, [p.ref]));
  },
  sot: (p, g) => BUILD.soic(p, g),
  dip: (p, g) => BUILD.soic(p, g),
  qfp: (p, g) => {
    g.add(box(p.su - 1.6, p.sv - 1.6, p.h, MAT.ic, 0, 0, p.h / 2 + 0.05));
    legs(g, p.su, p.sv, "all", 0.8);
    g.add(marking((p.su - 1.6) * 0.9, (p.sv - 1.6) * 0.9, p.h + 0.05, [p.ref, shortName(p)]));
  },
  dpak: (p, g) => {
    g.add(box(p.su, p.sv * 0.62, p.h, MAT.ic, 0, p.sv * 0.1, p.h / 2));
    g.add(box(p.su * 0.85, p.sv * 0.2, 0.5, MAT.tin, 0, p.sv * 0.42, 0.25));       // heat tab
    for (const x of [-p.su * 0.3, p.su * 0.3]) g.add(box(0.8, p.sv * 0.25, 0.3, MAT.tin, x, -p.sv * 0.38, 0.15));
  },
  smd_diode: (p, g) => {
    g.add(box(p.su, p.sv * 0.75, p.h, MAT.ic, 0, 0, p.h / 2));
    g.add(box(p.su * 0.7, p.sv, 0.3, MAT.tin, 0, 0, 0.15));
    g.add(box(p.su, 0.7, 0.02, MAT.white, 0, p.sv * 0.28, p.h + 0.01));           // cathode band
  },
  to220: (p, g) => {
    const body = p.h * 0.56;
    g.add(box(p.su, p.sv, body, MAT.ic, 0, 0, 2.5 + body / 2));                    // plastic body
    g.add(box(p.su, 1.3, p.h - 2.5, MAT.steel, 0, p.sv / 2 - 0.65, 2.5 + (p.h - 2.5) / 2));  // metal tab
    for (const x of [-2.54, 0, 2.54]) g.add(box(0.8, 0.5, 2.6, MAT.tin, x, -0.3, 1.3));
  },
  to92: (p, g) => {
    g.add(cyl(p.su / 2, p.h - 1.5, MAT.ic, "z", 0, 0, 1.5 + (p.h - 1.5) / 2));
    for (const x of [-1.27, 0, 1.27]) g.add(box(0.45, 0.45, 1.6, MAT.tin, x, 0, 0.8));
  },
  bridge: (p, g) => {
    g.add(box(p.su, p.sv, p.h - 2, MAT.ic, 0, 0, 2 + (p.h - 2) / 2));
    for (const x of [-7.5, -2.5, 2.5, 7.5]) g.add(box(1, 0.6, 2.2, MAT.tin, x, 0, 1.1));
  },

  ecap: (p, g) => {
    const lying = p.shape === "cyl_u";
    const radius = (lying ? p.sv : p.su) / 2, length = lying ? p.su : p.h;
    const sleeve = radius > 6 ? MAT.sleeveBlack : MAT.sleeve;
    const can = new THREE.Group();
    can.add(cyl(radius, length - 0.6, sleeve, "z", 0, 0, (length - 0.6) / 2));
    can.add(cyl(radius * 0.93, 0.6, MAT.alu, "z", 0, 0, length - 0.3));            // vented top
    can.add(box(radius * 1.5, 0.25, 0.05, MAT.steel, 0, 0, length + 0.01));
    can.add(box(0.25, radius * 1.5, 0.05, MAT.steel, 0, 0, length + 0.01));
    can.add(box(radius * 0.5, 0.2, length * 0.8, MAT.white, 0, -radius + 0.02, length * 0.45));  // polarity stripe
    if (lying) { can.rotation.y = Math.PI / 2; can.position.set(-length / 2, 0, radius); }
    g.add(can);
  },
  boxcap: (p, g) => {
    g.add(box(p.su, p.sv, p.h - 1, MAT.yellow, 0, 0, 1 + (p.h - 1) / 2));
    g.add(box(0.6, 0.6, 1.2, MAT.tin, 0, -p.sv * 0.35, 0.6), box(0.6, 0.6, 1.2, MAT.tin, 0, p.sv * 0.35, 0.6));
  },
  disc: (p, g) => {
    const d = p.desc.toLowerCase();
    const material = d.includes("ntc") ? MAT.greenDisc : MAT.blueDisc;
    const body = new THREE.Mesh(new THREE.SphereGeometry(1, 24, 16), material);
    body.scale.set(p.su / 2, p.sv / 2, (p.h - 2.5) / 2);
    body.position.z = 2.5 + (p.h - 2.5) / 2;
    g.add(body);
    for (const y of [-p.sv * 0.25, p.sv * 0.25]) g.add(box(0.5, 0.5, 3.2, MAT.tin, 0, y, 1.6));
  },
  fuse: (p, g) => {
    const z = p.h * 0.55, alongY = p.sv >= p.su;
    const axis = alongY ? "y" : "x", length = alongY ? p.sv : p.su;
    g.add(cyl(2.4, length - 9, MAT.glass, axis, 0, 0, z));
    g.add(cyl(0.12, length - 9, MAT.steel, axis, 0, 0, z, 8));                      // fuse wire
    for (const s of [-1, 1]) {
      const t = s * (length / 2 - 2.6);
      g.add(cyl(2.6, 5.2, MAT.steel, axis, alongY ? 0 : t, alongY ? t : 0, z));
      g.add(alongY ? box(p.su, 4.6, z, MAT.tin, 0, t, z / 2) : box(4.6, p.sv, z, MAT.tin, t, 0, z / 2));
    }
  },
  tantalum: (p, g) => {
    g.add(box(p.su, p.sv, p.h, MAT.yellow, 0, 0, p.h / 2));
    g.add(box(0.8, p.sv, 0.02, MAT.brown, -p.su * 0.32, 0, p.h + 0.01));
  },
  crystal: (p, g) => g.add(box(p.su, p.sv, p.h, MAT.steel, 0, 0, p.h / 2)),
  can: (p, g) => {
    g.add(box(p.su, p.sv, p.h, MAT.steel, 0, 0, p.h / 2));
    g.add(box(p.su + 0.5, p.sv + 0.5, 0.5, MAT.tin, 0, 0, 0.25));
    g.add(marking(p.su * 0.7, p.sv * 0.45, p.h, [p.ref]));
    g.children[g.children.length - 1].material = new THREE.MeshStandardMaterial({
      map: textTexture([p.ref, shortName(p)], { bg: "#b9bcc2", fg: "#5a5d63", dot: false }), roughness: 0.4, metalness: 0.6 });
  },
  chip_r: (p, g) => {
    const longX = p.su >= p.sv;
    g.add(box(longX ? p.su * 0.6 : p.su, longX ? p.sv : p.sv * 0.6, p.h, MAT.black, 0, 0, p.h / 2));
    for (const s of [-1, 1]) g.add(longX ? box(p.su * 0.2, p.sv, p.h, MAT.tin, s * p.su * 0.4, 0, p.h / 2)
                                         : box(p.su, p.sv * 0.2, p.h, MAT.tin, 0, s * p.sv * 0.4, p.h / 2));
  },
  chip_c: (p, g) => {
    const longX = p.su >= p.sv;
    g.add(box(longX ? p.su * 0.6 : p.su, longX ? p.sv : p.sv * 0.6, p.h, MAT.tan, 0, 0, p.h / 2));
    for (const s of [-1, 1]) g.add(longX ? box(p.su * 0.2, p.sv, p.h, MAT.tin, s * p.su * 0.4, 0, p.h / 2)
                                         : box(p.su, p.sv * 0.2, p.h, MAT.tin, 0, s * p.sv * 0.4, p.h / 2));
  },

  inductor: (p, g) => {
    g.add(box(p.su, p.sv, p.h, MAT.ferrite, 0, 0, p.h / 2));
    g.add(cyl(Math.min(p.su, p.sv) * 0.36, 0.1, MAT.copper, "z", 0, 0, p.h + 0.03));
    g.add(box(p.su * 0.3, p.sv + 0.3, 0.4, MAT.tin, 0, 0, 0.2));
  },
  drum: (p, g) => {
    const r = p.su / 2;
    g.add(cyl(r, 1.5, MAT.ferrite, "z", 0, 0, 0.75), cyl(r, 1.5, MAT.ferrite, "z", 0, 0, p.h - 0.75));
    g.add(cyl(r * 0.86, p.h - 3, MAT.copper, "z", 0, 0, p.h / 2));
  },
  toroid: (p, g) => {
    // Ring core standing on edge, wound with copper, on a small base.
    const flatX = p.su <= p.sv;
    const outer = Math.min(flatX ? p.sv : p.su, p.h - 1.5) / 2;
    const tube = Math.min(outer * 0.38, (flatX ? p.su : p.sv) / 2 - 0.3);
    const ring = new THREE.Mesh(new THREE.TorusGeometry(outer - tube, tube, 14, 40), MAT.copper);
    ring.rotation.set(flatX ? 0 : Math.PI / 2, flatX ? Math.PI / 2 : 0, 0);
    ring.position.z = 1.5 + outer;
    g.add(ring, box(p.su, p.sv, 1.5, MAT.black, 0, 0, 0.75));
    g.add(flatX ? box(tube * 2.2, 1.2, outer * 1.7, MAT.cream, 0, 0, 1.5 + outer)
                : box(1.2, tube * 2.2, outer * 1.7, MAT.cream, 0, 0, 1.5 + outer));  // divider between windings
  },
  transformer: (p, g) => {
    g.add(box(p.su, p.sv, 2, MAT.black, 0, 0, 1));                                  // bobbin base
    g.add(box(p.su * 0.92, p.sv * 0.46, p.h - 2, MAT.ferrite, 0, 0, 2 + (p.h - 2) / 2));   // ferrite core
    g.add(box(p.su * 0.56, p.sv * 0.94, (p.h - 2) * 0.66, MAT.yellowTape, 0, 0, 2 + (p.h - 2) / 2));  // taped winding
    for (let i = -3; i <= 3; i++) for (const s of [-1, 1])
      g.add(box(0.7, 0.7, 1.2, MAT.tin, i * p.su * 0.12, s * (p.sv / 2 - 0.6), 2.4));
  },
  plate: (p, g) => g.add(box(p.su, p.sv, p.h, MAT.alu, 0, 0, p.h / 2)),
  fins: (p, g) => {
    g.add(box(p.su, p.sv, 2, MAT.alu, 0, 0, 1));
    const count = 9, width = 1.5, pitch = (p.su - width) / (count - 1);
    for (let i = 0; i < count; i++) g.add(box(width, p.sv, p.h - 2, MAT.alu, -p.su / 2 + width / 2 + i * pitch, 0, 2 + (p.h - 2) / 2));
  },

  wafer: (p, g) => {
    const longX = p.su >= p.sv, length = longX ? p.su : p.sv;
    g.add(box(p.su, p.sv, p.h, MAT.cream, 0, 0, p.h / 2));
    g.add(box(p.su - 1.4, p.sv - 1.4, 0.05, MAT.brown, 0, 0, p.h + 0.02));         // open top
    const count = Math.max(2, Math.round((length - 2) / 2));
    for (let i = 0; i < count; i++) {
      const t = (i - (count - 1) / 2) * ((length - 3) / Math.max(1, count - 1));
      g.add(box(0.6, 0.6, p.h * 0.7, MAT.gold, longX ? t : 0, longX ? 0 : t, p.h * 0.65));
    }
  },
  header: (p, g) => {
    g.add(box(p.su, p.sv, 2.5, MAT.black, 0, 0, 1.25));
    const longX = p.su >= p.sv, count = Math.max(2, Math.round((longX ? p.su : p.sv) / 2.54));
    for (let i = 0; i < count; i++) {
      const t = (i - (count - 1) / 2) * 2.54;
      g.add(box(0.64, 0.64, p.h, MAT.gold, longX ? t : 0, longX ? 0 : t, p.h / 2));
    }
  },
  ffc: (p, g) => {
    const longX = p.su >= p.sv;
    g.add(box(p.su, p.sv, p.h, MAT.cream, 0, 0, p.h / 2));
    g.add(longX ? box(p.su * 0.94, p.sv * 0.3, p.h + 0.15, MAT.brown, 0, -p.sv * 0.3, p.h / 2)
                : box(p.su * 0.3, p.sv * 0.94, p.h + 0.15, MAT.brown, -p.su * 0.3, 0, p.h / 2));   // locking flap
  },

  // External sockets. Their mating face is the +x end.
  hdmi: (p, g) => {
    g.add(box(p.su, p.sv, p.h, MAT.steel, 0, 0, p.h / 2));
    g.add(box(0.1, p.sv - 1.6, p.h - 1.6, MAT.dark, p.su / 2 + 0.03, 0, p.h / 2));
    g.add(box(1.5, p.sv - 4.5, 1.0, MAT.black, p.su / 2 - 0.7, 0, p.h / 2));
  },
  usb: (p, g) => {
    g.add(box(p.su, p.sv, p.h, MAT.steel, 0, 0, p.h / 2));
    g.add(box(0.1, p.sv - 1.6, p.h - 1.6, MAT.dark, p.su / 2 + 0.03, 0, p.h / 2));
    g.add(box(1.5, p.sv - 3, 1.8, MAT.white, p.su / 2 - 0.7, 0, p.h * 0.36));
  },
  rj45: (p, g) => {
    g.add(box(p.su, p.sv, p.h, MAT.steel, 0, 0, p.h / 2));
    g.add(box(0.1, p.sv - 4, p.h - 5, MAT.dark, p.su / 2 + 0.03, 0, p.h * 0.42));
    g.add(box(0.12, 2.2, 1.4, MAT.green, p.su / 2 + 0.03, -p.sv / 2 + 2.2, p.h - 1.4));
    g.add(box(0.12, 2.2, 1.4, MAT.amber, p.su / 2 + 0.03, p.sv / 2 - 2.2, p.h - 1.4));
  },
  toslink: (p, g) => {
    g.add(box(p.su, p.sv, p.h, MAT.black, 0, 0, p.h / 2));
    g.add(box(0.1, p.sv * 0.55, p.h * 0.55, MAT.dark, p.su / 2 + 0.03, 0, p.h / 2));
    g.add(box(0.12, 1.4, 1.4, MAT.redGlow, p.su / 2 + 0.05, 0, p.h / 2));
  },
  jack: (p, g) => {
    g.add(box(p.su - 2.5, p.sv, p.h, MAT.black, -1.25, 0, p.h / 2));
    g.add(cyl(Math.min(p.sv, p.h) * 0.45, 2.5, MAT.steel, "x", p.su / 2 - 1.25, 0, p.h / 2));
    g.add(cyl(1.75, 0.1, MAT.dark, "x", p.su / 2 + 0.03, 0, p.h / 2));
  },
  rca: (p, g) => {
    const d = p.desc.toLowerCase();
    const colour = d.includes("yellow") ? MAT.rcaYellow : d.includes("white") ? MAT.rcaWhite : MAT.rcaRed;
    const r = Math.min(p.sv, p.h) * 0.42, barrel = p.su * 0.5;
    g.add(box(p.su - barrel, p.sv, p.h, MAT.black, -barrel / 2, 0, p.h / 2));
    g.add(cyl(r, barrel, MAT.steel, "x", p.su / 2 - barrel / 2, 0, p.h / 2));
    g.add(cyl(r * 0.8, 0.12, colour, "x", p.su / 2 + 0.04, 0, p.h / 2));
    g.add(cyl(r * 0.3, 0.14, MAT.dark, "x", p.su / 2 + 0.06, 0, p.h / 2));
    g.add(cyl(r * 1.12, 1.2, colour, "x", p.su / 2 - barrel + 0.6, 0, p.h / 2));
  },
  coax: (p, g) => {
    const r = Math.min(p.sv, p.h) * 0.4, barrel = p.su * 0.45;
    g.add(box(p.su - barrel, p.sv, p.h, MAT.steel, -barrel / 2, 0, p.h / 2));
    g.add(cyl(r, barrel, MAT.steel, "x", p.su / 2 - barrel / 2, 0, p.h / 2));
    for (let i = 0; i < 5; i++) g.add(cyl(r * 1.06, 0.4, MAT.tin, "x", p.su / 2 - 0.8 - i * 1.4, 0, p.h / 2));   // thread
    g.add(cyl(r * 0.7, 0.1, MAT.white, "x", p.su / 2 + 0.03, 0, p.h / 2));
    g.add(cyl(r * 0.2, 0.14, MAT.dark, "x", p.su / 2 + 0.05, 0, p.h / 2));
  },

  ir: (p, g) => {
    g.add(box(p.su, p.sv, p.h * 0.7, MAT.ic, 0, 0, p.h * 0.35));
    const dome = new THREE.Mesh(new THREE.SphereGeometry(p.su * 0.42, 20, 12, 0, 6.3, 0, 1.6), MAT.ic);
    dome.rotation.x = Math.PI / 2; dome.position.z = p.h * 0.7;
    g.add(dome);
  },
  led: (p, g) => {
    const r = p.su / 2;
    g.add(cyl(r, p.h - r, MAT.redGlow, "z", 0, 0, (p.h - r) / 2));
    const dome = new THREE.Mesh(new THREE.SphereGeometry(r, 20, 12), MAT.redGlow);
    dome.position.z = p.h - r;
    g.add(dome);
  },
  switch: (p, g) => g.add(box(p.su, p.sv, p.h, MAT.steel, 0, 0, p.h / 2)),
  plunger: (p, g) => g.add(cyl(p.su / 2, p.sv, MAT.black, "y", 0, 0, p.h / 2)),
};

// ---- board artwork ----------------------------------------------------------
const css = (rgb, mix = 0, to = 255) =>
  `rgb(${rgb.map((c) => Math.round(c * 255 * (1 - mix) + to * mix)).join(",")})`;

// Parts on a net, ordered so each is followed by its nearest unvisited neighbour.
function chain(parts) {
  const left = [...parts].sort((a, b) => a.u - b.u);
  const out = [left.shift()];
  while (left.length) {
    const last = out[out.length - 1];
    let best = 0, bestD = Infinity;
    left.forEach((p, i) => { const d = Math.abs(p.u - last.u) + Math.abs(p.v - last.v); if (d < bestD) { bestD = d; best = i; } });
    out.push(left.splice(best, 1)[0]);
  }
  return out;
}

const BUS_NETS = new Set(["DDR", "EMMC", "HDMI1", "HDMI2", "LVDS", "MINI_LVDS", "USB1", "USB2", "ETH"]);

function drawArtwork(canvas, board, nets, highlight) {
  const [W, H] = board.size;
  const s = canvas.width / W;                       // pixels per millimetre
  const c = canvas.getContext("2d");
  c.setTransform(1, 0, 0, 1, 0, 0);
  if (board.direction > 0) c.setTransform(-1, 0, 0, 1, canvas.width, 0);   // front-facing board: mirror
  const X = (u) => (u + W / 2) * s, Y = (v) => (H / 2 - v) * s;
  const mask = css(board.colour), copper = css(board.colour, 0.22), silk = "rgba(245,245,238,0.92)";

  c.fillStyle = mask;
  c.fillRect(0, 0, canvas.width, canvas.height);

  // Copper traces: join every part on a net, routed as horizontal + vertical runs.
  const netIndex = Object.fromEntries(nets.map((n, i) => [n.name, i]));
  const vias = [];
  for (const net of nets) {
    if (net.kind === "ground") continue;            // ground is a filled plane, not traces
    const members = board.parts.filter((p) => p.nets.includes(net.name));
    if (members.length < 2) continue;
    const isHot = highlight === net.name;
    const heavy = net.kind === "mains" || net.kind === "power";
    const offset = ((netIndex[net.name] % 7) - 3) * 0.55;
    const lanes = BUS_NETS.has(net.name) ? [-0.9, -0.3, 0.3, 0.9] : [0];
    c.strokeStyle = isHot ? net.colour : copper;
    c.lineWidth = (heavy ? 1.1 : 0.32) * s * (isHot ? 1.5 : 1);
    c.lineJoin = "round"; c.lineCap = "round";
    const order = chain(members);
    for (let i = 0; i + 1 < order.length; i++) {
      const a = order[i], b = order[i + 1];
      for (const lane of lanes) {
        const o = offset + lane;
        c.beginPath();
        c.moveTo(X(a.u), Y(a.v + o));
        if (i % 2 === 0) { c.lineTo(X(b.u + o), Y(a.v + o)); c.lineTo(X(b.u + o), Y(b.v)); }
        else { c.lineTo(X(a.u + o), Y(b.v + o)); c.lineTo(X(b.u), Y(b.v + o)); }
        c.stroke();
      }
      vias.push(i % 2 === 0 ? [b.u + offset, a.v + offset] : [a.u + offset, b.v + offset]);
    }
  }
  // Vias where traces change direction.
  for (const [u, v] of vias) {
    c.fillStyle = "#c9ccd1"; c.beginPath(); c.arc(X(u), Y(v), 0.5 * s, 0, 6.3); c.fill();
    c.fillStyle = "#1a1a1a"; c.beginPath(); c.arc(X(u), Y(v), 0.22 * s, 0, 6.3); c.fill();
  }

  // Mounting holes with plated rings, and routed slots.
  for (const [u, v] of board.holes) {
    c.fillStyle = "#c9ccd1"; c.beginPath(); c.arc(X(u), Y(v), 3.3 * s, 0, 6.3); c.fill();
    c.fillStyle = "#101010"; c.beginPath(); c.arc(X(u), Y(v), 1.6 * s, 0, 6.3); c.fill();
  }
  for (const [u, v, su, sv] of board.slots) {
    c.fillStyle = "#0a0a0a";
    c.fillRect(X(u - su / 2), Y(v + sv / 2), su * s, sv * s);
  }

  // Silkscreen: an outline round every part and its reference label.
  c.strokeStyle = silk; c.fillStyle = silk; c.lineWidth = 0.14 * s;
  c.textAlign = "center"; c.textBaseline = "middle";
  const flip = board.direction > 0;
  const text = (string, u, v, mm, weight = 600) => {
    c.save();
    c.translate(X(u), Y(v));
    if (flip) c.scale(-1, 1);                        // keep text readable on the mirrored board
    c.font = `${weight} ${mm * s}px system-ui, sans-serif`;
    c.fillText(string, 0, 0);
    c.restore();
  };
  for (const p of board.parts) {
    if (p.pkg === "plunger" || p.pkg === "fins") continue;
    c.strokeRect(X(p.u - p.su / 2 - 0.3), Y(p.v + p.sv / 2 + 0.3), (p.su + 0.6) * s, (p.sv + 0.6) * s);
    if (p.kind === "passive" && Math.max(p.su, p.sv) < 3.5) continue;   // too small to label
    const above = p.v + p.sv / 2 + 1.5 < H / 2 - 1;
    text(p.ref, p.u, above ? p.v + p.sv / 2 + 1.4 : p.v - p.sv / 2 - 1.4, Math.min(1.9, Math.max(1.1, W / 90)));
  }
  text(`${board.title.toUpperCase()}  REV A`, -W / 2 + Math.min(W * 0.3, 34), -H / 2 + 2.2, Math.min(2.2, H / 9), 700);

  // Mains warning on the power supply: mark the safety barrier.
  if (board.slots.length) {
    const [u] = board.slots[0];
    c.setLineDash([1.5 * s, 1.2 * s]); c.lineWidth = 0.35 * s; c.strokeStyle = "#f2f2ee";
    c.beginPath(); c.moveTo(X(u + 3), Y(H / 2 - 2)); c.lineTo(X(u + 3), Y(-H / 2 + 2)); c.stroke();
    c.setLineDash([]);
    text("PRIMARY - HIGH VOLTAGE", u - 38, -H / 2 + 6, 2.6, 800);
    text("SECONDARY", u + 38, -H / 2 + 6, 2.6, 800);
  }
}

// ---- public: build every board ----------------------------------------------
// Returns { groups, components, redraw }:
//   groups      Map of viewer entry name ("mainboard_chips") -> THREE.Group
//   components  [{ object, board, part }] for picking and labels
//   redraw(net) repaints the artwork, with one net's traces picked out
export function buildBoards(data, renderer) {
  const groups = new Map();
  const components = [];
  const artworks = [];

  for (const board of data.boards) {
    const [cx, cz] = board.centre;
    // Board frame: local x -> world X, local y -> world Z (up), local z -> out of the board.
    const frame = new THREE.Matrix4().makeBasis(
      new THREE.Vector3(1, 0, 0), new THREE.Vector3(0, 0, 1), new THREE.Vector3(0, board.direction, 0));
    frame.setPosition(cx, board.y_surface, cz);

    const entry = (category) => {
      const name = `${board.name}_${category}`;
      if (!groups.has(name)) {
        const outer = new THREE.Group();             // moved by the explode slider
        const inner = new THREE.Group();             // fixed board frame
        inner.matrixAutoUpdate = false;
        inner.matrix.copy(frame);
        outer.add(inner);
        outer.userData.inner = inner;
        groups.set(name, outer);
      }
      return groups.get(name).userData.inner;
    };

    // The bare board with its painted artwork.
    const [W, H] = board.size;
    const pcb = entry("pcb");
    pcb.add(box(W, H, board.thickness, M(new THREE.Color(...board.colour).multiplyScalar(0.8), 0.7), 0, 0, -board.thickness / 2));
    const canvas = document.createElement("canvas");
    const scale = Math.min(12, 2048 / Math.max(W, H));
    canvas.width = Math.round(W * scale); canvas.height = Math.round(H * scale);
    drawArtwork(canvas, board, data.nets, null);
    const texture = new THREE.CanvasTexture(canvas);
    texture.colorSpace = THREE.SRGBColorSpace;
    texture.anisotropy = renderer.capabilities.getMaxAnisotropy();
    const face = new THREE.Mesh(new THREE.PlaneGeometry(W, H),
      new THREE.MeshStandardMaterial({ map: texture, roughness: 0.55, side: THREE.DoubleSide }));
    face.position.z = 0.02;
    pcb.add(face);
    pcb.userData.pick = { type: "board", board };
    artworks.push({ canvas, texture, board });

    // Components.
    for (const part of board.parts) {
      const g = new THREE.Group();
      (BUILD[part.pkg] ?? BUILD.box)(part, g);
      g.position.set(part.u, part.v, part.lift);
      g.userData.pick = { type: "component", board, part };
      entry(part.category).add(g);
      components.push({ object: g, board, part });
    }

    // A screw on every mounting hole.
    for (const [u, v] of board.holes) {
      const g = new THREE.Group();
      g.add(cyl(2.75, 2, MAT.steel, "z", 0, 0, 1));
      g.add(box(3.2, 0.5, 0.1, MAT.dark, 0, 0, 2.02), box(0.5, 3.2, 0.1, MAT.dark, 0, 0, 2.02));
      g.position.set(u, v, 0);
      g.userData.pick = { type: "screw", board };
      entry("screws").add(g);
    }
  }

  const redraw = (net) => {
    for (const a of artworks) {
      drawArtwork(a.canvas, a.board, data.nets, net);
      a.texture.needsUpdate = true;
    }
  };
  return { groups, components, redraw };
}
