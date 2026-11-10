#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
STRANGE DAYS — Remastered Edition
==================================
A cinematic, atmospheric Japanese-inspired third-person action/adventure
experience built in Python 3.10.0 and PyGame.

Design Pillars:
- East Asian PS2/PS3-era cinematic minimalism (Fatal Frame / Heavy Rain /
  Alan Wake / Team Ico atmosphere, Final Fantasy XII-XIV facial stylization).
- Zero-texture low-poly geometry with gradient & multi-material lighting.
- High-craft articulated female protagonist (35 bones, analytical IK,
  secondary hair physics, blinking, gaze tracking, expressive anatomy).
- Weighty, grounded locomotion, idle vignettes (>10s), three procedural
  non-looped dances (keys 1/2/3) compatible with walking and smoking,
  and tactile cigarette pack / lighter / ash / smoke simulation.
- Pure diegetic presentation with zero HUD or on-screen UI clutter.

Remaster changes (v2 — Drastic Remaster):
- Outfit redesigned to a royal blue competitive one-piece swimsuit with
  crisp white side panels, light-blue piping accents, high scoop neckline
  near the collarbone, and thick racerback shoulder straps — full athletic
  torso coverage matching the reference image (no bare midriff / no shorts).
- Face refined to a soft oval with gently rounded cheeks, smoother jawline,
  larger almond-shaped dark-brown eyes with slightly droopy outer corners,
  delicate small nose, and a fuller lower lip with defined cupid's bow.
- Hairstyle updated to wispy see-through feathered fringe with varied
  strand lengths and subtle gaps for an airy, see-through quality, plus
  a slightly off-center part and longer face-framing side strands.
- Materials overhauled with expanded gradient usage: radial gradients on
  skin blush, iris, catchlight, gold foil, cigarette ember, and lamp shades;
  linear gradients deepened on swimsuit fabric, hair, and architectural
  surfaces for richer PS3-era cinematic depth (Killzone / Heavy Rain approach
  — more expressive design, not more polygons).
- Dance engine expanded from 8 to 10 motifs per style with per-motif tempo
  multipliers (0.82–1.18×) for rhythmic variety, plus brief transition
  flourishes (arm/body sweeps) that bridge motif changes into cohesive
  phrases. Non-repeating irrational phase modulation + FBM drift preserved.
- Dark ambient soundtrack expanded from 18s to 32s with a proper layered
  evolving texture: ultra-deep sub-bass drone (D0/D1), D minor harmonic
  stack with detuned chorus voices, a slowly crossfading A minor secondary
  tonal center for harmonic tension, three-band filtered noise bed (low
  rumble + mid wind + high hiss), sparse distant bell/chime tones at
  harmonic intervals, occasional sub-bass thunder pulses, and metallic
  shimmer accents — reads as a genuine dark ambient composition.
- VFX polished: three-layer lamp bloom (tight core + mid wash + ultra-wide
  atmospheric diffusion) with depth occlusion; smoke wisps now use layered
  dual-frequency curl (primary drift + secondary turbulent eddies) with
  age-dependent buoyancy for organic, living-air movement.
- Arm IK bending fixed: action-specific pole vectors ensure elbows bend
  outward-forward when reaching to the mouth/face and outward-down when
  reaching to props — no more wrong-direction elbow bending.
- Performance kept lean: baked static lighting, chunk frustum culling,

Remaster changes (v3 — Drastic Remaster II):
- SMOOTH SHADING: Per-vertex smooth normals computed in bind pose and
  deformed with the skinning rig each frame. Each triangle now shades with
  the average of its 3 vertex smooth normals instead of the flat face
  normal — adjacent triangles share vertex normals so their colors are
  correlated, eliminating ALL visible polygon borders on the character
  body. The result reads as a seamless AAA-quality surface (Killzone /
  Heavy Rain / Uncharted 2 standard) despite the low polygon count.
- FLOATING LIGHT SPHERE GLITCH FIXED: RadialGlowCache rewritten with a
  broader, more diffuse Gaussian falloff (k=1.8, 32 steps) that never
  concentrates enough alpha at center to read as a solid sphere. Lamp
  halos completely reworked: tight bright cores REMOVED — only broad
  diffuse atmospheric bloom remains (max alpha 3–10). The lamp shade's
  emissive material is now the sole visible light source; halos just
  soften the surrounding air into cinematic bloom. No more floating balls.
- SMALLER PARTICLES: Smoke wisp radii reduced ~40% (start 5–7mm, end
  22–34mm) for fine curling tendrils instead of big puffs. Dust motes
  now render at 1px only with lower alpha (12–32) for authentic fine
  particulate. Exhale puffs reduced ~35% for delicate breath wisps.
- STRAIGHT BANGS (齐刘海): Hairstyle redesigned to match the reference
  image — classic straight-across Japanese fringe at eyebrow level with
  10 continuous strands sharing the same tip Y. Hair extended longer:
  back curtains now reach lower back (~Y 0.82) and side falls extend
  past the chest to mid-torso for the signature long straight hairstyle.
- HIGHER TOPOLOGY: Mesh segment counts increased for smoother curves —
  face 14→16, torso 14→16, neck 10→12, arms 7→8, legs 8→10. Combined
  with smooth normals, the character silhouette is now seamlessly smooth.
- DANCE ENGINE ENHANCED: Phrase-aware motif selection (35% chance to flow
  to a naturally-related next motif for cohesive 2-3 motif phrases). Two
  flourish types now alternate (arm sweep + body wave) for richer
  transitions. Wider tempo variation (0.78–1.22×) and energy range.
- DARK AMBIENT SOUNDTRACK EXPANDED to 40s: Added ultra-deep D0 sub-bass
  drone (18.35Hz, felt as physical pressure), third F minor tonal center
  fading in late-loop for unresolved darkness, 4th bell tone (D6), slow
  heartbeat-like sub-bass throb (48 BPM visceral unease), and 4 thunder
  pulses instead of 3. Deeper, more evolving, more genuinely dark ambient.
- Performance kept lean: baked static lighting, chunk frustum culling,
  allocation-free shading path, capped particle budgets, internal render
  scale upscaling — smooth 60 FPS on low-end laptops.

Controls:
  W / A / S / D     : Move (relative to cinematic camera)
  Left Shift        : Run (disabled while dancing)
  Mouse Move        : Smooth cinematic camera orbit (Tab toggles grab)
  1 / 2 / 3         : Start / switch / stop procedural Dance 1, 2, or 3
  E                 : Interact (take cigarette from pack / light at lighter)
  Left Mouse Click  : Switch cigarette between fingers and lips
  Right Mouse Click : Flick / drop cigarette ash
  F11               : Toggle fullscreen
  Escape            : Quit
"""

from __future__ import annotations

import math
import random
import sys
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Sequence, Tuple

import pygame


# =============================================================================
# ENGINE CONFIGURATION & GLOBAL CONSTANTS
# =============================================================================

APP_TITLE = "Strange Days"
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
TARGET_FPS = 60
FIXED_DT = 1.0 / 60.0
MAX_FRAME_DT = 0.05

# Internal render scale: the software rasterizer fills an internal surface of
# this height and upscales to the window. Keeps the soft PS2-era filmic look
# while cutting per-polygon fill cost dramatically on low-end laptops.
RENDER_SCALE = 0.58

# Cinematic framing constants
LETTERBOX_RATIO = 0.075  # Subtle 2.15:1 widescreen cinematic bars
DEFAULT_FOV_DEG = 48.0
NEAR_CLIP = 0.12
FAR_CLIP = 24.0

# Room architectural dimensions (modern Japanese urban bedroom, meters)
ROOM_HALF_W = 2.55   # 5.10 m wide
ROOM_HALF_D = 2.35   # 4.70 m deep
ROOM_HEIGHT = 2.62   # 2.62 m ceiling height

# Protagonist physical metrics
PLAYER_HEIGHT = 1.62
PLAYER_CAPSULE_RADIUS = 0.22
PLAYER_WALK_SPEED = 1.38
PLAYER_DANCE_WALK_SPEED = 1.12
PLAYER_RUN_SPEED = 3.15
PLAYER_ACCEL = 9.5
PLAYER_DECEL = 11.5
PLAYER_TURN_SPEED = 9.0

# Idle & smoking gameplay tuning
IDLE_VIGNETTE_DELAY = 10.0
INTERACT_DISTANCE = 1.12
CIGARETTE_BURN_SECONDS = 95.0
CIGARETTE_PUFF_INTERVAL = 7.5
ASH_GROWTH_RATE = 0.011
ASH_MAX_LENGTH = 0.028

# Particle budgets (kept lean for low-end laptops)
MAX_SMOKE_PARTICLES = 42
MAX_ASH_PARTICLES = 12
MAX_DUST_MOTES = 18


# =============================================================================
# DETERMINISTIC MATH UTILITIES & EASING FUNCTIONS
# =============================================================================

TAU = math.pi * 2.0
HALF_PI = math.pi * 0.5
DEG2RAD = math.pi / 180.0
RAD2DEG = 180.0 / math.pi
EPSILON = 1e-6
sqrt = math.sqrt  # local alias for hot loops


def clamp(value: float, lo: float, hi: float) -> float:
    if value < lo:
        return lo
    if value > hi:
        return hi
    return value


def clamp01(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def inv_lerp(a: float, b: float, v: float) -> float:
    denom = b - a
    if abs(denom) < EPSILON:
        return 0.0
    return clamp01((v - a) / denom)


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    t = inv_lerp(edge0, edge1, x)
    return t * t * (3.0 - 2.0 * t)


def smootherstep(edge0: float, edge1: float, x: float) -> float:
    t = inv_lerp(edge0, edge1, x)
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)


def damp(current: float, target: float, lambda_rate: float, dt: float) -> float:
    return lerp(current, target, 1.0 - math.exp(-lambda_rate * dt))


def wrap_angle(angle: float) -> float:
    a = (angle + math.pi) % TAU
    if a < 0.0:
        a += TAU
    return a - math.pi


def lerp_angle(a: float, b: float, t: float) -> float:
    diff = wrap_angle(b - a)
    return wrap_angle(a + diff * t)


def damp_angle(current: float, target: float, rate: float, dt: float) -> float:
    factor = 1.0 - math.exp(-rate * dt)
    return lerp_angle(current, target, factor)


def ease_in_out_cubic(t: float) -> float:
    t = clamp01(t)
    if t < 0.5:
        return 4.0 * t * t * t
    return 1.0 - ((-2.0 * t + 2.0) ** 3) * 0.5


def ease_out_back(t: float) -> float:
    t = clamp01(t)
    c1 = 1.70158
    c3 = c1 + 1.0
    u = t - 1.0
    return 1.0 + c3 * u * u * u + c1 * u * u


def ease_in_out_sine(t: float) -> float:
    t = clamp01(t)
    return -(math.cos(math.pi * t) - 1.0) * 0.5


def ping_pong(t: float, length: float = 1.0) -> float:
    if length <= EPSILON:
        return 0.0
    q = t % (2.0 * length)
    if q > length:
        return 2.0 * length - q
    return q


def hash_1d(n: int) -> float:
    x = (n << 13) ^ n
    return 1.0 - ((x * (x * x * 15731 + 789221) + 1376312589) & 0x7FFFFFFF) / 1073741824.0


def value_noise_1d(x: float, seed: int = 0) -> float:
    i = math.floor(x)
    f = x - i
    u = f * f * (3.0 - 2.0 * f)
    a = hash_1d(i + seed * 131)
    b = hash_1d(i + 1 + seed * 131)
    return lerp(a, b, u)


def fbm_1d(x: float, octaves: int = 3, seed: int = 0) -> float:
    amp = 0.5
    freq = 1.0
    total = 0.0
    norm = 0.0
    for oct_idx in range(octaves):
        total += amp * value_noise_1d(x * freq, seed + oct_idx * 53)
        norm += amp
        amp *= 0.5
        freq *= 2.03
    return total / norm if norm > EPSILON else 0.0


def catmull_rom(p0: float, p1: float, p2: float, p3: float, t: float) -> float:
    t2 = t * t
    t3 = t2 * t
    return 0.5 * (
        (2.0 * p1)
        + (-p0 + p2) * t
        + (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * t2
        + (-p0 + 3.0 * p1 - 3.0 * p2 + p3) * t3
    )


# =============================================================================
# VECTOR, QUATERNION & MATRIX LIBRARY
# =============================================================================

@dataclass(slots=True)
class Vec2:
    x: float = 0.0
    y: float = 0.0

    def __add__(self, o: "Vec2") -> "Vec2":
        return Vec2(self.x + o.x, self.y + o.y)

    def __sub__(self, o: "Vec2") -> "Vec2":
        return Vec2(self.x - o.x, self.y - o.y)

    def __mul__(self, s: float) -> "Vec2":
        return Vec2(self.x * s, self.y * s)

    def __rmul__(self, s: float) -> "Vec2":
        return Vec2(self.x * s, self.y * s)

    def dot(self, o: "Vec2") -> float:
        return self.x * o.x + self.y * o.y

    def length_sq(self) -> float:
        return self.x * self.x + self.y * self.y

    def length(self) -> float:
        return math.sqrt(self.x * self.x + self.y * self.y)

    def normalized(self) -> "Vec2":
        l = self.length()
        if l < EPSILON:
            return Vec2(0.0, 0.0)
        inv = 1.0 / l
        return Vec2(self.x * inv, self.y * inv)

    def lerp(self, o: "Vec2", t: float) -> "Vec2":
        return Vec2(self.x + (o.x - self.x) * t, self.y + (o.y - self.y) * t)


@dataclass(slots=True)
class Vec3:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def __add__(self, o: "Vec3") -> "Vec3":
        return Vec3(self.x + o.x, self.y + o.y, self.z + o.z)

    def __sub__(self, o: "Vec3") -> "Vec3":
        return Vec3(self.x - o.x, self.y - o.y, self.z - o.z)

    def __neg__(self) -> "Vec3":
        return Vec3(-self.x, -self.y, -self.z)

    def __mul__(self, s: float) -> "Vec3":
        return Vec3(self.x * s, self.y * s, self.z * s)

    def __rmul__(self, s: float) -> "Vec3":
        return Vec3(self.x * s, self.y * s, self.z * s)

    def __truediv__(self, s: float) -> "Vec3":
        inv = 1.0 / s if abs(s) > EPSILON else 0.0
        return Vec3(self.x * inv, self.y * inv, self.z * inv)

    def copy(self) -> "Vec3":
        return Vec3(self.x, self.y, self.z)

    def dot(self, o: "Vec3") -> float:
        return self.x * o.x + self.y * o.y + self.z * o.z

    def cross(self, o: "Vec3") -> "Vec3":
        return Vec3(
            self.y * o.z - self.z * o.y,
            self.z * o.x - self.x * o.z,
            self.x * o.y - self.y * o.x,
        )

    def length_sq(self) -> float:
        return self.x * self.x + self.y * self.y + self.z * self.z

    def length(self) -> float:
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)

    def distance_to(self, o: "Vec3") -> float:
        dx = self.x - o.x
        dy = self.y - o.y
        dz = self.z - o.z
        return math.sqrt(dx * dx + dy * dy + dz * dz)

    def normalized(self) -> "Vec3":
        l = self.length()
        if l < EPSILON:
            return Vec3(0.0, 0.0, 0.0)
        inv = 1.0 / l
        return Vec3(self.x * inv, self.y * inv, self.z * inv)

    def lerp(self, o: "Vec3", t: float) -> "Vec3":
        return Vec3(
            self.x + (o.x - self.x) * t,
            self.y + (o.y - self.y) * t,
            self.z + (o.z - self.z) * t,
        )

    def damp_to(self, target: "Vec3", rate: float, dt: float) -> "Vec3":
        f = 1.0 - math.exp(-rate * dt)
        return self.lerp(target, f)

    def reflect(self, normal: "Vec3") -> "Vec3":
        d = 2.0 * self.dot(normal)
        return Vec3(self.x - d * normal.x, self.y - d * normal.y, self.z - d * normal.z)

    def tuple(self) -> Tuple[float, float, float]:
        return (self.x, self.y, self.z)


VEC3_ZERO = Vec3(0.0, 0.0, 0.0)
VEC3_UP = Vec3(0.0, 1.0, 0.0)
VEC3_RIGHT = Vec3(1.0, 0.0, 0.0)
VEC3_FORWARD = Vec3(0.0, 0.0, 1.0)


@dataclass(slots=True)
class Quat:
    w: float = 1.0
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    @staticmethod
    def identity() -> "Quat":
        return Quat(1.0, 0.0, 0.0, 0.0)

    @staticmethod
    def from_axis_angle(axis: Vec3, angle_rad: float) -> "Quat":
        n = axis.normalized()
        if n.length_sq() < EPSILON:
            return Quat.identity()
        half = angle_rad * 0.5
        s = math.sin(half)
        return Quat(math.cos(half), n.x * s, n.y * s, n.z * s).normalized()

    @staticmethod
    def from_euler_yxz(yaw: float, pitch: float, roll: float) -> "Quat":
        # Y (yaw) -> X (pitch) -> Z (roll) standard character joint convention
        cy = math.cos(yaw * 0.5)
        sy = math.sin(yaw * 0.5)
        cp = math.cos(pitch * 0.5)
        sp = math.sin(pitch * 0.5)
        cr = math.cos(roll * 0.5)
        sr = math.sin(roll * 0.5)
        w = cy * cp * cr + sy * sp * sr
        x = cy * sp * cr + sy * cp * sr
        y = sy * cp * cr - cy * sp * sr
        z = cy * cp * sr - sy * sp * cr
        return Quat(w, x, y, z).normalized()

    @staticmethod
    def from_euler_xyz(rx: float, ry: float, rz: float) -> "Quat":
        qx = Quat.from_axis_angle(VEC3_RIGHT, rx)
        qy = Quat.from_axis_angle(VEC3_UP, ry)
        qz = Quat.from_axis_angle(VEC3_FORWARD, rz)
        return (qz * qy * qx).normalized()

    @staticmethod
    def look_rotation(forward: Vec3, up_hint: Vec3 = VEC3_UP) -> "Quat":
        f = forward.normalized()
        if f.length_sq() < EPSILON:
            return Quat.identity()
        r = up_hint.cross(f).normalized()
        if r.length_sq() < EPSILON:
            r = Vec3(1.0, 0.0, 0.0)
        u = f.cross(r).normalized()
        m00, m01, m02 = r.x, u.x, f.x
        m10, m11, m12 = r.y, u.y, f.y
        m20, m21, m22 = r.z, u.z, f.z
        tr = m00 + m11 + m22
        if tr > 0.0:
            s = math.sqrt(tr + 1.0) * 2.0
            w = 0.25 * s
            x = (m21 - m12) / s
            y = (m02 - m20) / s
            z = (m10 - m01) / s
        elif m00 > m11 and m00 > m22:
            s = math.sqrt(1.0 + m00 - m11 - m22) * 2.0
            w = (m21 - m12) / s
            x = 0.25 * s
            y = (m01 + m10) / s
            z = (m02 + m20) / s
        elif m11 > m22:
            s = math.sqrt(1.0 + m11 - m00 - m22) * 2.0
            w = (m02 - m20) / s
            x = (m01 + m10) / s
            y = 0.25 * s
            z = (m12 + m21) / s
        else:
            s = math.sqrt(1.0 + m22 - m00 - m11) * 2.0
            w = (m10 - m01) / s
            x = (m02 + m20) / s
            y = (m12 + m21) / s
            z = 0.25 * s
        return Quat(w, x, y, z).normalized()

    def __mul__(self, o: "Quat") -> "Quat":
        return Quat(
            self.w * o.w - self.x * o.x - self.y * o.y - self.z * o.z,
            self.w * o.x + self.x * o.w + self.y * o.z - self.z * o.y,
            self.w * o.y - self.x * o.z + self.y * o.w + self.z * o.x,
            self.w * o.z + self.x * o.y - self.y * o.x + self.z * o.w,
        )

    def conjugate(self) -> "Quat":
        return Quat(self.w, -self.x, -self.y, -self.z)

    def normalized(self) -> "Quat":
        n = math.sqrt(self.w * self.w + self.x * self.x + self.y * self.y + self.z * self.z)
        if n < EPSILON:
            return Quat.identity()
        inv = 1.0 / n
        return Quat(self.w * inv, self.x * inv, self.y * inv, self.z * inv)

    def rotate_vec(self, v: Vec3) -> Vec3:
        # Optimized q * (0, v) * q^-1
        ux, uy, uz = self.x, self.y, self.z
        s = self.w
        dot_uv = ux * v.x + uy * v.y + uz * v.z
        dot_uu = ux * ux + uy * uy + uz * uz
        cx = uy * v.z - uz * v.y
        cy = uz * v.x - ux * v.z
        cz = ux * v.y - uy * v.x
        t1 = 2.0 * dot_uv
        t2 = s * s - dot_uu
        t3 = 2.0 * s
        return Vec3(
            t1 * ux + t2 * v.x + t3 * cx,
            t1 * uy + t2 * v.y + t3 * cy,
            t1 * uz + t2 * v.z + t3 * cz,
        )

    def slerp(self, o: "Quat", t: float) -> "Quat":
        dot = self.w * o.w + self.x * o.x + self.y * o.y + self.z * o.z
        ox, oy, oz, ow = o.x, o.y, o.z, o.w
        if dot < 0.0:
            dot = -dot
            ox, oy, oz, ow = -ox, -oy, -oz, -ow
        if dot > 0.9995:
            return Quat(
                self.w + (ow - self.w) * t,
                self.x + (ox - self.x) * t,
                self.y + (oy - self.y) * t,
                self.z + (oz - self.z) * t,
            ).normalized()
        theta_0 = math.acos(clamp(dot, -1.0, 1.0))
        theta = theta_0 * t
        sin_theta = math.sin(theta)
        sin_theta_0 = math.sin(theta_0)
        s0 = math.cos(theta) - dot * sin_theta / sin_theta_0
        s1 = sin_theta / sin_theta_0
        return Quat(
            s0 * self.w + s1 * ow,
            s0 * self.x + s1 * ox,
            s0 * self.y + s1 * oy,
            s0 * self.z + s1 * oz,
        )


@dataclass(slots=True)
class Transform:
    pos: Vec3 = field(default_factory=Vec3)
    rot: Quat = field(default_factory=Quat.identity)
    scale: Vec3 = field(default_factory=lambda: Vec3(1.0, 1.0, 1.0))

    def copy(self) -> "Transform":
        return Transform(self.pos.copy(), Quat(self.rot.w, self.rot.x, self.rot.y, self.rot.z), self.scale.copy())

    def apply_point(self, p: Vec3) -> Vec3:
        sp = Vec3(p.x * self.scale.x, p.y * self.scale.y, p.z * self.scale.z)
        rp = self.rot.rotate_vec(sp)
        return Vec3(rp.x + self.pos.x, rp.y + self.pos.y, rp.z + self.pos.z)

    def apply_dir(self, d: Vec3) -> Vec3:
        return self.rot.rotate_vec(d)

    def combine(self, child: "Transform") -> "Transform":
        world_pos = self.apply_point(child.pos)
        world_rot = (self.rot * child.rot).normalized()
        world_scale = Vec3(
            self.scale.x * child.scale.x,
            self.scale.y * child.scale.y,
            self.scale.z * child.scale.z,
        )
        return Transform(world_pos, world_rot, world_scale)


# =============================================================================
# COLOR MATH, MATERIALS & CINEMATIC INDOOR LIGHTING ENGINE
# =============================================================================

@dataclass(slots=True)
class Color3:
    r: float = 1.0
    g: float = 1.0
    b: float = 1.0

    def __add__(self, o: "Color3") -> "Color3":
        return Color3(self.r + o.r, self.g + o.g, self.b + o.b)

    def __mul__(self, s: float) -> "Color3":
        return Color3(self.r * s, self.g * s, self.b * s)

    def __rmul__(self, s: float) -> "Color3":
        return Color3(self.r * s, self.g * s, self.b * s)

    def mul_color(self, o: "Color3") -> "Color3":
        return Color3(self.r * o.r, self.g * o.g, self.b * o.b)

    def lerp(self, o: "Color3", t: float) -> "Color3":
        return Color3(
            self.r + (o.r - self.r) * t,
            self.g + (o.g - self.g) * t,
            self.b + (o.b - self.b) * t,
        )

    def to_rgb_int(self) -> Tuple[int, int, int]:
        # Filmic ACES-like curve for rich PS3-era cinematic contrast
        r = self.r
        g = self.g
        b = self.b
        r = (r * (2.51 * r + 0.03)) / (r * (2.43 * r + 0.59) + 0.14) if r > 0.0 else 0.0
        g = (g * (2.51 * g + 0.03)) / (g * (2.43 * g + 0.59) + 0.14) if g > 0.0 else 0.0
        b = (b * (2.51 * b + 0.03)) / (b * (2.43 * b + 0.59) + 0.14) if b > 0.0 else 0.0
        # Gentle shadow cool-indigo / highlight warm-gold split-toning
        luma = 0.2126 * r + 0.7152 * g + 0.0722 * b
        shadow_w = clamp01(1.0 - luma * 2.2) * 0.035
        hi_w = clamp01((luma - 0.5) * 1.6) * 0.025
        r = clamp01(r - shadow_w * 0.25 + hi_w * 0.85)
        g = clamp01(g - shadow_w * 0.08 + hi_w * 0.45)
        b = clamp01(b + shadow_w * 0.75 - hi_w * 0.20)
        return (int(r * 255.0), int(g * 255.0), int(b * 255.0))

    @staticmethod
    def from_hex(hex_str: str) -> "Color3":
        s = hex_str.lstrip("#")
        r = int(s[0:2], 16) / 255.0
        g = int(s[2:4], 16) / 255.0
        b = int(s[4:6], 16) / 255.0
        return Color3(r, g, b)


@dataclass(slots=True)
class Material:
    name: str
    base_color: Color3
    gradient_color: Optional[Color3] = None  # Secondary gradient end color
    roughness: float = 0.55
    specular: float = 0.18
    rim_strength: float = 0.22
    subsurface: float = 0.0      # Skin warm wrap scattering
    metallic: float = 0.0
    emissive: Color3 = field(default_factory=lambda: Color3(0.0, 0.0, 0.0))
    double_sided: bool = False
    is_gradient_radial: bool = False
    alpha: float = 1.0
    shadow_receive: float = 1.0


def build_material_library() -> Dict[str, Material]:
    """Curated PS3-era Japanese neo-noir + Team Ico palette (zero textures)."""
    mats: Dict[str, Material] = {}

    # Protagonist materials (Fatal Frame / FF13 delicate porcelain & vibrant swimwear)
    mats["skin"] = Material(
        name="skin",
        base_color=Color3(0.91, 0.75, 0.67),
        gradient_color=Color3(0.84, 0.64, 0.56),
        roughness=0.46,
        specular=0.22,
        rim_strength=0.38,
        subsurface=0.32,
    )
    # Skin blush with radial gradient for natural rosy cheek flush
    # (matching reference: subtle rosy flush on the cheeks)
    mats["skin_blush"] = Material(
        name="skin_blush",
        base_color=Color3(0.93, 0.72, 0.66),
        gradient_color=Color3(0.86, 0.58, 0.52),  # Deeper rosy center
        roughness=0.48,
        specular=0.18,
        rim_strength=0.34,
        subsurface=0.38,
        is_gradient_radial=True,
    )
    mats["lips"] = Material(
        name="lips",
        base_color=Color3(0.76, 0.36, 0.38),
        gradient_color=Color3(0.64, 0.28, 0.30),
        roughness=0.26,
        specular=0.46,
        rim_strength=0.20,
        subsurface=0.28,
    )
    mats["sclera"] = Material(
        name="sclera",
        base_color=Color3(0.95, 0.94, 0.96),
        gradient_color=Color3(0.82, 0.82, 0.87),
        roughness=0.18,
        specular=0.55,
        rim_strength=0.10,
    )
    mats["iris_black"] = Material(
        name="iris_black",
        base_color=Color3(0.04, 0.035, 0.045),
        gradient_color=Color3(0.11, 0.08, 0.09),
        roughness=0.10,
        specular=0.88,
        rim_strength=0.05,
        emissive=Color3(0.01, 0.01, 0.012),
    )
    # Dark brown iris (matching reference): rich warm brown with radial gradient
    # from deep mahogany center to lighter amber-brown rim for natural depth.
    mats["iris_dark_brown"] = Material(
        name="iris_dark_brown",
        base_color=Color3(0.16, 0.10, 0.06),    # Deep mahogany brown center
        gradient_color=Color3(0.28, 0.17, 0.09),  # Lighter amber-brown rim
        roughness=0.12,
        specular=0.82,
        rim_strength=0.08,
        emissive=Color3(0.012, 0.008, 0.005),
        is_gradient_radial=True,
    )
    mats["eye_catchlight"] = Material(
        name="eye_catchlight",
        base_color=Color3(0.96, 0.97, 1.0),
        gradient_color=Color3(0.72, 0.78, 0.92),  # Soft blue-white glow falloff
        roughness=0.05,
        specular=1.0,
        emissive=Color3(0.45, 0.44, 0.48),
        is_gradient_radial=True,
    )
    mats["lash_brow"] = Material(
        name="lash_brow",
        base_color=Color3(0.14, 0.09, 0.07),
        gradient_color=Color3(0.07, 0.04, 0.03),  # Deeper root-to-tip gradient
        roughness=0.65,
        specular=0.10,
        rim_strength=0.08,
    )
    mats["hair_dark_brown"] = Material(
        name="hair_dark_brown",
        base_color=Color3(0.17, 0.105, 0.075),
        gradient_color=Color3(0.10, 0.058, 0.042),
        roughness=0.34,
        specular=0.42,
        rim_strength=0.48,
        double_sided=True,
    )
    # Royal blue competitive one-piece swimsuit (matching reference image):
    # rich royal blue body fabric with deep navy gradient for athletic depth.
    mats["swimsuit_blue"] = Material(
        name="swimsuit_blue",
        base_color=Color3(0.13, 0.23, 0.52),   # Rich royal blue body
        gradient_color=Color3(0.06, 0.12, 0.32),  # Deep navy gradient end
        roughness=0.48,
        specular=0.28,
        rim_strength=0.38,
        double_sided=True,
    )
    # Crisp athletic white side-panel fabric with cool blue-grey gradient
    mats["swimsuit_white"] = Material(
        name="swimsuit_white",
        base_color=Color3(0.89, 0.91, 0.94),   # Crisp off-white panel
        gradient_color=Color3(0.66, 0.72, 0.82),  # Cool blue-grey shadow
        roughness=0.54,
        specular=0.30,
        rim_strength=0.34,
        double_sided=True,
    )
    # Light blue piping accent along white panel edges (thin decorative stitch)
    mats["swimsuit_piping"] = Material(
        name="swimsuit_piping",
        base_color=Color3(0.44, 0.64, 0.84),
        gradient_color=Color3(0.28, 0.46, 0.68),
        roughness=0.36,
        specular=0.46,
        rim_strength=0.30,
        double_sided=True,
    )
    # Bare skin tone (retained for limb/neck blends; torso now fully covered)
    mats["midriff_skin"] = Material(
        name="midriff_skin",
        base_color=Color3(0.92, 0.76, 0.68),
        gradient_color=Color3(0.85, 0.66, 0.58),
        roughness=0.47,
        specular=0.20,
        rim_strength=0.36,
        subsurface=0.30,
    )
    mats["sneaker_white"] = Material(
        name="sneaker_white",
        base_color=Color3(0.92, 0.92, 0.94),
        gradient_color=Color3(0.78, 0.80, 0.85),
        roughness=0.46,
        specular=0.24,
        rim_strength=0.22,
    )
    mats["sneaker_sole"] = Material(
        name="sneaker_sole",
        base_color=Color3(0.86, 0.87, 0.89),
        gradient_color=Color3(0.62, 0.64, 0.69),
        roughness=0.62,
        specular=0.14,
        rim_strength=0.16,
    )
    mats["sneaker_accent"] = Material(
        name="sneaker_accent",
        base_color=Color3(0.16, 0.34, 0.76),
        gradient_color=Color3(0.10, 0.22, 0.52),
        roughness=0.40,
        specular=0.28,
        rim_strength=0.20,
    )

    # Modern Japanese Bedroom architectural & furniture materials
    mats["floor_wood"] = Material(
        name="floor_wood",
        base_color=Color3(0.34, 0.23, 0.15),
        gradient_color=Color3(0.25, 0.16, 0.10),
        roughness=0.44,
        specular=0.28,
        rim_strength=0.12,
    )
    mats["floor_wood_alt"] = Material(
        name="floor_wood_alt",
        base_color=Color3(0.30, 0.20, 0.13),
        gradient_color=Color3(0.22, 0.14, 0.09),
        roughness=0.48,
        specular=0.24,
        rim_strength=0.12,
    )
    mats["wall_plaster"] = Material(
        name="wall_plaster",
        base_color=Color3(0.56, 0.55, 0.57),
        gradient_color=Color3(0.41, 0.41, 0.45),
        roughness=0.86,
        specular=0.05,
        rim_strength=0.08,
    )
    mats["wall_accent"] = Material(
        name="wall_accent",
        base_color=Color3(0.26, 0.28, 0.33),
        gradient_color=Color3(0.18, 0.20, 0.26),
        roughness=0.80,
        specular=0.08,
        rim_strength=0.12,
    )
    mats["ceiling"] = Material(
        name="ceiling",
        base_color=Color3(0.52, 0.52, 0.55),
        gradient_color=Color3(0.38, 0.39, 0.43),
        roughness=0.90,
        specular=0.04,
        rim_strength=0.05,
    )
    mats["baseboard"] = Material(
        name="baseboard",
        base_color=Color3(0.20, 0.17, 0.14),
        gradient_color=Color3(0.12, 0.09, 0.07),  # Top-to-bottom darkening
        roughness=0.55,
        specular=0.14,
    )
    mats["curtain_heavy"] = Material(
        name="curtain_heavy",
        base_color=Color3(0.16, 0.19, 0.28),
        gradient_color=Color3(0.09, 0.11, 0.19),
        roughness=0.88,
        specular=0.08,
        rim_strength=0.30,
        double_sided=True,
    )
    mats["window_glass_night"] = Material(
        name="window_glass_night",
        base_color=Color3(0.08, 0.13, 0.25),
        gradient_color=Color3(0.16, 0.25, 0.44),
        roughness=0.12,
        specular=0.75,
        emissive=Color3(0.08, 0.13, 0.25),
        is_gradient_radial=True,
    )
    mats["bed_frame"] = Material(
        name="bed_frame",
        base_color=Color3(0.20, 0.15, 0.11),
        gradient_color=Color3(0.14, 0.10, 0.08),
        roughness=0.52,
        specular=0.18,
    )
    mats["bed_sheet"] = Material(
        name="bed_sheet",
        base_color=Color3(0.76, 0.77, 0.80),
        gradient_color=Color3(0.55, 0.58, 0.65),
        roughness=0.78,
        specular=0.07,
        rim_strength=0.16,
    )
    mats["bed_duvet"] = Material(
        name="bed_duvet",
        base_color=Color3(0.24, 0.30, 0.42),
        gradient_color=Color3(0.15, 0.19, 0.29),
        roughness=0.82,
        specular=0.08,
        rim_strength=0.22,
    )
    mats["rug_woven"] = Material(
        name="rug_woven",
        base_color=Color3(0.32, 0.30, 0.29),
        gradient_color=Color3(0.22, 0.21, 0.22),
        roughness=0.95,
        specular=0.02,
        rim_strength=0.06,
    )
    mats["metal_dark"] = Material(
        name="metal_dark",
        base_color=Color3(0.13, 0.14, 0.16),
        gradient_color=Color3(0.08, 0.08, 0.10),
        roughness=0.28,
        specular=0.65,
        metallic=0.75,
        rim_strength=0.28,
    )
    mats["metal_chrome"] = Material(
        name="metal_chrome",
        base_color=Color3(0.74, 0.77, 0.82),
        gradient_color=Color3(0.42, 0.46, 0.54),
        roughness=0.14,
        specular=0.92,
        metallic=0.95,
        rim_strength=0.45,
    )
    mats["brass_warm"] = Material(
        name="brass_warm",
        base_color=Color3(0.78, 0.58, 0.28),
        gradient_color=Color3(0.48, 0.33, 0.14),
        roughness=0.24,
        specular=0.80,
        metallic=0.85,
        rim_strength=0.35,
    )
    mats["lamp_shade_warm"] = Material(
        name="lamp_shade_warm",
        base_color=Color3(0.95, 0.72, 0.46),
        gradient_color=Color3(0.78, 0.48, 0.26),
        roughness=0.70,
        specular=0.06,
        emissive=Color3(0.88, 0.56, 0.28),
        double_sided=True,
        is_gradient_radial=True,
    )
    mats["lamp_shade_tall"] = Material(
        name="lamp_shade_tall",
        base_color=Color3(0.92, 0.78, 0.62),
        gradient_color=Color3(0.72, 0.52, 0.34),
        roughness=0.72,
        specular=0.06,
        emissive=Color3(0.68, 0.48, 0.30),
        double_sided=True,
        is_gradient_radial=True,
    )
    mats["ac_plastic"] = Material(
        name="ac_plastic",
        base_color=Color3(0.84, 0.85, 0.87),
        gradient_color=Color3(0.70, 0.72, 0.76),
        roughness=0.42,
        specular=0.22,
    )
    mats["door_wood"] = Material(
        name="door_wood",
        base_color=Color3(0.28, 0.21, 0.16),
        gradient_color=Color3(0.21, 0.15, 0.11),
        roughness=0.55,
        specular=0.16,
    )
    mats["poster_art"] = Material(
        name="poster_art",
        base_color=Color3(0.22, 0.36, 0.48),
        gradient_color=Color3(0.76, 0.44, 0.28),
        roughness=0.50,
        specular=0.14,
        is_gradient_radial=True,
    )
    mats["cig_pack_body"] = Material(
        name="cig_pack_body",
        base_color=Color3(0.86, 0.86, 0.88),
        gradient_color=Color3(0.70, 0.72, 0.75),
        roughness=0.38,
        specular=0.25,
    )
    mats["cig_pack_band"] = Material(
        name="cig_pack_band",
        base_color=Color3(0.14, 0.25, 0.48),
        gradient_color=Color3(0.08, 0.15, 0.34),
        roughness=0.36,
        specular=0.28,
    )
    mats["cig_pack_gold"] = Material(
        name="cig_pack_gold",
        base_color=Color3(0.86, 0.70, 0.32),
        gradient_color=Color3(0.58, 0.44, 0.18),  # Rich gold gradient depth
        roughness=0.25,
        specular=0.65,
        metallic=0.7,
        is_gradient_radial=True,
    )
    mats["cig_paper"] = Material(
        name="cig_paper",
        base_color=Color3(0.95, 0.94, 0.91),
        gradient_color=Color3(0.82, 0.80, 0.76),
        roughness=0.80,
        specular=0.05,
    )
    mats["cig_filter"] = Material(
        name="cig_filter",
        base_color=Color3(0.82, 0.56, 0.28),
        gradient_color=Color3(0.68, 0.44, 0.20),
        roughness=0.72,
        specular=0.08,
    )
    mats["cig_ash"] = Material(
        name="cig_ash",
        base_color=Color3(0.42, 0.41, 0.43),
        gradient_color=Color3(0.24, 0.23, 0.25),
        roughness=0.95,
        specular=0.02,
    )
    mats["cig_ember"] = Material(
        name="cig_ember",
        base_color=Color3(1.0, 0.42, 0.10),
        gradient_color=Color3(0.85, 0.22, 0.04),  # Hot core to deep red edge
        roughness=0.80,
        emissive=Color3(1.6, 0.45, 0.06),
        is_gradient_radial=True,
    )
    mats["lighter_flame"] = Material(
        name="lighter_flame",
        base_color=Color3(1.0, 0.72, 0.24),
        gradient_color=Color3(0.32, 0.52, 1.0),
        roughness=0.10,
        emissive=Color3(2.2, 1.25, 0.35),
        double_sided=True,
    )
    return mats


@dataclass(slots=True)
class PointLight:
    pos: Vec3
    color: Color3
    intensity: float
    radius: float
    enabled: bool = True
    flicker_amp: float = 0.0
    flicker_speed: float = 0.0
    # Transient lights (lighter flame / cigarette ember) are excluded from the
    # static light bake and re-added dynamically each frame for nearby tris.
    transient: bool = False


@dataclass(slots=True)
class SpotLight:
    pos: Vec3
    direction: Vec3
    color: Color3
    intensity: float
    radius: float
    cos_inner: float
    cos_outer: float
    enabled: bool = True


class LightingRig:
    """
    Low-overhead physically-grounded indoor lighting solver.
    Without active light sources, the closed room drops to deep darkness.
    Active evening lamps + subtle window curtain moonlight leakage + transient
    lighter flame / cigarette ember create dramatic Japanese neo-noir mood.
    """

    def __init__(self) -> None:
        self.ambient_base = Color3(0.014, 0.018, 0.028)  # Deep indoor darkness floor
        self.hemi_sky = Color3(0.032, 0.044, 0.075)      # Faint cool ceiling bounce
        self.hemi_ground = Color3(0.026, 0.019, 0.015)   # Faint warm floor bounce

        # Moonlight directional beam creeping past curtains (+X/+Z window side)
        self.moon_dir = Vec3(-0.68, 0.52, -0.52).normalized()
        self.moon_color = Color3(0.24, 0.36, 0.64)
        self.moon_intensity = 0.42

        # Bedside warm tungsten lamp (primary key light on left side of bed)
        self.bedside_lamp = PointLight(
            pos=Vec3(-1.62, 0.84, -1.68),
            color=Color3(1.0, 0.66, 0.34),
            intensity=2.35,
            radius=4.6,
            flicker_amp=0.015,
            flicker_speed=4.7,
        )
        # Tall standing corner floor lamp (soft warm-peach fill near desk/right corner)
        self.floor_lamp = PointLight(
            pos=Vec3(1.88, 1.56, 1.52),
            color=Color3(0.98, 0.72, 0.48),
            intensity=1.95,
            radius=5.0,
            flicker_amp=0.01,
            flicker_speed=3.1,
        )
        # Cool moonlight leakage spot from balcony curtains (along Z = +2.35)
        self.curtain_spill = PointLight(
            pos=Vec3(-0.15, 1.45, 2.02),
            color=Color3(0.32, 0.48, 0.88),
            intensity=1.15,
            radius=4.2,
        )
        # Transient lighter flame light
        self.lighter_light = PointLight(
            pos=Vec3(0.0, 1.0, 0.0),
            color=Color3(1.0, 0.58, 0.18),
            intensity=0.0,
            radius=2.8,
            enabled=False,
            flicker_amp=0.18,
            flicker_speed=23.0,
            transient=True,
        )
        # Transient cigarette ember light (illuminates lips/cheek on drag!)
        self.ember_light = PointLight(
            pos=Vec3(0.0, 1.4, 0.0),
            color=Color3(1.0, 0.32, 0.06),
            intensity=0.0,
            radius=1.35,
            enabled=False,
            transient=True,
        )

        self.point_lights: List[PointLight] = [
            self.bedside_lamp,
            self.floor_lamp,
            self.curtain_spill,
            self.lighter_light,
            self.ember_light,
        ]
        self._time = 0.0
        self._eff_intensities: List[float] = [1.0] * len(self.point_lights)
        # Frozen light tables for the fast shading path (rebuilt every update)
        self.frozen_static_lights: Tuple[Tuple[float, ...], ...] = ()
        self.frozen_transient_lights: Tuple[Tuple[float, ...], ...] = ()
        self.frozen_all_lights: Tuple[Tuple[float, ...], ...] = ()
        self.frozen_char_lights: Tuple[Tuple[float, ...], ...] = ()
        self.static_version = 0
        self._static_state = -1

    def update(self, elapsed: float) -> None:
        self._time = elapsed
        static: List[Tuple[float, float, float, float, float, float, float, float]] = []
        transient: List[Tuple[float, float, float, float, float, float, float, float]] = []
        static_state = 0
        for idx, pl in enumerate(self.point_lights):
            if not pl.enabled or pl.intensity <= 0.0:
                eff = 0.0
            elif pl.flicker_amp > 0.0:
                f = (
                    math.sin(elapsed * pl.flicker_speed) * 0.55
                    + math.sin(elapsed * pl.flicker_speed * 2.37 + 1.3) * 0.45
                )
                eff = pl.intensity * (1.0 + f * pl.flicker_amp)
            else:
                eff = pl.intensity
            self._eff_intensities[idx] = eff
            entry = (
                pl.pos.x, pl.pos.y, pl.pos.z,
                pl.color.r, pl.color.g, pl.color.b,
                eff, pl.radius * pl.radius,
            )
            if pl.transient:
                if eff > 0.001:
                    transient.append(entry)
            else:
                if eff > 0.001:
                    static.append(entry)
                static_state |= (1 << idx) if pl.enabled else 0

        self.frozen_static_lights = tuple(static)
        self.frozen_all_lights = tuple(static) + tuple(transient)
        self.frozen_transient_lights = tuple(transient)
        # Character shading uses the two warm key lights only (the cool curtain
        # spill is still felt via the moon window-band term) — cheaper hot path
        self.frozen_char_lights = (
            tuple(e for i, e in enumerate(static) if i != 2) + tuple(transient)
        )
        if static_state != self._static_state:
            self._static_state = static_state
            self.static_version += 1

    def compute_surface_color(
        self,
        world_pos: Vec3,
        normal: Vec3,
        cam_pos: Vec3,
        mat: Material,
        grad_t: float = 0.5,
        occlusion: float = 1.0,
        lights: Optional[Sequence[Tuple[float, float, float, float, float, float, float, float]]] = None,
    ) -> Color3:
        """Compatibility wrapper around the fast shade path (returns Color3)."""
        r, g, b = shade_point(
            world_pos.x, world_pos.y, world_pos.z,
            normal.x, normal.y, normal.z,
            cam_pos.x, cam_pos.y, cam_pos.z,
            mat, grad_t, occlusion,
            self.frozen_all_lights if lights is None else lights,
        )
        return Color3(r / 255.0, g / 255.0, b / 255.0)


# Material scalar cache: name -> packed tuple (built once per material library)
# Layout: (ar, ag, ab, br, bg, bb, has_grad, spec, spec_pow, rim, sss, metal, emr, emg, emb)
_MAT_CACHE: Dict[str, Tuple[float, ...]] = {}


def build_mat_cache(materials: Dict[str, Material]) -> None:
    """Pre-extract material scalars into flat tuples for the hot shading loop."""
    for name, m in materials.items():
        if m.gradient_color is not None:
            has_grad = 1.0
            br, bg, bb = m.gradient_color.r, m.gradient_color.g, m.gradient_color.b
        else:
            has_grad = 0.0
            br = bg = bb = 0.0
        spec_pow = 8.0 + (1.0 - m.roughness) * 44.0
        _MAT_CACHE[name] = (
            m.base_color.r, m.base_color.g, m.base_color.b,
            br, bg, bb,
            has_grad,
            m.specular, spec_pow, m.rim_strength, m.subsurface, m.metallic,
            m.emissive.r, m.emissive.g, m.emissive.b,
        )


def _mat_mc(mat: Material) -> Tuple[float, ...]:
    mc = _MAT_CACHE.get(mat.name)
    if mc is None:
        build_mat_cache({mat.name: mat})
        mc = _MAT_CACHE[mat.name]
    return mc


def tonemap_rgb(r: float, g: float, b: float) -> Tuple[int, int, int]:
    """Filmic ACES-like tonemap via 1024-entry LUT + shadow-cool / warm split."""
    # ACES curve LUT (shared by all channels) built lazily on first call
    global _ACES_LUT
    if _ACES_LUT is None:
        lut = [0] * 1024
        for i in range(1024):
            x = i * (4.0 / 1023.0)
            y = (x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14)
            lut[i] = clamp(int(y * 255.0), 0, 255)
        _ACES_LUT = lut
    lut = _ACES_LUT
    ri = int(r * 255.75)
    if ri < 0:
        ri = 0
    elif ri > 1023:
        ri = 1023
    gi = int(g * 255.75)
    if gi < 0:
        gi = 0
    elif gi > 1023:
        gi = 1023
    bi = int(b * 255.75)
    if bi < 0:
        bi = 0
    elif bi > 1023:
        bi = 1023
    r8 = lut[ri]
    g8 = lut[gi]
    b8 = lut[bi]
    # Gentle shadow cool-indigo / highlight warm-gold split-toning (8-bit domain,
    # matches the original: sw' = sw*0.035, hw' = hw*0.025 on normalized channels)
    luma = (0.2126 * r8 + 0.7152 * g8 + 0.0722 * b8) * (1.0 / 255.0)
    sw = 1.0 - luma * 2.2
    if sw < 0.0:
        sw = 0.0
    hw = (luma - 0.5) * 1.6
    if hw < 0.0:
        hw = 0.0
    r = r8 - sw * 2.23 + hw * 5.36
    g = g8 - sw * 0.71 + hw * 2.84
    b = b8 + sw * 6.68 - hw * 1.28
    if r < 0.0:
        r = 0.0
    elif r > 255.0:
        r = 255.0
    if g < 0.0:
        g = 0.0
    elif g > 255.0:
        g = 255.0
    if b < 0.0:
        b = 0.0
    elif b > 255.0:
        b = 255.0
    return (int(r), int(g), int(b))


_ACES_LUT: Optional[List[int]] = None


def _shade_core(
    px: float,
    py: float,
    pz: float,
    nx: float,
    ny: float,
    nz: float,
    ex: float,
    ey: float,
    ez: float,
    mc: Tuple[float, ...],
    grad_t: float,
    occlusion: float,
    lights: Sequence[Tuple[float, float, float, float, float, float, float, float]],
) -> Tuple[int, int, int]:
    """Hot-path flat shading on a pre-extracted material tuple. No allocations."""
    # Albedo (base <-> gradient blend)
    if mc[6] > 0.5:
        t = grad_t
        if t < 0.0:
            t = 0.0
        elif t > 1.0:
            t = 1.0
        ar = mc[0] + (mc[3] - mc[0]) * t
        ag = mc[1] + (mc[4] - mc[1]) * t
        ab = mc[2] + (mc[5] - mc[2]) * t
    else:
        ar = mc[0]
        ag = mc[1]
        ab = mc[2]

    # Hemispheric ambient (linear mix of ground/sky bounce + base floor)
    hemi_t = ny * 0.5 + 0.5
    if hemi_t < 0.0:
        hemi_t = 0.0
    elif hemi_t > 1.0:
        hemi_t = 1.0
    acc_r = (0.040 + 0.006 * hemi_t) * ar * occlusion
    acc_g = (0.037 + 0.025 * hemi_t) * ag * occlusion
    acc_b = (0.043 + 0.060 * hemi_t) * ab * occlusion

    sss = mc[10]
    spec = mc[7]
    spec_pow = mc[8]
    rim_s = mc[9]
    metal = mc[11]

    # Cool moonlight leakage through window curtains (+Z side)
    if pz > -0.6:
        t = (pz + 0.6) * 0.3509  # / 2.85
        if t > 1.0:
            t = 1.0
        window_band = t * t * (3.0 - 2.0 * t)
        moon_ndotl = nx * -0.513 + ny * 0.392 + nz * -0.392
        if moon_ndotl < 0.0:
            moon_ndotl = 0.0
        if sss > 0.0:
            moon_ndotl = moon_ndotl * (1.0 - sss * 0.5) + sss * 0.35
            if moon_ndotl > 1.0:
                moon_ndotl = 1.0
        mw = 0.42 * window_band * moon_ndotl * occlusion
        acc_r += ar * 0.24 * mw
        acc_g += ag * 0.36 * mw
        acc_b += ab * 0.64 * mw

    # View vector (normalized) — needed only when spec or rim are active
    vx = vy = vz = 0.0
    need_view = spec > 0.01 or rim_s > 0.01
    if need_view:
        vx = ex - px
        vy = ey - py
        vz = ez - pz
        v_len = sqrt(vx * vx + vy * vy + vz * vz)
        if v_len > EPSILON:
            inv_v = 1.0 / v_len
            vx *= inv_v
            vy *= inv_v
            vz *= inv_v
        else:
            vx, vy, vz = 0.0, 0.0, 1.0

    # Cubic Fresnel approximation of (1-ndotv)^2.6 (pow-free)
    if rim_s > 0.01:
        ndotv = nx * vx + ny * vy + nz * vz
        if ndotv < 0.0:
            ndotv = 0.0
        fres = 1.0 - ndotv
        fresnel = fres * fres * fres

    for lx, ly, lz, cr, cg, cb, eff, rad_sq in lights:
        lx -= px
        ly -= py
        lz -= pz
        dist_sq = lx * lx + ly * ly + lz * lz
        if dist_sq >= rad_sq:
            continue
        dist = sqrt(dist_sq)
        if dist > EPSILON:
            inv_d = 1.0 / dist
            lx *= inv_d
            ly *= inv_d
            lz *= inv_d

        ratio = dist_sq / rad_sq
        win = 1.0 - ratio
        win *= win
        atten = (eff * win) / (1.0 + dist_sq * 0.68)
        if atten < 1e-5:
            continue

        ndotl = nx * lx + ny * ly + nz * lz
        if sss > 0.0:
            wrap = (ndotl + sss) / (1.0 + sss)
            if wrap < 0.0:
                wrap = 0.0
            elif wrap > 1.0:
                wrap = 1.0
            diff = wrap
            sss_boost = (1.0 - (ndotl if ndotl >= 0.0 else -ndotl)) * sss * 0.42
            if sss_boost < 0.0:
                sss_boost = 0.0
        else:
            diff = ndotl if ndotl > 0.0 else 0.0
            sss_boost = 0.0

        lr = cr * atten
        lg = cg * atten
        lb = cb * atten

        acc_r += ar * lr * (diff + sss_boost * 1.15)
        acc_g += ag * lg * (diff + sss_boost * 0.55)
        acc_b += ab * lb * (diff + sss_boost * 0.35)

        if spec > 0.01 and ndotl > -0.1:
            hx = lx + vx
            hy = ly + vy
            hz = lz + vz
            hl = sqrt(hx * hx + hy * hy + hz * hz)
            if hl > EPSILON:
                ndoth = (nx * hx + ny * hy + nz * hz) / hl
                # Early-out: skip the pow for grazing half-vectors (negligible spec)
                if ndoth > 0.32:
                    if ndoth < 0.0:
                        ndoth = 0.0
                    s = (ndoth ** spec_pow) * spec * atten
                    if metal > 0.1:
                        acc_r += lr * s * (1.0 + (ar - 1.0) * metal)
                        acc_g += lg * s * (1.0 + (ag - 1.0) * metal)
                        acc_b += lb * s * (1.0 + (ab - 1.0) * metal)
                    else:
                        acc_r += lr * s
                        acc_g += lg * s
                        acc_b += lb * s

        if rim_s > 0.01:
            rim_dir = 0.45 + 0.55 * (1.0 - (lx * vx + ly * vy + lz * vz)) * 0.5
            if rim_dir > 1.0:
                rim_dir = 1.0
            rim = fresnel * rim_s * atten * rim_dir * 1.05
            acc_r += lr * rim * (0.65 + 0.35 * ar)
            acc_g += lg * rim * (0.65 + 0.35 * ag)
            acc_b += lb * rim * (0.65 + 0.35 * ab)

    # Emissive
    acc_r += mc[12]
    acc_g += mc[13]
    acc_b += mc[14]

    return tonemap_rgb(acc_r, acc_g, acc_b)


def shade_point(
    px: float,
    py: float,
    pz: float,
    nx: float,
    ny: float,
    nz: float,
    ex: float,
    ey: float,
    ez: float,
    mat: Material,
    grad_t: float,
    occlusion: float,
    lights: Sequence[Tuple[float, float, float, float, float, float, float, float]],
    mc: Optional[Tuple[float, ...]] = None,
) -> Tuple[int, int, int]:
    """Shade with material object (looks up the scalar cache) — compat entry."""
    if mc is None:
        mc = _MAT_CACHE.get(mat.name)
        if mc is None:
            build_mat_cache({mat.name: mat})
            mc = _MAT_CACHE[mat.name]
    return _shade_core(px, py, pz, nx, ny, nz, ex, ey, ez, mc, grad_t, occlusion, lights)


def shade_point_hdr(
    px: float,
    py: float,
    pz: float,
    nx: float,
    ny: float,
    nz: float,
    mat: Material,
    grad_t: float,
    occlusion: float,
    lights: Sequence[Tuple[float, float, float, float, float, float, float, float]],
) -> Tuple[float, float, float]:
    """View-independent (bake) shading: ambient + moon + point lights + emissive."""
    mc = _MAT_CACHE.get(mat.name)
    if mc is None:
        build_mat_cache({mat.name: mat})
        mc = _MAT_CACHE[mat.name]

    if mc[6] > 0.5:
        t = grad_t
        if t < 0.0:
            t = 0.0
        elif t > 1.0:
            t = 1.0
        ar = mc[0] + (mc[3] - mc[0]) * t
        ag = mc[1] + (mc[4] - mc[1]) * t
        ab = mc[2] + (mc[5] - mc[2]) * t
    else:
        ar = mc[0]
        ag = mc[1]
        ab = mc[2]

    hemi_t = ny * 0.5 + 0.5
    if hemi_t < 0.0:
        hemi_t = 0.0
    elif hemi_t > 1.0:
        hemi_t = 1.0
    acc_r = (0.014 + 0.026 + (0.032 - 0.026) * hemi_t) * ar * occlusion
    acc_g = (0.018 + 0.019 + (0.044 - 0.019) * hemi_t) * ag * occlusion
    acc_b = (0.028 + 0.015 + (0.075 - 0.015) * hemi_t) * ab * occlusion

    sss = mc[10]

    if pz > -0.6:
        t = (pz + 0.6) / 2.85
        if t < 0.0:
            t = 0.0
        elif t > 1.0:
            t = 1.0
        window_band = t * t * (3.0 - 2.0 * t)
        moon_ndotl = nx * -0.513 + ny * 0.392 + nz * -0.392
        if moon_ndotl < 0.0:
            moon_ndotl = 0.0
        if sss > 0.0:
            moon_ndotl = moon_ndotl * (1.0 - sss * 0.5) + sss * 0.35
            if moon_ndotl > 1.0:
                moon_ndotl = 1.0
        mw = 0.42 * window_band * moon_ndotl * occlusion
        acc_r += ar * 0.24 * mw
        acc_g += ag * 0.36 * mw
        acc_b += ab * 0.64 * mw

    for lx, ly, lz, cr, cg, cb, eff, rad_sq in lights:
        lx -= px
        ly -= py
        lz -= pz
        dist_sq = lx * lx + ly * ly + lz * lz
        if dist_sq >= rad_sq:
            continue
        dist = math.sqrt(dist_sq)
        if dist > EPSILON:
            inv_d = 1.0 / dist
            lx *= inv_d
            ly *= inv_d
            lz *= inv_d
        ratio = dist_sq / rad_sq
        win = 1.0 - ratio
        win *= win
        atten = (eff * win) / (1.0 + dist_sq * 0.68)
        if atten < 1e-5:
            continue
        ndotl = nx * lx + ny * ly + nz * lz
        if sss > 0.0:
            wrap = (ndotl + sss) / (1.0 + sss)
            if wrap < 0.0:
                wrap = 0.0
            elif wrap > 1.0:
                wrap = 1.0
            diff = wrap
            sss_boost = (1.0 - (ndotl if ndotl >= 0.0 else -ndotl)) * sss * 0.42
            if sss_boost < 0.0:
                sss_boost = 0.0
        else:
            diff = ndotl if ndotl > 0.0 else 0.0
            sss_boost = 0.0
        lr = cr * atten
        lg = cg * atten
        lb = cb * atten
        acc_r += ar * lr * (diff + sss_boost * 1.15)
        acc_g += ag * lg * (diff + sss_boost * 0.55)
        acc_b += ab * lb * (diff + sss_boost * 0.35)

    acc_r += mc[12]
    acc_g += mc[13]
    acc_b += mc[14]
    return (acc_r, acc_g, acc_b)


def transient_diffuse(
    px: float,
    py: float,
    pz: float,
    nx: float,
    ny: float,
    nz: float,
    mat: Material,
    grad_t: float,
    occlusion: float,
    lights: Sequence[Tuple[float, float, float, float, float, float, float, float]],
) -> Tuple[float, float, float]:
    """Additive HDR contribution of transient lights only (for baked geometry)."""
    mc = _MAT_CACHE.get(mat.name)
    if mc is None:
        build_mat_cache({mat.name: mat})
        mc = _MAT_CACHE[mat.name]
    if mc[6] > 0.5:
        t = grad_t
        if t < 0.0:
            t = 0.0
        elif t > 1.0:
            t = 1.0
        ar = mc[0] + (mc[3] - mc[0]) * t
        ag = mc[1] + (mc[4] - mc[1]) * t
        ab = mc[2] + (mc[5] - mc[2]) * t
    else:
        ar = mc[0]
        ag = mc[1]
        ab = mc[2]
    acc_r = acc_g = acc_b = 0.0
    for lx, ly, lz, cr, cg, cb, eff, rad_sq in lights:
        lx -= px
        ly -= py
        lz -= pz
        dist_sq = lx * lx + ly * ly + lz * lz
        if dist_sq >= rad_sq:
            continue
        dist = math.sqrt(dist_sq)
        if dist > EPSILON:
            inv_d = 1.0 / dist
            lx *= inv_d
            ly *= inv_d
            lz *= inv_d
        ratio = dist_sq / rad_sq
        win = 1.0 - ratio
        win *= win
        atten = (eff * win) / (1.0 + dist_sq * 0.68)
        if atten < 1e-5:
            continue
        ndotl = nx * lx + ny * ly + nz * lz
        diff = ndotl if ndotl > 0.0 else 0.0
        acc_r += ar * cr * atten * diff
        acc_g += ag * cg * atten * diff
        acc_b += ab * cb * atten * diff
    return (acc_r, acc_g, acc_b)


# =============================================================================
# 3D SOFTWARE RASTERIZER, NEAR-CLIPPER & CINEMATIC POST-PROCESSING
# =============================================================================

_SHADOW_SCALES = (18, 28, 44, 68, 104, 150)


class RadialGlowCache:
    """Pre-baked radial gradient sprites for zero-cost atmospheric bloom & halos.

    Sprites are cached at the exact requested pixel radius (quantized to 4 px
    steps) so no per-frame rescaling is ever needed.
    """

    def __init__(self) -> None:
        self._cache: Dict[Tuple[int, int, int, int, int], pygame.Surface] = {}

    def get_glow(self, radius: int, color: Tuple[int, int, int], max_alpha: int = 120) -> pygame.Surface:
        r_q = clamp(radius, 4, 384)
        r_q = max(4, (r_q // 4) * 4)
        c_q = ((color[0] // 16) * 16, (color[1] // 16) * 16, (color[2] // 16) * 16)
        a_q = clamp(max_alpha, 8, 240)
        key = (r_q, c_q[0], c_q[1], c_q[2], a_q)
        surf = self._cache.get(key)
        if surf is not None:
            return surf

        size = r_q * 2
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        # 32 steps for ultra-smooth gradient — eliminates any visible banding
        # or circular rim that could read as a solid floating sphere.
        steps = 32
        for i in range(steps, 0, -1):
            t = i / steps
            ring_r = max(1, int(r_q * t))
            # Very broad, diffuse Gaussian falloff (k=1.8) — the bloom spreads
            # softly across the full radius with no concentrated central disc.
            # This ensures light sources read as atmospheric haze / volumetric
            # bloom, never as opaque floating balls.
            falloff = math.exp(-1.8 * t * t) * (1.0 - t * t) ** 0.6
            alpha = clamp(int(a_q * falloff * 0.48), 0, 255)
            if alpha > 0:
                pygame.draw.circle(surf, (c_q[0], c_q[1], c_q[2], alpha), (r_q, r_q), ring_r)
        if len(self._cache) > 220:
            self._cache.clear()
        self._cache[key] = surf
        return surf


class CinematicPostFX:
    """Soft filmic vignette + letterbox framing baked into ONE overlay blit."""

    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.letterbox_h = 0
        self.overlay: Optional[pygame.Surface] = None
        self.rebuild(width, height)

    def rebuild(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.letterbox_h = int(height * LETTERBOX_RATIO)

        # Radial vignette overlay generated with concentric dark borders
        vig = pygame.Surface((width, height), pygame.SRCALPHA)
        vig.fill((0, 0, 0, 0))
        cx, cy = width * 0.5, height * 0.5
        max_r = math.sqrt(cx * cx + cy * cy)
        rings = 20
        for i in range(rings):
            t0 = i / rings
            if t0 < 0.48:
                continue
            strength = ((t0 - 0.48) / 0.52) ** 1.9
            alpha = clamp(int(strength * 145), 0, 180)
            rx = int(cx * (1.15 - (t0 - 0.48) * 0.45))
            ry = int(cy * (1.15 - (t0 - 0.48) * 0.45))
            rect = pygame.Rect(int(cx - rx), int(cy - ry), rx * 2, ry * 2)
            pygame.draw.ellipse(vig, (6, 7, 12, alpha // 3), rect, max(6, int(max_r / rings)))
        # Corner soft darkening
        corner_r = int(max(width, height) * 0.42)
        corner_glow = pygame.Surface((corner_r * 2, corner_r * 2), pygame.SRCALPHA)
        for s in range(10, 0, -1):
            frac = s / 10.0
            a = int((1.0 - frac) * 28)
            pygame.draw.circle(corner_glow, (4, 5, 10, a), (corner_r, corner_r), int(corner_r * frac))
        vig.blit(corner_glow, (int(width * 0.5 - corner_r), int(height * 0.5 - corner_r)))
        # Letterbox bars baked straight into the overlay (single blit per frame)
        if self.letterbox_h > 0:
            pygame.draw.rect(vig, (5, 5, 8, 255), (0, 0, width, self.letterbox_h))
            pygame.draw.rect(
                vig,
                (5, 5, 8, 255),
                (0, height - self.letterbox_h, width, self.letterbox_h),
            )
        self.overlay = vig

    def apply(self, screen: pygame.Surface) -> None:
        if self.overlay is not None:
            screen.blit(self.overlay, (0, 0))


class CameraProjection:
    """View basis and perspective projection with fast point/triangle clipping."""

    def __init__(self, width: int, height: int, fov_deg: float = DEFAULT_FOV_DEG) -> None:
        self.width = width
        self.height = height
        self.cx = width * 0.5
        self.cy = height * 0.5
        self.pos = Vec3(0.0, 1.4, -2.0)
        self.forward = Vec3(0.0, 0.0, 1.0)
        self.right = Vec3(1.0, 0.0, 0.0)
        self.up = Vec3(0.0, 1.0, 0.0)
        self.fov_deg = fov_deg
        self.focal_len = 1.0
        self.set_fov(fov_deg)

    def resize(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.cx = width * 0.5
        self.cy = height * 0.5
        self.set_fov(self.fov_deg)

    def set_fov(self, fov_deg: float) -> None:
        self.fov_deg = fov_deg
        fov_rad = fov_deg * DEG2RAD
        self.focal_len = (self.height * 0.5) / math.tan(fov_rad * 0.5)

    def set_look_at(self, eye: Vec3, target: Vec3, world_up: Vec3 = VEC3_UP) -> None:
        self.pos = eye.copy()
        fwd = (target - eye).normalized()
        if fwd.length_sq() < EPSILON:
            fwd = Vec3(0.0, 0.0, 1.0)
        r = world_up.cross(fwd).normalized()
        if r.length_sq() < EPSILON:
            r = Vec3(1.0, 0.0, 0.0)
        u = fwd.cross(r).normalized()
        self.forward = fwd
        self.right = r
        self.up = u

    def world_to_view(self, p: Vec3) -> Tuple[float, float, float]:
        dx = p.x - self.pos.x
        dy = p.y - self.pos.y
        dz = p.z - self.pos.z
        vx = dx * self.right.x + dy * self.right.y + dz * self.right.z
        vy = dx * self.up.x + dy * self.up.y + dz * self.up.z
        vz = dx * self.forward.x + dy * self.forward.y + dz * self.forward.z
        return (vx, vy, vz)

    def project_view_point(self, vx: float, vy: float, vz: float) -> Tuple[float, float]:
        inv_z = self.focal_len / vz
        sx = self.cx + vx * inv_z
        sy = self.cy - vy * inv_z
        return (sx, sy)

    def project_world_point(self, p: Vec3) -> Optional[Tuple[float, float, float]]:
        vx, vy, vz = self.world_to_view(p)
        if vz <= NEAR_CLIP:
            return None
        sx, sy = self.project_view_point(vx, vy, vz)
        return (sx, sy, vz)


class SceneRenderer:
    """
    Layered software 3D rasterizer for PyGame (tuple-based hot path).
    Layer order:
      0 = Room outer shell (floor, walls, ceiling, window glass)
      1 = Floor rug & contact shadows
      2 = Room architecture trims, curtains, furniture, static props
      3 = Protagonist body, face features, hair, handheld props (one depth-sorted bucket
          so facial details are correctly occluded by the head from every angle)
      4 = Reserved
    Entries are flat tuples: (depth, x0, y0, x1, y1, x2, y2, color) — sorted with a
    plain tuple sort (no key lambda) and drawn with pygame.draw.polygon.
    """

    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.proj = CameraProjection(width, height)
        self.glow_cache = RadialGlowCache()
        self.post_fx = CinematicPostFX(width, height)

        self._tri_buckets: List[List[Tuple[float, ...]]] = [[] for _ in range(5)]
        self._alpha_polys: List[Tuple[float, List[Tuple[float, float]], Tuple[int, int, int, int]]] = []
        self._alpha_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        self._shadow_surf = pygame.Surface((128, 128), pygame.SRCALPHA)
        self._build_contact_shadow_sprite()
        self._prescale_shadow_sprites()

        # Occluder spheres for glow depth-testing: (cx, cy, cz, radius)
        self.static_occluders: List[Tuple[float, float, float, float]] = []
        self.character_occluders: List[Tuple[float, float, float, float]] = []

        # Per-frame cached camera basis (avoid attribute chase in hot loop)
        self._cam = (0.0, 0.0, 0.0)
        self._fwd = (0.0, 0.0, 1.0)
        self._rgt = (1.0, 0.0, 0.0)
        self._up = (0.0, 1.0, 0.0)
        self._fl = 1.0
        self._hw = width * 0.5
        self._hh = height * 0.5
        self.sync_camera()

    def _build_contact_shadow_sprite(self) -> None:
        self._shadow_surf.fill((0, 0, 0, 0))
        cx, cy = 64, 64
        for i in range(14, 0, -1):
            t = i / 14.0
            r = int(58 * t)
            a = int(14 * (1.0 - t * 0.72))
            pygame.draw.circle(self._shadow_surf, (6, 6, 10, a), (cx, cy), r)

    def resize(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.proj.resize(width, height)
        self.post_fx.rebuild(width, height)
        self._alpha_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        self.sync_camera()

    def sync_camera(self) -> None:
        p = self.proj
        self._cam = (p.pos.x, p.pos.y, p.pos.z)
        self._fwd = (p.forward.x, p.forward.y, p.forward.z)
        self._rgt = (p.right.x, p.right.y, p.right.z)
        self._up = (p.up.x, p.up.y, p.up.z)
        self._fl = p.focal_len
        self._hw = self.width * 0.5
        self._hh = self.height * 0.5

    def begin_frame(self) -> None:
        for b in self._tri_buckets:
            b.clear()
        self._alpha_polys.clear()
        self.sync_camera()

    # ------------------------------------------------------------------
    # Frustum & occlusion helpers
    # ------------------------------------------------------------------
    def sphere_outside_frustum(self, cx: float, cy: float, cz: float, radius: float) -> bool:
        """Conservative whole-chunk rejection using view-space extents."""
        ex, ey, ez = self._cam
        fx, fy, fz = self._fwd
        rx, ry, rz = self._rgt
        ux, uy, uz = self._up
        dx = cx - ex
        dy = cy - ey
        dz = cz - ez
        vz = dx * fx + dy * fy + dz * fz
        if vz < -radius or vz > FAR_CLIP + radius:
            return True
        vx = dx * rx + dy * ry + dz * rz
        if abs(vx) > vz * self._hw / self._fl + radius:
            return True
        vy = dx * ux + dy * uy + dz * uz
        if abs(vy) > vz * self._hh / self._fl + radius:
            return True
        return False

    def _ray_occluded(self, wx: float, wy: float, wz: float) -> bool:
        """True if the segment camera -> point passes through any occluder sphere."""
        ex, ey, ez = self._cam
        dx = wx - ex
        dy = wy - ey
        dz = wz - ez
        dist = math.sqrt(dx * dx + dy * dy + dz * dz)
        if dist < 1e-4:
            return False
        inv = 1.0 / dist
        dx *= inv
        dy *= inv
        dz *= inv
        max_t = dist * 0.94
        for occl in (self.static_occluders, self.character_occluders):
            for cx, cy, cz, r in occl:
                gx = wx - cx
                gy = wy - cy
                gz = wz - cz
                # Skip occluders that contain the glow point itself (light's own shade)
                rr = r * 0.92
                if gx * gx + gy * gy + gz * gz < rr * rr:
                    continue
                ox = cx - ex
                oy = cy - ey
                oz = cz - ez
                proj = ox * dx + oy * dy + oz * dz
                if proj <= 0.0 or proj >= max_t:
                    continue
                perp_sq = ox * ox + oy * oy + oz * oz - proj * proj
                if perp_sq < r * r:
                    return True
        return False

    def submit_triangle(
        self,
        v0: Vec3,
        v1: Vec3,
        v2: Vec3,
        normal: Vec3,
        mat: Material,
        lighting: LightingRig,
        layer: int = 2,
        grad_t: float = 0.5,
        depth_bias: float = 0.0,
        occlusion: float = 1.0,
        precomputed_color: Optional[Tuple[int, int, int]] = None,
        mc: Optional[Tuple[float, ...]] = None,
        min_area: float = 1.4,
        lights: Optional[Sequence[Tuple[float, ...]]] = None,
    ) -> None:
        """Flat-shaded triangle submit. Flat tuples, inline transforms, early rejects."""
        proj = self.proj
        ex, ey, ez = self._cam
        rx, ry, rz = self._rgt
        ux, uy, uz = self._up
        fx, fy, fz = self._fwd

        v0x = v0.x
        v0y = v0.y
        v0z = v0.z
        cx = (v0x + v1.x + v2.x) * 0.3333333
        cy = (v0y + v1.y + v2.y) * 0.3333333
        cz = (v0z + v1.z + v2.z) * 0.3333333

        to_cam_x = ex - cx
        to_cam_y = ey - cy
        to_cam_z = ez - cz
        ndotc = normal.x * to_cam_x + normal.y * to_cam_y + normal.z * to_cam_z

        if not mat.double_sided:
            if ndotc <= -0.002:
                return

        # Inline view-space transform (no per-vertex allocations)
        dx = v0x - ex
        dy = v0y - ey
        dz = v0z - ez
        z0 = dx * fx + dy * fy + dz * fz
        if z0 > FAR_CLIP:
            return
        x0v = dx * rx + dy * ry + dz * rz
        y0v = dx * ux + dy * uy + dz * uz

        dx = v1.x - ex
        dy = v1.y - ey
        dz = v1.z - ez
        z1 = dx * fx + dy * fy + dz * fz
        x1v = dx * rx + dy * ry + dz * rz
        y1v = dx * ux + dy * uy + dz * uz

        dx = v2.x - ex
        dy = v2.y - ey
        dz = v2.z - ez
        z2 = dx * fx + dy * fy + dz * fz
        x2v = dx * rx + dy * ry + dz * rz
        y2v = dx * ux + dy * uy + dz * uz

        if z0 < NEAR_CLIP and z1 < NEAR_CLIP and z2 < NEAR_CLIP:
            return

        # Shade only triangles that survive culling
        if precomputed_color is not None:
            color = precomputed_color
        else:
            if lights is None:
                lights = lighting.frozen_all_lights
            if mat.double_sided and ndotc < 0.0:
                color = _shade_core(
                    cx, cy, cz,
                    -normal.x, -normal.y, -normal.z,
                    ex, ey, ez,
                    mc if mc is not None else _mat_mc(mat), grad_t, occlusion,
                    lights,
                )
            else:
                color = _shade_core(
                    cx, cy, cz,
                    normal.x, normal.y, normal.z,
                    ex, ey, ez,
                    mc if mc is not None else _mat_mc(mat), grad_t, occlusion,
                    lights,
                )

        fl = self._fl
        hw = self._hw
        hh = self._hh
        w_lim = self.width + 80.0
        h_lim = self.height + 80.0

        if z0 >= NEAR_CLIP and z1 >= NEAR_CLIP and z2 >= NEAR_CLIP:
            inv0 = fl / z0
            s0x = hw + x0v * inv0
            s0y = hh - y0v * inv0
            inv1 = fl / z1
            s1x = hw + x1v * inv1
            s1y = hh - y1v * inv1
            inv2 = fl / z2
            s2x = hw + x2v * inv2
            s2y = hh - y2v * inv2

            # Screen-bounds trivial reject
            if (
                (s0x < -80.0 and s1x < -80.0 and s2x < -80.0)
                or (s0x > w_lim and s1x > w_lim and s2x > w_lim)
                or (s0y < -80.0 and s1y < -80.0 and s2y < -80.0)
                or (s0y > h_lim and s1y > h_lim and s2y > h_lim)
            ):
                return

            # Sub-pixel area reject (kills shimmering distant tessellation)
            # areax - areay is twice the signed screen area of the triangle
            area2 = (s1x - s0x) * (s2y - s0y) - (s1y - s0y) * (s2x - s0x)
            if -min_area < area2 < min_area:
                return

            avg_z = (z0 + z1 + z2) * 0.3333333 + depth_bias
            self._tri_buckets[layer].append(
                (avg_z, s0x, s0y, s1x, s1y, s2x, s2y, color)
            )
            return

        # Sutherland-Hodgman near-plane clip (rare path)
        verts = ((x0v, y0v, z0), (x1v, y1v, z1), (x2v, y2v, z2))
        clipped: List[Tuple[float, float, float]] = []
        for idx in range(3):
            cur = verts[idx]
            nxt = verts[(idx + 1) % 3]
            cur_in = cur[2] >= NEAR_CLIP
            nxt_in = nxt[2] >= NEAR_CLIP
            if cur_in and nxt_in:
                clipped.append(nxt)
            elif cur_in and not nxt_in:
                t = (NEAR_CLIP - cur[2]) / (nxt[2] - cur[2])
                clipped.append((
                    cur[0] + (nxt[0] - cur[0]) * t,
                    cur[1] + (nxt[1] - cur[1]) * t,
                    NEAR_CLIP,
                ))
            elif not cur_in and nxt_in:
                t = (NEAR_CLIP - cur[2]) / (nxt[2] - cur[2])
                clipped.append((
                    cur[0] + (nxt[0] - cur[0]) * t,
                    cur[1] + (nxt[1] - cur[1]) * t,
                    NEAR_CLIP,
                ))
                clipped.append(nxt)

        if len(clipped) >= 3:
            pts_2d = [proj.project_view_point(vx, vy, vz) for (vx, vy, vz) in clipped]
            avg_z = sum(v[2] for v in clipped) / len(clipped) + depth_bias
            self._tri_buckets[layer].append(
                (avg_z, pts_2d[0][0], pts_2d[0][1], pts_2d[1][0], pts_2d[1][1], pts_2d[2][0], pts_2d[2][1], color)
            )
            if len(clipped) == 4:
                self._tri_buckets[layer].append(
                    (avg_z, pts_2d[0][0], pts_2d[0][1], pts_2d[2][0], pts_2d[2][1], pts_2d[3][0], pts_2d[3][1], color)
                )

    def submit_alpha_quad(
        self,
        world_pts: Sequence[Vec3],
        rgba: Tuple[int, int, int, int],
    ) -> None:
        if rgba[3] <= 1:
            return
        projected: List[Tuple[float, float]] = []
        z_sum = 0.0
        for p in world_pts:
            res = self.proj.project_world_point(p)
            if res is None:
                return
            projected.append((res[0], res[1]))
            z_sum += res[2]
        avg_z = z_sum / len(world_pts)
        self._alpha_polys.append((avg_z, projected, rgba))

    def draw_contact_shadow(self, screen: pygame.Surface, foot_pos: Vec3, radius_world: float = 0.28, alpha_scale: float = 1.0) -> None:
        res = self.proj.project_world_point(foot_pos)
        if res is None or res[2] <= NEAR_CLIP:
            return
        sx, sy, vz = res
        px_r = clamp(int((radius_world * self.proj.focal_len) / vz), 6, 160)
        # Pick a pre-scaled sprite (no per-frame smoothscale)
        best_k = min(_SHADOW_SCALES, key=lambda k: abs(k - px_r))
        scaled = self._shadow_prescale[best_k]
        py_r = max(4, int(best_k * 0.56))
        if sx + best_k < 0 or sx - best_k > self.width or sy + py_r < 0 or sy - py_r > self.height:
            return
        if alpha_scale < 0.99:
            alpha = int(255 * clamp01(alpha_scale))
            scaled.set_alpha(alpha)
        else:
            scaled.set_alpha(None)
        screen.blit(scaled, (int(sx - best_k), int(sy - py_r)))

    def _prescale_shadow_sprites(self) -> None:
        self._shadow_prescale = {}
        for k in _SHADOW_SCALES:
            py_r = max(4, int(k * 0.56))
            self._shadow_prescale[k] = pygame.transform.smoothscale(
                self._shadow_surf, (k * 2, py_r * 2)
            )

    def draw_radial_glow(
        self,
        screen: pygame.Surface,
        world_pos: Vec3,
        world_radius: float,
        color: Tuple[int, int, int],
        max_alpha: int = 120,
        additive: bool = True,
        occlude: bool = False,
    ) -> None:
        res = self.proj.project_world_point(world_pos)
        if res is None or res[2] <= NEAR_CLIP:
            return
        sx, sy, vz = res
        px_r = clamp(int((world_radius * self.proj.focal_len) / vz), 4, 360)
        if sx + px_r < 0 or sx - px_r > self.width or sy + px_r < 0 or sy - px_r > self.height:
            return
        # Depth-occlusion: skip halos hidden behind furniture or the character
        if occlude and self._ray_occluded(world_pos.x, world_pos.y, world_pos.z):
            return
        glow = self.glow_cache.get_glow(px_r, color, max_alpha)
        flags = pygame.BLEND_RGB_ADD if additive else 0
        screen.blit(glow, (int(sx - px_r), int(sy - px_r)), special_flags=flags)

    def draw_soft_point(
        self,
        screen: pygame.Surface,
        world_pos: Vec3,
        pixel_radius: int,
        color: Tuple[int, int, int],
        max_alpha: int,
    ) -> None:
        """Tiny soft ambient point (dust motes): 1-4 px feathered sprite."""
        if pixel_radius < 1:
            return
        if pixel_radius > 5:
            pixel_radius = 5
        res = self.proj.project_world_point(world_pos)
        if res is None or res[2] <= NEAR_CLIP:
            return
        sx, sy, _vz = res
        if sx < -4 or sx > self.width + 4 or sy < -4 or sy > self.height + 4:
            return
        spr = self.glow_cache.get_glow(pixel_radius * 2, color, max_alpha)
        screen.blit(spr, (int(sx - pixel_radius * 2), int(sy - pixel_radius * 2)), special_flags=pygame.BLEND_RGB_ADD)

    def flush_geometry(self, screen: pygame.Surface) -> None:
        draw_poly = pygame.draw.polygon
        for layer_idx in range(5):
            bucket = self._tri_buckets[layer_idx]
            if not bucket:
                continue
            bucket.sort(reverse=True)
            for depth, x0, y0, x1, y1, x2, y2, color in bucket:
                draw_poly(screen, color, ((x0, y0), (x1, y1), (x2, y2)))

    def flush_atmospherics(
        self,
        screen: pygame.Surface,
        lighting: LightingRig,
        smoke_particles: Sequence[Tuple[Vec3, float, Tuple[int, int, int], int]],
        dust_motes: Sequence[Tuple[Vec3, float, Tuple[int, int, int], int]],
    ) -> None:
        # Volumetric moonlight shafts spilling through balcony curtain edge
        self._alpha_surf.fill((0, 0, 0, 0))
        if self._alpha_polys:
            self._alpha_polys.sort(key=lambda item: item[0], reverse=True)
            for _, pts, rgba in self._alpha_polys:
                pygame.draw.polygon(self._alpha_surf, rgba, pts)
            screen.blit(self._alpha_surf, (0, 0))

        # Soft lamp halos & lighter/ember glows (additive bloom).
        # CRITICAL FIX: Previous version used a tight bright core (0.06 radius,
        # alpha 48) that rendered as a visible floating sphere. Now ONLY diffuse
        # atmospheric bloom layers are drawn — the lamp shade's emissive material
        # provides the visible light source itself, and these halos just soften
        # the surrounding air into cinematic bloom. No tight cores, no spheres.
        if lighting.bedside_lamp.enabled:
            lp = lighting.bedside_lamp.pos
            halo = Vec3(lp.x, lp.y + 0.10, lp.z)
            # Single broad diffuse wash only — reads as warm air glow, not a ball
            self.draw_radial_glow(screen, halo, 0.22, (255, 168, 88), max_alpha=10, additive=True, occlude=True)
            self.draw_radial_glow(screen, halo, 0.48, (255, 155, 75), max_alpha=4, additive=True, occlude=True)
        if lighting.floor_lamp.enabled:
            lp = lighting.floor_lamp.pos
            halo = Vec3(lp.x, lp.y + 0.14, lp.z)
            self.draw_radial_glow(screen, halo, 0.22, (250, 195, 128), max_alpha=8, additive=True, occlude=True)
            self.draw_radial_glow(screen, halo, 0.48, (248, 182, 115), max_alpha=3, additive=True, occlude=True)
        # (The curtain moonlight spill reads through the emissive window glass
        # and the volumetric shaft quads — no circular halo there, which used
        # to render as a floating blue ball on the curtains.)
        if lighting.lighter_light.enabled and lighting.lighter_light.intensity > 0.05:
            # Lighter flame: small diffuse glow only (the flame cone mesh is the
            # visible light source). No tight core that could read as a sphere.
            self.draw_radial_glow(
                screen,
                lighting.lighter_light.pos,
                0.10,
                (255, 150, 50),
                max_alpha=28,
                additive=True,
                occlude=False,
            )
        if lighting.ember_light.enabled and lighting.ember_light.intensity > 0.02:
            # Cigarette ember: tiny faint diffuse glow. The ember mesh cylinder
            # itself is the visible light source; this just adds lip/cheek warmth.
            self.draw_radial_glow(
                screen,
                lighting.ember_light.pos,
                0.035 + lighting.ember_light.intensity * 0.025,
                (255, 100, 30),
                max_alpha=clamp(int(14 + lighting.ember_light.intensity * 22), 10, 28),
                additive=True,
                occlude=False,
            )

        # Dust motes drifting in the Team Ico stillness: sub-pixel specks
        for pos, _rad, col, alpha in dust_motes:
            res = self.proj.project_world_point(pos)
            if res is None:
                continue
            vz = res[2]
            # Ultra-fine dust: 1px only for authentic atmospheric particulate
            pr = 1
            self.draw_soft_point(screen, pos, pr, col, alpha)

        # Curling cigarette smoke wisps (soft radial sprites, back-to-front)
        if smoke_particles:
            ordered = []
            for pos, rad, col, alpha in smoke_particles:
                if alpha <= 2:
                    continue
                res = self.proj.project_world_point(pos)
                if res is None:
                    continue
                ordered.append((res[2], pos, rad, col, alpha))
            ordered.sort(reverse=True)
            for _vz, pos, rad, col, alpha in ordered:
                self.draw_radial_glow(screen, pos, rad, col, max_alpha=alpha, additive=False)


# =============================================================================
# COLLISION ENGINE, CAMERA RAY SWEEP & SECONDARY HAIR SPRING PHYSICS
# =============================================================================

@dataclass(slots=True)
class AABBCollider:
    name: str
    min_x: float
    max_x: float
    min_y: float
    max_y: float
    min_z: float
    max_z: float
    blocks_camera: bool = True

    def push_out_circle_xz(self, px: float, pz: float, radius: float) -> Tuple[float, float, bool]:
        """Resolve 2D circle vs AABB in XZ plane with smooth wall sliding."""
        closest_x = clamp(px, self.min_x, self.max_x)
        closest_z = clamp(pz, self.min_z, self.max_z)
        dx = px - closest_x
        dz = pz - closest_z
        dist_sq = dx * dx + dz * dz
        if dist_sq >= radius * radius:
            return px, pz, False

        if dist_sq > EPSILON:
            dist = math.sqrt(dist_sq)
            push = radius - dist
            nx = dx / dist
            nz = dz / dist
            return px + nx * push, pz + nz * push, True

        # Center inside AABB: push out via nearest face
        pen_left = px - self.min_x
        pen_right = self.max_x - px
        pen_back = pz - self.min_z
        pen_front = self.max_z - pz
        m = min(pen_left, pen_right, pen_back, pen_front)
        if m == pen_left:
            return self.min_x - radius, pz, True
        if m == pen_right:
            return self.max_x + radius, pz, True
        if m == pen_back:
            return px, self.min_z - radius, True
        return px, self.max_z + radius, True

    def ray_intersect(self, orig: Vec3, direction: Vec3, max_t: float) -> Optional[float]:
        """Slab intersection returning nearest hit t in [0, max_t], or None."""
        tmin = 0.0
        tmax = max_t

        for o_c, d_c, bmin, bmax in (
            (orig.x, direction.x, self.min_x, self.max_x),
            (orig.y, direction.y, self.min_y, self.max_y),
            (orig.z, direction.z, self.min_z, self.max_z),
        ):
            if abs(d_c) < 1e-7:
                if o_c < bmin or o_c > bmax:
                    return None
            else:
                inv_d = 1.0 / d_c
                t1 = (bmin - o_c) * inv_d
                t2 = (bmax - o_c) * inv_d
                if t1 > t2:
                    t1, t2 = t2, t1
                if t1 > tmin:
                    tmin = t1
                if t2 < tmax:
                    tmax = t2
                if tmin > tmax:
                    return None
        return tmin


class RoomCollisionWorld:
    """Contains room walls and furniture colliders for grounded movement & camera safety."""

    def __init__(self) -> None:
        self.colliders: List[AABBCollider] = []
        self._build_room_colliders()

    def _build_room_colliders(self) -> None:
        # Platform bed (placed along back-left wall, X in [-2.45, -0.82], Z in [-2.28, -0.18])
        self.colliders.append(
            AABBCollider("platform_bed", -2.48, -0.80, 0.0, 0.56, -2.30, -0.16, blocks_camera=False)
        )
        # Bedside nightstand (left of bed corner? Actually right beside bed head: X in [-0.76, -0.26], Z in [-2.26, -1.78])
        # Wait: let's place nightstand on the left side of bed or right side so she can walk easily around!
        # Let's put Bed at X in [-2.42, -1.04], Z in [-2.25, -0.15] (headboard at Z=-2.25)
        # Wait: let's keep Bed at X in [-2.42, -1.02], Z in [-2.26, -0.18], Nightstand at X in [-0.94, -0.44], Z in [-2.26, -1.76]
        # Let's update platform_bed cleanly:
        self.colliders.clear()
        self.colliders.append(
            AABBCollider("platform_bed", -2.44, -1.02, 0.0, 0.58, -2.28, -0.18, blocks_camera=False)
        )
        self.colliders.append(
            AABBCollider("nightstand", -0.96, -0.44, 0.0, 0.62, -2.28, -1.74, blocks_camera=False)
        )
        # Compact modern Japanese desk/sideboard along right wall (X in [1.72, 2.46], Z in [-0.75, 0.78])
        self.colliders.append(
            AABBCollider("desk", 1.72, 2.48, 0.0, 0.78, -0.78, 0.78, blocks_camera=False)
        )
        # Minimalist desk chair tucked partly near desk (X in [1.22, 1.72], Z in [-0.26, 0.28])
        self.colliders.append(
            AABBCollider("desk_chair", 1.24, 1.74, 0.0, 0.85, -0.26, 0.28, blocks_camera=False)
        )
        # Wardrobe / closet along back-right wall (X in [0.98, 2.46], Z in [-2.30, -1.66])
        self.colliders.append(
            AABBCollider("wardrobe", 0.96, 2.48, 0.0, 2.15, -2.32, -1.64, blocks_camera=True)
        )
        # Standing floor lamp base in front-right corner (X in [1.70, 2.16], Z in [1.34, 1.82])
        self.colliders.append(
            AABBCollider("floor_lamp", 1.70, 2.18, 0.0, 1.72, 1.34, 1.82, blocks_camera=False)
        )
        # Low coffee / side table near window left (X in [-2.25, -1.48], Z in [1.05, 1.80])
        self.colliders.append(
            AABBCollider("low_table", -2.26, -1.46, 0.0, 0.44, 1.04, 1.82, blocks_camera=False)
        )

    def resolve_character_position(self, pos: Vec3, radius: float) -> Tuple[Vec3, bool]:
        px, pz = pos.x, pos.z
        collided = False

        # Two relaxation iterations eliminate corner oscillation
        for _ in range(2):
            for col in self.colliders:
                px, pz, hit = col.push_out_circle_xz(px, pz, radius)
                if hit:
                    collided = True

            # Room interior wall boundaries (leaving slight margin for baseboards & curtains)
            min_x = -ROOM_HALF_W + radius + 0.06
            max_x = ROOM_HALF_W - radius - 0.06
            min_z = -ROOM_HALF_D + radius + 0.06
            max_z = ROOM_HALF_D - radius - 0.12  # Curtains along +Z window wall

            if px < min_x:
                px = min_x
                collided = True
            elif px > max_x:
                px = max_x
                collided = True
            if pz < min_z:
                pz = min_z
                collided = True
            elif pz > max_z:
                pz = max_z
                collided = True

        return Vec3(px, 0.0, pz), collided

    def clamp_camera_position(self, target: Vec3, desired_eye: Vec3, margin: float = 0.16) -> Vec3:
        """Keep cinematic camera inside room walls and clear of tall wardrobe."""
        vec = desired_eye - target
        dist = vec.length()
        if dist < EPSILON:
            return desired_eye.copy()
        direction = vec / dist

        best_t = dist
        # Check room walls
        bounds = (
            (-ROOM_HALF_W + margin, ROOM_HALF_W - margin),
            (0.14, ROOM_HEIGHT - 0.14),
            (-ROOM_HALF_D + margin, ROOM_HALF_D - margin),
        )
        orig_comps = (target.x, target.y, target.z)
        dir_comps = (direction.x, direction.y, direction.z)

        for oc, dc, (bmin, bmax) in zip(orig_comps, dir_comps, bounds):
            if abs(dc) > 1e-6:
                if dc < 0.0:
                    t_hit = (bmin - oc) / dc
                    if 0.05 < t_hit < best_t:
                        best_t = t_hit
                else:
                    t_hit = (bmax - oc) / dc
                    if 0.05 < t_hit < best_t:
                        best_t = t_hit

        for col in self.colliders:
            if not col.blocks_camera:
                continue
            hit_t = col.ray_intersect(target, direction, best_t)
            if hit_t is not None and hit_t > 0.05:
                best_t = max(0.28, hit_t - 0.12)

        final_eye = target + direction * best_t
        final_eye.x = clamp(final_eye.x, -ROOM_HALF_W + margin, ROOM_HALF_W - margin)
        final_eye.y = clamp(final_eye.y, 0.16, ROOM_HEIGHT - 0.15)
        final_eye.z = clamp(final_eye.z, -ROOM_HALF_D + margin, ROOM_HALF_D - margin)
        return final_eye


@dataclass(slots=True)
class HairStrandSpring:
    """Damped harmonic oscillator for realistic dark-brown shoulder-length hair sway."""
    pitch: float = 0.0
    roll: float = 0.0
    vel_pitch: float = 0.0
    vel_roll: float = 0.0
    stiffness: float = 48.0
    damping: float = 7.5
    max_angle: float = 0.58

    def step(self, target_pitch: float, target_roll: float, dt: float) -> Tuple[float, float]:
        acc_p = (target_pitch - self.pitch) * self.stiffness - self.vel_pitch * self.damping
        acc_r = (target_roll - self.roll) * self.stiffness - self.vel_roll * self.damping
        self.vel_pitch += acc_p * dt
        self.vel_roll += acc_r * dt
        self.pitch = clamp(self.pitch + self.vel_pitch * dt, -self.max_angle, self.max_angle)
        self.roll = clamp(self.roll + self.vel_roll * dt, -self.max_angle, self.max_angle)
        return self.pitch, self.roll


class HairPhysicsRig:
    """Drives 6 independent hair strand chains (back L/C/R, temple L/R, bangs)."""

    def __init__(self) -> None:
        self.back_center = HairStrandSpring(stiffness=42.0, damping=6.2, max_angle=0.62)
        self.back_left = HairStrandSpring(stiffness=46.0, damping=6.5, max_angle=0.65)
        self.back_right = HairStrandSpring(stiffness=46.0, damping=6.5, max_angle=0.65)
        self.temple_left = HairStrandSpring(stiffness=54.0, damping=7.2, max_angle=0.52)
        self.temple_right = HairStrandSpring(stiffness=54.0, damping=7.2, max_angle=0.52)
        self.bangs = HairStrandSpring(stiffness=75.0, damping=9.5, max_angle=0.22)
        self._prev_head_pos = Vec3(0.0, 1.5, 0.0)
        self._prev_yaw = 0.0
        self._init = False

    def update(
        self,
        head_world_pos: Vec3,
        head_world_rot: Quat,
        char_yaw: float,
        dt: float,
        elapsed: float,
    ) -> Dict[str, Tuple[float, float]]:
        if not self._init or dt <= EPSILON:
            self._prev_head_pos = head_world_pos.copy()
            self._prev_yaw = char_yaw
            self._init = True
            return {
                "back_center": (0.0, 0.0),
                "back_left": (0.0, 0.0),
                "back_right": (0.0, 0.0),
                "temple_left": (0.0, 0.0),
                "temple_right": (0.0, 0.0),
                "bangs": (0.0, 0.0),
            }

        inv_dt = 1.0 / dt
        vel_world = (head_world_pos - self._prev_head_pos) * inv_dt
        yaw_vel = wrap_angle(char_yaw - self._prev_yaw) * inv_dt
        self._prev_head_pos = head_world_pos.copy()
        self._prev_yaw = char_yaw

        # Transform world velocity into head-local space for directional inertia
        head_inv = head_world_rot.conjugate()
        local_vel = head_inv.rotate_vec(vel_world)
        local_down = head_inv.rotate_vec(Vec3(0.0, -1.0, 0.0))

        # Gravity tilt when head nods or tilts sideways
        grav_pitch = clamp(local_down.z * 0.42, -0.35, 0.45)
        grav_roll = clamp(-local_down.x * 0.42, -0.38, 0.38)

        # Inertia trails behind velocity (+local_vel.z forward -> hair trails -pitch/backwards)
        inertia_pitch = clamp(local_vel.z * 0.14 - abs(local_vel.y) * 0.04, -0.35, 0.45)
        inertia_roll = clamp(-local_vel.x * 0.15 - yaw_vel * 0.055, -0.45, 0.45)

        breeze = math.sin(elapsed * 1.45) * 0.014
        bc = self.back_center.step(grav_pitch + inertia_pitch + 0.04 + breeze, grav_roll + inertia_roll, dt)
        bl = self.back_left.step(grav_pitch + inertia_pitch + 0.03, grav_roll + inertia_roll - 0.03 - yaw_vel * 0.02, dt)
        br = self.back_right.step(grav_pitch + inertia_pitch + 0.03, grav_roll + inertia_roll + 0.03 - yaw_vel * 0.02, dt)
        tl = self.temple_left.step(grav_pitch * 0.7 + inertia_pitch * 0.85, grav_roll * 0.8 + inertia_roll - yaw_vel * 0.025, dt)
        tr = self.temple_right.step(grav_pitch * 0.7 + inertia_pitch * 0.85, grav_roll * 0.8 + inertia_roll - yaw_vel * 0.025, dt)
        bg = self.bangs.step(clamp(local_vel.y * 0.06 + local_vel.z * 0.04, -0.15, 0.15), clamp(-local_vel.x * 0.04, -0.12, 0.12), dt)

        return {
            "back_center": bc,
            "back_left": bl,
            "back_right": br,
            "temple_left": tl,
            "temple_right": tr,
            "bangs": bg,
        }


class CharacterMotor:
    """
    Weighty Uncharted 2 / RDR2 / Heavy Rain inspired movement physics.
    Produces grounded acceleration, deceleration follow-through, turn banking,
    180-degree pivot triggers, and continuous footstep phase.
    """

    def __init__(self, start_pos: Vec3, start_yaw: float = 0.0) -> None:
        self.pos = start_pos.copy()
        self.vel = Vec3(0.0, 0.0, 0.0)
        self.yaw = start_yaw
        self.target_yaw = start_yaw
        self.angular_vel = 0.0

        self.speed = 0.0
        self.norm_speed = 0.0  # 0 = idle, ~0.44 = walk, 1.0 = run
        self.stride_phase = 0.0
        self.turn_lean = 0.0
        self.fwd_lean = 0.0
        self.pivot_timer = 0.0
        self.pivot_dir = 0.0
        self.stop_impulse_timer = 0.0
        self.was_moving = False

    def step(
        self,
        wish_dir_xz: Vec3,
        wants_run: bool,
        is_dancing: bool,
        movement_locked: bool,
        world: RoomCollisionWorld,
        dt: float,
    ) -> None:
        has_input = (not movement_locked) and (wish_dir_xz.length_sq() > 0.01)

        if has_input:
            wish = wish_dir_xz.normalized()
            desired_yaw = math.atan2(wish.x, wish.z)
            angle_delta = wrap_angle(desired_yaw - self.yaw)

            # Detect crisp 180-degree pivot initiation from walk/run
            if abs(angle_delta) > 2.15 and self.speed > 0.55 and self.pivot_timer <= 0.0 and not is_dancing:
                self.pivot_timer = 0.34
                self.pivot_dir = 1.0 if angle_delta > 0.0 else -1.0

            if is_dancing:
                # While dancing, running is disallowed; turns remain fluid & musical
                max_spd = PLAYER_DANCE_WALK_SPEED
                turn_rate = 6.8
            elif wants_run:
                max_spd = PLAYER_RUN_SPEED
                turn_rate = 8.4
            else:
                max_spd = PLAYER_WALK_SPEED
                turn_rate = 9.6

            target_vel = wish * max_spd
            # Slight momentum dip during hard 180-degree pivot
            if self.pivot_timer > 0.0:
                self.pivot_timer = max(0.0, self.pivot_timer - dt)
                target_vel = target_vel * 0.45

            accel_rate = PLAYER_ACCEL if not is_dancing else 7.2
            self.vel = self.vel.damp_to(target_vel, accel_rate, dt)

            prev_yaw = self.yaw
            self.yaw = damp_angle(self.yaw, desired_yaw, turn_rate, dt)
            self.angular_vel = wrap_angle(self.yaw - prev_yaw) / max(dt, EPSILON)
            self.was_moving = True
        else:
            if self.was_moving and self.speed > 0.75:
                self.stop_impulse_timer = 0.28
            self.was_moving = False
            self.vel = self.vel.damp_to(VEC3_ZERO, PLAYER_DECEL, dt)
            self.angular_vel = damp(self.angular_vel, 0.0, 12.0, dt)
            if self.pivot_timer > 0.0:
                self.pivot_timer = max(0.0, self.pivot_timer - dt)

        if self.stop_impulse_timer > 0.0:
            self.stop_impulse_timer = max(0.0, self.stop_impulse_timer - dt)

        # Integrate position and resolve smooth room/furniture sliding
        next_pos = self.pos + Vec3(self.vel.x * dt, 0.0, self.vel.z * dt)
        resolved_pos, hit = world.resolve_character_position(next_pos, PLAYER_CAPSULE_RADIUS)
        if hit:
            # Project velocity along resolved slide delta so wall-slides stay smooth
            actual_dx = resolved_pos.x - self.pos.x
            actual_dz = resolved_pos.z - self.pos.z
            if dt > EPSILON:
                slide_vx = actual_dx / dt
                slide_vz = actual_dz / dt
                self.vel.x = lerp(self.vel.x, slide_vx, 0.65)
                self.vel.z = lerp(self.vel.z, slide_vz, 0.65)
        self.pos = resolved_pos

        self.speed = math.sqrt(self.vel.x * self.vel.x + self.vel.z * self.vel.z)
        self.norm_speed = clamp01(self.speed / PLAYER_RUN_SPEED)

        # Advance gait stride phase proportional to ground velocity
        if self.speed > 0.06:
            stride_freq = 1.65 + (self.speed / PLAYER_RUN_SPEED) * 1.45
            self.stride_phase = (self.stride_phase + stride_freq * dt * TAU) % TAU
        else:
            # Relax stride phase smoothly toward neutral stance
            self.stride_phase = lerp(self.stride_phase, 0.0, 1.0 - math.exp(-5.0 * dt))

        # Body lean into turns & forward acceleration
        target_turn_lean = clamp(-self.angular_vel * 0.045 * clamp01(self.speed * 0.7), -0.22, 0.22)
        target_fwd_lean = clamp(self.speed / PLAYER_RUN_SPEED * 0.14, 0.0, 0.15)
        if self.stop_impulse_timer > 0.0:
            target_fwd_lean -= 0.08 * (self.stop_impulse_timer / 0.28)
        self.turn_lean = damp(self.turn_lean, target_turn_lean, 10.0, dt)
        self.fwd_lean = damp(self.fwd_lean, target_fwd_lean, 9.0, dt)


# =============================================================================
# SKELETAL RIG, POSE BLENDING, FORWARD KINEMATICS & ANALYTICAL 2-BONE IK
# =============================================================================

class BoneID:
    ROOT = 0
    PELVIS = 1
    SPINE_LOWER = 2
    SPINE_UPPER = 3
    CHEST = 4
    NECK = 5
    HEAD = 6
    EYELID_L = 7
    EYELID_R = 8
    EYE_L = 9
    EYE_R = 10
    HAIR_BACK_C = 11
    HAIR_BACK_L = 12
    HAIR_BACK_R = 13
    HAIR_TEMPLE_L = 14
    HAIR_TEMPLE_R = 15
    HAIR_BANGS = 16
    CLAVICLE_L = 17
    UPPER_ARM_L = 18
    FOREARM_L = 19
    HAND_L = 20
    CLAVICLE_R = 21
    UPPER_ARM_R = 22
    FOREARM_R = 23
    HAND_R = 24
    CIG_SOCKET_HAND = 25
    CIG_SOCKET_MOUTH = 26
    THIGH_L = 27
    SHIN_L = 28
    FOOT_L = 29
    TOE_L = 30
    THIGH_R = 31
    SHIN_R = 32
    FOOT_R = 33
    TOE_R = 34
    COUNT = 35


@dataclass(slots=True)
class BoneDef:
    index: int
    name: str
    parent: int
    bind_pos: Vec3
    bind_rot: Quat = field(default_factory=Quat.identity)


class Pose:
    """Stores local offsets and local Euler/Quaternion rotations for all 35 bones."""

    def __init__(self) -> None:
        self.local_rot: List[Quat] = [Quat.identity() for _ in range(BoneID.COUNT)]
        self.local_pos_offset: List[Vec3] = [Vec3(0.0, 0.0, 0.0) for _ in range(BoneID.COUNT)]
        self.local_scale: List[Vec3] = [Vec3(1.0, 1.0, 1.0) for _ in range(BoneID.COUNT)]

    def clear(self) -> None:
        for i in range(BoneID.COUNT):
            self.local_rot[i] = Quat.identity()
            self.local_pos_offset[i] = Vec3(0.0, 0.0, 0.0)
            self.local_scale[i] = Vec3(1.0, 1.0, 1.0)

    def copy_from(self, other: "Pose") -> None:
        for i in range(BoneID.COUNT):
            self.local_rot[i] = Quat(
                other.local_rot[i].w,
                other.local_rot[i].x,
                other.local_rot[i].y,
                other.local_rot[i].z,
            )
            self.local_pos_offset[i] = other.local_pos_offset[i].copy()
            self.local_scale[i] = other.local_scale[i].copy()

    def set_rot_euler(self, bone_id: int, pitch_x: float, yaw_y: float, roll_z: float) -> None:
        self.local_rot[bone_id] = Quat.from_euler_yxz(yaw_y, pitch_x, roll_z)

    def add_rot_euler(self, bone_id: int, pitch_x: float, yaw_y: float, roll_z: float) -> None:
        delta = Quat.from_euler_yxz(yaw_y, pitch_x, roll_z)
        self.local_rot[bone_id] = (self.local_rot[bone_id] * delta).normalized()

    def blend_with(self, target: "Pose", weight: float, bone_mask: Optional[Sequence[float]] = None) -> None:
        w_global = clamp01(weight)
        if w_global <= 0.0001:
            return
        for i in range(BoneID.COUNT):
            w = w_global if bone_mask is None else clamp01(w_global * bone_mask[i])
            if w <= 0.0001:
                continue
            self.local_rot[i] = self.local_rot[i].slerp(target.local_rot[i], w)
            self.local_pos_offset[i] = self.local_pos_offset[i].lerp(target.local_pos_offset[i], w)
            self.local_scale[i] = self.local_scale[i].lerp(target.local_scale[i], w)


def make_upper_body_mask(
    spine_w: float = 1.0,
    left_arm_w: float = 1.0,
    right_arm_w: float = 1.0,
    head_w: float = 1.0,
    legs_w: float = 0.0,
) -> List[float]:
    m = [0.0] * BoneID.COUNT
    m[BoneID.PELVIS] = spine_w * 0.35
    m[BoneID.SPINE_LOWER] = spine_w * 0.75
    m[BoneID.SPINE_UPPER] = spine_w
    m[BoneID.CHEST] = spine_w
    m[BoneID.NECK] = head_w
    m[BoneID.HEAD] = head_w
    for b in (BoneID.CLAVICLE_L, BoneID.UPPER_ARM_L, BoneID.FOREARM_L, BoneID.HAND_L):
        m[b] = left_arm_w
    for b in (BoneID.CLAVICLE_R, BoneID.UPPER_ARM_R, BoneID.FOREARM_R, BoneID.HAND_R):
        m[b] = right_arm_w
    for b in (BoneID.THIGH_L, BoneID.SHIN_L, BoneID.FOOT_L, BoneID.TOE_L,
              BoneID.THIGH_R, BoneID.SHIN_R, BoneID.FOOT_R, BoneID.TOE_R):
        m[b] = legs_w
    return m


class Skeleton:
    """
    Anatomically proportioned 1.62m young adult Japanese woman rig.
    Bind pose stands upright facing +Z, +Y up, +X character-left.
    """

    def __init__(self) -> None:
        self.bones: List[BoneDef] = self._build_bone_defs()
        self.world_transforms: List[Transform] = [Transform() for _ in range(BoneID.COUNT)]
        self.bind_world: List[Transform] = [Transform() for _ in range(BoneID.COUNT)]
        self.bind_inv_pos: List[Vec3] = [Vec3() for _ in range(BoneID.COUNT)]
        self._compute_bind_pose()

    def _build_bone_defs(self) -> List[BoneDef]:
        # Proportions tuned for slightly athletic, delicate 1.62m female anatomy
        # Ground = 0.0; Sole height = 0.022; Ankle = 0.088; Knee = 0.488; Hip = 0.905
        defs = [None] * BoneID.COUNT
        defs[BoneID.ROOT] = BoneDef(BoneID.ROOT, "root", -1, Vec3(0.0, 0.0, 0.0))
        defs[BoneID.PELVIS] = BoneDef(BoneID.PELVIS, "pelvis", BoneID.ROOT, Vec3(0.0, 0.915, 0.0))
        defs[BoneID.SPINE_LOWER] = BoneDef(BoneID.SPINE_LOWER, "spine_lower", BoneID.PELVIS, Vec3(0.0, 0.105, 0.0))
        defs[BoneID.SPINE_UPPER] = BoneDef(BoneID.SPINE_UPPER, "spine_upper", BoneID.SPINE_LOWER, Vec3(0.0, 0.125, -0.006))
        defs[BoneID.CHEST] = BoneDef(BoneID.CHEST, "chest", BoneID.SPINE_UPPER, Vec3(0.0, 0.135, 0.008))
        defs[BoneID.NECK] = BoneDef(BoneID.NECK, "neck", BoneID.CHEST, Vec3(0.0, 0.125, -0.005))
        defs[BoneID.HEAD] = BoneDef(BoneID.HEAD, "head", BoneID.NECK, Vec3(0.0, 0.085, 0.010))

        # Facial animation & eye bones
        defs[BoneID.EYELID_L] = BoneDef(BoneID.EYELID_L, "eyelid_l", BoneID.HEAD, Vec3(0.031, 0.062, 0.084))
        defs[BoneID.EYELID_R] = BoneDef(BoneID.EYELID_R, "eyelid_r", BoneID.HEAD, Vec3(-0.031, 0.062, 0.084))
        defs[BoneID.EYE_L] = BoneDef(BoneID.EYE_L, "eye_l", BoneID.HEAD, Vec3(0.031, 0.056, 0.078))
        defs[BoneID.EYE_R] = BoneDef(BoneID.EYE_R, "eye_r", BoneID.HEAD, Vec3(-0.031, 0.056, 0.078))

        # Secondary physics hair chains (shoulder-length dark-brown hair)
        defs[BoneID.HAIR_BACK_C] = BoneDef(BoneID.HAIR_BACK_C, "hair_back_c", BoneID.HEAD, Vec3(0.0, 0.082, -0.078))
        defs[BoneID.HAIR_BACK_L] = BoneDef(BoneID.HAIR_BACK_L, "hair_back_l", BoneID.HEAD, Vec3(0.062, 0.075, -0.058))
        defs[BoneID.HAIR_BACK_R] = BoneDef(BoneID.HAIR_BACK_R, "hair_back_r", BoneID.HEAD, Vec3(-0.062, 0.075, -0.058))
        defs[BoneID.HAIR_TEMPLE_L] = BoneDef(BoneID.HAIR_TEMPLE_L, "hair_temple_l", BoneID.HEAD, Vec3(0.074, 0.068, 0.018))
        defs[BoneID.HAIR_TEMPLE_R] = BoneDef(BoneID.HAIR_TEMPLE_R, "hair_temple_r", BoneID.HEAD, Vec3(-0.074, 0.068, 0.018))
        defs[BoneID.HAIR_BANGS] = BoneDef(BoneID.HAIR_BANGS, "hair_bangs", BoneID.HEAD, Vec3(0.0, 0.118, 0.062))

        # Left arm (+X)
        defs[BoneID.CLAVICLE_L] = BoneDef(BoneID.CLAVICLE_L, "clavicle_l", BoneID.CHEST, Vec3(0.035, 0.095, 0.008))
        defs[BoneID.UPPER_ARM_L] = BoneDef(BoneID.UPPER_ARM_L, "upper_arm_l", BoneID.CLAVICLE_L, Vec3(0.132, -0.008, -0.008))
        defs[BoneID.FOREARM_L] = BoneDef(BoneID.FOREARM_L, "forearm_l", BoneID.UPPER_ARM_L, Vec3(0.0, -0.265, 0.0))
        defs[BoneID.HAND_L] = BoneDef(BoneID.HAND_L, "hand_l", BoneID.FOREARM_L, Vec3(0.0, -0.235, 0.0))

        # Right arm (-X)
        defs[BoneID.CLAVICLE_R] = BoneDef(BoneID.CLAVICLE_R, "clavicle_r", BoneID.CHEST, Vec3(-0.035, 0.095, 0.008))
        defs[BoneID.UPPER_ARM_R] = BoneDef(BoneID.UPPER_ARM_R, "upper_arm_r", BoneID.CLAVICLE_R, Vec3(-0.132, -0.008, -0.008))
        defs[BoneID.FOREARM_R] = BoneDef(BoneID.FOREARM_R, "forearm_r", BoneID.UPPER_ARM_R, Vec3(0.0, -0.265, 0.0))
        defs[BoneID.HAND_R] = BoneDef(BoneID.HAND_R, "hand_r", BoneID.FOREARM_R, Vec3(0.0, -0.235, 0.0))

        # Cigarette attachment sockets (between R index/middle fingers, and corner of lips)
        defs[BoneID.CIG_SOCKET_HAND] = BoneDef(
            BoneID.CIG_SOCKET_HAND, "cig_socket_hand", BoneID.HAND_R, Vec3(0.008, -0.092, 0.026)
        )
        defs[BoneID.CIG_SOCKET_MOUTH] = BoneDef(
            BoneID.CIG_SOCKET_MOUTH, "cig_socket_mouth", BoneID.HEAD, Vec3(-0.012, 0.006, 0.098)
        )

        # Left leg (+X)
        defs[BoneID.THIGH_L] = BoneDef(BoneID.THIGH_L, "thigh_l", BoneID.PELVIS, Vec3(0.088, -0.022, 0.0))
        defs[BoneID.SHIN_L] = BoneDef(BoneID.SHIN_L, "shin_l", BoneID.THIGH_L, Vec3(0.0, -0.405, 0.0))
        defs[BoneID.FOOT_L] = BoneDef(BoneID.FOOT_L, "foot_l", BoneID.SHIN_L, Vec3(0.0, -0.402, 0.0))
        defs[BoneID.TOE_L] = BoneDef(BoneID.TOE_L, "toe_l", BoneID.FOOT_L, Vec3(0.0, -0.058, 0.115))

        # Right leg (-X)
        defs[BoneID.THIGH_R] = BoneDef(BoneID.THIGH_R, "thigh_r", BoneID.PELVIS, Vec3(-0.088, -0.022, 0.0))
        defs[BoneID.SHIN_R] = BoneDef(BoneID.SHIN_R, "shin_r", BoneID.THIGH_R, Vec3(0.0, -0.405, 0.0))
        defs[BoneID.FOOT_R] = BoneDef(BoneID.FOOT_R, "foot_r", BoneID.SHIN_R, Vec3(0.0, -0.402, 0.0))
        defs[BoneID.TOE_R] = BoneDef(BoneID.TOE_R, "toe_r", BoneID.FOOT_R, Vec3(0.0, -0.058, 0.115))

        return defs  # type: ignore

    def _compute_bind_pose(self) -> None:
        for b in self.bones:
            local = Transform(b.bind_pos.copy(), b.bind_rot, Vec3(1.0, 1.0, 1.0))
            if b.parent < 0:
                self.bind_world[b.index] = local
            else:
                self.bind_world[b.index] = self.bind_world[b.parent].combine(local)
            self.bind_inv_pos[b.index] = -self.bind_world[b.index].pos

    def evaluate_fk(self, pose: Pose, root_world_pos: Vec3, root_yaw: float) -> None:
        root_rot = Quat.from_axis_angle(VEC3_UP, root_yaw)
        for b in self.bones:
            idx = b.index
            if idx == BoneID.ROOT:
                self.world_transforms[idx] = Transform(
                    root_world_pos + pose.local_pos_offset[idx],
                    (root_rot * pose.local_rot[idx]).normalized(),
                    pose.local_scale[idx].copy(),
                )
            else:
                local = Transform(
                    b.bind_pos + pose.local_pos_offset[idx],
                    (b.bind_rot * pose.local_rot[idx]).normalized(),
                    pose.local_scale[idx].copy(),
                )
                self.world_transforms[idx] = self.world_transforms[b.parent].combine(local)

    def solve_arm_ik_world(
        self,
        pose: Pose,
        root_world_pos: Vec3,
        root_yaw: float,
        is_right: bool,
        target_world: Vec3,
        pole_dir_world: Vec3,
        blend_weight: float = 1.0,
    ) -> None:
        """
        Analytical two-bone IK in world space for reaching cigarette pack,
        lighter, or bringing hand cleanly to lips.
        """
        w = clamp01(blend_weight)
        if w <= 0.001:
            return

        self.evaluate_fk(pose, root_world_pos, root_yaw)
        upper_id = BoneID.UPPER_ARM_R if is_right else BoneID.UPPER_ARM_L
        fore_id = BoneID.FOREARM_R if is_right else BoneID.FOREARM_L
        clav_id = BoneID.CLAVICLE_R if is_right else BoneID.CLAVICLE_L

        shoulder_pos = self.world_transforms[upper_id].pos
        clav_rot = self.world_transforms[clav_id].rot
        len1 = 0.265
        len2 = 0.235

        to_target = target_world - shoulder_pos
        dist = clamp(to_target.length(), 0.06, len1 + len2 - 0.005)
        dir_t = to_target.normalized()

        # Law of cosines for shoulder & elbow angles
        cos_a = clamp((len1 * len1 + dist * dist - len2 * len2) / (2.0 * len1 * dist), -1.0, 1.0)
        angle_a = math.acos(cos_a)
        cos_b = clamp((len1 * len1 + len2 * len2 - dist * dist) / (2.0 * len1 * len2), -1.0, 1.0)
        elbow_bend = math.pi - math.acos(cos_b)

        # Build orthonormal frame toward target & pole
        side = dir_t.cross(pole_dir_world).normalized()
        if side.length_sq() < EPSILON:
            side = dir_t.cross(VEC3_UP).normalized()
        bend_normal = side.cross(dir_t).normalized()

        # Upper arm world direction points from shoulder toward elbow
        upper_dir = (dir_t * math.cos(angle_a) + bend_normal * math.sin(angle_a)).normalized()

        # Limb rest axis in bind pose is -Y (0, -1, 0)
        # Rotate (0, -1, 0) -> upper_dir
        rest_axis = Vec3(0.0, -1.0, 0.0)
        dot_u = clamp(rest_axis.dot(upper_dir), -1.0, 1.0)
        if dot_u < -0.999:
            q_world = Quat.from_axis_angle(Vec3(1.0, 0.0, 0.0), math.pi)
        else:
            cross_u = rest_axis.cross(upper_dir)
            q_world = Quat(1.0 + dot_u, cross_u.x, cross_u.y, cross_u.z).normalized()

        # Align elbow bend axis with 'side'
        cur_side = q_world.rotate_vec(Vec3(1.0, 0.0, 0.0) if not is_right else Vec3(-1.0, 0.0, 0.0))
        proj_cur = (cur_side - upper_dir * cur_side.dot(upper_dir)).normalized()
        proj_des = (side - upper_dir * side.dot(upper_dir)).normalized()
        if proj_cur.length_sq() > 0.01 and proj_des.length_sq() > 0.01:
            c_dot = clamp(proj_cur.dot(proj_des), -1.0, 1.0)
            twist_ang = math.acos(c_dot)
            if proj_cur.cross(proj_des).dot(upper_dir) < 0.0:
                twist_ang = -twist_ang
            q_world = (Quat.from_axis_angle(upper_dir, twist_ang) * q_world).normalized()

        upper_local_ik = (clav_rot.conjugate() * q_world).normalized()
        # Forearm bends forward (+Z -> pitch_x negative in our rig, check: rotating (0,-1,0) around +X by -90 deg -> (0,0,+1)!)
        fore_local_ik = Quat.from_axis_angle(Vec3(1.0, 0.0, 0.0), -elbow_bend)

        pose.local_rot[upper_id] = pose.local_rot[upper_id].slerp(upper_local_ik, w)
        pose.local_rot[fore_id] = pose.local_rot[fore_id].slerp(fore_local_ik, w)
        self.evaluate_fk(pose, root_world_pos, root_yaw)

    def apply_head_look_at(
        self,
        pose: Pose,
        root_world_pos: Vec3,
        root_yaw: float,
        look_target_world: Optional[Vec3],
        weight: float = 0.65,
    ) -> None:
        if look_target_world is None or weight <= 0.01:
            return
        self.evaluate_fk(pose, root_world_pos, root_yaw)
        head_pos = self.world_transforms[BoneID.HEAD].pos
        chest_rot = self.world_transforms[BoneID.CHEST].rot

        to_t = look_target_world - head_pos
        if to_t.length_sq() < 0.04:
            return
        local_dir = chest_rot.conjugate().rotate_vec(to_t.normalized())
        # Clamp anatomical neck/head limits so gaze never twists unnaturally
        yaw = clamp(math.atan2(local_dir.x, max(0.15, local_dir.z)), -0.78, 0.78)
        pitch = clamp(-math.asin(clamp(local_dir.y, -0.8, 0.8)), -0.45, 0.48)

        neck_delta = Quat.from_euler_yxz(yaw * 0.42 * weight, pitch * 0.35 * weight, 0.0)
        head_delta = Quat.from_euler_yxz(yaw * 0.58 * weight, pitch * 0.65 * weight, 0.0)
        pose.local_rot[BoneID.NECK] = (pose.local_rot[BoneID.NECK] * neck_delta).normalized()
        pose.local_rot[BoneID.HEAD] = (pose.local_rot[BoneID.HEAD] * head_delta).normalized()

        # Subtle black-eye iris gaze tracking inside head
        eye_yaw = clamp(yaw * 0.28, -0.18, 0.18)
        eye_pitch = clamp(pitch * 0.25, -0.14, 0.14)
        eye_q = Quat.from_euler_yxz(eye_yaw, eye_pitch, 0.0)
        pose.local_rot[BoneID.EYE_L] = (pose.local_rot[BoneID.EYE_L] * eye_q).normalized()
        pose.local_rot[BoneID.EYE_R] = (pose.local_rot[BoneID.EYE_R] * eye_q).normalized()


# =============================================================================
# LOW-POLY MESH BUILDERS, LOFTING TOOLS & DUAL-BONE SKINNING ENGINE
# =============================================================================

@dataclass(slots=True)
class StaticTri:
    i0: int
    i1: int
    i2: int
    normal: Vec3
    mat_name: str
    grad_t: float = 0.5
    layer: int = 2
    depth_bias: float = 0.0
    occlusion: float = 1.0
    cx: float = 0.0
    cy: float = 0.0
    cz: float = 0.0
    baked_rgb: Optional[Tuple[int, int, int]] = None
    baked_hdr: Tuple[float, float, float] = (0.0, 0.0, 0.0)


class StaticMesh:
    """World-space static geometry with one-time baked lighting & chunk culling."""

    def __init__(self) -> None:
        self.verts: List[Vec3] = []
        self.tris: List[StaticTri] = []
        self._chunks: List[Tuple[float, float, float, float, List[StaticTri]]] = []
        self._baked_version: int = -1

    def add_vert(self, p: Vec3) -> int:
        idx = len(self.verts)
        self.verts.append(p)
        return idx

    def add_tri(
        self,
        i0: int,
        i1: int,
        i2: int,
        mat_name: str,
        grad_t: float = 0.5,
        layer: int = 2,
        depth_bias: float = 0.0,
        occlusion: float = 1.0,
    ) -> None:
        v0 = self.verts[i0]
        v1 = self.verts[i1]
        v2 = self.verts[i2]
        n = (v1 - v0).cross(v2 - v0)
        l = n.length()
        if l < 1e-7:
            return
        n = n / l
        tri = StaticTri(
            i0, i1, i2, n, mat_name, grad_t, layer, depth_bias, occlusion,
            cx=(v0.x + v1.x + v2.x) / 3.0,
            cy=(v0.y + v1.y + v2.y) / 3.0,
            cz=(v0.z + v1.z + v2.z) / 3.0,
        )
        self.tris.append(tri)

    def add_quad(
        self,
        i0: int,
        i1: int,
        i2: int,
        i3: int,
        mat_name: str,
        grad_t0: float = 0.35,
        grad_t1: float = 0.65,
        layer: int = 2,
        depth_bias: float = 0.0,
        occlusion: float = 1.0,
    ) -> None:
        # Expects CCW order (i0 -> i1 -> i2 -> i3) viewed from outside
        self.add_tri(i0, i1, i2, mat_name, grad_t0, layer, depth_bias, occlusion)
        self.add_tri(i0, i2, i3, mat_name, grad_t1, layer, depth_bias, occlusion)

    def add_box(
        self,
        cx: float,
        cy: float,
        cz: float,
        sx: float,
        sy: float,
        sz: float,
        mat_name: str,
        layer: int = 2,
        top_mat: Optional[str] = None,
        bottom_mat: Optional[str] = None,
        occlusion: float = 1.0,
        yaw: float = 0.0,
    ) -> None:
        hx, hy, hz = sx * 0.5, sy * 0.5, sz * 0.5
        corners_local = [
            Vec3(-hx, -hy, -hz),  # 0: L B Back
            Vec3( hx, -hy, -hz),  # 1: R B Back
            Vec3( hx,  hy, -hz),  # 2: R T Back
            Vec3(-hx,  hy, -hz),  # 3: L T Back
            Vec3(-hx, -hy,  hz),  # 4: L B Front
            Vec3( hx, -hy,  hz),  # 5: R B Front
            Vec3( hx,  hy,  hz),  # 6: R T Front
            Vec3(-hx,  hy,  hz),  # 7: L T Front
        ]
        q = Quat.from_axis_angle(VEC3_UP, yaw) if abs(yaw) > 1e-5 else None
        base = len(self.verts)
        for c in corners_local:
            p = q.rotate_vec(c) if q is not None else c
            self.verts.append(Vec3(cx + p.x, cy + p.y, cz + p.z))

        t_mat = top_mat if top_mat is not None else mat_name
        b_mat = bottom_mat if bottom_mat is not None else mat_name

        # Front (+Z): 4 -> 5 -> 6 -> 7
        self.add_quad(base + 4, base + 5, base + 6, base + 7, mat_name, 0.75, 0.25, layer, 0.0, occlusion)
        # Back (-Z): 1 -> 0 -> 3 -> 2
        self.add_quad(base + 1, base + 0, base + 3, base + 2, mat_name, 0.75, 0.25, layer, 0.0, occlusion)
        # Right (+X): 5 -> 1 -> 2 -> 6
        self.add_quad(base + 5, base + 1, base + 2, base + 6, mat_name, 0.70, 0.30, layer, 0.0, occlusion)
        # Left (-X): 0 -> 4 -> 7 -> 3
        self.add_quad(base + 0, base + 4, base + 7, base + 3, mat_name, 0.70, 0.30, layer, 0.0, occlusion)
        # Top (+Y): 7 -> 6 -> 2 -> 3
        self.add_quad(base + 7, base + 6, base + 2, base + 3, t_mat, 0.20, 0.45, layer, 0.0, occlusion)
        # Bottom (-Y): 0 -> 1 -> 5 -> 4
        self.add_quad(base + 0, base + 1, base + 5, base + 4, b_mat, 0.85, 0.90, layer, 0.0, occlusion)

    def add_cylinder(
        self,
        base_center: Vec3,
        top_center: Vec3,
        r_bottom: float,
        r_top: float,
        segments: int,
        mat_name: str,
        cap_bottom: bool = True,
        cap_top: bool = True,
        layer: int = 2,
    ) -> None:
        axis = top_center - base_center
        h = axis.length()
        if h < EPSILON:
            return
        up = axis / h
        ref = Vec3(1.0, 0.0, 0.0) if abs(up.x) < 0.8 else Vec3(0.0, 0.0, 1.0)
        tangent = up.cross(ref).normalized()
        bitangent = up.cross(tangent).normalized()

        ring_b: List[int] = []
        ring_t: List[int] = []
        for i in range(segments):
            ang = (i / segments) * TAU
            ca = math.cos(ang)
            sa = math.sin(ang)
            radial = tangent * ca + bitangent * sa
            ring_b.append(self.add_vert(base_center + radial * r_bottom))
            ring_t.append(self.add_vert(top_center + radial * r_top))

        for i in range(segments):
            nxt = (i + 1) % segments
            # Viewed from outside, ring_b[nxt] -> ring_b[i] -> ring_t[i] -> ring_t[nxt]
            # Wait: check cross(tangent, bitangent): up x ref = tangent, up x tangent = bitangent
            # Wait: if ang increases from tangent toward bitangent, (radial_nxt - radial_i) ~ bitangent
            # and (top - bottom) ~ up. tangent x up = -bitangent, bitangent x up = tangent!
            # So (b[i] -> b[nxt] -> t[nxt]) has (b_nxt - b_i) x (t_nxt - b_i) ~ bitangent x up = +tangent (OUTWARD!)
            grad = 0.25 + 0.55 * (i / max(1, segments - 1))
            self.add_quad(ring_b[i], ring_b[nxt], ring_t[nxt], ring_t[i], mat_name, grad, grad, layer)

        if cap_top and r_top > 1e-4:
            tc = self.add_vert(top_center)
            for i in range(segments):
                nxt = (i + 1) % segments
                self.add_tri(tc, ring_t[i], ring_t[nxt], mat_name, 0.25, layer)
        if cap_bottom and r_bottom > 1e-4:
            bc = self.add_vert(base_center)
            for i in range(segments):
                nxt = (i + 1) % segments
                self.add_tri(bc, ring_b[nxt], ring_b[i], mat_name, 0.75, layer)

    def bake_lighting(self, materials: Dict[str, Material], lighting: LightingRig) -> None:
        """One-time view-independent bake of static light contributions.

        Stores both tonemapped RGB (fast path) and linear HDR (for transient
        light add-ons). Uses static lights only — transient flame/ember lights
        are re-added per frame for nearby triangles.
        """
        mats_sc = {}
        for tri in self.tris:
            m = materials[tri.mat_name]
            hdr = shade_point_hdr(
                tri.cx, tri.cy, tri.cz,
                tri.normal.x, tri.normal.y, tri.normal.z,
                m, tri.grad_t, tri.occlusion,
                lighting.frozen_static_lights,
            )
            tri.baked_hdr = hdr
            tri.baked_rgb = tonemap_rgb(hdr[0], hdr[1], hdr[2])
        self._baked_version = lighting.static_version

    def render(self, renderer: SceneRenderer, materials: Dict[str, Material], lighting: LightingRig) -> None:
        if self._baked_version != lighting.static_version:
            self.bake_lighting(materials, lighting)
        verts = self.verts
        transients = lighting.frozen_transient_lights
        for chunk in self._chunks:
            if renderer.sphere_outside_frustum(chunk[0], chunk[1], chunk[2], chunk[3]):
                continue
            if transients:
                for tri in chunk[4]:
                    hdr_r = tri.baked_hdr[0]
                    hdr_g = tri.baked_hdr[1]
                    hdr_b = tri.baked_hdr[2]
                    near = False
                    for tl in transients:
                        ddx = tl[0] - tri.cx
                        ddy = tl[1] - tri.cy
                        ddz = tl[2] - tri.cz
                        if ddx * ddx + ddy * ddy + ddz * ddz < tl[7]:
                            near = True
                            break
                    if near:
                        m = materials[tri.mat_name]
                        add = transient_diffuse(
                            tri.cx, tri.cy, tri.cz,
                            tri.normal.x, tri.normal.y, tri.normal.z,
                            m, tri.grad_t, tri.occlusion, transients,
                        )
                        rgb = tonemap_rgb(hdr_r + add[0], hdr_g + add[1], hdr_b + add[2])
                    else:
                        rgb = tri.baked_rgb
                    renderer.submit_triangle(
                        verts[tri.i0], verts[tri.i1], verts[tri.i2],
                        tri.normal, materials[tri.mat_name], lighting,
                        layer=tri.layer, grad_t=tri.grad_t,
                        depth_bias=tri.depth_bias, occlusion=tri.occlusion,
                        precomputed_color=rgb, min_area=2.2,
                    )
            else:
                for tri in chunk[4]:
                    renderer.submit_triangle(
                        verts[tri.i0], verts[tri.i1], verts[tri.i2],
                        tri.normal, materials[tri.mat_name], lighting,
                        layer=tri.layer, grad_t=tri.grad_t,
                        depth_bias=tri.depth_bias, occlusion=tri.occlusion,
                        precomputed_color=tri.baked_rgb, min_area=2.2,
                    )

    def build_chunks(self, cell: float = 1.7, band: float = 1.25) -> None:
        """Group triangles into coarse 3D-grid chunks (XZ cells x Y bands) with
        bounding spheres. Smaller spheres let the frustum test cull ceiling /
        wall-top chunks behind the camera, not just whole-room slabs."""
        groups: Dict[Tuple[int, int, int], List[StaticTri]] = {}
        for tri in self.tris:
            key = (
                int(tri.cx // cell),
                int(tri.cy // band),
                int(tri.cz // cell),
            )
            groups.setdefault(key, []).append(tri)
        self._chunks = []
        for tris in groups.values():
            cx = sum(t.cx for t in tris) / len(tris)
            cy = sum(t.cy for t in tris) / len(tris)
            cz = sum(t.cz for t in tris) / len(tris)
            radius = 0.0
            for t in tris:
                for vi in (t.i0, t.i1, t.i2):
                    v = self.verts[vi]
                    dx = v.x - cx
                    dy = v.y - cy
                    dz = v.z - cz
                    d = dx * dx + dy * dy + dz * dz
                    if d > radius:
                        radius = d
            self._chunks.append((cx, cy, cz, sqrt(radius) + 0.05, tris))


@dataclass(slots=True)
class SkinnedVert:
    bind_pos: Vec3
    bone0: int
    bone1: int
    weight0: float
    # Precomputed offsets relative to bone0 and bone1 bind positions
    off0: Vec3 = field(default_factory=Vec3)
    off1: Vec3 = field(default_factory=Vec3)


# Reusable normal proxy: submit_triangle only reads x/y/z within the call,
# so a single scratch instance avoids ~1900 Vec3 allocations per frame.
_SCRATCH_NORMAL = Vec3()


def _scratch_normal(nx: float, ny: float, nz: float) -> Vec3:
    _SCRATCH_NORMAL.x = nx
    _SCRATCH_NORMAL.y = ny
    _SCRATCH_NORMAL.z = nz
    return _SCRATCH_NORMAL


@dataclass(slots=True)
class SkinnedTri:
    i0: int
    i1: int
    i2: int
    mat_name: str
    grad_t: float = 0.5
    layer: int = 3
    depth_bias: float = 0.0
    flip_normal: bool = False


class SkinnedMesh:
    """Dual-bone skinned low-poly character mesh with anatomical lofting helpers."""

    def __init__(self) -> None:
        self.verts: List[SkinnedVert] = []
        self.tris: List[SkinnedTri] = []
        self.deformed_verts: List[Vec3] = []
        self._bound = False
        self._tri_mats: Optional[List[Material]] = None
        self._tri_mcs: Optional[List[Tuple[float, ...]]] = None
        # Smooth per-vertex normals for Gouraud-style smooth shading.
        # These eliminate visible polygon borders on the character body,
        # producing a seamless AAA-quality surface like Killzone / Heavy Rain.
        self._bind_smooth_normals: List[Vec3] = []
        self._deformed_normals: List[Vec3] = []

    def add_vert(self, pos: Vec3, bone0: int, bone1: int = -1, weight0: float = 1.0) -> int:
        if bone1 < 0:
            bone1 = bone0
            weight0 = 1.0
        idx = len(self.verts)
        self.verts.append(SkinnedVert(pos.copy(), bone0, bone1, clamp01(weight0)))
        self._bound = False
        return idx

    def add_tri(
        self,
        i0: int,
        i1: int,
        i2: int,
        mat_name: str,
        grad_t: float = 0.5,
        layer: int = 3,
        depth_bias: float = 0.0,
    ) -> None:
        if i0 == i1 or i1 == i2 or i0 == i2:
            return
        self.tris.append(SkinnedTri(i0, i1, i2, mat_name, grad_t, layer, depth_bias))

    def add_quad(
        self,
        i0: int,
        i1: int,
        i2: int,
        i3: int,
        mat_name: str,
        grad_t0: float = 0.35,
        grad_t1: float = 0.65,
        layer: int = 3,
        depth_bias: float = 0.0,
    ) -> None:
        self.add_tri(i0, i1, i2, mat_name, grad_t0, layer, depth_bias)
        self.add_tri(i0, i2, i3, mat_name, grad_t1, layer, depth_bias)

    def add_lofted_rings(
        self,
        rings: Sequence[Sequence[int]],
        mat_fn,
        layer: int = 3,
        closed_u: bool = True,
        reverse_winding: bool = False,
        depth_bias: float = 0.0,
    ) -> None:
        """
        Connects a sequence of vertex index rings along a limb or torso.
        mat_fn(ring_idx, seg_idx, total_segs) -> (mat_name, grad_t)
        """
        num_rings = len(rings)
        if num_rings < 2:
            return
        segs = len(rings[0])
        u_limit = segs if closed_u else segs - 1
        for r in range(num_rings - 1):
            row_a = rings[r]
            row_b = rings[r + 1]
            for s in range(u_limit):
                sn = (s + 1) % segs
                mat_name, grad_t = mat_fn(r, s, segs)
                if reverse_winding:
                    self.add_quad(row_a[s], row_b[s], row_b[sn], row_a[sn], mat_name, grad_t, grad_t, layer, depth_bias)
                else:
                    self.add_quad(row_a[s], row_a[sn], row_b[sn], row_b[s], mat_name, grad_t, grad_t, layer, depth_bias)

    def add_ellipsoid(
        self,
        center: Vec3,
        rx: float,
        ry: float,
        rz: float,
        u_segs: int,
        v_segs: int,
        bone0: int,
        bone1: int,
        weight0: float,
        mat_name: str,
        layer: int = 3,
        depth_bias: float = 0.0,
        rot: Optional[Quat] = None,
    ) -> None:
        rings: List[List[int]] = []
        top_p = Vec3(0.0, ry, 0.0)
        bot_p = Vec3(0.0, -ry, 0.0)
        if rot is not None:
            top_p = rot.rotate_vec(top_p)
            bot_p = rot.rotate_vec(bot_p)
        top_idx = self.add_vert(center + top_p, bone0, bone1, weight0)
        bot_idx = self.add_vert(center + bot_p, bone0, bone1, weight0)

        for v in range(1, v_segs):
            phi = (v / v_segs) * math.pi  # 0 (top) to pi (bottom)
            sp = math.sin(phi)
            cp = math.cos(phi)
            ring: List[int] = []
            for u in range(u_segs):
                theta = (u / u_segs) * TAU
                lp = Vec3(rx * sp * math.cos(theta), ry * cp, rz * sp * math.sin(theta))
                if rot is not None:
                    lp = rot.rotate_vec(lp)
                ring.append(self.add_vert(center + lp, bone0, bone1, weight0))
            rings.append(ring)

        # Top cap
        first_ring = rings[0]
        for u in range(u_segs):
            un = (u + 1) % u_segs
            # Note: theta=0 is +X, theta=pi/2 is +Z; increasing theta moves +X -> +Z (clockwise from +Y!)
            # So outward winding from top_idx: top_idx -> first_ring[un] -> first_ring[u]
            self.add_tri(top_idx, first_ring[un], first_ring[u], mat_name, 0.25, layer, depth_bias)

        # Middle bands
        for r in range(len(rings) - 1):
            ra = rings[r]
            rb = rings[r + 1]
            gt = (r + 0.5) / max(1, len(rings) - 1)
            for u in range(u_segs):
                un = (u + 1) % u_segs
                self.add_quad(ra[u], ra[un], rb[un], rb[u], mat_name, gt, gt, layer, depth_bias)

        # Bottom cap
        last_ring = rings[-1]
        for u in range(u_segs):
            un = (u + 1) % u_segs
            self.add_tri(bot_idx, last_ring[u], last_ring[un], mat_name, 0.80, layer, depth_bias)

    def bind_to_skeleton(self, skeleton: Skeleton) -> None:
        for v in self.verts:
            b0_pos = skeleton.bind_world[v.bone0].pos
            b1_pos = skeleton.bind_world[v.bone1].pos
            v.off0 = v.bind_pos - b0_pos
            v.off1 = v.bind_pos - b1_pos
        self.deformed_verts = [Vec3() for _ in range(len(self.verts))]
        # ------------------------------------------------------------------
        # Compute smooth per-vertex normals by averaging adjacent face normals.
        # This is the key to eliminating visible polygon borders: adjacent
        # triangles share vertex normals, so their shading is correlated and
        # facet edges become invisible. The result reads as a smooth, seamless
        # surface like a proper AAA game character model.
        # ------------------------------------------------------------------
        vn_acc_x = [0.0] * len(self.verts)
        vn_acc_y = [0.0] * len(self.verts)
        vn_acc_z = [0.0] * len(self.verts)
        for tri in self.tris:
            v0 = self.verts[tri.i0].bind_pos
            v1 = self.verts[tri.i1].bind_pos
            v2 = self.verts[tri.i2].bind_pos
            e1x = v1.x - v0.x
            e1y = v1.y - v0.y
            e1z = v1.z - v0.z
            e2x = v2.x - v0.x
            e2y = v2.y - v0.y
            e2z = v2.z - v0.z
            nx = e1y * e2z - e1z * e2y
            ny = e1z * e2x - e1x * e2z
            nz = e1x * e2y - e1y * e2x
            i0 = tri.i0
            i1 = tri.i1
            i2 = tri.i2
            vn_acc_x[i0] += nx; vn_acc_y[i0] += ny; vn_acc_z[i0] += nz
            vn_acc_x[i1] += nx; vn_acc_y[i1] += ny; vn_acc_z[i1] += nz
            vn_acc_x[i2] += nx; vn_acc_y[i2] += ny; vn_acc_z[i2] += nz
        self._bind_smooth_normals = []
        for i in range(len(self.verts)):
            fx = vn_acc_x[i]
            fy = vn_acc_y[i]
            fz = vn_acc_z[i]
            l = math.sqrt(fx * fx + fy * fy + fz * fz)
            if l > 1e-10:
                inv = 1.0 / l
                self._bind_smooth_normals.append(Vec3(fx * inv, fy * inv, fz * inv))
            else:
                self._bind_smooth_normals.append(Vec3(0.0, 1.0, 0.0))
        self._deformed_normals = [Vec3() for _ in range(len(self.verts))]
        self._bound = True

    def deform(self, skeleton: Skeleton) -> None:
        if not self._bound:
            self.bind_to_skeleton(skeleton)
        wt = skeleton.world_transforms
        out = self.deformed_verts
        bn = self._bind_smooth_normals
        dn = self._deformed_normals
        for idx, v in enumerate(self.verts):
            t0 = wt[v.bone0]
            q = t0.rot
            # Inline quaternion rotate + translate (avoids apply_point allocs)
            qw = q.w
            qx = q.x
            qy = q.y
            qz = q.z
            o = v.off0
            ox = o.x
            oy = o.y
            oz = o.z
            dot_uv = qx * ox + qy * oy + qz * oz
            dot_uu = qx * qx + qy * qy + qz * qz
            cxr = qy * oz - qz * oy
            cyr = qz * ox - qx * oz
            czr = qx * oy - qy * ox
            t1 = 2.0 * dot_uv
            t2 = qw * qw - dot_uu
            t3 = 2.0 * qw
            p = t0.pos
            px0 = p.x + t1 * qx + t2 * ox + t3 * cxr
            py0 = p.y + t1 * qy + t2 * oy + t3 * cyr
            pz0 = p.z + t1 * qz + t2 * oz + t3 * czr
            # Deform smooth normal (rotation only — normals are directions)
            bn_v = bn[idx]
            bnx = bn_v.x
            bny = bn_v.y
            bnz = bn_v.z
            dot_un = qx * bnx + qy * bny + qz * bnz
            cxn = qy * bnz - qz * bny
            cyn = qz * bnx - qx * bnz
            czn = qx * bny - qy * bnx
            t1n = 2.0 * dot_un
            t2n = qw * qw - dot_uu
            t3n = 2.0 * qw
            nx0 = t1n * qx + t2n * bnx + t3n * cxn
            ny0 = t1n * qy + t2n * bny + t3n * cyn
            nz0 = t1n * qz + t2n * bnz + t3n * czn
            if v.weight0 >= 0.999 or v.bone0 == v.bone1:
                out[idx] = Vec3(px0, py0, pz0)
                # Normalize deformed normal
                l = math.sqrt(nx0 * nx0 + ny0 * ny0 + nz0 * nz0)
                if l > 1e-10:
                    inv = 1.0 / l
                    dn[idx] = Vec3(nx0 * inv, ny0 * inv, nz0 * inv)
                else:
                    dn[idx] = Vec3(0.0, 1.0, 0.0)
            else:
                t1b = wt[v.bone1]
                q = t1b.rot
                qw = q.w
                qx = q.x
                qy = q.y
                qz = q.z
                o = v.off1
                ox = o.x
                oy = o.y
                oz = o.z
                dot_uv = qx * ox + qy * oy + qz * oz
                dot_uu = qx * qx + qy * qy + qz * qz
                cxr = qy * oz - qz * oy
                cyr = qz * ox - qx * oz
                czr = qx * oy - qy * ox
                t1 = 2.0 * dot_uv
                t2 = qw * qw - dot_uu
                t3 = 2.0 * qw
                p = t1b.pos
                w0 = v.weight0
                w1 = 1.0 - w0
                out[idx] = Vec3(
                    px0 * w0 + (p.x + t1 * qx + t2 * ox + t3 * cxr) * w1,
                    py0 * w0 + (p.y + t1 * qy + t2 * oy + t3 * cyr) * w1,
                    pz0 * w0 + (p.z + t1 * qz + t2 * oz + t3 * czr) * w1,
                )
                # Blend deformed normals by skinning weights
                dot_un = qx * bnx + qy * bny + qz * bnz
                cxn = qy * bnz - qz * bny
                cyn = qz * bnx - qx * bnz
                czn = qx * bny - qy * bnx
                t1n = 2.0 * dot_un
                t2n = qw * qw - dot_uu
                t3n = 2.0 * qw
                nx1 = t1n * qx + t2n * bnx + t3n * cxn
                ny1 = t1n * qy + t2n * bny + t3n * cyn
                nz1 = t1n * qz + t2n * bnz + t3n * czn
                fx = nx0 * w0 + nx1 * w1
                fy = ny0 * w0 + ny1 * w1
                fz = nz0 * w0 + nz1 * w1
                l = math.sqrt(fx * fx + fy * fy + fz * fz)
                if l > 1e-10:
                    inv = 1.0 / l
                    dn[idx] = Vec3(fx * inv, fy * inv, fz * inv)
                else:
                    dn[idx] = Vec3(0.0, 1.0, 0.0)

    def render(self, renderer: SceneRenderer, materials: Dict[str, Material], lighting: LightingRig) -> None:
        verts = self.deformed_verts
        sn = self._deformed_normals
        if self._tri_mats is None:
            self._tri_mats = [materials[t.mat_name] for t in self.tris]
            self._tri_mcs = [_mat_mc(m) for m in self._tri_mats]
        tri_mats = self._tri_mats
        tri_mcs = self._tri_mcs
        for i, tri in enumerate(self.tris):
            i0 = tri.i0
            i1 = tri.i1
            i2 = tri.i2
            v0 = verts[i0]
            v1 = verts[i1]
            v2 = verts[i2]
            # ----------------------------------------------------------------
            # Smooth shading: use the AVERAGE of the 3 deformed smooth vertex
            # normals as the face's shading normal. Because adjacent triangles
            # share vertex normals, their averaged normals are correlated,
            # producing smooth color transitions with NO visible facet edges.
            # This is what makes the character read as a seamless AAA-quality
            # surface (Killzone / Heavy Rain / Uncharted 2 visual standard)
            # despite the low polygon count.
            # ----------------------------------------------------------------
            n0 = sn[i0]
            n1 = sn[i1]
            n2 = sn[i2]
            nx = (n0.x + n1.x + n2.x) * 0.3333333
            ny = (n0.y + n1.y + n2.y) * 0.3333333
            nz = (n0.z + n1.z + n2.z) * 0.3333333
            l = nx * nx + ny * ny + nz * nz
            if l < 1e-14:
                # Fallback to geometric face normal if smooth normals degenerate
                e1x = v1.x - v0.x
                e1y = v1.y - v0.y
                e1z = v1.z - v0.z
                e2x = v2.x - v0.x
                e2y = v2.y - v0.y
                e2z = v2.z - v0.z
                nx = e1y * e2z - e1z * e2y
                ny = e1z * e2x - e1x * e2z
                nz = e1x * e2y - e1y * e2x
                l = nx * nx + ny * ny + nz * nz
                if l < 1e-14:
                    continue
            inv_l = 1.0 / sqrt(l)
            renderer.submit_triangle(
                v0, v1, v2, _scratch_normal(nx * inv_l, ny * inv_l, nz * inv_l),
                tri_mats[i], lighting,
                layer=tri.layer,
                grad_t=tri.grad_t,
                depth_bias=tri.depth_bias,
                mc=tri_mcs[i],
                lights=lighting.frozen_char_lights,
            )


# =============================================================================
# PROTAGONIST ANATOMY PART 1: HEAD, DELICATE FACIAL FEATURES & SHOULDER HAIR
# =============================================================================

class ProtagonistHeadBuilder:
    """
    Sculpts the protagonist's head, delicate Final Fantasy XII/XIII/XIV-inspired
    facial anatomy, Fatal Frame girl-next-door aura, black eyes with specular
    catchlights, blinking eyelids, and layered shoulder-length dark-brown hair.
    """

    @staticmethod
    def build_head_and_hair(mesh: SkinnedMesh, skel: Skeleton) -> None:
        head_base = skel.bind_world[BoneID.HEAD].pos
        neck_base = skel.bind_world[BoneID.NECK].pos
        chest_base = skel.bind_world[BoneID.CHEST].pos

        # ---------------------------------------------------------------------
        # 1. NECK (Slender anatomical taper from trapezius/clavicle to jaw)
        # ---------------------------------------------------------------------
        neck_rings_spec = [
            # (y_rel_neck, rx, rz, z_off, b0, b1, w0)
            (-0.060, 0.064, 0.060, -0.006, BoneID.CHEST, BoneID.NECK, 0.55),  # tucked deep into torso
            (-0.020, 0.057, 0.053, -0.004, BoneID.CHEST, BoneID.NECK, 0.65),
            (0.018, 0.047, 0.045, 0.000, BoneID.NECK, BoneID.CHEST, 0.78),
            (0.056, 0.043, 0.043, 0.004, BoneID.NECK, BoneID.HEAD, 0.68),
            (0.090, 0.045, 0.047, 0.008, BoneID.HEAD, BoneID.NECK, 0.72),
        ]
        neck_segs = 12
        neck_rings: List[List[int]] = []
        for y_off, rx, rz, z_off, b0, b1, w0 in neck_rings_spec:
            ring: List[int] = []
            for s in range(neck_segs):
                ang = (s / neck_segs) * TAU
                vx = neck_base.x + math.cos(ang) * rx
                vy = neck_base.y + y_off
                vz = neck_base.z + z_off + math.sin(ang) * rz
                ring.append(mesh.add_vert(Vec3(vx, vy, vz), b0, b1, w0))
            neck_rings.append(ring)

        # NOTE: rings ascend (+Y). The loft's default winding faces INWARD for
        # ascending polar rings, so reverse_winding=True makes normals point out.
        mesh.add_lofted_rings(
            neck_rings,
            lambda r, s, n: ("skin", 0.35 + 0.15 * r),
            layer=3,
            reverse_winding=True,
        )

        # ---------------------------------------------------------------------
        # 2. CRANIUM & DELICATE FACIAL CONTOUR (Lofted sculpted cross-sections)
        # ---------------------------------------------------------------------
        # Head origin at ~ (0, 1.490, 0.007); crown ~ 1.652, chin ~ 1.448
        hc = head_base
        # Cross-section angles: 0 (+X left cheek), pi/2 (+Z face front), pi (-X right), 3pi/2 (-Z back)
        face_segs = 16
        head_profile = [
            # (y_rel, rx, rz_front, rz_back, z_center, chin_pinch, cheek_pinch)
            # Softened jawline: reduced chin/cheek pinch for smooth rounded oval
            # (matching reference: soft oval, gently rounded cheeks, tapered chin)
            (-0.042, 0.020, 0.038, 0.012, 0.048, 0.42, 0.14),   # Chin tip (softer)
            (-0.022, 0.044, 0.070, 0.034, 0.024, 0.26, 0.10),   # Lower jaw (rounder)
            (0.004,  0.058, 0.082, 0.060, 0.012, 0.14, 0.06),   # Lips / lower cheek
            (0.032,  0.068, 0.088, 0.080, 0.006, 0.06, 0.00),   # Cheekbones / nose base
            (0.060,  0.071, 0.084, 0.090, 0.002, 0.03, 0.00),   # Orbital / eye level (slightly wider)
            (0.088,  0.072, 0.084, 0.094, -0.002, 0.02, 0.00),  # Forehead / brow
            (0.118,  0.066, 0.076, 0.088, -0.006, 0.00, 0.00),  # Upper forehead
            (0.145,  0.050, 0.058, 0.068, -0.008, 0.00, 0.00),  # Crown taper
        ]

        head_rings: List[List[int]] = []
        for r_idx, (dy, rx, rzf, rzb, zc, c_pinch, k_pinch) in enumerate(head_profile):
            ring: List[int] = []
            for s in range(face_segs):
                ang = (s / face_segs) * TAU
                ca = math.cos(ang)
                sa = math.sin(ang)
                rz = rzf if sa >= 0.0 else rzb
                # Taper front chin / jaw into graceful V-line
                if sa > 0.25 and c_pinch > 0.0:
                    rx_eff = rx * (1.0 - c_pinch * 0.22 * sa)
                    rz_eff = rz * (1.0 + c_pinch * 0.06 * sa)
                else:
                    rx_eff = rx
                    rz_eff = rz
                # Slight orbital indentation around eyes (r_idx == 4, front corners)
                eye_recess = 0.0
                if r_idx == 4 and sa > 0.65 and 0.20 < abs(ca) < 0.72:
                    eye_recess = -0.0055
                vx = hc.x + ca * rx_eff
                vy = hc.y + dy
                vz = hc.z + zc + sa * rz_eff + eye_recess
                ring.append(mesh.add_vert(Vec3(vx, vy, vz), BoneID.HEAD))
            head_rings.append(ring)

        # Chin bottom closure & crown cap (windings matched to outward normals)
        chin_tip = mesh.add_vert(Vec3(hc.x, hc.y - 0.048, hc.z + 0.068), BoneID.HEAD)
        crown_tip = mesh.add_vert(Vec3(hc.x, hc.y + 0.162, hc.z - 0.010), BoneID.HEAD)

        for s in range(face_segs):
            sn = (s + 1) % face_segs
            # Under-chin cap faces down/forward: reversed fan order
            mesh.add_tri(chin_tip, head_rings[0][sn], head_rings[0][s], "skin", 0.55, layer=3)
            # Crown cap faces up: standard fan order after reversed check
            mesh.add_tri(crown_tip, head_rings[-1][sn], head_rings[-1][s], "hair_dark_brown", 0.25, layer=3)

        def head_mat_fn(r: int, s: int, total: int) -> Tuple[str, float]:
            # Back & crown of cranium use dark-brown hair scalp base; the front
            # hairline sits at r6 (~y+0.118) so the forehead stays visible
            ang = (s / total) * TAU
            sa = math.sin(ang)
            if r >= 6 or sa < -0.15:
                return ("hair_dark_brown", 0.30 + 0.08 * r)
            if r == 3 and 0.35 < abs(math.cos(ang)) < 0.85 and sa > 0.4:
                return ("skin_blush", 0.35)
            return ("skin", 0.25 + 0.07 * (5 - r))

        mesh.add_lofted_rings(head_rings, head_mat_fn, layer=3, reverse_winding=True)

        # ---------------------------------------------------------------------
        # 3. DELICATE NOSE BRIDGE & TIP
        # ---------------------------------------------------------------------
        n_top = mesh.add_vert(Vec3(hc.x, hc.y + 0.066, hc.z + 0.084), BoneID.HEAD)
        n_mid = mesh.add_vert(Vec3(hc.x, hc.y + 0.044, hc.z + 0.092), BoneID.HEAD)
        n_tip = mesh.add_vert(Vec3(hc.x, hc.y + 0.030, hc.z + 0.101), BoneID.HEAD)
        n_base = mesh.add_vert(Vec3(hc.x, hc.y + 0.023, hc.z + 0.090), BoneID.HEAD)
        n_l = mesh.add_vert(Vec3(hc.x + 0.010, hc.y + 0.030, hc.z + 0.086), BoneID.HEAD)
        n_r = mesh.add_vert(Vec3(hc.x - 0.010, hc.y + 0.030, hc.z + 0.086), BoneID.HEAD)

        mesh.add_tri(n_top, n_l, n_mid, "skin", 0.25, layer=3, depth_bias=-0.010)
        mesh.add_tri(n_top, n_mid, n_r, "skin", 0.25, layer=3, depth_bias=-0.010)
        mesh.add_tri(n_mid, n_l, n_tip, "skin", 0.20, layer=3, depth_bias=-0.010)
        mesh.add_tri(n_mid, n_tip, n_r, "skin", 0.20, layer=3, depth_bias=-0.010)
        mesh.add_tri(n_tip, n_l, n_base, "skin", 0.72, layer=3, depth_bias=-0.010)
        mesh.add_tri(n_tip, n_base, n_r, "skin", 0.72, layer=3, depth_bias=-0.010)

        # ---------------------------------------------------------------------
        # 4. SCULPTED LIPS (Youthful delicate bow with fuller lower lip)
        # ---------------------------------------------------------------------
        # Matching reference: full-ish lower lip with defined cupid's bow,
        # natural rosy-pink tone, closed in a faint neutral expression.
        lp_l = mesh.add_vert(Vec3(hc.x + 0.018, hc.y + 0.008, hc.z + 0.087), BoneID.HEAD)
        lp_r = mesh.add_vert(Vec3(hc.x - 0.018, hc.y + 0.008, hc.z + 0.087), BoneID.HEAD)
        lp_up_c = mesh.add_vert(Vec3(hc.x, hc.y + 0.014, hc.z + 0.093), BoneID.HEAD)   # Cupid's bow peak
        lp_mid_c = mesh.add_vert(Vec3(hc.x, hc.y + 0.008, hc.z + 0.094), BoneID.HEAD)
        # Fuller lower lip: wider, pushed forward, slightly lower for volume
        lp_lo_l = mesh.add_vert(Vec3(hc.x + 0.009, hc.y - 0.002, hc.z + 0.094), BoneID.HEAD)
        lp_lo_r = mesh.add_vert(Vec3(hc.x - 0.009, hc.y - 0.002, hc.z + 0.094), BoneID.HEAD)
        lp_lo_c = mesh.add_vert(Vec3(hc.x, hc.y - 0.003, hc.z + 0.095), BoneID.HEAD)   # Fuller lower lip tip

        mesh.add_tri(lp_l, lp_mid_c, lp_up_c, "lips", 0.25, layer=3, depth_bias=-0.016)
        mesh.add_tri(lp_mid_c, lp_r, lp_up_c, "lips", 0.25, layer=3, depth_bias=-0.016)
        mesh.add_tri(lp_l, lp_lo_l, lp_mid_c, "lips", 0.60, layer=3, depth_bias=-0.016)
        mesh.add_tri(lp_mid_c, lp_lo_l, lp_lo_c, "lips", 0.68, layer=3, depth_bias=-0.016)
        mesh.add_tri(lp_mid_c, lp_lo_c, lp_lo_r, "lips", 0.68, layer=3, depth_bias=-0.016)
        mesh.add_tri(lp_mid_c, lp_lo_r, lp_r, "lips", 0.60, layer=3, depth_bias=-0.016)
        # Lower lip underside (subtle shadow fold for fullness)
        mesh.add_tri(lp_lo_l, lp_lo_c, lp_lo_r, "lips", 0.82, layer=3, depth_bias=-0.018)

        # ---------------------------------------------------------------------
        # 5. EXPRESSIVE DARK BROWN EYES, SCLERA, CATCHLIGHTS, EYELASHES, EYELIDS & BROWS
        # ---------------------------------------------------------------------
        # Matching reference: large almond-shaped eyes with gentle slightly droopy
        # outer corners, softly defined double eyelids, calm serene gaze.
        for side_sign, eye_bone, lid_bone in (
            (1.0, BoneID.EYE_L, BoneID.EYELID_L),
            (-1.0, BoneID.EYE_R, BoneID.EYELID_R),
        ):
            ex = hc.x + side_sign * 0.029
            ey = hc.y + 0.056
            ez = hc.z + 0.079

            # Sclera almond patch — enlarged with droopy outer corner
            # (outer corner sits ~2mm lower than inner for the gentle droop)
            s_in = mesh.add_vert(Vec3(ex - side_sign * 0.018, ey + 0.000, ez + 0.003), BoneID.HEAD)
            s_out = mesh.add_vert(Vec3(ex + side_sign * 0.018, ey - 0.0025, ez - 0.002), BoneID.HEAD)  # droopy outer
            s_top = mesh.add_vert(Vec3(ex, ey + 0.0105, ez + 0.005), BoneID.HEAD)   # taller upper lid
            s_bot = mesh.add_vert(Vec3(ex, ey - 0.0085, ez + 0.005), BoneID.HEAD)   # slightly fuller lower lid
            if side_sign > 0:
                mesh.add_tri(s_in, s_bot, s_top, "sclera", 0.35, layer=3, depth_bias=-0.018)
                mesh.add_tri(s_top, s_bot, s_out, "sclera", 0.45, layer=3, depth_bias=-0.018)
            else:
                mesh.add_tri(s_in, s_top, s_bot, "sclera", 0.35, layer=3, depth_bias=-0.018)
                mesh.add_tri(s_top, s_out, s_bot, "sclera", 0.45, layer=3, depth_bias=-0.018)

            # Dark brown iris octagon (attached to EYE bone for gaze tracking)
            # Reference: dark brown irises (not pure black) — richer, warmer tone
            iris_c = mesh.add_vert(Vec3(ex, ey - 0.0005, ez + 0.0075), eye_bone)
            iris_ring: List[int] = []
            iris_segs = 8
            for k in range(iris_segs):
                a = (k / iris_segs) * TAU
                iris_ring.append(
                    mesh.add_vert(
                        Vec3(ex + math.cos(a) * 0.0088, ey - 0.0005 + math.sin(a) * 0.0082, ez + 0.0068),
                        eye_bone,
                    )
                )
            for k in range(iris_segs):
                kn = (k + 1) % iris_segs
                mesh.add_tri(iris_c, iris_ring[k], iris_ring[kn], "iris_dark_brown", 0.35, layer=3, depth_bias=-0.024)

            # Anime/FF13 luminous catchlight diamond in upper-left of iris
            cl_c = Vec3(ex + 0.0026, ey + 0.0028, ez + 0.0085)
            cl0 = mesh.add_vert(cl_c + Vec3(-0.0018, 0.0, 0.0), eye_bone)
            cl1 = mesh.add_vert(cl_c + Vec3(0.0, -0.0018, 0.0), eye_bone)
            cl2 = mesh.add_vert(cl_c + Vec3(0.0018, 0.0, 0.0), eye_bone)
            cl3 = mesh.add_vert(cl_c + Vec3(0.0, 0.0018, 0.0), eye_bone)
            mesh.add_quad(cl0, cl1, cl2, cl3, "eye_catchlight", 0.2, 0.2, layer=3, depth_bias=-0.030)

            # Upper eyelash arch
            lash_in = mesh.add_vert(Vec3(ex - side_sign * 0.014, ey + 0.001, ez + 0.005), BoneID.HEAD)
            lash_mid = mesh.add_vert(Vec3(ex, ey + 0.009, ez + 0.007), BoneID.HEAD)
            lash_out = mesh.add_vert(Vec3(ex + side_sign * 0.016, ey + 0.003, ez + 0.000), BoneID.HEAD)
            lash_top = mesh.add_vert(Vec3(ex, ey + 0.0115, ez + 0.0072), BoneID.HEAD)
            if side_sign > 0:
                mesh.add_tri(lash_in, lash_mid, lash_top, "lash_brow", 0.3, layer=3, depth_bias=-0.028)
                mesh.add_tri(lash_mid, lash_out, lash_top, "lash_brow", 0.3, layer=3, depth_bias=-0.028)
            else:
                mesh.add_tri(lash_in, lash_top, lash_mid, "lash_brow", 0.3, layer=3, depth_bias=-0.028)
                mesh.add_tri(lash_mid, lash_top, lash_out, "lash_brow", 0.3, layer=3, depth_bias=-0.028)

            # Delicate eyebrow
            br_in = mesh.add_vert(Vec3(ex - side_sign * 0.015, ey + 0.018, ez + 0.007), BoneID.HEAD)
            br_mid = mesh.add_vert(Vec3(ex + side_sign * 0.002, ey + 0.022, ez + 0.006), BoneID.HEAD)
            br_out = mesh.add_vert(Vec3(ex + side_sign * 0.017, ey + 0.017, ez + 0.000), BoneID.HEAD)
            br_top = mesh.add_vert(Vec3(ex + side_sign * 0.002, ey + 0.025, ez + 0.006), BoneID.HEAD)
            if side_sign > 0:
                mesh.add_tri(br_in, br_mid, br_top, "lash_brow", 0.4, layer=3, depth_bias=-0.025)
                mesh.add_tri(br_mid, br_out, br_top, "lash_brow", 0.4, layer=3, depth_bias=-0.025)
            else:
                mesh.add_tri(br_in, br_top, br_mid, "lash_brow", 0.4, layer=3, depth_bias=-0.025)
                mesh.add_tri(br_mid, br_top, br_out, "lash_brow", 0.4, layer=3, depth_bias=-0.025)

            # Blinking upper eyelid flap (rotates downward around X during blink)
            lid_p = skel.bind_world[lid_bone].pos
            l0 = mesh.add_vert(Vec3(lid_p.x - side_sign * 0.015, lid_p.y + 0.002, lid_p.z + 0.003), lid_bone)
            l1 = mesh.add_vert(Vec3(lid_p.x + side_sign * 0.015, lid_p.y + 0.002, lid_p.z - 0.001), lid_bone)
            l2 = mesh.add_vert(Vec3(lid_p.x + side_sign * 0.014, lid_p.y - 0.001, lid_p.z + 0.004), lid_bone)
            l3 = mesh.add_vert(Vec3(lid_p.x - side_sign * 0.014, lid_p.y - 0.001, lid_p.z + 0.006), lid_bone)
            if side_sign > 0:
                mesh.add_quad(l0, l3, l2, l1, "skin", 0.45, 0.55, layer=3, depth_bias=-0.027)
            else:
                mesh.add_quad(l0, l1, l2, l3, "skin", 0.45, 0.55, layer=3, depth_bias=-0.027)

        # ---------------------------------------------------------------------
        # 6. DELICATE EARS
        # ---------------------------------------------------------------------
        for side_sign in (1.0, -1.0):
            mesh.add_ellipsoid(
                Vec3(hc.x + side_sign * 0.068, hc.y + 0.042, hc.z - 0.006),
                0.009, 0.024, 0.014, 6, 4,
                BoneID.HEAD, BoneID.HEAD, 1.0, "skin", layer=3,
            )

        # ---------------------------------------------------------------------
        # 7. LONG STRAIGHT DARK-BROWN HAIR (reference look: side-swept bangs,
        #    face-framing side falls over the chest, long back curtains)
        # ---------------------------------------------------------------------
        # Side-swept fringe (attached to HAIR_BANGS, parted on her right side)
        ProtagonistHeadBuilder._build_hair_bangs(mesh, hc)

        # Face-framing side falls: temple -> over shoulder -> down past chest
        # (matching reference: long straight dark brown hair falling past shoulders)
        # Extended longer to reach mid-torso (~Y 0.85) for the signature long-hair look.
        for side_sign, t_bone in ((1.0, BoneID.HAIR_TEMPLE_L), (-1.0, BoneID.HAIR_TEMPLE_R)):
            ProtagonistHeadBuilder._build_hair_ribbon_strand(
                mesh,
                points=[
                    Vec3(hc.x + side_sign * 0.066, hc.y + 0.112, hc.z + 0.028),
                    Vec3(hc.x + side_sign * 0.078, hc.y + 0.050, hc.z + 0.040),
                    Vec3(hc.x + side_sign * 0.086, hc.y - 0.035, hc.z + 0.050),
                    Vec3(hc.x + side_sign * 0.100, hc.y - 0.115, hc.z + 0.072),
                    Vec3(hc.x + side_sign * 0.104, hc.y - 0.200, hc.z + 0.086),
                    Vec3(hc.x + side_sign * 0.102, hc.y - 0.290, hc.z + 0.096),
                    Vec3(hc.x + side_sign * 0.094, hc.y - 0.380, hc.z + 0.082),
                    Vec3(hc.x + side_sign * 0.084, hc.y - 0.470, hc.z + 0.060),
                    Vec3(hc.x + side_sign * 0.072, hc.y - 0.550, hc.z + 0.040),
                    Vec3(hc.x + side_sign * 0.060, hc.y - 0.620, hc.z + 0.022),
                ],
                widths=[0.040, 0.048, 0.052, 0.052, 0.050, 0.046, 0.040, 0.034, 0.026, 0.018],
                thickness=0.011,
                bone_top=BoneID.HEAD,
                bone_tip=t_bone,
                side_sign=side_sign,
                wide_axis="x",
            )

        # Long back curtains: crown -> shoulder blades -> mid back (~Y 0.96)
        ProtagonistHeadBuilder._build_back_curtain(
            mesh,
            hc,
            ang_start=math.pi * 1.22,
            ang_end=math.pi * 1.78,
            bone_tip=BoneID.HAIR_BACK_C,
        )
        ProtagonistHeadBuilder._build_back_curtain(
            mesh,
            hc,
            ang_start=math.pi * 1.74,
            ang_end=math.pi * 2.08,
            bone_tip=BoneID.HAIR_BACK_L,
        )
        ProtagonistHeadBuilder._build_back_curtain(
            mesh,
            hc,
            ang_start=math.pi * 0.92,
            ang_end=math.pi * 1.26,
            bone_tip=BoneID.HAIR_BACK_R,
        )

    @staticmethod
    def _build_hair_bangs(mesh: SkinnedMesh, hc: Vec3) -> None:
        """Straight-across bangs (齐刘海) matching the reference image:
        A clean straight fringe cut evenly across the forehead at eyebrow level,
        with subtle natural variation in strand tips for realism without looking
        ragged. The reference shows classic straight Japanese bangs — not
        side-swept, not feathered — just a neat horizontal fringe."""
        # 10 strands forming a continuous straight fringe across the forehead.
        # All tips terminate at approximately the same Y level (eyebrow height)
        # for the signature straight-across look. Tiny Z variation per strand
        # adds natural texture without breaking the straight silhouette.
        bang_specs = [
            # (root_x0, root_x1, root_z, tip_z)
            (-0.084, -0.068, 0.044, 0.070),  # Left temple edge
            (-0.066, -0.050, 0.048, 0.074),  # Left outer
            (-0.048, -0.032, 0.052, 0.078),  # Left
            (-0.030, -0.014, 0.055, 0.080),  # Center-left
            (-0.012,  0.004, 0.057, 0.082),  # Center
            ( 0.006,  0.022, 0.057, 0.082),  # Center
            ( 0.024,  0.040, 0.055, 0.080),  # Center-right
            ( 0.042,  0.058, 0.052, 0.078),  # Right
            ( 0.060,  0.076, 0.048, 0.074),  # Right outer
            ( 0.078,  0.084, 0.044, 0.070),  # Right temple edge
        ]
        # All strands share the same tip Y for the straight-across cut.
        # Slight 0.002 variation prevents a mechanical ruler-edge look.
        straight_tip_y = hc.y + 0.082
        for idx, (x0, x1, zr, zt) in enumerate(bang_specs):
            tiny_var = 0.002 * ((idx % 3) - 1)  # -0.002, 0, +0.002
            tip_y = straight_tip_y + tiny_var
            # Root row at the hairline crown
            r_l = mesh.add_vert(Vec3(hc.x + x0, hc.y + 0.132, hc.z + zr), BoneID.HEAD)
            r_r = mesh.add_vert(Vec3(hc.x + x1, hc.y + 0.132, hc.z + zr), BoneID.HEAD)
            # Mid row: curves forward and down
            mid_z = max(zr, zt) + 0.008
            m_l = mesh.add_vert(Vec3(hc.x + x0, hc.y + 0.108, hc.z + mid_z), BoneID.HEAD, BoneID.HAIR_BANGS, 0.35)
            m_r = mesh.add_vert(Vec3(hc.x + x1, hc.y + 0.108, hc.z + mid_z), BoneID.HEAD, BoneID.HAIR_BANGS, 0.35)
            # Tip row: straight across at eyebrow level
            t_z = zt + 0.003
            tip_l = mesh.add_vert(Vec3(hc.x + x0, tip_y, hc.z + t_z), BoneID.HAIR_BANGS, BoneID.HEAD, 0.85)
            tip_r = mesh.add_vert(Vec3(hc.x + x1, tip_y, hc.z + t_z), BoneID.HAIR_BANGS, BoneID.HEAD, 0.85)
            # Top section (root -> mid)
            mesh.add_quad(r_l, m_l, m_r, r_r, "hair_dark_brown", 0.20, 0.30, layer=3)
            # Bottom section (mid -> straight tip)
            mesh.add_quad(m_l, tip_l, tip_r, m_r, "hair_dark_brown", 0.50, 0.66, layer=3, depth_bias=-0.002)

        # Longer face-framing side strands blending into the side falls
        for side_sign in (1.0, -1.0):
            fx0 = side_sign * 0.080
            fx1 = side_sign * 0.096
            r_l = mesh.add_vert(Vec3(hc.x + fx0, hc.y + 0.128, hc.z + 0.040), BoneID.HEAD)
            r_r = mesh.add_vert(Vec3(hc.x + fx1, hc.y + 0.128, hc.z + 0.036), BoneID.HEAD)
            temple_bone = BoneID.HAIR_TEMPLE_L if side_sign > 0 else BoneID.HAIR_TEMPLE_R
            m_l = mesh.add_vert(Vec3(hc.x + fx0, hc.y + 0.090, hc.z + 0.056), BoneID.HEAD, temple_bone, 0.55)
            m_r = mesh.add_vert(Vec3(hc.x + fx1, hc.y + 0.090, hc.z + 0.052), BoneID.HEAD, temple_bone, 0.55)
            tip_l = mesh.add_vert(Vec3(hc.x + fx0, hc.y + 0.040, hc.z + 0.070), temple_bone, BoneID.HEAD, 0.88)
            tip_r = mesh.add_vert(Vec3(hc.x + fx1, hc.y + 0.040, hc.z + 0.066), temple_bone, BoneID.HEAD, 0.88)
            mesh.add_quad(r_l, m_l, m_r, r_r, "hair_dark_brown", 0.28, 0.38, layer=3)
            mesh.add_quad(m_l, tip_l, tip_r, m_r, "hair_dark_brown", 0.56, 0.72, layer=3)

    @staticmethod
    def _build_hair_ribbon_strand(
        mesh: SkinnedMesh,
        points: List[Vec3],
        widths: List[float],
        thickness: float,
        bone_top: int,
        bone_tip: int,
        side_sign: float,
        wide_axis: str = "z",
    ) -> None:
        """Diamond cross-section ribbon strand. wide_axis='x' makes the broad
        dimension run along X (hair panels seen from the front), 'z' along Z."""
        rings: List[List[int]] = []
        n_pts = len(points)
        for i, (pt, w) in enumerate(zip(points, widths)):
            t = i / max(1, n_pts - 1)
            w0 = clamp01(1.0 - t * 0.85)
            if wide_axis == "x":
                v_out = mesh.add_vert(Vec3(pt.x + w * 0.5, pt.y, pt.z), bone_top, bone_tip, w0)
                v_fwd = mesh.add_vert(Vec3(pt.x, pt.y, pt.z + thickness), bone_top, bone_tip, w0)
                v_in = mesh.add_vert(Vec3(pt.x - w * 0.5, pt.y, pt.z), bone_top, bone_tip, w0)
                v_bck = mesh.add_vert(Vec3(pt.x, pt.y, pt.z - thickness * 0.6), bone_top, bone_tip, w0)
            else:
                v_out = mesh.add_vert(Vec3(pt.x + side_sign * thickness, pt.y, pt.z), bone_top, bone_tip, w0)
                v_fwd = mesh.add_vert(Vec3(pt.x, pt.y, pt.z + w * 0.5), bone_top, bone_tip, w0)
                v_in = mesh.add_vert(Vec3(pt.x - side_sign * thickness * 0.6, pt.y, pt.z), bone_top, bone_tip, w0)
                v_bck = mesh.add_vert(Vec3(pt.x, pt.y, pt.z - w * 0.5), bone_top, bone_tip, w0)
            rings.append([v_out, v_fwd, v_in, v_bck])

        for i in range(n_pts - 1):
            ra = rings[i]
            rb = rings[i + 1]
            gt = 0.20 + 0.65 * (i / max(1, n_pts - 2))
            for s in range(4):
                sn = (s + 1) % 4
                if side_sign > 0:
                    mesh.add_quad(ra[s], rb[s], rb[sn], ra[sn], "hair_dark_brown", gt, gt, layer=3)
                else:
                    mesh.add_quad(ra[s], ra[sn], rb[sn], rb[s], "hair_dark_brown", gt, gt, layer=3)

    @staticmethod
    def _build_back_curtain(
        mesh: SkinnedMesh,
        hc: Vec3,
        ang_start: float,
        ang_end: float,
        bone_tip: int,
    ) -> None:
        """Long back curtain: arcs from crown down to mid-back, narrowing and
        shifting behind the torso as it descends so it never clips the body."""
        # (y_off, rad_x, rad_z, z_shift, weight_to_tip, ang0, ang1)
        # Extended longer: hair now reaches down to lower back (~Y 0.82)
        # for the long straight dark-brown hairstyle matching the reference.
        levels = [
            (0.112,  0.072, 0.088, -0.004, 0.05, ang_start,        ang_end),
            (0.048,  0.079, 0.095, -0.010, 0.28, ang_start,        ang_end),
            (-0.032, 0.086, 0.096, -0.020, 0.58, ang_start,        ang_end),
            (-0.128, 0.096, 0.092, -0.026, 0.86, ang_start + 0.04, ang_end - 0.04),
            (-0.235, 0.094, 0.088, -0.028, 1.00, ang_start + 0.10, ang_end - 0.10),
            (-0.350, 0.088, 0.084, -0.030, 1.00, ang_start + 0.16, ang_end - 0.16),
            (-0.460, 0.078, 0.076, -0.032, 1.00, ang_start + 0.22, ang_end - 0.22),
            (-0.560, 0.068, 0.066, -0.030, 1.00, ang_start + 0.26, ang_end - 0.26),
            (-0.650, 0.056, 0.054, -0.026, 1.00, ang_start + 0.30, ang_end - 0.30),
        ]
        u_segs = 4
        outer_rings: List[List[int]] = []
        for y_off, rx, rz, zs, wt, a0, a1 in levels:
            ring: List[int] = []
            for u in range(u_segs + 1):
                ang = lerp(a0, a1, u / u_segs)
                vx = hc.x + math.cos(ang) * rx
                vy = hc.y + y_off
                vz = hc.z + zs + math.sin(ang) * rz
                ring.append(mesh.add_vert(Vec3(vx, vy, vz), bone_tip, BoneID.HEAD, wt))
            outer_rings.append(ring)

        for r in range(len(outer_rings) - 1):
            ra = outer_rings[r]
            rb = outer_rings[r + 1]
            gt = 0.18 + 0.72 * (r / (len(outer_rings) - 2))
            for u in range(u_segs):
                # Note: hair_dark_brown is double_sided=True, clean shading from both front & back
                mesh.add_quad(ra[u], ra[u + 1], rb[u + 1], rb[u], "hair_dark_brown", gt, gt, layer=3)


# =============================================================================
# PROTAGONIST ANATOMY PART 2: TORSO, TWO-TONE SPEEDO SWIMSUIT, ARMS & HANDS
# =============================================================================

class ProtagonistTorsoArmBuilder:
    """
    Sculpts the athletic female torso, cobalt-blue & crisp-white competitive
    racerback swimsuit, clavicles, deltoids, forearms, and articulated hands.
    """

    @staticmethod
    def build_torso_and_arms(mesh: SkinnedMesh, skel: Skeleton) -> None:
        # ---------------------------------------------------------------------
        # 1. TORSO & TWO-TONE COMPETITIVE SWIMSUIT ("SPEEDO")
        # ---------------------------------------------------------------------
        # 16->14 segment sculpted cross-section rings from lower pelvis up to trapezius/collarbone
        segs = 16
        # Anatomical cross-section rings from lower pelvis up to trapezius/collarbone
        torso_levels = [
            # (y, rx, rz_f, rz_b, z_off, b0, b1, w0, waist_pinch, bust_lift, glute_lift)
            (0.845, 0.128, 0.072, 0.092, -0.006, BoneID.PELVIS, BoneID.THIGH_L, 0.90, 0.0, 0.0, 0.014),  # Upper hip / pelvis base
            (0.905, 0.146, 0.088, 0.112, -0.008, BoneID.PELVIS, BoneID.SPINE_LOWER, 0.88, 0.0, 0.0, 0.022),  # Full hip / glute contour
            (0.965, 0.132, 0.084, 0.094, -0.004, BoneID.PELVIS, BoneID.SPINE_LOWER, 0.55, 0.0, 0.0, 0.010),  # Iliac crest
            (1.035, 0.112, 0.078, 0.080,  0.002, BoneID.SPINE_LOWER, BoneID.SPINE_UPPER, 0.68, 0.06, 0.0, 0.0),  # Natural waist
            (1.115, 0.118, 0.084, 0.084,  0.002, BoneID.SPINE_UPPER, BoneID.SPINE_LOWER, 0.72, 0.0, 0.0, 0.0),  # Lower ribcage
            (1.195, 0.132, 0.098, 0.092,  0.004, BoneID.SPINE_UPPER, BoneID.CHEST, 0.50, 0.0, 0.022, 0.0),  # Lower bust / mid-rib
            (1.255, 0.138, 0.102, 0.095,  0.005, BoneID.CHEST, BoneID.SPINE_UPPER, 0.75, 0.0, 0.032, 0.0),  # Bust / pectoral line
            (1.315, 0.142, 0.088, 0.090,  0.002, BoneID.CHEST, BoneID.CLAVICLE_L, 0.85, 0.0, 0.010, 0.0),   # Upper chest / underarm
            (1.372, 0.126, 0.070, 0.074, -0.002, BoneID.CHEST, BoneID.NECK, 0.78, 0.0, 0.0, 0.0),          # Clavicle / shoulder base
        ]

        rings: List[List[int]] = []
        for y, rx, rzf, rzb, z_off, b0, b1, w0, w_pinch, b_lift, g_lift in torso_levels:
            ring: List[int] = []
            for s in range(segs):
                ang = (s / segs) * TAU
                ca = math.cos(ang)
                sa = math.sin(ang)
                rz = rzf if sa >= 0.0 else rzb

                # Bilateral breast contour on front upper chest (sa > 0.35, dual peaks around |ca| ~ 0.48)
                chest_shape = 0.0
                if b_lift > 0.0 and sa > 0.25:
                    lobe = math.exp(-((abs(ca) - 0.45) ** 2) / 0.12)
                    chest_shape = b_lift * sa * (0.35 + 0.85 * lobe)

                # Sculpted glute contour on back pelvis (sa < -0.25)
                glute_shape = 0.0
                if g_lift > 0.0 and sa < -0.20:
                    lobe = math.exp(-((abs(ca) - 0.42) ** 2) / 0.15)
                    glute_shape = g_lift * (-sa) * (0.4 + 0.85 * lobe)

                # Slight spinal furrow along center back
                spine_groove = 0.0
                if sa < -0.85 and abs(ca) < 0.25:
                    spine_groove = 0.007 * (1.0 - abs(ca) * 4.0)

                vx = ca * (rx - w_pinch * 0.08 * (1.0 - abs(sa)))
                vy = y
                vz = z_off + sa * rz + chest_shape - glute_shape + spine_groove

                # Split side weights cleanly at shoulders/hips
                eff_b1 = b1
                if b1 == BoneID.CLAVICLE_L and ca < 0.0:
                    eff_b1 = BoneID.CLAVICLE_R
                elif b1 == BoneID.THIGH_L and ca < 0.0:
                    eff_b1 = BoneID.THIGH_R
                ring.append(mesh.add_vert(Vec3(vx, vy, vz), b0, eff_b1, w0))
            rings.append(ring)

        # Crotch / pelvis underside closure for one-piece swimsuit bottom
        # (full fan closure with outward-facing (downward) winding)
        crotch_f = mesh.add_vert(Vec3(0.0, 0.785, 0.032), BoneID.PELVIS)
        crotch_b = mesh.add_vert(Vec3(0.0, 0.782, -0.038), BoneID.PELVIS)
        base_r = rings[0]
        for s in range(segs):
            sn = (s + 1) % segs
            ang_m = ((s + 0.5) / segs) * TAU
            sa = math.sin(ang_m)
            target_c = crotch_f if sa >= 0.0 else crotch_b
            mesh.add_tri(target_c, base_r[sn], base_r[s], "swimsuit_blue", 0.72, layer=3)

        # Royal blue competitive one-piece swimsuit with white side panels
        # (matching reference: high scoop neckline near collarbone, full torso
        # coverage, white lateral panels, racerback shoulder straps added below)
        torso_y_values = [lvl[0] for lvl in torso_levels]
        # Neckline: high scoop at front (near collarbone), slightly higher at back.
        # Front scoop dips to ~1.32, sides/back rise to ~1.375.
        neckline_front_y = 1.320
        neckline_back_y = 1.375

        def torso_swimsuit_mat(r: int, s: int, total: int) -> Tuple[str, float]:
            ang = ((s + 0.5) / total) * TAU
            ca = math.cos(ang)
            sa = math.sin(ang)
            y = torso_y_values[r]

            # Compute blended neckline height for this segment's angular position.
            # Front (sa>0) scoops lower; back (sa<0) sits higher for athletic back.
            if sa > 0.0:
                neck_y = lerp(neckline_back_y, neckline_front_y, sa)
            else:
                neck_y = neckline_back_y

            # Above the neckline: bare skin (neck, upper chest above scoop, shoulders)
            if y >= neck_y:
                return ("skin", 0.28 + 0.06 * sa)

            # Within swimsuit coverage: royal blue body with white lateral panels.
            # White side panels wrap the lateral seam (|ca| high) on both sides.
            side_factor = abs(ca)
            if side_factor > 0.90:
                # Crisp white side panel with vertical gradient for athletic depth
                grad = 0.22 + 0.30 * clamp01((neck_y - y) / (neck_y - 0.845))
                return ("swimsuit_white", grad)
            # Royal blue body with vertical gradient (lighter at chest, deeper at hip)
            grad = 0.18 + 0.40 * clamp01((neck_y - y) / (neck_y - 0.845))
            # Subtle front/back shading variation for sculpted depth
            grad += 0.05 * sa
            return ("swimsuit_blue", clamp(grad, 0.12, 0.85))

        mesh.add_lofted_rings(rings, torso_swimsuit_mat, layer=3, reverse_winding=True)

        # Thin light-blue piping strips along the white panel edges (both sides)
        # run vertically from the neckline down to the hip line for athletic accent.
        for side_sign in (1.0, -1.0):
            piping_z = 0.0  # At the lateral seam (X = ±max, Z ≈ 0)
            # Approximate panel-edge X at the side seam from the torso rings
            p_top = None
            p_mid = None
            p_bot = None
            for r_idx in range(len(rings)):
                y_val = torso_y_values[r_idx]
                # Find ring closest to neckline, mid-torso, and hip
                if y_val >= 1.30 and p_top is None:
                    p_top = rings[r_idx]
                if 0.99 < y_val < 1.05:
                    p_mid = rings[r_idx]
                if y_val <= 0.88:
                    p_bot = rings[r_idx]
                    break
            # Build a thin piping strip as 2-3 small quads along the panel boundary
            # Use the side-most vertex of each located ring
            if p_top is not None and p_bot is not None:
                # Side-most vertex = index 0 (ang=0, +X) or index segs//2 (ang=pi, -X)
                side_idx = 0 if side_sign > 0 else segs // 2
                v_top = p_top[side_idx]
                v_mid = p_mid[side_idx] if p_mid is not None else v_top
                v_bot = p_bot[side_idx]
                # Offset slightly outward in X so piping sits proud of the fabric
                ox = side_sign * 0.003
                # Thin quad strip along the seam: add 4 verts per level (thin ribbon)
                levels_pv = [(v_top, 1.30), (v_mid, 1.02), (v_bot, 0.87)]
                pipe_rings: List[List[int]] = []
                for ring_ref, _yv in levels_pv:
                    # Read back the vert position via mesh.verts
                    base_v = mesh.verts[ring_ref]
                    cx_p = base_v.x + ox
                    cz_p = base_v.z
                    cy_p = base_v.y
                    # Thin ribbon: 4 verts forming a narrow vertical strip
                    v0 = mesh.add_vert(Vec3(cx_p - side_sign * 0.003, cy_p - 0.004, cz_p + 0.001),
                                       BoneID.CHEST, BoneID.SPINE_UPPER, 0.7)
                    v1 = mesh.add_vert(Vec3(cx_p + side_sign * 0.003, cy_p - 0.004, cz_p + 0.001),
                                       BoneID.CHEST, BoneID.SPINE_UPPER, 0.7)
                    v2 = mesh.add_vert(Vec3(cx_p + side_sign * 0.003, cy_p + 0.004, cz_p + 0.001),
                                       BoneID.CHEST, BoneID.SPINE_UPPER, 0.7)
                    v3 = mesh.add_vert(Vec3(cx_p - side_sign * 0.003, cy_p + 0.004, cz_p + 0.001),
                                       BoneID.CHEST, BoneID.SPINE_UPPER, 0.7)
                    pipe_rings.append([v0, v1, v2, v3])
                for pi in range(len(pipe_rings) - 1):
                    ra = pipe_rings[pi]
                    rb = pipe_rings[pi + 1]
                    mesh.add_quad(ra[0], ra[1], rb[1], rb[0], "swimsuit_piping", 0.35, 0.45, layer=3, depth_bias=-0.004)
                    mesh.add_quad(ra[1], ra[2], rb[2], rb[1], "swimsuit_piping", 0.40, 0.50, layer=3, depth_bias=-0.004)
                    mesh.add_quad(ra[2], ra[3], rb[3], rb[2], "swimsuit_piping", 0.45, 0.55, layer=3, depth_bias=-0.004)
                    mesh.add_quad(ra[3], ra[0], rb[0], rb[3], "swimsuit_piping", 0.40, 0.50, layer=3, depth_bias=-0.004)

        # Shoulder yoke fillers: bridge the torso top ring into the deltoids so
        # no gap opens between arms and body during idle sway or dances
        for side_sign, clav_b in ((1.0, BoneID.CLAVICLE_L), (-1.0, BoneID.CLAVICLE_R)):
            yoke_c = Vec3(side_sign * 0.118, 1.348, 0.002)
            mesh.add_ellipsoid(
                yoke_c,
                0.055, 0.042, 0.052, 7, 4,
                clav_b, BoneID.CHEST, 0.72, "skin", layer=3,
            )

        # Hip blend fillers: smooth the thigh->pelvis junction on the sides
        for side_sign, th_b in ((1.0, BoneID.THIGH_L), (-1.0, BoneID.THIGH_R)):
            hip_c = Vec3(side_sign * 0.108, 0.868, 0.000)
            mesh.add_ellipsoid(
                hip_c,
                0.058, 0.052, 0.062, 7, 4,
                BoneID.PELVIS, th_b, 0.62, "skin", layer=3,
            )

        # Racerback shoulder straps: thick royal-blue strips running from the
        # front scoop neckline over each shoulder peak to the upper back.
        for side_sign, clav_b in ((1.0, BoneID.CLAVICLE_L), (-1.0, BoneID.CLAVICLE_R)):
            strap_pts = [
                Vec3(side_sign * 0.096, 1.328, 0.040),   # Front neckline anchor
                Vec3(side_sign * 0.116, 1.372, 0.020),   # Shoulder front slope
                Vec3(side_sign * 0.132, 1.386, 0.000),   # Shoulder peak
                Vec3(side_sign * 0.120, 1.378, -0.022),  # Shoulder back slope
                Vec3(side_sign * 0.098, 1.368, -0.042),  # Back neckline anchor
            ]
            strap_w = 0.024   # 2.4cm wide athletic strap
            strap_t = 0.009   # Stands ~9mm proud of the skin for solid form
            strap_rings: List[List[int]] = []
            for i, pt in enumerate(strap_pts):
                # Tangent along strap centerline
                if i == 0:
                    tangent = (strap_pts[1] - strap_pts[0]).normalized()
                elif i == len(strap_pts) - 1:
                    tangent = (strap_pts[-1] - strap_pts[-2]).normalized()
                else:
                    tangent = (strap_pts[i + 1] - strap_pts[i - 1]).normalized()
                # Perpendicular frame: side = tangent x up, up_corr = side x tangent
                side_v = tangent.cross(VEC3_UP).normalized()
                up_corr = side_v.cross(tangent).normalized()
                b0 = clav_b
                b1 = BoneID.CHEST
                w0 = 0.78
                v0 = mesh.add_vert(pt + side_v * strap_w * 0.5, b0, b1, w0)
                v1 = mesh.add_vert(pt - side_v * strap_w * 0.5, b0, b1, w0)
                v2 = mesh.add_vert(pt - side_v * strap_w * 0.5 + up_corr * strap_t, b0, b1, w0)
                v3 = mesh.add_vert(pt + side_v * strap_w * 0.5 + up_corr * strap_t, b0, b1, w0)
                strap_rings.append([v0, v1, v2, v3])
            for si in range(len(strap_rings) - 1):
                ra = strap_rings[si]
                rb = strap_rings[si + 1]
                gt = 0.25 + 0.12 * si
                mesh.add_quad(ra[0], ra[1], rb[1], rb[0], "swimsuit_blue", gt, gt, layer=3, depth_bias=-0.003)
                mesh.add_quad(ra[1], ra[2], rb[2], rb[1], "swimsuit_blue", gt + 0.05, gt + 0.05, layer=3, depth_bias=-0.003)
                mesh.add_quad(ra[2], ra[3], rb[3], rb[2], "swimsuit_blue", gt + 0.10, gt + 0.10, layer=3, depth_bias=-0.003)
                mesh.add_quad(ra[3], ra[0], rb[0], rb[3], "swimsuit_blue", gt + 0.05, gt + 0.05, layer=3, depth_bias=-0.003)

        # ---------------------------------------------------------------------
        # 2. SHOULDERS, UPPER ARMS, FOREARMS & ARTICULATED HANDS
        # ---------------------------------------------------------------------
        for is_right in (False, True):
            side_sign = -1.0 if is_right else 1.0
            clav_b = BoneID.CLAVICLE_R if is_right else BoneID.CLAVICLE_L
            up_b = BoneID.UPPER_ARM_R if is_right else BoneID.UPPER_ARM_L
            fore_b = BoneID.FOREARM_R if is_right else BoneID.FOREARM_L
            hand_b = BoneID.HAND_R if is_right else BoneID.HAND_L

            sh_pos = skel.bind_world[up_b].pos
            el_pos = skel.bind_world[fore_b].pos
            wr_pos = skel.bind_world[hand_b].pos

            # Sculpted deltoid cap (bridges arm into torso shoulder)
            mesh.add_ellipsoid(
                Vec3(sh_pos.x - side_sign * 0.014, sh_pos.y + 0.006, sh_pos.z),
                0.050, 0.052, 0.048, 7, 4,
                up_b, clav_b, 0.65, "skin", layer=3,
            )

            # Upper arm + forearm continuous athletic lofted tube (8 rings, 7 segs)
            arm_segs = 8
            arm_profile = [
                # (y_world, rx, rz, x_off, b0, b1, w0)
                (sh_pos.y - 0.016, 0.046, 0.045,  0.000, up_b, clav_b, 0.85),
                (sh_pos.y - 0.085, 0.039, 0.040,  0.003, up_b, up_b,   1.00),
                (sh_pos.y - 0.175, 0.036, 0.037,  0.005, up_b, up_b,   1.00),
                (el_pos.y + 0.015, 0.033, 0.034,  0.006, up_b, fore_b, 0.55),  # Elbow joint
                (el_pos.y - 0.025, 0.034, 0.035,  0.006, fore_b, up_b, 0.72),  # Upper forearm
                (el_pos.y - 0.095, 0.032, 0.033,  0.006, fore_b, fore_b, 1.00),  # Mid forearm
                (el_pos.y - 0.175, 0.026, 0.025,  0.006, fore_b, fore_b, 1.00),
                (wr_pos.y + 0.006, 0.024, 0.020,  0.006, fore_b, hand_b, 0.55),  # Slender wrist
            ]
            arm_rings: List[List[int]] = []
            for yw, rx, rz, xo, b0, b1, w0 in arm_profile:
                ring: List[int] = []
                cx = sh_pos.x + side_sign * xo
                cz = sh_pos.z
                for s in range(arm_segs):
                    ang = (s / arm_segs) * TAU
                    ring.append(
                        mesh.add_vert(
                            Vec3(cx + math.cos(ang) * rx, yw, cz + math.sin(ang) * rz),
                            b0, b1, w0,
                        )
                    )
                arm_rings.append(ring)

            mesh.add_lofted_rings(
                arm_rings,
                lambda r, s, n: ("skin", 0.28 + 0.08 * r),
                layer=3,
            )

            # Elbow joint sphere (moves with the forearm, fills the bend gap)
            mesh.add_ellipsoid(
                Vec3(el_pos.x + side_sign * 0.006, el_pos.y + 0.002, el_pos.z),
                0.034, 0.036, 0.034, 6, 4,
                fore_b, up_b, 0.45, "skin", layer=3,
            )

            # Sculpted Hand: Palm + Thumb + Index + Middle + Ring/Pinky
            ProtagonistTorsoArmBuilder._build_hand(
                mesh,
                Vec3(wr_pos.x + side_sign * 0.006, wr_pos.y, wr_pos.z),
                side_sign,
                hand_b,
                is_right=is_right,
            )

    @staticmethod
    def _build_hand(
        mesh: SkinnedMesh,
        wrist_pos: Vec3,
        side_sign: float,
        hand_bone: int,
        is_right: bool,
    ) -> None:
        # Palm box-loft (slightly flattened in X, facing inward toward body)
        # Note: +X is left side, so left palm faces -X (inward), right palm faces +X (inward)
        inward = -side_sign
        palm_rings = [
            # (dy, thick_x, width_z, z_shift)
            (0.000, 0.013, 0.023, 0.000),
            (-0.036, 0.014, 0.031, 0.003),
            (-0.072, 0.011, 0.030, 0.004),
        ]
        p_rings: List[List[int]] = []
        for dy, tx, wz, zs in palm_rings:
            v0 = mesh.add_vert(Vec3(wrist_pos.x + tx, wrist_pos.y + dy, wrist_pos.z + zs + wz), hand_bone)
            v1 = mesh.add_vert(Vec3(wrist_pos.x - tx, wrist_pos.y + dy, wrist_pos.z + zs + wz), hand_bone)
            v2 = mesh.add_vert(Vec3(wrist_pos.x - tx, wrist_pos.y + dy, wrist_pos.z + zs - wz), hand_bone)
            v3 = mesh.add_vert(Vec3(wrist_pos.x + tx, wrist_pos.y + dy, wrist_pos.z + zs - wz), hand_bone)
            p_rings.append([v0, v1, v2, v3])

        mesh.add_lofted_rings(
            p_rings,
            lambda r, s, n: ("skin", 0.35 + 0.15 * r),
            layer=3,
        )
        # Knuckle cap
        kc = mesh.add_vert(Vec3(wrist_pos.x, wrist_pos.y - 0.076, wrist_pos.z + 0.004), hand_bone)
        for s in range(4):
            sn = (s + 1) % 4
            mesh.add_tri(kc, p_rings[-1][s], p_rings[-1][sn], "skin", 0.55, layer=3)

        # Thumb (angled forward +Z and slightly inward)
        thumb_base = Vec3(wrist_pos.x + inward * 0.006, wrist_pos.y - 0.026, wrist_pos.z + 0.028)
        thumb_tip = Vec3(wrist_pos.x + inward * 0.015, wrist_pos.y - 0.068, wrist_pos.z + 0.044)
        ProtagonistTorsoArmBuilder._add_finger(mesh, thumb_base, thumb_tip, 0.0075, 0.0055, hand_bone)

        # Index finger (angled slightly apart from middle on right hand for cigarette pinch!)
        idx_spread = 0.018 if is_right else 0.016
        idx_base = Vec3(wrist_pos.x, wrist_pos.y - 0.068, wrist_pos.z + idx_spread)
        idx_tip_x = wrist_pos.x + (0.009 if is_right else inward * 0.008)
        idx_tip = Vec3(idx_tip_x, wrist_pos.y - 0.132, wrist_pos.z + idx_spread + 0.006)
        ProtagonistTorsoArmBuilder._add_finger(mesh, idx_base, idx_tip, 0.0065, 0.0045, hand_bone)

        # Middle finger (creates natural V-gap with index on right hand!)
        mid_base = Vec3(wrist_pos.x, wrist_pos.y - 0.070, wrist_pos.z + 0.002)
        mid_tip_x = wrist_pos.x + (-0.004 if is_right else inward * 0.010)
        mid_tip = Vec3(mid_tip_x, wrist_pos.y - 0.138, wrist_pos.z + 0.001)
        ProtagonistTorsoArmBuilder._add_finger(mesh, mid_base, mid_tip, 0.0068, 0.0046, hand_bone)

        # Ring & pinky softly curled cluster
        ring_base = Vec3(wrist_pos.x + inward * 0.004, wrist_pos.y - 0.068, wrist_pos.z - 0.016)
        ring_tip = Vec3(wrist_pos.x + inward * 0.018, wrist_pos.y - 0.120, wrist_pos.z - 0.018)
        ProtagonistTorsoArmBuilder._add_finger(mesh, ring_base, ring_tip, 0.0095, 0.0060, hand_bone)

    @staticmethod
    def _add_finger(
        mesh: SkinnedMesh,
        p0: Vec3,
        p1: Vec3,
        r0: float,
        r1: float,
        bone: int,
    ) -> None:
        axis = (p1 - p0).normalized()
        ref = Vec3(1.0, 0.0, 0.0) if abs(axis.x) < 0.8 else Vec3(0.0, 0.0, 1.0)
        t = axis.cross(ref).normalized()
        b = axis.cross(t).normalized()
        mid = p0.lerp(p1, 0.55)
        rm = (r0 + r1) * 0.52

        rings: List[List[int]] = []
        for center, rad in ((p0, r0), (mid, rm), (p1, r1)):
            ring: List[int] = []
            for s in range(4):
                ang = (s / 4.0) * TAU
                radial = t * math.cos(ang) + b * math.sin(ang)
                ring.append(mesh.add_vert(center + radial * rad, bone))
            rings.append(ring)

        mesh.add_lofted_rings(rings, lambda r, s, n: ("skin", 0.35 + 0.2 * r), layer=3)
        tip_v = mesh.add_vert(p1 + axis * (r1 * 0.7), bone)
        for s in range(4):
            sn = (s + 1) % 4
            mesh.add_tri(tip_v, rings[-1][s], rings[-1][sn], "skin", 0.55, layer=3)


# =============================================================================
# PROTAGONIST ANATOMY PART 3: ATHLETIC LEGS, WHITE SNEAKERS & CIGARETTE PROP
# =============================================================================

class ProtagonistLegSneakerBuilder:
    """
    Sculpts the protagonist's slightly athletic legs (quads, knees, calves, ankles)
    and low-poly white athletic sneakers with sculpted outsole, toe-cap, tongue,
    padded collar, and heel counter.
    """

    @staticmethod
    def build_legs_and_sneakers(mesh: SkinnedMesh, skel: Skeleton) -> None:
        for is_right in (False, True):
            side_sign = -1.0 if is_right else 1.0
            th_b = BoneID.THIGH_R if is_right else BoneID.THIGH_L
            sh_b = BoneID.SHIN_R if is_right else BoneID.SHIN_L
            ft_b = BoneID.FOOT_R if is_right else BoneID.FOOT_L
            toe_b = BoneID.TOE_R if is_right else BoneID.TOE_L

            hp = skel.bind_world[th_b].pos
            kn = skel.bind_world[sh_b].pos
            ak = skel.bind_world[ft_b].pos

            # Hip-to-thigh anatomical blend cap
            cx_base = hp.x
            leg_segs = 10
            leg_profile = [
                # (y, rx, rz, x_off, z_off, b0, b1, w0)
                (hp.y - 0.008, 0.076, 0.080, -0.004, -0.002, th_b, BoneID.PELVIS, 0.62),  # sunk into pelvis
                (hp.y - 0.095, 0.068, 0.072, -0.002,  0.004, th_b, th_b,          1.00),  # Mid-upper quad
                (hp.y - 0.215, 0.059, 0.063,  0.000,  0.005, th_b, th_b,          1.00),  # Lower quad taper
                (hp.y - 0.335, 0.049, 0.052,  0.000,  0.004, th_b, sh_b,          0.78),  # Above knee
                (kn.y,         0.046, 0.050,  0.000,  0.006, th_b, sh_b,          0.50),  # Patella / knee joint
                (kn.y - 0.055, 0.045, 0.048,  0.000, -0.004, sh_b, th_b,          0.80),  # Upper shin
                (kn.y - 0.145, 0.051, 0.056,  0.000, -0.012, sh_b, sh_b,          1.00),  # Gastrocnemius calf peak
                (kn.y - 0.265, 0.041, 0.044,  0.000, -0.006, sh_b, sh_b,          1.00),  # Lower calf taper
                (ak.y + 0.025, 0.032, 0.036,  0.000, -0.002, sh_b, ft_b,          0.65),  # Slender ankle
                (ak.y - 0.006, 0.034, 0.040,  0.000,  0.000, ft_b, sh_b,          0.82),  # Sneaker collar tuck
            ]

            leg_rings: List[List[int]] = []
            for yw, rx, rz, xo, zo, b0, b1, w0 in leg_profile:
                ring: List[int] = []
                cx = cx_base + side_sign * xo
                cz = hp.z + zo
                for s in range(leg_segs):
                    ang = (s / leg_segs) * TAU
                    ring.append(
                        mesh.add_vert(
                            Vec3(cx + math.cos(ang) * rx, yw, cz + math.sin(ang) * rz),
                            b0, b1, w0,
                        )
                    )
                leg_rings.append(ring)

            mesh.add_lofted_rings(
                leg_rings,
                lambda r, s, n: ("skin", 0.26 + 0.06 * r),
                layer=3,
            )

            # Knee joint sphere (bound to the shin, fills the bend gap)
            mesh.add_ellipsoid(
                Vec3(kn.x, kn.y, kn.z),
                0.044, 0.044, 0.046, 6, 4,
                sh_b, th_b, 0.42, "skin", layer=3,
            )

            # Sculpted White Sneaker
            ProtagonistLegSneakerBuilder._build_sneaker(
                mesh, ak, side_sign, ft_b, toe_b
            )

    @staticmethod
    def _build_sneaker(
        mesh: SkinnedMesh,
        ankle_pos: Vec3,
        side_sign: float,
        foot_bone: int,
        toe_bone: int,
    ) -> None:
        # Cross-section profile from heel (Z = -0.048) to rounded toe cap (Z = +0.185)
        # Outsole touches Y = 0.000 cleanly!
        cx = ankle_pos.x
        # (z_off, y_bot, y_mid_sole, y_top, half_w, b0, b1, w0, mat_upper)
        shoe_slices = [
            (-0.048, 0.003, 0.024, 0.088, 0.034, foot_bone, foot_bone, 1.0, "sneaker_white"),  # Heel counter
            (-0.015, 0.000, 0.024, 0.096, 0.039, foot_bone, foot_bone, 1.0, "sneaker_white"),  # Ankle collar
            (0.038,  0.000, 0.022, 0.084, 0.041, foot_bone, foot_bone, 1.0, "sneaker_white"),  # Tongue / midfoot
            (0.092,  0.000, 0.020, 0.064, 0.044, foot_bone, toe_bone,  0.6, "sneaker_white"),  # Ball / vamp
            (0.145,  0.001, 0.019, 0.046, 0.040, toe_bone,  foot_bone, 0.85,"sneaker_white"),  # Toe box
            (0.184,  0.006, 0.020, 0.032, 0.026, toe_bone,  toe_bone,  1.0, "sneaker_white"),  # Toe tip
        ]

        # Build 8-vertex closed shoe cross-section at each slice:
        # 0: sole_L, 1: sole_R, 2: welt_R, 3: top_R, 4: top_C, 5: top_L, 6: welt_L, 7: sole_C_bot
        # Actually 6-vertex ring around perimeter is super clean & watertight:
        # 0: bot_L, 1: mid_L, 2: top_L, 3: top_R, 4: mid_R, 5: bot_R
        # Wait: let's keep sole ring and upper ring crisp so sole has sneaker_sole material!
        sole_rings: List[List[int]] = []
        upper_rings: List[List[int]] = []
        for z_off, yb, ym, yt, hw, b0, b1, w0, _ in shoe_slices:
            z = ankle_pos.z + z_off
            # 4-pt sole section: bot_L, welt_L, welt_R, bot_R
            s_ring = [
                mesh.add_vert(Vec3(cx + hw * 0.92, yb, z), b0, b1, w0),
                mesh.add_vert(Vec3(cx + hw,        ym, z), b0, b1, w0),
                mesh.add_vert(Vec3(cx - hw,        ym, z), b0, b1, w0),
                mesh.add_vert(Vec3(cx - hw * 0.92, yb, z), b0, b1, w0),
            ]
            sole_rings.append(s_ring)

            # Upper section sharing welt_L & welt_R: welt_L, top_L, top_C, top_R, welt_R
            u_ring = [
                s_ring[1],
                mesh.add_vert(Vec3(cx + hw * 0.65, yt * 0.90, z), b0, b1, w0),
                mesh.add_vert(Vec3(cx,             yt,        z), b0, b1, w0),
                mesh.add_vert(Vec3(cx - hw * 0.65, yt * 0.90, z), b0, b1, w0),
                s_ring[2],
            ]
            upper_rings.append(u_ring)

        # Sole sides & bottom
        for r in range(len(sole_rings) - 1):
            sa = sole_rings[r]
            sb = sole_rings[r + 1]
            # Left sole wall (sa[0] -> sb[0] -> sb[1] -> sa[1])
            mesh.add_quad(sa[0], sb[0], sb[1], sa[1], "sneaker_sole", 0.45, 0.35, layer=3)
            # Right sole wall (sa[2] -> sb[2] -> sb[3] -> sa[3])
            mesh.add_quad(sa[2], sb[2], sb[3], sa[3], "sneaker_sole", 0.45, 0.35, layer=3)
            # Bottom outsole (sa[3] -> sb[3] -> sb[0] -> sa[0])
            mesh.add_quad(sa[3], sb[3], sb[0], sa[0], "sneaker_sole", 0.85, 0.85, layer=3)

        # Upper body with subtle cobalt sneaker accent on midfoot side panel
        for r in range(len(upper_rings) - 1):
            ua = upper_rings[r]
            ub = upper_rings[r + 1]
            for seg in range(4):
                mat_u = "sneaker_white"
                if r == 1 and seg in (0, 3):
                    mat_u = "sneaker_accent"
                elif r == 2 and seg in (1, 2):
                    # Lace / tongue detail band
                    mat_u = "sneaker_sole"
                mesh.add_quad(ua[seg], ub[seg], ub[seg + 1], ua[seg + 1], mat_u, 0.25 + 0.1 * r, 0.35 + 0.1 * r, layer=3)

        # Heel cap & Toe cap closure
        h_s = sole_rings[0]
        h_u = upper_rings[0]
        mesh.add_quad(h_s[0], h_s[1], h_s[2], h_s[3], "sneaker_sole", 0.6, 0.6, layer=3)
        mesh.add_quad(h_u[0], h_u[2], h_u[4], h_u[0], "sneaker_white", 0.5, 0.5, layer=3)
        mesh.add_tri(h_u[0], h_u[1], h_u[2], "sneaker_white", 0.4, layer=3)
        mesh.add_tri(h_u[2], h_u[3], h_u[4], "sneaker_white", 0.4, layer=3)

        t_s = sole_rings[-1]
        t_u = upper_rings[-1]
        mesh.add_quad(t_s[3], t_s[2], t_s[1], t_s[0], "sneaker_sole", 0.5, 0.5, layer=3)
        mesh.add_tri(t_u[0], t_u[2], t_u[1], "sneaker_white", 0.3, layer=3)
        mesh.add_tri(t_u[0], t_u[4], t_u[2], "sneaker_white", 0.3, layer=3)
        mesh.add_tri(t_u[2], t_u[4], t_u[3], "sneaker_white", 0.3, layer=3)


class ProtagonistRigModel:
    """Complete assembled protagonist skeleton + anatomical low-poly mesh."""

    def __init__(self) -> None:
        self.skeleton = Skeleton()
        self.mesh = SkinnedMesh()
        ProtagonistHeadBuilder.build_head_and_hair(self.mesh, self.skeleton)
        ProtagonistTorsoArmBuilder.build_torso_and_arms(self.mesh, self.skeleton)
        ProtagonistLegSneakerBuilder.build_legs_and_sneakers(self.mesh, self.skeleton)
        self.mesh.bind_to_skeleton(self.skeleton)

    def update_and_render(
        self,
        pose: Pose,
        world_pos: Vec3,
        yaw: float,
        renderer: SceneRenderer,
        materials: Dict[str, Material],
        lighting: LightingRig,
    ) -> None:
        self.skeleton.evaluate_fk(pose, world_pos, yaw)
        self.mesh.deform(self.skeleton)
        self.mesh.render(renderer, materials, lighting)


class DynamicCigaretteProp:
    """
    Renders the protagonist's active cigarette attached either between her right
    index/middle fingers (CIG_SOCKET_HAND) or held in her lips (CIG_SOCKET_MOUTH).
    Supports progressive burn-down, growing grey ash tip, and glowing ember!
    """

    @staticmethod
    def compute_transform(
        skeleton: Skeleton,
        in_mouth: bool,
    ) -> Transform:
        if in_mouth:
            sock = skeleton.world_transforms[BoneID.CIG_SOCKET_MOUTH]
            # Point forward (+Z) and angled subtly downward/left from lips
            local_rot = Quat.from_euler_yxz(-0.14, 0.16, 0.0)
            return Transform(sock.pos, (sock.rot * local_rot).normalized(), Vec3(1.0, 1.0, 1.0))
        else:
            sock = skeleton.world_transforms[BoneID.CIG_SOCKET_HAND]
            # Held between index & middle fingers: points forward-outward from hand
            local_rot = Quat.from_euler_yxz(0.28, -0.35, 0.0)
            return Transform(sock.pos, (sock.rot * local_rot).normalized(), Vec3(1.0, 1.0, 1.0))

    @staticmethod
    def get_tip_world_pos(
        cig_xform: Transform,
        burn_progress: float,
        ash_length: float,
    ) -> Vec3:
        total_paper = lerp(0.056, 0.008, clamp01(burn_progress))
        tip_z = 0.022 + total_paper + ash_length
        return cig_xform.apply_point(Vec3(0.0, 0.0, tip_z))

    @staticmethod
    def render(
        cig_xform: Transform,
        is_lit: bool,
        burn_progress: float,
        ash_length: float,
        ember_pulse: float,
        renderer: SceneRenderer,
        materials: Dict[str, Material],
        lighting: LightingRig,
    ) -> None:
        filter_len = 0.022
        paper_len = lerp(0.056, 0.008, clamp01(burn_progress))
        rad = 0.0042

        # Filter segment: z in [0.0, filter_len]
        DynamicCigaretteProp._draw_cyl_seg(
            cig_xform, 0.0, filter_len, rad, "cig_filter", renderer, materials, lighting
        )
        # Paper segment: z in [filter_len, filter_len + paper_len]
        z_paper_end = filter_len + paper_len
        DynamicCigaretteProp._draw_cyl_seg(
            cig_xform, filter_len, z_paper_end, rad * 0.98, "cig_paper", renderer, materials, lighting
        )

        # Lit glowing ember ring + growing ash cylinder
        if is_lit:
            z_ember_end = z_paper_end + 0.0035
            ember_mat = Material(
                name="dyn_ember",
                base_color=Color3(1.0, 0.42, 0.10),
                roughness=0.7,
                emissive=Color3(
                    1.2 + ember_pulse * 1.8,
                    0.28 + ember_pulse * 0.65,
                    0.04 + ember_pulse * 0.12,
                ),
            )
            DynamicCigaretteProp._draw_cyl_seg(
                cig_xform, z_paper_end, z_ember_end, rad * 0.96, ember_mat, renderer, materials, lighting, cap_end=True
            )
            if ash_length > 0.0015:
                DynamicCigaretteProp._draw_cyl_seg(
                    cig_xform,
                    z_ember_end,
                    z_ember_end + ash_length,
                    rad * 0.88,
                    "cig_ash",
                    renderer,
                    materials,
                    lighting,
                    cap_end=True,
                )

    @staticmethod
    def _draw_cyl_seg(
        xf: Transform,
        z0: float,
        z1: float,
        radius: float,
        mat_or_name,
        renderer: SceneRenderer,
        materials: Dict[str, Material],
        lighting: LightingRig,
        cap_end: bool = False,
    ) -> None:
        mat = mat_or_name if isinstance(mat_or_name, Material) else materials[mat_or_name]
        segs = 6
        ring0: List[Vec3] = []
        ring1: List[Vec3] = []
        for s in range(segs):
            a = (s / segs) * TAU
            px = math.cos(a) * radius
            py = math.sin(a) * radius
            ring0.append(xf.apply_point(Vec3(px, py, z0)))
            ring1.append(xf.apply_point(Vec3(px, py, z1)))

        for s in range(segs):
            sn = (s + 1) % segs
            v0, v1, v2, v3 = ring0[s], ring0[sn], ring1[sn], ring1[s]
            n = (v1 - v0).cross(v3 - v0).normalized()
            renderer.submit_triangle(v0, v1, v2, n, mat, lighting, layer=3, grad_t=0.4, depth_bias=-0.025)
            renderer.submit_triangle(v0, v2, v3, n, mat, lighting, layer=3, grad_t=0.6, depth_bias=-0.025)

        if cap_end:
            c1 = xf.apply_point(Vec3(0.0, 0.0, z1))
            n_cap = xf.apply_dir(Vec3(0.0, 0.0, 1.0)).normalized()
            for s in range(segs):
                sn = (s + 1) % segs
                renderer.submit_triangle(c1, ring1[s], ring1[sn], n_cap, mat, lighting, layer=3, grad_t=0.3, depth_bias=-0.028)


# =============================================================================
# WORLD GEOMETRY PART 1: MODERN JAPANESE BEDROOM ARCHITECTURE
# =============================================================================

class BedroomArchitectureBuilder:
    """
    Constructs a contemporary Japanese urban bedroom (non-traditional):
    - Tessellated oak flooring planks for smooth pools of warm & cool light.
    - Subdivided plaster walls + dark slate accent wall behind the bed.
    - Sliding balcony window with pleated evening curtains & moonlight bleed.
    - Interior door with aluminum lever & neatly placed indoor slippers.
    - Wall-mounted Japanese split AC unit, baseboards, outlets, & wall art.
    """

    @staticmethod
    def build_architecture(mesh: StaticMesh) -> List[List[Vec3]]:
        hw = ROOM_HALF_W
        hd = ROOM_HALF_D
        rh = ROOM_HEIGHT

        # ---------------------------------------------------------------------
        # 1. WOODEN PLANK FLOOR (Subdivided strips along Z for rich lamp pools)
        # ---------------------------------------------------------------------
        plank_cols = 14
        plank_rows = 10
        dx = (hw * 2.0) / plank_cols
        dz = (hd * 2.0) / plank_rows
        for ix in range(plank_cols):
            x0 = -hw + ix * dx
            x1 = x0 + dx
            mat_p = "floor_wood" if (ix % 2 == 0) else "floor_wood_alt"
            for iz in range(plank_rows):
                z0 = -hd + iz * dz
                z1 = z0 + dz
                v0 = mesh.add_vert(Vec3(x0, 0.0, z0))
                v1 = mesh.add_vert(Vec3(x0, 0.0, z1))
                v2 = mesh.add_vert(Vec3(x1, 0.0, z1))
                v3 = mesh.add_vert(Vec3(x1, 0.0, z0))
                # Facing +Y: (v1 - v0) x (v2 - v0) = (0,0,+dz) x (+dx,0,+dz) = (0, +dz*dx, 0)
                grad = 0.25 + 0.50 * (((ix * 7 + iz * 13) % 5) / 4.0)
                mesh.add_quad(v0, v1, v2, v3, mat_p, grad, grad * 0.9, layer=0)

        # Woven charcoal area rug under center/bed-edge of room
        rug_x0, rug_x1 = -1.05, 0.95
        rug_z0, rug_z1 = -1.25, 1.05
        BedroomArchitectureBuilder._add_tessellated_plate(
            mesh, rug_x0, rug_x1, rug_z0, rug_z1, 0.008, 4, 4, "rug_woven", layer=1
        )

        # ---------------------------------------------------------------------
        # 2. SUBDIVIDED ROOM WALLS & CEILING
        # ---------------------------------------------------------------------
        # Back Wall (Z = -hd, normal +Z): modern Japanese dark slate accent behind bed!
        BedroomArchitectureBuilder._add_wall_grid(
            mesh,
            origin=Vec3(-hw, 0.0, -hd),
            u_dir=Vec3(1.0, 0.0, 0.0), u_len=hw * 2.0, u_divs=8,
            v_dir=Vec3(0.0, 1.0, 0.0), v_len=rh, v_divs=5,
            mat_name="wall_accent",
            layer=0,
        )

        # Left Wall (X = -hw, normal +X)
        BedroomArchitectureBuilder._add_wall_grid(
            mesh,
            origin=Vec3(-hw, 0.0, hd),
            u_dir=Vec3(0.0, 0.0, -1.0), u_len=hd * 2.0, u_divs=8,
            v_dir=Vec3(0.0, 1.0, 0.0), v_len=rh, v_divs=5,
            mat_name="wall_plaster",
            layer=0,
        )

        # Right Wall (X = +hw, normal -X)
        BedroomArchitectureBuilder._add_wall_grid(
            mesh,
            origin=Vec3(hw, 0.0, -hd),
            u_dir=Vec3(0.0, 0.0, 1.0), u_len=hd * 2.0, u_divs=8,
            v_dir=Vec3(0.0, 1.0, 0.0), v_len=rh, v_divs=5,
            mat_name="wall_plaster",
            layer=0,
        )

        # Front / Balcony Window Wall (Z = +hd, normal -Z), leaving central window recess
        # Left pillar of window wall (X in [-hw, -1.52])
        BedroomArchitectureBuilder._add_wall_grid(
            mesh,
            origin=Vec3(hw, 0.0, hd),
            u_dir=Vec3(-1.0, 0.0, 0.0), u_len=hw - 1.52, u_divs=2,
            v_dir=Vec3(0.0, 1.0, 0.0), v_len=rh, v_divs=5,
            mat_name="wall_plaster",
            layer=0,
        )
        # Right pillar of window wall (X in [1.52, hw])
        BedroomArchitectureBuilder._add_wall_grid(
            mesh,
            origin=Vec3(-1.52, 0.0, hd),
            u_dir=Vec3(-1.0, 0.0, 0.0), u_len=hw - 1.52, u_divs=2,
            v_dir=Vec3(0.0, 1.0, 0.0), v_len=rh, v_divs=5,
            mat_name="wall_plaster",
            layer=0,
        )
        # Header lintel above window (Y in [2.16, rh], X in [-1.52, 1.52])
        BedroomArchitectureBuilder._add_wall_grid(
            mesh,
            origin=Vec3(1.52, 2.16, hd),
            u_dir=Vec3(-1.0, 0.0, 0.0), u_len=3.04, u_divs=5,
            v_dir=Vec3(0.0, 1.0, 0.0), v_len=rh - 2.16, v_divs=2,
            mat_name="wall_plaster",
            layer=0,
        )
        # Low sill wall below balcony window (Y in [0.0, 0.16], X in [-1.52, 1.52])
        BedroomArchitectureBuilder._add_wall_grid(
            mesh,
            origin=Vec3(1.52, 0.0, hd),
            u_dir=Vec3(-1.0, 0.0, 0.0), u_len=3.04, u_divs=5,
            v_dir=Vec3(0.0, 1.0, 0.0), v_len=0.16, v_divs=1,
            mat_name="wall_plaster",
            layer=0,
        )

        # Ceiling (Y = rh, normal -Y)
        BedroomArchitectureBuilder._add_wall_grid(
            mesh,
            origin=Vec3(-hw, rh, -hd),
            u_dir=Vec3(1.0, 0.0, 0.0), u_len=hw * 2.0, u_divs=7,
            v_dir=Vec3(0.0, 0.0, 1.0), v_len=hd * 2.0, v_divs=7,
            mat_name="ceiling",
            layer=0,
        )

        # Baseboards around perimeter
        mesh.add_box(0.0, 0.045, -hd + 0.015, hw * 2.0, 0.09, 0.03, "baseboard", layer=2)
        mesh.add_box(-hw + 0.015, 0.045, 0.0, 0.03, 0.09, hd * 2.0, "baseboard", layer=2)
        mesh.add_box(hw - 0.015, 0.045, 0.0, 0.03, 0.09, hd * 2.0, "baseboard", layer=2)
        mesh.add_box(0.0, 0.045, hd - 0.015, hw * 2.0, 0.09, 0.03, "baseboard", layer=2)

        # Off-state minimalist Japanese ceiling pendant ring (center of ceiling)
        mesh.add_cylinder(Vec3(0.0, rh - 0.04, 0.0), Vec3(0.0, rh, 0.0), 0.24, 0.24, 14, "ac_plastic", layer=2)
        mesh.add_cylinder(Vec3(0.0, rh - 0.05, 0.0), Vec3(0.0, rh - 0.038, 0.0), 0.25, 0.25, 14, "metal_dark", layer=2)

        # ---------------------------------------------------------------------
        # 3. BALCONY SLIDING WINDOW, NIGHT GLASS & HEAVY PLEATED CURTAINS
        # ---------------------------------------------------------------------
        # Dark aluminum balcony sash frame
        mesh.add_box(0.0, 2.14, hd - 0.02, 3.06, 0.05, 0.06, "metal_dark", layer=2)
        mesh.add_box(0.0, 0.16, hd - 0.02, 3.06, 0.05, 0.06, "metal_dark", layer=2)
        mesh.add_box(-1.50, 1.15, hd - 0.02, 0.05, 1.98, 0.06, "metal_dark", layer=2)
        mesh.add_box(1.50, 1.15, hd - 0.02, 0.05, 1.98, 0.06, "metal_dark", layer=2)
        mesh.add_box(0.0, 1.15, hd - 0.02, 0.04, 1.98, 0.05, "metal_dark", layer=2)  # Center mullion

        # Evening sky night glass panes
        g_l = mesh.add_vert(Vec3(-1.48, 0.18, hd + 0.01), )
        BedroomArchitectureBuilder._add_wall_grid(
            mesh,
            origin=Vec3(1.48, 0.18, hd + 0.01),
            u_dir=Vec3(-1.0, 0.0, 0.0), u_len=2.96, u_divs=4,
            v_dir=Vec3(0.0, 1.0, 0.0), v_len=1.94, v_divs=3,
            mat_name="window_glass_night",
            layer=0,
        )

        # Curtain rail above window
        mesh.add_cylinder(
            Vec3(-1.68, 2.24, hd - 0.09), Vec3(1.68, 2.24, hd - 0.09),
            0.014, 0.014, 8, "metal_chrome", layer=2,
        )

        # Pleated heavy evening curtains drawn across window with narrow ~14cm moonlit center gap!
        BedroomArchitectureBuilder._build_pleated_curtain(
            mesh, x_start=-1.60, x_end=-0.09, y_bot=0.06, y_top=2.23, z_base=hd - 0.10, pleats=8
        )
        BedroomArchitectureBuilder._build_pleated_curtain(
            mesh, x_start=0.07, x_end=1.60, y_bot=0.06, y_top=2.23, z_base=hd - 0.10, pleats=8
        )

        # Volumetric moonlight shaft polygons streaming through curtain gap
        light_shafts = [
            [
                Vec3(-0.08, 2.10, hd - 0.12),
                Vec3(0.06, 2.10, hd - 0.12),
                Vec3(0.32, 0.02, 0.65),
                Vec3(-0.34, 0.02, 0.65),
            ],
            [
                Vec3(-0.06, 1.85, hd - 0.12),
                Vec3(0.05, 1.85, hd - 0.12),
                Vec3(0.18, 0.02, 1.15),
                Vec3(-0.22, 0.02, 1.15),
            ],
        ]

        # ---------------------------------------------------------------------
        # 4. INTERIOR BEDROOM DOOR (Left Wall X = -hw, Z = +0.42) & SLIPPERS
        # ---------------------------------------------------------------------
        door_z = 0.42
        # Door frame
        mesh.add_box(-hw + 0.025, 1.04, door_z - 0.44, 0.05, 2.08, 0.06, "baseboard", layer=2)
        mesh.add_box(-hw + 0.025, 1.04, door_z + 0.44, 0.05, 2.08, 0.06, "baseboard", layer=2)
        mesh.add_box(-hw + 0.025, 2.08, door_z, 0.05, 0.06, 0.94, "baseboard", layer=2)
        # Door leaf
        mesh.add_box(-hw + 0.022, 1.02, door_z, 0.032, 2.02, 0.82, "door_wood", layer=2)
        # Chrome lever handle
        mesh.add_box(-hw + 0.055, 0.98, door_z + 0.30, 0.04, 0.025, 0.11, "metal_chrome", layer=2)

        # Pair of neat Japanese indoor slippers waiting near the door
        for sz_off in (-0.11, 0.11):
            mesh.add_box(-hw + 0.28, 0.022, door_z + sz_off, 0.24, 0.028, 0.09, "bed_duvet", layer=2, yaw=0.08)
            mesh.add_box(-hw + 0.25, 0.044, door_z + sz_off, 0.11, 0.026, 0.088, "curtain_heavy", layer=2, yaw=0.08)

        # ---------------------------------------------------------------------
        # 5. JAPANESE WALL-MOUNTED SPLIT AC UNIT & FRAMED WALL ART
        # ---------------------------------------------------------------------
        # AC indoor unit mounted high on left wall near window
        mesh.add_box(-hw + 0.12, 2.26, 1.62, 0.22, 0.27, 0.82, "ac_plastic", layer=2)
        mesh.add_box(-hw + 0.225, 2.15, 1.62, 0.02, 0.03, 0.72, "metal_dark", layer=2)  # Air vent louver

        # Framed minimalist artwork above desk on right wall (X = +hw)
        mesh.add_box(hw - 0.018, 1.54, 0.0, 0.03, 0.68, 0.52, "metal_dark", layer=2)
        mesh.add_box(hw - 0.028, 1.54, 0.0, 0.015, 0.60, 0.44, "poster_art", layer=2)

        # Electrical wall outlet plate near nightstand
        mesh.add_box(-0.70, 0.32, -hd + 0.012, 0.08, 0.12, 0.015, "ac_plastic", layer=2)

        return light_shafts

    @staticmethod
    def _add_tessellated_plate(
        mesh: StaticMesh,
        x0: float,
        x1: float,
        z0: float,
        z1: float,
        y: float,
        nx: int,
        nz: int,
        mat_name: str,
        layer: int = 1,
    ) -> None:
        dx = (x1 - x0) / nx
        dz = (z1 - z0) / nz
        for ix in range(nx):
            xa = x0 + ix * dx
            xb = xa + dx
            for iz in range(nz):
                za = z0 + iz * dz
                zb = za + dz
                v0 = mesh.add_vert(Vec3(xa, y, za))
                v1 = mesh.add_vert(Vec3(xa, y, zb))
                v2 = mesh.add_vert(Vec3(xb, y, zb))
                v3 = mesh.add_vert(Vec3(xb, y, za))
                grad = 0.30 + 0.35 * ((ix + iz) / max(1, nx + nz - 2))
                mesh.add_quad(v0, v1, v2, v3, mat_name, grad, grad, layer=layer)

    @staticmethod
    def _add_wall_grid(
        mesh: StaticMesh,
        origin: Vec3,
        u_dir: Vec3,
        u_len: float,
        u_divs: int,
        v_dir: Vec3,
        v_len: float,
        v_divs: int,
        mat_name: str,
        layer: int = 0,
    ) -> None:
        du = u_len / u_divs
        dv = v_len / v_divs
        grid: List[List[int]] = []
        for iv in range(v_divs + 1):
            row: List[int] = []
            for iu in range(u_divs + 1):
                p = origin + u_dir * (iu * du) + v_dir * (iv * dv)
                row.append(mesh.add_vert(p))
            grid.append(row)

        for iv in range(v_divs):
            grad = 0.72 - 0.52 * (iv / max(1, v_divs - 1))
            for iu in range(u_divs):
                # (grid[iv][iu] -> grid[iv][iu+1] -> grid[iv+1][iu+1] -> grid[iv+1][iu])
                # Cross: u_dir x v_dir points INWARD toward room interior!
                mesh.add_quad(
                    grid[iv][iu],
                    grid[iv][iu + 1],
                    grid[iv + 1][iu + 1],
                    grid[iv + 1][iu],
                    mat_name,
                    grad,
                    grad * 0.92,
                    layer=layer,
                )

    @staticmethod
    def _build_pleated_curtain(
        mesh: StaticMesh,
        x_start: float,
        x_end: float,
        y_bot: float,
        y_top: float,
        z_base: float,
        pleats: int,
    ) -> None:
        cols = pleats * 2
        rows = 4
        dx = (x_end - x_start) / cols
        grid: List[List[int]] = []
        for r in range(rows + 1):
            y = lerp(y_bot, y_top, r / rows)
            row: List[int] = []
            for c in range(cols + 1):
                x = x_start + c * dx
                wave = math.sin((c / cols) * pleats * TAU) * 0.045
                row.append(mesh.add_vert(Vec3(x, y, z_base + wave)))
            grid.append(row)

        for r in range(rows):
            grad = 0.78 - 0.56 * (r / max(1, rows - 1))
            for c in range(cols):
                mesh.add_quad(
                    grid[r][c],
                    grid[r + 1][c],
                    grid[r + 1][c + 1],
                    grid[r][c + 1],
                    "curtain_heavy",
                    grad,
                    grad,
                    layer=2,
                )


# =============================================================================
# WORLD GEOMETRY PART 2: FURNITURE, LAMPS & INTERACTIVE CIGARETTE PACK / LIGHTER
# =============================================================================

class CigarettePackProp:
    """Interactive flip-top cigarette pack resting on the desk."""

    def __init__(self, pos: Vec3) -> None:
        self.pos = pos.copy()
        self.yaw = -0.35
        self.remaining_cigs = 14
        self.lid_open_t = 0.0  # Animates open briefly when taking a cigarette

    def get_grab_target_world(self) -> Vec3:
        return self.pos + Vec3(0.0, 0.065, 0.0)

    def render(self, renderer: SceneRenderer, materials: Dict[str, Material], lighting: LightingRig) -> None:
        m = StaticMesh()
        cx, cy, cz = self.pos.x, self.pos.y, self.pos.z
        # Main lower pack body (5.5cm x 6.2cm x 2.4cm scaled slightly for crisp visibility)
        m.add_box(cx, cy + 0.032, cz, 0.064, 0.064, 0.028, "cig_pack_body", layer=2, yaw=self.yaw)
        # Signature navy-blue Japanese brand band
        m.add_box(cx, cy + 0.024, cz, 0.066, 0.026, 0.030, "cig_pack_band", layer=2, yaw=self.yaw)
        # Gold foil rim peeking at top
        m.add_box(cx, cy + 0.065, cz, 0.058, 0.008, 0.022, "cig_pack_gold", layer=2, yaw=self.yaw)

        # Visible cigarette filters inside when lid opens
        if self.lid_open_t > 0.05:
            q = Quat.from_axis_angle(VEC3_UP, self.yaw)
            for k in range(4):
                off = q.rotate_vec(Vec3(-0.018 + k * 0.012, 0.072, 0.0))
                m.add_cylinder(
                    Vec3(cx + off.x, cy + 0.062, cz + off.z),
                    Vec3(cx + off.x, cy + 0.078, cz + off.z),
                    0.0042, 0.0042, 5, "cig_filter", layer=2,
                )

        # Hinged flip-top lid
        lid_pitch = -self.lid_open_t * 1.45
        q_yaw = Quat.from_axis_angle(VEC3_UP, self.yaw)
        hinge_local = Vec3(0.0, 0.064, -0.014)
        hinge_world = self.pos + q_yaw.rotate_vec(hinge_local)
        lid_rot = (q_yaw * Quat.from_axis_angle(Vec3(1.0, 0.0, 0.0), lid_pitch)).normalized()
        lid_center = hinge_world + lid_rot.rotate_vec(Vec3(0.0, 0.013, 0.014))
        # Render lid box rotated via yaw & pitch
        hx, hy, hz = 0.0325, 0.013, 0.0145
        corners = [
            Vec3(-hx, -hy, -hz), Vec3(hx, -hy, -hz), Vec3(hx, hy, -hz), Vec3(-hx, hy, -hz),
            Vec3(-hx, -hy,  hz), Vec3(hx, -hy,  hz), Vec3(hx, hy,  hz), Vec3(-hx, hy,  hz),
        ]
        base = len(m.verts)
        for c in corners:
            m.verts.append(lid_center + lid_rot.rotate_vec(c))
        m.add_quad(base + 4, base + 5, base + 6, base + 7, "cig_pack_body", 0.3, 0.5, layer=2)
        m.add_quad(base + 1, base + 0, base + 3, base + 2, "cig_pack_body", 0.3, 0.5, layer=2)
        m.add_quad(base + 5, base + 1, base + 2, base + 6, "cig_pack_band", 0.3, 0.5, layer=2)
        m.add_quad(base + 0, base + 4, base + 7, base + 3, "cig_pack_band", 0.3, 0.5, layer=2)
        m.add_quad(base + 7, base + 6, base + 2, base + 3, "cig_pack_body", 0.2, 0.3, layer=2)

        m.render(renderer, materials, lighting)


class LighterProp:
    """Interactive chrome flip-lighter resting beside a small ashtray on the low table."""

    def __init__(self, pos: Vec3) -> None:
        self.pos = pos.copy()
        self.yaw = 0.55
        self.cap_open_t = 0.0
        self.flame_strength = 0.0
        self.active_world_pos: Optional[Vec3] = None  # Overridden when held during lighting
        self.active_world_rot: Optional[Quat] = None

    def get_grab_target_world(self) -> Vec3:
        return self.pos + Vec3(0.0, 0.035, 0.0)

    def get_flame_world_pos(self) -> Vec3:
        base_pos = self.active_world_pos if self.active_world_pos is not None else self.pos
        rot = self.active_world_rot if self.active_world_rot is not None else Quat.from_axis_angle(VEC3_UP, self.yaw)
        return base_pos + rot.rotate_vec(Vec3(0.0, 0.088, 0.0))

    def render(self, renderer: SceneRenderer, materials: Dict[str, Material], lighting: LightingRig, elapsed: float) -> None:
        m = StaticMesh()
        base_pos = self.active_world_pos if self.active_world_pos is not None else self.pos
        rot = self.active_world_rot if self.active_world_rot is not None else Quat.from_axis_angle(VEC3_UP, self.yaw)

        def add_oriented_box(local_c: Vec3, sx: float, sy: float, sz: float, mat_name: str, extra_rot: Optional[Quat] = None) -> None:
            hx, hy, hz = sx * 0.5, sy * 0.5, sz * 0.5
            r_eff = (rot * extra_rot).normalized() if extra_rot is not None else rot
            c_world = base_pos + rot.rotate_vec(local_c)
            b_idx = len(m.verts)
            for cx_s in (-hx, hx):
                pass
            corners = [
                Vec3(-hx, -hy, -hz), Vec3(hx, -hy, -hz), Vec3(hx, hy, -hz), Vec3(-hx, hy, -hz),
                Vec3(-hx, -hy,  hz), Vec3(hx, -hy,  hz), Vec3(hx, hy,  hz), Vec3(-hx, hy,  hz),
            ]
            for c in corners:
                m.verts.append(c_world + r_eff.rotate_vec(c))
            m.add_quad(b_idx + 4, b_idx + 5, b_idx + 6, b_idx + 7, mat_name, 0.3, 0.6, layer=2)
            m.add_quad(b_idx + 1, b_idx + 0, b_idx + 3, b_idx + 2, mat_name, 0.3, 0.6, layer=2)
            m.add_quad(b_idx + 5, b_idx + 1, b_idx + 2, b_idx + 6, mat_name, 0.3, 0.6, layer=2)
            m.add_quad(b_idx + 0, b_idx + 4, b_idx + 7, b_idx + 3, mat_name, 0.3, 0.6, layer=2)
            m.add_quad(b_idx + 7, b_idx + 6, b_idx + 2, b_idx + 3, mat_name, 0.2, 0.4, layer=2)
            m.add_quad(b_idx + 0, b_idx + 1, b_idx + 5, b_idx + 4, mat_name, 0.7, 0.8, layer=2)

        # Chrome lighter casing
        add_oriented_box(Vec3(0.0, 0.025, 0.0), 0.038, 0.048, 0.015, "metal_chrome")
        # Brass chimney & flint wheel
        add_oriented_box(Vec3(-0.004, 0.056, 0.0), 0.014, 0.016, 0.011, "brass_warm")
        add_oriented_box(Vec3(0.011, 0.055, 0.0), 0.010, 0.010, 0.008, "metal_dark")

        # Hinged cap
        cap_ang = self.cap_open_t * 1.95
        cap_rot = Quat.from_axis_angle(Vec3(0.0, 0.0, 1.0), cap_ang)
        cap_offset = Vec3(-0.019, 0.049, 0.0) + cap_rot.rotate_vec(Vec3(0.019, 0.008, 0.0))
        add_oriented_box(cap_offset, 0.038, 0.016, 0.015, "metal_chrome", extra_rot=cap_rot)

        m.render(renderer, materials, lighting)

        # Dynamic flickering lighter flame cone
        if self.flame_strength > 0.05:
            f_pos = self.get_flame_world_pos()
            sway = math.sin(elapsed * 26.0) * 0.004 * self.flame_strength
            h = 0.036 * self.flame_strength
            w = 0.009 * self.flame_strength
            tip = f_pos + Vec3(sway, h, sway * 0.5)
            b0 = f_pos + Vec3(-w, 0.0, 0.0)
            b1 = f_pos + Vec3(0.0, 0.0, w)
            b2 = f_pos + Vec3(w, 0.0, 0.0)
            b3 = f_pos + Vec3(0.0, 0.0, -w)
            f_mat = materials["lighter_flame"]
            for p_a, p_b in ((b0, b1), (b1, b2), (b2, b3), (b3, b0)):
                n = (p_b - p_a).cross(tip - p_a).normalized()
                renderer.submit_triangle(p_a, p_b, tip, n, f_mat, lighting, layer=3, grad_t=0.2, depth_bias=-0.035)


class BedroomFurnitureBuilder:
    """Populates the contemporary Japanese bedroom with furniture & props."""

    @staticmethod
    def build_furniture(mesh: StaticMesh, lighting: LightingRig) -> Tuple[CigarettePackProp, LighterProp]:
        # ---------------------------------------------------------------------
        # 1. LOW PLATFORM BED (X in [-2.44, -1.02], Z in [-2.28, -0.18])
        # ---------------------------------------------------------------------
        # Walnut platform base
        mesh.add_box(-1.73, 0.14, -1.23, 1.40, 0.24, 2.08, "bed_frame", layer=2)
        # Minimalist headboard against back accent wall
        mesh.add_box(-1.73, 0.56, -2.23, 1.44, 0.72, 0.08, "bed_frame", layer=2)
        # Mattress with crisp white sheet
        mesh.add_box(-1.73, 0.35, -1.20, 1.32, 0.20, 1.98, "bed_sheet", layer=2)
        # Folded indigo-slate duvet covering lower 70% of mattress
        mesh.add_box(-1.73, 0.39, -0.86, 1.36, 0.17, 1.34, "bed_duvet", layer=2)
        # Two plump pillows near headboard
        mesh.add_box(-2.03, 0.50, -1.96, 0.54, 0.11, 0.34, "bed_sheet", layer=2, yaw=0.04)
        mesh.add_box(-1.43, 0.50, -1.96, 0.54, 0.11, 0.34, "bed_sheet", layer=2, yaw=-0.05)

        # ---------------------------------------------------------------------
        # 2. BEDSIDE NIGHTSTAND & WARM AMBER LAMP (X in [-0.96, -0.44], Z in [-2.28, -1.74])
        # ---------------------------------------------------------------------
        ns_x, ns_z = -0.70, -2.01
        mesh.add_box(ns_x, 0.31, ns_z, 0.50, 0.60, 0.50, "bed_frame", layer=2)
        mesh.add_box(ns_x, 0.44, ns_z + 0.252, 0.44, 0.20, 0.018, "door_wood", layer=2)  # Drawer face
        mesh.add_box(ns_x, 0.44, ns_z + 0.268, 0.12, 0.018, 0.018, "metal_chrome", layer=2)  # Handle

        # Bedside lamp on nightstand (aligns lighting.bedside_lamp.pos cleanly!)
        lamp_x, lamp_y, lamp_z = ns_x, 0.61, ns_z
        mesh.add_cylinder(Vec3(lamp_x, lamp_y, lamp_z), Vec3(lamp_x, lamp_y + 0.025, lamp_z), 0.09, 0.08, 10, "metal_dark", layer=2)
        mesh.add_cylinder(Vec3(lamp_x, lamp_y + 0.025, lamp_z), Vec3(lamp_x, lamp_y + 0.20, lamp_z), 0.015, 0.015, 8, "brass_warm", layer=2)
        mesh.add_cylinder(
            Vec3(lamp_x, lamp_y + 0.17, lamp_z),
            Vec3(lamp_x, lamp_y + 0.34, lamp_z),
            0.135, 0.095, 12, "lamp_shade_warm", cap_bottom=False, cap_top=True, layer=2,
        )
        lighting.bedside_lamp.pos = Vec3(lamp_x, lamp_y + 0.23, lamp_z)

        # ---------------------------------------------------------------------
        # 3. WARDROBE / CLOSET (X in [0.98, 2.46], Z in [-2.30, -1.66])
        # ---------------------------------------------------------------------
        mesh.add_box(1.72, 1.07, -1.98, 1.48, 2.14, 0.62, "door_wood", layer=2)
        # Double door seam & slender aluminum handles
        mesh.add_box(1.72, 1.07, -1.668, 0.012, 2.08, 0.010, "metal_dark", layer=2)
        mesh.add_box(1.66, 1.04, -1.660, 0.016, 0.28, 0.022, "metal_chrome", layer=2)
        mesh.add_box(1.78, 1.04, -1.660, 0.016, 0.28, 0.022, "metal_chrome", layer=2)

        # ---------------------------------------------------------------------
        # 4. MODERN DESK, CHAIR & CLUTTER (X in [1.74, 2.46], Z in [-0.75, 0.75])
        # ---------------------------------------------------------------------
        # Tabletop
        mesh.add_box(2.10, 0.76, 0.0, 0.72, 0.04, 1.50, "bed_frame", layer=2)
        # Four steel desk legs
        for lx in (1.79, 2.41):
            for lz in (-0.69, 0.69):
                mesh.add_box(lx, 0.37, lz, 0.04, 0.74, 0.04, "metal_dark", layer=2)
        # Closed laptop & stacked books on desk
        mesh.add_box(2.14, 0.79, -0.18, 0.26, 0.018, 0.34, "metal_dark", layer=2, yaw=0.06)
        mesh.add_box(2.22, 0.80, -0.54, 0.22, 0.04, 0.16, "curtain_heavy", layer=2, yaw=-0.12)
        mesh.add_box(2.21, 0.835, -0.53, 0.20, 0.03, 0.15, "bed_duvet", layer=2, yaw=0.14)

        # Minimalist desk chair tucked neatly near center of desk
        ch_x, ch_z = 1.50, 0.02
        mesh.add_box(ch_x, 0.45, ch_z, 0.44, 0.045, 0.44, "wall_accent", layer=2, yaw=0.18)
        mesh.add_box(ch_x - 0.19, 0.66, ch_z - 0.03, 0.04, 0.42, 0.42, "wall_accent", layer=2, yaw=0.18)
        for leg_x in (-0.17, 0.17):
            for leg_z in (-0.17, 0.17):
                mesh.add_cylinder(
                    Vec3(ch_x + leg_x, 0.0, ch_z + leg_z),
                    Vec3(ch_x + leg_x, 0.44, ch_z + leg_z),
                    0.014, 0.014, 6, "metal_dark", layer=2,
                )

        # ---------------------------------------------------------------------
        # 5. STANDING CORNER FLOOR LAMP (X = 1.92, Z = 1.56)
        # ---------------------------------------------------------------------
        fl_x, fl_z = 1.92, 1.56
        mesh.add_cylinder(Vec3(fl_x, 0.0, fl_z), Vec3(fl_x, 0.03, fl_z), 0.20, 0.18, 12, "metal_dark", layer=2)
        mesh.add_cylinder(Vec3(fl_x, 0.03, fl_z), Vec3(fl_x, 1.48, fl_z), 0.018, 0.016, 8, "metal_dark", layer=2)
        mesh.add_cylinder(
            Vec3(fl_x, 1.42, fl_z), Vec3(fl_x, 1.72, fl_z),
            0.19, 0.16, 14, "lamp_shade_tall", cap_bottom=False, cap_top=True, layer=2,
        )
        lighting.floor_lamp.pos = Vec3(fl_x, 1.56, fl_z)

        # ---------------------------------------------------------------------
        # 6. LOW SIDE TABLE NEAR WINDOW & ASHTRAY (X in [-2.22, -1.50], Z in [1.08, 1.78])
        # ---------------------------------------------------------------------
        lt_x, lt_z = -1.86, 1.43
        mesh.add_box(lt_x, 0.42, lt_z, 0.72, 0.038, 0.70, "bed_frame", layer=2)
        for lx in (-0.30, 0.30):
            for lz in (-0.29, 0.29):
                mesh.add_box(lt_x + lx, 0.20, lt_z + lz, 0.04, 0.40, 0.04, "metal_dark", layer=2)
        # Minimalist ceramic ashtray beside lighter
        mesh.add_cylinder(Vec3(lt_x + 0.10, 0.44, lt_z - 0.14), Vec3(lt_x + 0.10, 0.465, lt_z - 0.14), 0.055, 0.062, 10, "metal_dark", layer=2)

        # ---------------------------------------------------------------------
        # 7. INTERACTIVE PROPS: CIGARETTE PACK (on Desk) & LIGHTER (on Low Table)
        # ---------------------------------------------------------------------
        cig_pack = CigarettePackProp(Vec3(1.86, 0.78, 0.44))
        lighter = LighterProp(Vec3(lt_x + 0.20, 0.44, lt_z + 0.04))

        return cig_pack, lighter


# =============================================================================
# CORE LOCOMOTION, BLINK/GAZE & CIGARETTE HAND OVERLAY ANIMATIONS
# =============================================================================

class CoreLocomotionAnimator:
    """
    Produces Uncharted 2 / Red Dead Redemption 2 / Heavy Rain caliber
    grounded locomotion with pelvic weight transfer, spine counter-rotation,
    knee/ankle articulation, and follow-through inertia.
    """

    @staticmethod
    def eval_idle(pose: Pose, elapsed: float, out_pose: Optional[Pose] = None) -> Pose:
        p = out_pose if out_pose is not None else pose
        p.clear()

        breath = math.sin(elapsed * 1.65)
        micro_sway = math.sin(elapsed * 0.72)
        micro_yaw = math.sin(elapsed * 0.43 + 0.8)

        # Relaxed feminine contrapposto weight shift slightly onto right leg
        p.local_pos_offset[BoneID.PELVIS] = Vec3(0.010 * micro_sway, -0.008 + breath * 0.003, 0.0)
        p.set_rot_euler(BoneID.PELVIS, 0.02, -0.04 + micro_yaw * 0.03, -0.035 + micro_sway * 0.015)

        p.set_rot_euler(BoneID.SPINE_LOWER, -0.02 + breath * 0.012, 0.02, 0.025 - micro_sway * 0.012)
        p.set_rot_euler(BoneID.SPINE_UPPER, 0.01 + breath * 0.015, 0.02, 0.012)
        p.set_rot_euler(BoneID.CHEST, 0.02 + breath * 0.018, 0.01, 0.0)
        p.set_rot_euler(BoneID.NECK, 0.03 - breath * 0.008, -0.02, 0.0)
        p.set_rot_euler(BoneID.HEAD, -0.03 - breath * 0.010, 0.04 + micro_yaw * 0.04, 0.015 * micro_sway)

        # Shoulders & relaxed arms hanging naturally with gentle curve
        p.set_rot_euler(BoneID.CLAVICLE_L, 0.0, 0.0, -0.04 + breath * 0.012)
        p.set_rot_euler(BoneID.CLAVICLE_R, 0.0, 0.0, 0.04 - breath * 0.012)

        p.set_rot_euler(BoneID.UPPER_ARM_L, -0.03, 0.04, 0.09 + breath * 0.015)
        p.set_rot_euler(BoneID.FOREARM_L, -0.18 - breath * 0.02, 0.0, -0.06)
        p.set_rot_euler(BoneID.HAND_L, 0.0, -0.08, -0.08)

        p.set_rot_euler(BoneID.UPPER_ARM_R, -0.04, -0.04, -0.09 - breath * 0.015)
        p.set_rot_euler(BoneID.FOREARM_R, -0.20 - breath * 0.02, 0.0, 0.06)
        p.set_rot_euler(BoneID.HAND_R, 0.0, 0.08, 0.08)

        # Grounded legs (right leg slightly planted, left knee softly unlocked)
        p.set_rot_euler(BoneID.THIGH_L, -0.06, 0.05, 0.035)
        p.set_rot_euler(BoneID.SHIN_L, 0.12, 0.0, 0.0)
        p.set_rot_euler(BoneID.FOOT_L, -0.06, 0.04, -0.02)

        p.set_rot_euler(BoneID.THIGH_R, 0.03, -0.03, -0.025)
        p.set_rot_euler(BoneID.SHIN_R, 0.04, 0.0, 0.0)
        p.set_rot_euler(BoneID.FOOT_R, -0.04, -0.03, 0.02)
        return p

    @staticmethod
    def eval_walk(
        pose: Pose,
        stride_phase: float,
        speed_weight: float,
        turn_lean: float,
        fwd_lean: float,
        out_pose: Optional[Pose] = None,
    ) -> Pose:
        p = out_pose if out_pose is not None else pose
        p.clear()

        s = math.sin(stride_phase)
        c = math.cos(stride_phase)
        s2 = math.sin(stride_phase * 2.0)
        c2 = math.cos(stride_phase * 2.0)

        amp = clamp(speed_weight, 0.35, 1.05)

        # Double-frequency vertical stride bob (lowest at double-support, highest at passing)
        bob_y = -0.020 * amp + c2 * -0.016 * amp
        hip_sway_x = s * 0.018 * amp
        p.local_pos_offset[BoneID.PELVIS] = Vec3(hip_sway_x, bob_y, 0.0)

        # Pelvis twist & gentle hip drop
        pelvis_yaw = s * 0.11 * amp
        pelvis_roll = -s * 0.055 * amp + turn_lean * 0.45
        p.set_rot_euler(BoneID.PELVIS, 0.04 + fwd_lean * 0.35, pelvis_yaw, pelvis_roll)

        # Counter-rotating torso for fluid natural human gait
        p.set_rot_euler(BoneID.SPINE_LOWER, 0.02 + fwd_lean * 0.25, -pelvis_yaw * 0.45, -pelvis_roll * 0.4 + turn_lean * 0.35)
        p.set_rot_euler(BoneID.SPINE_UPPER, 0.02 + fwd_lean * 0.20, -pelvis_yaw * 0.45, -pelvis_roll * 0.35)
        p.set_rot_euler(BoneID.CHEST, 0.02 + s2 * 0.015, -pelvis_yaw * 0.40, turn_lean * 0.20)
        p.set_rot_euler(BoneID.NECK, -fwd_lean * 0.35, pelvis_yaw * 0.20, -turn_lean * 0.25)
        p.set_rot_euler(BoneID.HEAD, -fwd_lean * 0.30, pelvis_yaw * 0.15, -turn_lean * 0.25)

        # Counter-swinging arms (Left arm swings forward when Right leg swings forward -> phase +pi)
        arm_swing = 0.34 * amp
        p.set_rot_euler(BoneID.CLAVICLE_L, 0.0, s * 0.05 * amp, -0.03)
        p.set_rot_euler(BoneID.UPPER_ARM_L, s * arm_swing, 0.04, 0.08)
        elbow_l = -0.26 - max(0.0, -s) * 0.22 * amp
        p.set_rot_euler(BoneID.FOREARM_L, elbow_l, 0.0, -0.04)
        p.set_rot_euler(BoneID.HAND_L, 0.04, -0.06, -0.05)

        p.set_rot_euler(BoneID.CLAVICLE_R, 0.0, s * 0.05 * amp, 0.03)
        p.set_rot_euler(BoneID.UPPER_ARM_R, -s * arm_swing, -0.04, -0.08)
        elbow_r = -0.26 - max(0.0, s) * 0.22 * amp
        p.set_rot_euler(BoneID.FOREARM_R, elbow_r, 0.0, 0.04)
        p.set_rot_euler(BoneID.HAND_R, 0.04, 0.06, 0.05)

        # Legs: Left leg at phase, Right leg at phase + pi
        CoreLocomotionAnimator._eval_walk_leg(p, stride_phase, amp, is_left=True)
        CoreLocomotionAnimator._eval_walk_leg(p, stride_phase + math.pi, amp, is_left=False)
        return p

    @staticmethod
    def _eval_walk_leg(pose: Pose, phase: float, amp: float, is_left: bool) -> None:
        th_b = BoneID.THIGH_L if is_left else BoneID.THIGH_R
        sh_b = BoneID.SHIN_L if is_left else BoneID.SHIN_R
        ft_b = BoneID.FOOT_L if is_left else BoneID.FOOT_R
        toe_b = BoneID.TOE_L if is_left else BoneID.TOE_R
        side = 1.0 if is_left else -1.0

        # Negative pitch_x = swing thigh forward
        thigh_pitch = -math.sin(phase) * 0.44 * amp - 0.03
        # Knee bends strongly during swing phase (when cos(phase) > 0 as leg passes forward)
        swing_lift = max(0.0, math.cos(phase - 0.35))
        stance_cushion = max(0.0, -math.sin(phase - 0.5)) * 0.14
        shin_pitch = (0.06 + swing_lift * 0.72 + stance_cushion) * amp

        # Ankle plantarflexes on push-off, dorsiflexes on heel strike
        foot_pitch = math.sin(phase - 0.55) * 0.26 * amp - shin_pitch * 0.35 - thigh_pitch * 0.25
        toe_pitch = -max(0.0, -math.cos(phase)) * 0.28 * amp

        pose.set_rot_euler(th_b, thigh_pitch, side * 0.02, side * 0.02)
        pose.set_rot_euler(sh_b, shin_pitch, 0.0, 0.0)
        pose.set_rot_euler(ft_b, foot_pitch, 0.0, 0.0)
        pose.set_rot_euler(toe_b, toe_pitch, 0.0, 0.0)

    @staticmethod
    def eval_run(
        pose: Pose,
        stride_phase: float,
        speed_weight: float,
        turn_lean: float,
        fwd_lean: float,
        out_pose: Optional[Pose] = None,
    ) -> Pose:
        p = out_pose if out_pose is not None else pose
        p.clear()

        s = math.sin(stride_phase)
        c2 = math.cos(stride_phase * 2.0)
        amp = clamp(speed_weight, 0.65, 1.05)

        bob_y = -0.042 * amp + c2 * -0.034 * amp
        p.local_pos_offset[BoneID.PELVIS] = Vec3(s * 0.015, bob_y, 0.0)

        pelvis_yaw = s * 0.15 * amp
        p.set_rot_euler(BoneID.PELVIS, 0.14 + fwd_lean * 0.6, pelvis_yaw, -s * 0.06 + turn_lean * 0.7)
        p.set_rot_euler(BoneID.SPINE_LOWER, 0.08, -pelvis_yaw * 0.5, turn_lean * 0.45)
        p.set_rot_euler(BoneID.SPINE_UPPER, 0.08, -pelvis_yaw * 0.5, turn_lean * 0.25)
        p.set_rot_euler(BoneID.CHEST, 0.06, -pelvis_yaw * 0.4, 0.0)
        p.set_rot_euler(BoneID.NECK, -0.14, pelvis_yaw * 0.2, -turn_lean * 0.4)
        p.set_rot_euler(BoneID.HEAD, -0.14, pelvis_yaw * 0.1, -turn_lean * 0.4)

        # Crisp athletic bent-elbow arm pump
        arm_swing = 0.72 * amp
        p.set_rot_euler(BoneID.CLAVICLE_L, 0.0, s * 0.08, -0.04)
        p.set_rot_euler(BoneID.UPPER_ARM_L, s * arm_swing + 0.08, 0.08, 0.12)
        p.set_rot_euler(BoneID.FOREARM_L, -1.18 - max(0.0, -s) * 0.25, 0.0, -0.10)
        p.set_rot_euler(BoneID.HAND_L, 0.0, -0.12, -0.08)

        p.set_rot_euler(BoneID.CLAVICLE_R, 0.0, s * 0.08, 0.04)
        p.set_rot_euler(BoneID.UPPER_ARM_R, -s * arm_swing + 0.08, -0.08, -0.12)
        p.set_rot_euler(BoneID.FOREARM_R, -1.18 - max(0.0, s) * 0.25, 0.0, 0.10)
        p.set_rot_euler(BoneID.HAND_R, 0.0, 0.12, 0.08)

        CoreLocomotionAnimator._eval_run_leg(p, stride_phase, amp, is_left=True)
        CoreLocomotionAnimator._eval_run_leg(p, stride_phase + math.pi, amp, is_left=False)
        return p

    @staticmethod
    def _eval_run_leg(pose: Pose, phase: float, amp: float, is_left: bool) -> None:
        th_b = BoneID.THIGH_L if is_left else BoneID.THIGH_R
        sh_b = BoneID.SHIN_L if is_left else BoneID.SHIN_R
        ft_b = BoneID.FOOT_L if is_left else BoneID.FOOT_R
        toe_b = BoneID.TOE_L if is_left else BoneID.TOE_R
        side = 1.0 if is_left else -1.0

        thigh_pitch = -math.sin(phase) * 0.76 * amp - 0.12
        swing_bend = max(0.0, math.cos(phase - 0.45))
        shin_pitch = (0.14 + swing_bend * 1.25) * amp
        foot_pitch = math.sin(phase - 0.5) * 0.34 - shin_pitch * 0.32 - thigh_pitch * 0.20
        toe_pitch = -max(0.0, -math.cos(phase)) * 0.36

        pose.set_rot_euler(th_b, thigh_pitch, 0.0, side * 0.025)
        pose.set_rot_euler(sh_b, shin_pitch, 0.0, 0.0)
        pose.set_rot_euler(ft_b, foot_pitch, 0.0, 0.0)
        pose.set_rot_euler(toe_b, toe_pitch, 0.0, 0.0)

    @staticmethod
    def apply_pivot_overlay(pose: Pose, pivot_timer: float, pivot_dir: float) -> None:
        if pivot_timer <= 0.001:
            return
        t = clamp01(pivot_timer / 0.34)
        arch = math.sin(t * math.pi)
        pose.local_pos_offset[BoneID.PELVIS].y -= 0.045 * arch
        pose.add_rot_euler(BoneID.SPINE_UPPER, 0.06 * arch, -pivot_dir * 0.28 * arch, pivot_dir * 0.10 * arch)
        pose.add_rot_euler(BoneID.CHEST, 0.04 * arch, -pivot_dir * 0.24 * arch, 0.0)
        pose.add_rot_euler(BoneID.THIGH_L, -0.14 * arch, 0.0, 0.04 * arch)
        pose.add_rot_euler(BoneID.SHIN_L, 0.28 * arch, 0.0, 0.0)
        pose.add_rot_euler(BoneID.THIGH_R, -0.14 * arch, 0.0, -0.04 * arch)
        pose.add_rot_euler(BoneID.SHIN_R, 0.28 * arch, 0.0, 0.0)

    @staticmethod
    def apply_cigarette_finger_hold(pose: Pose, weight: float, elapsed: float, is_moving: bool) -> None:
        """
        Poses her right arm gracefully when holding a cigarette between her fingers.
        Used both during idle/walk and to lock/exclude the smoking hand during dances.
        """
        w = clamp01(weight)
        if w <= 0.001:
            return
        cig_pose = Pose()
        cig_pose.copy_from(pose)
        sway = math.sin(elapsed * 1.7) * (0.04 if not is_moving else 0.06)
        cig_pose.set_rot_euler(BoneID.CLAVICLE_R, 0.0, 0.04, 0.04)
        cig_pose.set_rot_euler(BoneID.UPPER_ARM_R, -0.22 + sway, -0.14, -0.18)
        cig_pose.set_rot_euler(BoneID.FOREARM_R, -1.05 + sway * 0.5, 0.18, 0.24)
        cig_pose.set_rot_euler(BoneID.HAND_R, 0.12, 0.28, -0.14)
        mask = [0.0] * BoneID.COUNT
        for b in (BoneID.CLAVICLE_R, BoneID.UPPER_ARM_R, BoneID.FOREARM_R, BoneID.HAND_R):
            mask[b] = 1.0
        pose.blend_with(cig_pose, w, mask)


class BlinkAndGazeController:
    """Natural involuntary eye blinking & subtle thoughtful eye darts."""

    def __init__(self, seed: int = 42) -> None:
        self._rng = random.Random(seed)
        self._blink_timer = 2.6
        self._blink_phase = 0.0
        self._is_blinking = False
        self._saccade_timer = 1.8
        self._eye_target_yaw = 0.0
        self._eye_target_pitch = 0.0
        self._eye_yaw = 0.0
        self._eye_pitch = 0.0

    def update(self, pose: Pose, dt: float) -> None:
        # Blinking state machine (~160ms close-open curve)
        if self._is_blinking:
            self._blink_phase += dt * 6.4
            if self._blink_phase >= 1.0:
                self._is_blinking = False
                self._blink_phase = 0.0
                # Occasional natural double-blink
                self._blink_timer = 0.16 if self._rng.random() < 0.18 else self._rng.uniform(2.5, 5.2)
            lid_amt = math.sin(self._blink_phase * math.pi)
        else:
            self._blink_timer -= dt
            lid_amt = 0.0
            if self._blink_timer <= 0.0:
                self._is_blinking = True
                self._blink_phase = 0.0

        # Subtle eye saccades
        self._saccade_timer -= dt
        if self._saccade_timer <= 0.0:
            self._saccade_timer = self._rng.uniform(1.1, 3.4)
            self._eye_target_yaw = self._rng.uniform(-0.14, 0.14)
            self._eye_target_pitch = self._rng.uniform(-0.08, 0.07)

        self._eye_yaw = damp(self._eye_yaw, self._eye_target_yaw, 14.0, dt)
        self._eye_pitch = damp(self._eye_pitch, self._eye_target_pitch, 14.0, dt)

        # Eyelid closes downward (+pitch_x) & lowers slightly in Y
        pose.set_rot_euler(BoneID.EYELID_L, lid_amt * 0.95, 0.0, 0.0)
        pose.set_rot_euler(BoneID.EYELID_R, lid_amt * 0.95, 0.0, 0.0)
        pose.local_pos_offset[BoneID.EYELID_L].y = -lid_amt * 0.008
        pose.local_pos_offset[BoneID.EYELID_R].y = -lid_amt * 0.008

        pose.add_rot_euler(BoneID.EYE_L, self._eye_pitch, self._eye_yaw, 0.0)
        pose.add_rot_euler(BoneID.EYE_R, self._eye_pitch, self._eye_yaw, 0.0)


# =============================================================================
# RANDOM IDLE VIGNETTES (>10s) & SMOKING INTERACTION ANIMATION SYSTEM
# =============================================================================

class IdleVignetteType(Enum):
    NONE = auto()
    HIP_WEIGHT_SHIFT = auto()
    BRUSH_HAIR = auto()
    SHOULDER_STRETCH = auto()
    LOOK_AROUND = auto()
    CHECK_HAND = auto()
    SOFT_SIGH = auto()


class IdleVignetteDirector:
    """
    Triggers varied, natural idle vignettes randomly once the player leaves
    controls untouched for >10 seconds. Smoothly blends in & out and yields
    immediately to any movement, dance, or smoking input.
    """

    def __init__(self, seed: int = 108) -> None:
        self._rng = random.Random(seed)
        self.untouched_timer = 0.0
        self.current = IdleVignetteType.NONE
        self.timer = 0.0
        self.duration = 0.0
        self.cooldown = 0.0
        self._last_type = IdleVignetteType.NONE

        self._durations: Dict[IdleVignetteType, float] = {
            IdleVignetteType.HIP_WEIGHT_SHIFT: 4.6,
            IdleVignetteType.BRUSH_HAIR: 3.1,
            IdleVignetteType.SHOULDER_STRETCH: 3.8,
            IdleVignetteType.LOOK_AROUND: 4.4,
            IdleVignetteType.CHECK_HAND: 3.4,
            IdleVignetteType.SOFT_SIGH: 2.9,
        }

    def notify_input(self) -> None:
        self.untouched_timer = 0.0
        if self.current != IdleVignetteType.NONE:
            self.current = IdleVignetteType.NONE
            self.timer = 0.0

    def update(self, is_idle_ready: bool, dt: float) -> None:
        if not is_idle_ready:
            self.untouched_timer = 0.0
            self.current = IdleVignetteType.NONE
            self.timer = 0.0
            return

        self.untouched_timer += dt
        if self.untouched_timer < IDLE_VIGNETTE_DELAY:
            return

        if self.current != IdleVignetteType.NONE:
            self.timer += dt
            if self.timer >= self.duration:
                self.current = IdleVignetteType.NONE
                self.timer = 0.0
                self.cooldown = self._rng.uniform(3.0, 6.5)
            return

        if self.cooldown > 0.0:
            self.cooldown -= dt
            return

        choices = [t for t in self._durations.keys() if t != self._last_type]
        chosen = self._rng.choice(choices)
        self._last_type = chosen
        self.current = chosen
        self.timer = 0.0
        self.duration = self._durations[chosen]

    def apply_to_pose(self, pose: Pose, has_cig_in_fingers: bool) -> None:
        if self.current == IdleVignetteType.NONE or self.duration <= EPSILON:
            return

        u = clamp01(self.timer / self.duration)
        # Smooth bell envelope (0 -> 1 -> 0)
        w = smoothstep(0.0, 0.22, u) * (1.0 - smoothstep(0.76, 1.0, u))
        if w <= 0.001:
            return

        v_pose = Pose()
        v_pose.copy_from(pose)

        if self.current == IdleVignetteType.HIP_WEIGHT_SHIFT:
            v_pose.local_pos_offset[BoneID.PELVIS] = Vec3(-0.028, -0.014, 0.0)
            v_pose.set_rot_euler(BoneID.PELVIS, 0.03, 0.06, 0.085)
            v_pose.set_rot_euler(BoneID.SPINE_LOWER, -0.02, -0.04, -0.06)
            v_pose.set_rot_euler(BoneID.SPINE_UPPER, 0.01, -0.03, -0.04)
            v_pose.set_rot_euler(BoneID.HEAD, -0.02, 0.14, -0.05)
            # Rest left hand lightly on hip
            v_pose.set_rot_euler(BoneID.UPPER_ARM_L, 0.14, 0.10, 0.34)
            v_pose.set_rot_euler(BoneID.FOREARM_L, -0.95, 0.0, -0.36)
            v_pose.set_rot_euler(BoneID.HAND_L, 0.10, 0.0, -0.22)
            v_pose.set_rot_euler(BoneID.THIGH_L, 0.02, -0.04, -0.03)
            v_pose.set_rot_euler(BoneID.SHIN_L, 0.04, 0.0, 0.0)
            v_pose.set_rot_euler(BoneID.THIGH_R, -0.10, 0.06, -0.06)
            v_pose.set_rot_euler(BoneID.SHIN_R, 0.20, 0.0, 0.0)

        elif self.current == IdleVignetteType.BRUSH_HAIR:
            # Tuck dark-brown hair gracefully behind left ear (keeps right hand free for cig!)
            tuck = math.sin(clamp01((u - 0.15) / 0.70) * math.pi)
            v_pose.set_rot_euler(BoneID.HEAD, 0.06, -0.18, -0.10)
            v_pose.set_rot_euler(BoneID.NECK, 0.04, -0.08, -0.04)
            v_pose.set_rot_euler(BoneID.CLAVICLE_L, 0.0, 0.05, 0.10)
            v_pose.set_rot_euler(BoneID.UPPER_ARM_L, -1.18, 0.24, 0.36)
            v_pose.set_rot_euler(BoneID.FOREARM_L, -1.48 - tuck * 0.14, -0.12, -0.32)
            v_pose.set_rot_euler(BoneID.HAND_L, 0.20, -0.24, -0.15)

        elif self.current == IdleVignetteType.SHOULDER_STRETCH:
            arc = math.sin(u * math.pi)
            v_pose.set_rot_euler(BoneID.SPINE_UPPER, -0.08 * arc, 0.0, 0.0)
            v_pose.set_rot_euler(BoneID.CHEST, -0.10 * arc, 0.0, 0.0)
            v_pose.set_rot_euler(BoneID.HEAD, -0.12 * arc, 0.14 * math.sin(u * TAU), 0.08 * math.sin(u * TAU))
            v_pose.set_rot_euler(BoneID.CLAVICLE_L, 0.0, -0.10 * arc, 0.16 * arc)
            v_pose.set_rot_euler(BoneID.UPPER_ARM_L, 0.12 * arc, 0.0, 0.24 * arc)
            if not has_cig_in_fingers:
                v_pose.set_rot_euler(BoneID.CLAVICLE_R, 0.0, 0.10 * arc, -0.16 * arc)
                v_pose.set_rot_euler(BoneID.UPPER_ARM_R, 0.12 * arc, 0.0, -0.24 * arc)

        elif self.current == IdleVignetteType.LOOK_AROUND:
            pan = math.sin(u * TAU * 0.85)
            v_pose.set_rot_euler(BoneID.SPINE_UPPER, 0.01, pan * 0.12, 0.0)
            v_pose.set_rot_euler(BoneID.CHEST, 0.01, pan * 0.16, 0.0)
            v_pose.set_rot_euler(BoneID.NECK, 0.02, pan * 0.24, 0.0)
            v_pose.set_rot_euler(BoneID.HEAD, -0.04 + 0.05 * math.cos(u * TAU), pan * 0.42, pan * 0.05)

        elif self.current == IdleVignetteType.CHECK_HAND:
            # Inspect left hand fingers softly
            v_pose.set_rot_euler(BoneID.HEAD, 0.18, 0.20, 0.06)
            v_pose.set_rot_euler(BoneID.NECK, 0.10, 0.10, 0.0)
            v_pose.set_rot_euler(BoneID.CLAVICLE_L, 0.0, 0.06, 0.04)
            v_pose.set_rot_euler(BoneID.UPPER_ARM_L, -0.58, -0.26, 0.12)
            v_pose.set_rot_euler(BoneID.FOREARM_L, -1.25, 0.18, -0.20)
            v_pose.set_rot_euler(BoneID.HAND_L, 0.22 * math.sin(u * TAU), -0.35, 0.25)

        elif self.current == IdleVignetteType.SOFT_SIGH:
            inhale = math.sin(clamp01(u / 0.45) * HALF_PI) if u < 0.45 else math.cos(clamp01((u - 0.45) / 0.55) * HALF_PI)
            drop = smoothstep(0.45, 0.90, u)
            v_pose.set_rot_euler(BoneID.CHEST, -0.06 * inhale + 0.07 * drop, 0.0, 0.0)
            v_pose.set_rot_euler(BoneID.HEAD, -0.05 * inhale + 0.14 * drop, 0.04, 0.03 * drop)
            v_pose.set_rot_euler(BoneID.CLAVICLE_L, 0.0, 0.0, 0.07 * inhale - 0.05 * drop)
            v_pose.set_rot_euler(BoneID.CLAVICLE_R, 0.0, 0.0, -0.07 * inhale + 0.05 * drop)

        # Preserve cigarette right hand if holding in fingers
        mask = [1.0] * BoneID.COUNT
        if has_cig_in_fingers:
            for b in (BoneID.CLAVICLE_R, BoneID.UPPER_ARM_R, BoneID.FOREARM_R, BoneID.HAND_R):
                mask[b] = 0.0
        pose.blend_with(v_pose, w, mask)


class SmokingAction(Enum):
    NONE = auto()
    TAKE_CIG = auto()
    SWITCH_TO_MOUTH = auto()
    SWITCH_TO_FINGERS = auto()
    LIGHT_CIG = auto()
    INHALE_DRAG = auto()
    FLICK_ASH = auto()
    DROP_BUTT = auto()


class SmokingInteractionController:
    """
    Coordinates all cigarette & lighter state transitions, timed interaction
    sequences, IK hand reaches, lighter flame/cap animations, and ash drops.
    """

    def __init__(self) -> None:
        self.has_cigarette = False
        self.in_mouth = False
        self.is_lit = False
        self.burn_progress = 0.0     # 0.0 = fresh, 1.0 = finished
        self.ash_length = 0.0        # meters
        self.ember_glow = 0.0
        self.puff_cooldown = 4.5

        self.action = SmokingAction.NONE
        self.action_timer = 0.0
        self.action_duration = 0.0
        self._action_target_pos = Vec3()
        self._action_committed = False

        # Signals consumed by particle & lighting system each frame
        self.emit_exhale_puff = 0.0
        self.drop_ash_event_pos: Optional[Vec3] = None

    def is_movement_locked(self) -> bool:
        return self.action in (SmokingAction.TAKE_CIG, SmokingAction.LIGHT_CIG)

    def can_take_cigarette(self, player_pos: Vec3, pack: CigarettePackProp) -> bool:
        if self.has_cigarette or self.action != SmokingAction.NONE or pack.remaining_cigs <= 0:
            return False
        dx = player_pos.x - pack.pos.x
        dz = player_pos.z - pack.pos.z
        return (dx * dx + dz * dz) <= (INTERACT_DISTANCE * INTERACT_DISTANCE)

    def can_light_cigarette(self, player_pos: Vec3, lighter: LighterProp) -> bool:
        if (not self.has_cigarette) or self.is_lit or self.action != SmokingAction.NONE:
            return False
        dx = player_pos.x - lighter.pos.x
        dz = player_pos.z - lighter.pos.z
        return (dx * dx + dz * dz) <= (INTERACT_DISTANCE * INTERACT_DISTANCE)

    def start_take_cigarette(self, pack: CigarettePackProp) -> None:
        self.action = SmokingAction.TAKE_CIG
        self.action_timer = 0.0
        self.action_duration = 1.25
        self._action_target_pos = pack.get_grab_target_world()
        self._action_committed = False

    def start_toggle_grip_mode(self) -> None:
        if not self.has_cigarette:
            return
        if self.action not in (SmokingAction.NONE, SmokingAction.INHALE_DRAG):
            return
        self.action = SmokingAction.SWITCH_TO_FINGERS if self.in_mouth else SmokingAction.SWITCH_TO_MOUTH
        self.action_timer = 0.0
        self.action_duration = 0.56
        self._action_committed = False

    def start_light_cigarette(self, lighter: LighterProp) -> None:
        self.action = SmokingAction.LIGHT_CIG
        self.action_timer = 0.0
        self.action_duration = 1.90
        self._action_target_pos = lighter.get_grab_target_world()
        self._action_committed = False

    def start_flick_ash(self) -> None:
        if not self.has_cigarette or not self.is_lit:
            return
        if self.action != SmokingAction.NONE:
            return
        self.action = SmokingAction.FLICK_ASH
        self.action_timer = 0.0
        self.action_duration = 0.52
        self._action_committed = False

    def update(
        self,
        dt: float,
        motor: CharacterMotor,
        pack: CigarettePackProp,
        lighter: LighterProp,
        cig_tip_pos: Vec3,
    ) -> None:
        self.emit_exhale_puff = 0.0
        self.drop_ash_event_pos = None

        # Decay pack lid & lighter cap when not actively animating them
        if self.action != SmokingAction.TAKE_CIG:
            pack.lid_open_t = damp(pack.lid_open_t, 0.0, 6.0, dt)
        if self.action != SmokingAction.LIGHT_CIG:
            lighter.cap_open_t = damp(lighter.cap_open_t, 0.0, 7.0, dt)
            lighter.flame_strength = damp(lighter.flame_strength, 0.0, 12.0, dt)
            lighter.active_world_pos = None
            lighter.active_world_rot = None

        # Passive burn & ash accumulation when lit
        if self.has_cigarette and self.is_lit:
            self.burn_progress += dt / CIGARETTE_BURN_SECONDS
            self.ash_length = min(ASH_MAX_LENGTH, self.ash_length + dt * ASH_GROWTH_RATE * 0.08)
            self.ember_glow = damp(self.ember_glow, 0.28, 3.5, dt)

            # Natural periodic drag / puff cycle
            if self.action == SmokingAction.NONE:
                self.puff_cooldown -= dt
                if self.puff_cooldown <= 0.0:
                    self.action = SmokingAction.INHALE_DRAG
                    self.action_timer = 0.0
                    self.action_duration = 1.70
                    self._action_committed = False
                    self.puff_cooldown = CIGARETTE_PUFF_INTERVAL

            # Cigarette ends -> drop butt
            if self.burn_progress >= 1.0 and self.action in (SmokingAction.NONE, SmokingAction.INHALE_DRAG):
                self.action = SmokingAction.DROP_BUTT
                self.action_timer = 0.0
                self.action_duration = 0.72
                self._action_committed = False
        else:
            self.ember_glow = damp(self.ember_glow, 0.0, 8.0, dt)

        # Step active action timeline
        if self.action == SmokingAction.NONE:
            return

        self.action_timer += dt
        u = clamp01(self.action_timer / max(EPSILON, self.action_duration))

        if self.action == SmokingAction.TAKE_CIG:
            # Turn smoothly toward the cigarette pack
            to_pack = self._action_target_pos - motor.pos
            target_yaw = math.atan2(to_pack.x, to_pack.z)
            motor.yaw = damp_angle(motor.yaw, target_yaw, 8.5, dt)
            pack.lid_open_t = math.sin(smoothstep(0.10, 0.85, u) * math.pi)
            if u >= 0.52 and not self._action_committed:
                self._action_committed = True
                self.has_cigarette = True
                self.in_mouth = False
                self.is_lit = False
                self.burn_progress = 0.0
                self.ash_length = 0.0
                pack.remaining_cigs = max(0, pack.remaining_cigs - 1)

        elif self.action == SmokingAction.SWITCH_TO_MOUTH:
            if u >= 0.50 and not self._action_committed:
                self._action_committed = True
                self.in_mouth = True

        elif self.action == SmokingAction.SWITCH_TO_FINGERS:
            if u >= 0.50 and not self._action_committed:
                self._action_committed = True
                self.in_mouth = False

        elif self.action == SmokingAction.LIGHT_CIG:
            to_l = self._action_target_pos - motor.pos
            target_yaw = math.atan2(to_l.x, to_l.z)
            motor.yaw = damp_angle(motor.yaw, target_yaw, 8.5, dt)
            # Flip lighter cap open & spark flame between u=0.35..0.78
            lighter.cap_open_t = smoothstep(0.22, 0.38, u) * (1.0 - smoothstep(0.80, 0.95, u))
            if 0.38 <= u <= 0.78:
                lighter.flame_strength = smoothstep(0.38, 0.45, u) * (1.0 - smoothstep(0.72, 0.78, u))
            else:
                lighter.flame_strength = 0.0
            if u >= 0.62 and not self._action_committed:
                self._action_committed = True
                self.is_lit = True
                self.ember_glow = 1.0
                self.puff_cooldown = 4.2

        elif self.action == SmokingAction.INHALE_DRAG:
            if 0.25 <= u <= 0.58:
                self.ember_glow = lerp(self.ember_glow, 1.0, dt * 8.0)
                self.burn_progress += dt * 0.015
                self.ash_length = min(ASH_MAX_LENGTH, self.ash_length + dt * ASH_GROWTH_RATE)
            if 0.64 <= u <= 0.95:
                self.emit_exhale_puff = math.sin(((u - 0.64) / 0.31) * math.pi)

        elif self.action == SmokingAction.FLICK_ASH:
            if u >= 0.52 and not self._action_committed:
                self._action_committed = True
                if self.ash_length > 0.002:
                    self.drop_ash_event_pos = cig_tip_pos.copy()
                self.ash_length = 0.0

        elif self.action == SmokingAction.DROP_BUTT:
            if u >= 0.58 and not self._action_committed:
                self._action_committed = True
                self.has_cigarette = False
                self.is_lit = False
                self.in_mouth = False
                self.burn_progress = 0.0
                self.ash_length = 0.0
                self.ember_glow = 0.0

        if self.action_timer >= self.action_duration:
            self.action = SmokingAction.NONE
            self.action_timer = 0.0

    def apply_pose_and_ik(
        self,
        pose: Pose,
        skel: Skeleton,
        motor: CharacterMotor,
        lighter: LighterProp,
    ) -> None:
        if self.action == SmokingAction.NONE:
            return

        u = clamp01(self.action_timer / max(EPSILON, self.action_duration))
        # Action-specific pole vectors ensure the elbow bends in the correct
        # direction: outward-forward when reaching UP to the mouth/face,
        # outward-down-backward when reaching DOWN to props on tables.
        yaw_q = Quat.from_axis_angle(VEC3_UP, motor.yaw)
        # Right arm poles (character's right = -X local)
        pole_r_up = yaw_q.rotate_vec(Vec3(-0.85, -0.15, 0.55))    # elbow out-fwd (mouth reach)
        pole_r_down = yaw_q.rotate_vec(Vec3(-0.60, -0.55, -0.60)) # elbow out-back-down (pack reach)
        # Left arm poles (character's left = +X local)
        pole_l_up = yaw_q.rotate_vec(Vec3(0.85, -0.15, 0.55))
        pole_l_down = yaw_q.rotate_vec(Vec3(0.60, -0.55, -0.60))

        if self.action == SmokingAction.TAKE_CIG:
            # Subtle waist lean & right hand IK reaching smoothly onto cigarette pack
            lean = math.sin(u * math.pi)
            pose.add_rot_euler(BoneID.SPINE_LOWER, 0.16 * lean, 0.0, 0.0)
            pose.add_rot_euler(BoneID.SPINE_UPPER, 0.18 * lean, -0.10 * lean, 0.0)
            pose.add_rot_euler(BoneID.HEAD, 0.16 * lean, 0.0, 0.0)
            reach_w = smoothstep(0.08, 0.45, u) * (1.0 - smoothstep(0.60, 0.96, u))
            skel.solve_arm_ik_world(
                pose, motor.pos, motor.yaw, True,
                self._action_target_pos + Vec3(0.0, 0.08, 0.0), pole_r_down, reach_w,
            )

        elif self.action in (SmokingAction.SWITCH_TO_MOUTH, SmokingAction.SWITCH_TO_FINGERS):
            # Bring right hand cleanly up to CIG_SOCKET_MOUTH with elbow bending outward
            w = math.sin(u * math.pi)
            skel.evaluate_fk(pose, motor.pos, motor.yaw)
            mouth_world = skel.world_transforms[BoneID.CIG_SOCKET_MOUTH].pos
            # Target slightly below and in front of the mouth so the hand approaches naturally
            target = mouth_world + Vec3(-0.015, -0.04, 0.035)
            skel.solve_arm_ik_world(pose, motor.pos, motor.yaw, True, target, pole_r_up, w)
            pose.add_rot_euler(BoneID.HEAD, -0.06 * w, -0.08 * w, 0.0)

        elif self.action == SmokingAction.LIGHT_CIG:
            # Phase 1 (0..0.38): reach down to low table to pick up lighter
            # Phase 2 (0.38..0.75): lift lighter up to face/cigarette tip & light!
            # Phase 3 (0.75..1.0): place lighter back on table
            lean = math.sin(clamp01(u / 0.45) * math.pi) * 0.5 + math.sin(clamp01((u - 0.65) / 0.35) * math.pi) * 0.45
            pose.add_rot_euler(BoneID.SPINE_LOWER, 0.24 * lean, 0.0, 0.0)
            pose.add_rot_euler(BoneID.SPINE_UPPER, 0.24 * lean, 0.0, 0.0)
            pose.add_rot_euler(BoneID.HEAD, 0.22 * lean, 0.0, 0.0)

            skel.evaluate_fk(pose, motor.pos, motor.yaw)
            mouth_world = skel.world_transforms[BoneID.CIG_SOCKET_MOUTH].pos
            fwd = Quat.from_axis_angle(VEC3_UP, motor.yaw).rotate_vec(Vec3(0.0, 0.0, 1.0))
            right_v = Quat.from_axis_angle(VEC3_UP, motor.yaw).rotate_vec(Vec3(-1.0, 0.0, 0.0))
            face_light_pt = mouth_world + fwd * 0.085 + Vec3(0.0, -0.04, 0.0)

            if u < 0.35:
                w = smoothstep(0.0, 0.26, u)
                hand_target = self._action_target_pos + Vec3(0.0, 0.06, 0.0)
                skel.solve_arm_ik_world(pose, motor.pos, motor.yaw, False, hand_target, pole_l_down, w)
            elif u < 0.78:
                lift = smoothstep(0.26, 0.44, u) * (1.0 - smoothstep(0.70, 0.86, u))
                hand_target = self._action_target_pos.lerp(face_light_pt, lift)
                # Left hand holds lighter up; right hand holds cig near mouth if in fingers
                # Use upward pole when lifting toward face, downward pole when reaching down
                cur_pole_l = pole_l_up if lift > 0.3 else pole_l_down
                skel.solve_arm_ik_world(pose, motor.pos, motor.yaw, False, hand_target, cur_pole_l, 0.95)
                if not self.in_mouth:
                    cig_pt = mouth_world + right_v * 0.015 + Vec3(0.0, -0.045, 0.025)
                    skel.solve_arm_ik_world(pose, motor.pos, motor.yaw, True, cig_pt, pole_r_up, lift)
                # Attach lighter mesh to left hand during lift!
                if lift > 0.15:
                    skel.evaluate_fk(pose, motor.pos, motor.yaw)
                    lh_xf = skel.world_transforms[BoneID.HAND_L]
                    lighter.active_world_pos = lh_xf.pos + Vec3(0.0, -0.06, 0.0)
                    lighter.active_world_rot = Quat.from_axis_angle(VEC3_UP, motor.yaw)
            else:
                w = 1.0 - smoothstep(0.80, 1.0, u)
                hand_target = self._action_target_pos + Vec3(0.0, 0.06, 0.0)
                skel.solve_arm_ik_world(pose, motor.pos, motor.yaw, False, hand_target, pole_l_down, w)

        elif self.action == SmokingAction.INHALE_DRAG:
            if not self.in_mouth:
                # Raise right hand to lips with elbow bending naturally outward-forward
                lift = smoothstep(0.0, 0.28, u) * (1.0 - smoothstep(0.56, 0.88, u))
                skel.evaluate_fk(pose, motor.pos, motor.yaw)
                mouth_world = skel.world_transforms[BoneID.CIG_SOCKET_MOUTH].pos
                skel.solve_arm_ik_world(
                    pose, motor.pos, motor.yaw, True,
                    mouth_world + Vec3(-0.015, -0.04, 0.035), pole_r_up, lift,
                )
            # Subtle exhale head tilt back
            exhale = smoothstep(0.58, 0.78, u) * (1.0 - smoothstep(0.82, 1.0, u))
            pose.add_rot_euler(BoneID.HEAD, -0.14 * exhale, 0.05 * exhale, 0.0)
            pose.add_rot_euler(BoneID.CHEST, -0.04 * exhale, 0.0, 0.0)

        elif self.action == SmokingAction.FLICK_ASH:
            # Crisp wrist flick (or quick reach-and-tap if in lips)
            w = math.sin(u * math.pi)
            if self.in_mouth:
                skel.evaluate_fk(pose, motor.pos, motor.yaw)
                mouth_world = skel.world_transforms[BoneID.CIG_SOCKET_MOUTH].pos
                skel.solve_arm_ik_world(
                    pose, motor.pos, motor.yaw, True,
                    mouth_world + Vec3(-0.02, -0.04, 0.05), pole_r_up, w,
                )
            flick = math.sin(clamp01((u - 0.35) / 0.35) * math.pi) if 0.35 <= u <= 0.70 else 0.0
            pose.add_rot_euler(BoneID.FOREARM_R, -0.22 * w, 0.0, 0.14 * flick)
            pose.add_rot_euler(BoneID.HAND_R, 0.38 * flick, 0.22 * flick, -0.35 * flick)

        elif self.action == SmokingAction.DROP_BUTT:
            w = math.sin(u * math.pi)
            pose.add_rot_euler(BoneID.UPPER_ARM_R, -0.25 * w, 0.0, -0.25 * w)
            pose.add_rot_euler(BoneID.FOREARM_R, 0.30 * w, 0.0, 0.0)
            pose.add_rot_euler(BoneID.HAND_R, 0.45 * w, 0.0, -0.35 * w)


# =============================================================================
# PROCEDURAL NON-LOOPED DANCE ENGINE (STYLES 1, 2, 3) + WALK/TURN/SMOKE BLEND
# =============================================================================

class DanceStyle(Enum):
    NONE = 0
    POETIC_FLOW = 1    # Key 1: Contemporary / Team Ico melancholic lyrical flow
    IDOL_GROOVE = 2    # Key 2: Crisp rhythmic J-Pop / AKB-inspired upbeat groove
    URBAN_JAZZ = 3     # Key 3: Syncopated modern jazz & expressive isolations


class ProceduralDanceEngine:
    """
    Generates continuously evolving, non-repeating choreography across three
    distinct styles. Seamlessly blends with walking (never running), turns
    directional changes into natural dance flourishes, and excludes the right
    arm whenever the protagonist holds a cigarette in her fingers.
    """

    def __init__(self, seed: int = 777) -> None:
        self._rng = random.Random(seed)
        self.active_style = DanceStyle.NONE
        self.blend_weight = 0.0
        self.dance_time = 0.0

        # Non-repeating motif phrase state
        self._motif_idx = 0
        self._prev_motif_idx = 0
        self._motif_timer = 0.0
        self._motif_duration = 2.4
        self._motif_blend = 1.0
        self._mirror = 1.0
        self._energy = 1.0
        self._groove_seed = 0.0
        self._tempo_mult = 1.0
        self._flourish_dir = 1.0
        self._flourish_type = 0
        self._flourish_timer = 1.0  # >0.4 so no flourish on first frame

    def toggle_style(self, style: DanceStyle) -> None:
        if self.active_style == style:
            self.active_style = DanceStyle.NONE
        else:
            self.active_style = style
            self._pick_next_motif(initial=True)

    def stop(self) -> None:
        self.active_style = DanceStyle.NONE

    def is_dancing(self) -> bool:
        return self.active_style != DanceStyle.NONE or self.blend_weight > 0.02

    def _pick_next_motif(self, initial: bool = False) -> None:
        self._prev_motif_idx = self._motif_idx
        # Phrase-aware motif selection: 35% chance to pick a motif that flows
        # naturally from the current one (creating cohesive 2-3 motif phrases
        # rather than random jumps). This makes the choreography read as
        # structured dance phrases, not a shuffled loop.
        phrase_flows = {
            0: [2, 4, 6],   # After weight sweep -> hip swing, plie, or rock
            1: [3, 5],      # After toe rise -> turn pivot or leg extend
            2: [0, 7],      # After hip swing -> weight sweep or body wave
            3: [1, 6],      # After turn pivot -> toe rise or rock
            4: [5, 7],      # After plie -> leg extend or body wave
            5: [4, 2],      # After leg extend -> plie or hip swing
            6: [0, 3],      # After rock -> weight sweep or turn pivot
            7: [0, 2, 6],   # After body wave -> weight sweep, hip swing, or rock
            8: [9, 0, 2],   # Phrase bridge motifs
            9: [8, 1, 3],
        }
        if not initial and self._rng.random() < 0.35:
            candidates = phrase_flows.get(self._motif_idx, list(range(10)))
            self._motif_idx = self._rng.choice(candidates)
        else:
            candidates = [i for i in range(10) if i != self._motif_idx]
            self._motif_idx = self._rng.choice(candidates)
        self._motif_timer = 0.0
        if self.active_style == DanceStyle.POETIC_FLOW:
            self._motif_duration = self._rng.uniform(2.0, 3.6)
        elif self.active_style == DanceStyle.IDOL_GROOVE:
            self._motif_duration = self._rng.uniform(1.3, 2.5)
        else:
            self._motif_duration = self._rng.uniform(1.5, 3.0)
        self._motif_blend = 1.0 if initial else 0.0
        if self._rng.random() < 0.65:
            self._mirror = -self._mirror
        self._energy = self._rng.uniform(0.82, 1.22)
        self._groove_seed = self._rng.uniform(0.0, 50.0)
        # Wider per-motif tempo multiplier for richer rhythmic variety
        self._tempo_mult = self._rng.uniform(0.78, 1.22)
        # Transition flourish: choose between arm sweep (0) or body wave (1)
        self._flourish_dir = self._rng.choice([-1.0, 1.0])
        self._flourish_type = self._rng.choice([0, 1])
        self._flourish_timer = 0.0

    def update(self, dt: float) -> None:
        target_w = 1.0 if self.active_style != DanceStyle.NONE else 0.0
        self.blend_weight = damp(self.blend_weight, target_w, 6.5, dt)
        if self.blend_weight <= 0.002 and self.active_style == DanceStyle.NONE:
            return

        self.dance_time += dt
        self._motif_timer += dt
        self._flourish_timer += dt
        self._motif_blend = clamp01(self._motif_blend + dt * 2.8)
        if self._motif_timer >= self._motif_duration:
            self._pick_next_motif(initial=False)

    def apply_to_pose(
        self,
        base_pose: Pose,
        walk_speed_norm: float,
        angular_vel: float,
        cig_in_fingers: bool,
    ) -> None:
        if self.blend_weight <= 0.002:
            return

        style = self.active_style if self.active_style != DanceStyle.NONE else DanceStyle.POETIC_FLOW
        pose_prev = Pose()
        pose_cur = Pose()

        self._eval_motif_pose(pose_prev, style, self._prev_motif_idx, self.dance_time)
        self._eval_motif_pose(pose_cur, style, self._motif_idx, self.dance_time)
        pose_prev.blend_with(pose_cur, smoothstep(0.0, 1.0, self._motif_blend))

        # Turning while dancing turns the shoulders/head naturally into the arc!
        turn_lead = clamp(angular_vel * 0.075, -0.34, 0.34)
        pose_prev.add_rot_euler(BoneID.SPINE_UPPER, 0.0, turn_lead * 0.45, -turn_lead * 0.22)
        pose_prev.add_rot_euler(BoneID.CHEST, 0.02, turn_lead * 0.55, -turn_lead * 0.15)
        pose_prev.add_rot_euler(BoneID.HEAD, -0.02, turn_lead * 0.70, -turn_lead * 0.25)

        # Build compatibility mask:
        # 1) When walking while dancing, lower body blends back to walk stride cleanly!
        # 2) When holding cigarette in fingers, right arm is excluded so she dances with left arm/body!
        walk_factor = clamp01(walk_speed_norm * 2.2)  # Full walk speed ~0.44 -> walk_factor = ~0.97
        legs_w = 1.0 - walk_factor * 0.90
        right_arm_w = 0.0 if cig_in_fingers else 1.0

        mask = make_upper_body_mask(
            spine_w=1.0,
            left_arm_w=1.0,
            right_arm_w=right_arm_w,
            head_w=1.0,
            legs_w=legs_w,
        )
        # Keep subtle dance hip bounce even while walking!
        mask[BoneID.PELVIS] = 1.0 - walk_factor * 0.55

        # Transition flourish: a brief expressive gesture during the first ~0.4s
        # of each new motif. Two flourish types alternate for variety:
        #   Type 0: Sweeping arm gesture (both arms rise and sweep sideways)
        #   Type 1: Body wave (torso undulates from pelvis through head)
        # Both create organic bridging between motifs so the choreography reads
        # as cohesive phrases, not loops.
        if self._flourish_timer < 0.42:
            ft = self._flourish_timer / 0.42
            # Bell envelope: 0 -> 1 (peak at 0.4) -> 0
            fw = math.sin(ft * math.pi) * self.blend_weight
            fd = self._flourish_dir
            flourish_pose = Pose()
            flourish_pose.copy_from(pose_prev)
            sweep = math.sin(ft * math.pi) * 0.55
            if self._flourish_type == 0:
                # Type 0: Sweeping arm gesture
                flourish_pose.set_rot_euler(BoneID.CLAVICLE_L, 0.0, fd * 0.10, fd * 0.18)
                flourish_pose.set_rot_euler(BoneID.UPPER_ARM_L, -0.55 - sweep * 0.35, fd * 0.16, 0.30 + sweep * 0.22)
                flourish_pose.set_rot_euler(BoneID.FOREARM_L, -0.40 - sweep * 0.25, 0.0, -0.10)
                flourish_pose.set_rot_euler(BoneID.HAND_L, 0.10 * sweep, -0.18, -0.08)
                if not cig_in_fingers:
                    flourish_pose.set_rot_euler(BoneID.CLAVICLE_R, 0.0, -fd * 0.10, -fd * 0.18)
                    flourish_pose.set_rot_euler(BoneID.UPPER_ARM_R, -0.55 - sweep * 0.35, -fd * 0.16, -0.30 - sweep * 0.22)
                    flourish_pose.set_rot_euler(BoneID.FOREARM_R, -0.40 - sweep * 0.25, 0.0, 0.10)
                    flourish_pose.set_rot_euler(BoneID.HAND_R, 0.10 * sweep, 0.18, 0.08)
                flourish_pose.add_rot_euler(BoneID.SPINE_UPPER, 0.04 * sweep, fd * 0.10 * sweep, fd * 0.06 * sweep)
                flourish_pose.add_rot_euler(BoneID.CHEST, 0.02 * sweep, fd * 0.08 * sweep, 0.0)
                flourish_pose.add_rot_euler(BoneID.HEAD, -0.06 * sweep, fd * 0.12 * sweep, fd * 0.04 * sweep)
            else:
                # Type 1: Body wave (torso undulates from pelvis through head)
                wave = math.sin(ft * math.pi * 1.5) * 0.35
                flourish_pose.add_rot_euler(BoneID.PELVIS, 0.06 * sweep, fd * wave * 0.20, fd * wave * 0.12)
                flourish_pose.add_rot_euler(BoneID.SPINE_LOWER, -0.04 * sweep, -fd * wave * 0.18, -fd * wave * 0.10)
                flourish_pose.add_rot_euler(BoneID.SPINE_UPPER, 0.08 * sweep, fd * wave * 0.22, fd * wave * 0.14)
                flourish_pose.add_rot_euler(BoneID.CHEST, -0.06 * sweep, -fd * wave * 0.16, -fd * wave * 0.08)
                flourish_pose.add_rot_euler(BoneID.NECK, 0.04 * sweep, fd * wave * 0.12, 0.0)
                flourish_pose.add_rot_euler(BoneID.HEAD, -0.08 * sweep, -fd * wave * 0.18, -fd * wave * 0.06)
                # Subtle arm follow-through
                flourish_pose.add_rot_euler(BoneID.UPPER_ARM_L, -0.12 * sweep, 0.0, 0.08 * sweep)
                if not cig_in_fingers:
                    flourish_pose.add_rot_euler(BoneID.UPPER_ARM_R, -0.12 * sweep, 0.0, -0.08 * sweep)
            # Flourish mask: upper body + arms + head (not legs, so walking stays clean)
            flourish_mask = make_upper_body_mask(
                spine_w=0.60, left_arm_w=1.0,
                right_arm_w=(0.0 if cig_in_fingers else 1.0),
                head_w=0.80, legs_w=0.0,
            )
            pose_prev.blend_with(flourish_pose, fw, flourish_mask)

        base_pose.blend_with(pose_prev, self.blend_weight, mask)

    def _eval_motif_pose(self, p: Pose, style: DanceStyle, motif: int, t: float) -> None:
        p.clear()
        m = self._mirror
        e = self._energy
        # Non-repeating irrational phase modulation + smooth FBM drift.
        # Per-motif tempo multiplier adds rhythmic variety (slower/faster phrasing).
        tempo = self._tempo_mult
        drift = fbm_1d(t * 0.42 + self._groove_seed, octaves=2, seed=motif * 17)
        phi = t * tempo * (1.0 + drift * 0.08)

        if style == DanceStyle.POETIC_FLOW:
            self._eval_poetic_flow(p, motif, phi, m, e, drift)
        elif style == DanceStyle.IDOL_GROOVE:
            self._eval_idol_groove(p, motif, phi, m, e, drift)
        else:
            self._eval_urban_jazz(p, motif, phi, m, e, drift)

    def _eval_poetic_flow(self, p: Pose, motif: int, t: float, m: float, e: float, drift: float) -> None:
        """Style 1: Lyrical contemporary — body-led slow waves with deep leg
        articulation, weight shifts, and sweeping torso curves. Arms follow
        the body's momentum rather than leading."""
        w1 = math.sin(t * 1.65)
        w2 = math.sin(t * 1.02 + 0.9)
        w3 = math.cos(t * 2.20 - 0.4)
        c1 = math.cos(t * 1.65)
        w4 = math.sin(t * 0.82 + 0.3)

        # Deep pelvic weight transfer & body dip — the core driver
        sway_x = w1 * 0.075 * m * e
        dip_y = -0.035 - abs(c1) * 0.038 * e
        pelvis_z = w4 * 0.020 * m
        p.local_pos_offset[BoneID.PELVIS] = Vec3(sway_x, dip_y, pelvis_z)
        p.set_rot_euler(BoneID.PELVIS, 0.06 + w2 * 0.08, w1 * 0.18 * m, -w1 * 0.14 * m)

        # Full spine ripple — wave travels from pelvis through chest
        p.set_rot_euler(BoneID.SPINE_LOWER, w2 * 0.14, -w1 * 0.12 * m, w1 * 0.10 * m)
        p.set_rot_euler(BoneID.SPINE_UPPER, w3 * 0.16, w2 * 0.16 * m, c1 * 0.12 * m)
        p.set_rot_euler(BoneID.CHEST, -w2 * 0.14 + 0.05, w1 * 0.18 * m, w2 * 0.10 * m)
        p.set_rot_euler(BoneID.NECK, -w3 * 0.08, -w2 * 0.12 * m, -w1 * 0.08 * m)
        p.set_rot_euler(BoneID.HEAD, -0.08 + w2 * 0.14, w1 * 0.20 * m, c1 * 0.12 * m)

        # Subtle arms that follow body momentum (not leading)
        arm_follow = w1 * 0.15 * m
        p.set_rot_euler(BoneID.UPPER_ARM_L, -0.35 + arm_follow, 0.08, 0.22 + w2 * 0.12)
        p.set_rot_euler(BoneID.FOREARM_L, -0.30 - abs(w2) * 0.18, 0.0, -0.08)
        p.set_rot_euler(BoneID.UPPER_ARM_R, -0.35 - arm_follow, -0.08, -0.22 - w2 * 0.12)
        p.set_rot_euler(BoneID.FOREARM_R, -0.30 - abs(w1) * 0.18, 0.0, 0.08)

        # Motif-varied deep leg & body choreography (the main focus)
        if motif == 0:  # Long-arc weight sweep with deep lunge
            lunge = max(0.0, w1 * m)
            r_lunge = max(0.0, -w1 * m)
            p.set_rot_euler(BoneID.THIGH_L, -0.08 - lunge * 0.42, 0.04, 0.08 + lunge * 0.14)
            p.set_rot_euler(BoneID.SHIN_L, 0.18 + lunge * 0.52, 0.0, 0.0)
            p.set_rot_euler(BoneID.FOOT_L, -0.04 + lunge * 0.28, 0.0, 0.0)
            p.set_rot_euler(BoneID.THIGH_R, -0.08 - r_lunge * 0.42, -0.04, -0.08 - r_lunge * 0.14)
            p.set_rot_euler(BoneID.SHIN_R, 0.18 + r_lunge * 0.52, 0.0, 0.0)
            p.set_rot_euler(BoneID.FOOT_R, -0.04 + r_lunge * 0.28, 0.0, 0.0)
        elif motif == 1:  # Rise onto toes with body arch
            rise = max(0.0, w3) * 0.5
            p.local_pos_offset[BoneID.PELVIS].y += rise * 0.04
            p.set_rot_euler(BoneID.THIGH_L, -0.04, 0.02, 0.02)
            p.set_rot_euler(BoneID.SHIN_L, 0.10 + rise * 0.22, 0.0, 0.0)
            p.set_rot_euler(BoneID.FOOT_L, 0.12 + rise * 0.35, 0.0, 0.0)
            p.set_rot_euler(BoneID.THIGH_R, -0.04, -0.02, -0.02)
            p.set_rot_euler(BoneID.SHIN_R, 0.10 + rise * 0.22, 0.0, 0.0)
            p.set_rot_euler(BoneID.FOOT_R, 0.12 + rise * 0.35, 0.0, 0.0)
            p.add_rot_euler(BoneID.CHEST, -rise * 0.18, 0.0, 0.0)
        elif motif == 2:  # Side-to-side hip swing with crossed steps
            cross_l = max(0.0, w2 * m)
            cross_r = max(0.0, -w2 * m)
            p.set_rot_euler(BoneID.THIGH_L, -0.10 - cross_l * 0.20, 0.12 * m + cross_l * 0.18, 0.06)
            p.set_rot_euler(BoneID.SHIN_L, 0.22 + cross_l * 0.30, 0.0, 0.0)
            p.set_rot_euler(BoneID.FOOT_L, -0.02 + cross_l * 0.14, 0.0, 0.0)
            p.set_rot_euler(BoneID.THIGH_R, -0.10 - cross_r * 0.20, -0.12 * m - cross_r * 0.18, -0.06)
            p.set_rot_euler(BoneID.SHIN_R, 0.22 + cross_r * 0.30, 0.0, 0.0)
            p.set_rot_euler(BoneID.FOOT_R, -0.02 + cross_r * 0.14, 0.0, 0.0)
        elif motif == 3:  # Slow turn pivot with body spiral
            spiral = w1 * 0.30 * m
            p.set_rot_euler(BoneID.THIGH_L, -0.06 + spiral * 0.4, spiral * 0.15, 0.04)
            p.set_rot_euler(BoneID.SHIN_L, 0.16 + abs(spiral) * 0.20, 0.0, 0.0)
            p.set_rot_euler(BoneID.FOOT_L, -0.02 + spiral * 0.18, 0.0, 0.0)
            p.set_rot_euler(BoneID.THIGH_R, -0.06 - spiral * 0.4, -spiral * 0.15, -0.04)
            p.set_rot_euler(BoneID.SHIN_R, 0.16 + abs(spiral) * 0.20, 0.0, 0.0)
            p.set_rot_euler(BoneID.FOOT_R, -0.02 - spiral * 0.18, 0.0, 0.0)
            p.add_rot_euler(BoneID.PELVIS, 0.0, spiral, 0.0)
        elif motif == 4:  # Deep plie descent with body roll
            plie = (0.5 + 0.5 * w3) * 0.6
            p.local_pos_offset[BoneID.PELVIS].y -= plie * 0.06
            p.set_rot_euler(BoneID.THIGH_L, -0.04 - plie * 0.35, 0.06 * m, 0.10 + plie * 0.08)
            p.set_rot_euler(BoneID.SHIN_L, 0.14 + plie * 0.55, 0.0, 0.0)
            p.set_rot_euler(BoneID.FOOT_L, -0.02 + plie * 0.12, 0.0, 0.0)
            p.set_rot_euler(BoneID.THIGH_R, -0.04 - plie * 0.35, -0.06 * m, -0.10 - plie * 0.08)
            p.set_rot_euler(BoneID.SHIN_R, 0.14 + plie * 0.55, 0.0, 0.0)
            p.set_rot_euler(BoneID.FOOT_R, -0.02 + plie * 0.12, 0.0, 0.0)
            p.add_rot_euler(BoneID.SPINE_UPPER, plie * 0.15, 0.0, 0.0)
        elif motif == 5:  # Leg extend & hold with body counterbalance
            ext_l = max(0.0, w2 * m) * 0.8
            ext_r = max(0.0, -w2 * m) * 0.8
            p.set_rot_euler(BoneID.THIGH_L, -0.02 - ext_l * 0.55, 0.08 * m, 0.12 + ext_l * 0.20)
            p.set_rot_euler(BoneID.SHIN_L, 0.06 + ext_l * 0.18, 0.0, 0.0)
            p.set_rot_euler(BoneID.FOOT_L, 0.04 + ext_l * 0.30, 0.0, 0.0)
            p.set_rot_euler(BoneID.THIGH_R, -0.02 - ext_r * 0.55, -0.08 * m, -0.12 - ext_r * 0.20)
            p.set_rot_euler(BoneID.SHIN_R, 0.06 + ext_r * 0.18, 0.0, 0.0)
            p.set_rot_euler(BoneID.FOOT_R, 0.04 + ext_r * 0.30, 0.0, 0.0)
            p.add_rot_euler(BoneID.CHEST, 0.0, -w2 * 0.10 * m, 0.0)
        elif motif == 6:  # Swaying weight rock with knee flex
            rock = w1 * 0.5 * m
            p.set_rot_euler(BoneID.THIGH_L, -0.06 - max(0.0, rock) * 0.30, 0.04, 0.06)
            p.set_rot_euler(BoneID.SHIN_L, 0.16 + max(0.0, rock) * 0.38, 0.0, 0.0)
            p.set_rot_euler(BoneID.FOOT_L, -0.02 + max(0.0, rock) * 0.16, 0.0, 0.0)
            p.set_rot_euler(BoneID.THIGH_R, -0.06 - max(0.0, -rock) * 0.30, -0.04, -0.06)
            p.set_rot_euler(BoneID.SHIN_R, 0.16 + max(0.0, -rock) * 0.38, 0.0, 0.0)
            p.set_rot_euler(BoneID.FOOT_R, -0.02 + max(0.0, -rock) * 0.16, 0.0, 0.0)
        else:  # Floating body wave with gentle knee pulse
            pulse = abs(w3) * 0.3
            p.local_pos_offset[BoneID.PELVIS].y -= pulse * 0.025
            p.set_rot_euler(BoneID.THIGH_L, -0.04 - pulse * 0.18, 0.02, 0.04)
            p.set_rot_euler(BoneID.SHIN_L, 0.12 + pulse * 0.28, 0.0, 0.0)
            p.set_rot_euler(BoneID.FOOT_L, -0.02 + pulse * 0.10, 0.0, 0.0)
            p.set_rot_euler(BoneID.THIGH_R, -0.04 - pulse * 0.18, -0.02, -0.04)
            p.set_rot_euler(BoneID.SHIN_R, 0.12 + pulse * 0.28, 0.0, 0.0)
            p.set_rot_euler(BoneID.FOOT_R, -0.02 + pulse * 0.10, 0.0, 0.0)
            p.add_rot_euler(BoneID.SPINE_LOWER, pulse * 0.08, 0.0, 0.0)

    def _eval_idol_groove(self, p: Pose, motif: int, t: float, m: float, e: float, drift: float) -> None:
        """Style 2: Crisp upbeat J-pop — energetic hip bounce, quick step-touch
        footwork, and rhythmic body pops. Legs and torso lead the groove."""
        beat = t * 4.0
        half = t * 2.0
        sb = math.sin(beat)
        cb = math.cos(beat)
        sh = math.sin(half)
        ch = math.cos(half)
        beat2 = math.sin(beat * 2.0)

        # Deep down-beat hip & knee bounce — the groove engine
        bounce = -0.045 - (0.5 + 0.5 * beat2) * 0.040 * e
        hip_x = sh * 0.065 * m
        hip_z = sb * 0.020
        p.local_pos_offset[BoneID.PELVIS] = Vec3(hip_x, bounce, hip_z)
        p.set_rot_euler(BoneID.PELVIS, 0.08, sb * 0.18 * m, -sh * 0.14 * m)

        # Crisp torso counter-pop
        p.set_rot_euler(BoneID.SPINE_LOWER, 0.04 + cb * 0.06, -sb * 0.10 * m, sh * 0.10 * m)
        p.set_rot_euler(BoneID.SPINE_UPPER, 0.06 + sb * 0.08, sb * 0.14 * m, sh * 0.08 * m)
        p.set_rot_euler(BoneID.CHEST, 0.06 - cb * 0.07, sh * 0.18 * m, -sb * 0.07 * m)
        p.set_rot_euler(BoneID.NECK, -0.04, -sh * 0.10 * m, 0.0)
        p.set_rot_euler(BoneID.HEAD, 0.04 + sb * 0.08, sh * 0.16 * m, sb * 0.10 * m)

        # Compact arms held near body — rhythmic accents, not leads
        p.set_rot_euler(BoneID.UPPER_ARM_L, -0.45 + sb * 0.12, 0.10, 0.20 + cb * 0.08)
        p.set_rot_euler(BoneID.FOREARM_L, -0.85 - abs(sb) * 0.15, 0.0, -0.12)
        p.set_rot_euler(BoneID.UPPER_ARM_R, -0.45 - sb * 0.12, -0.10, -0.20 - cb * 0.08)
        p.set_rot_euler(BoneID.FOREARM_R, -0.85 - abs(sb) * 0.15, 0.0, 0.12)

        # Motif-varied footwork & body grooves (the main focus)
        if motif == 0:  # Step-touch: alternating side steps with hip pop
            step_l = max(0.0, sh * m)
            step_r = max(0.0, -sh * m)
            p.set_rot_euler(BoneID.THIGH_L, -0.16 - step_l * 0.35, 0.08 * m + step_l * 0.16, 0.06 + step_l * 0.12)
            p.set_rot_euler(BoneID.SHIN_L, 0.22 + step_l * 0.42, 0.0, 0.0)
            p.set_rot_euler(BoneID.FOOT_L, -0.04 + step_l * 0.16, 0.0, 0.0)
            p.set_rot_euler(BoneID.THIGH_R, -0.16 - step_r * 0.35, -0.08 * m - step_r * 0.16, -0.06 - step_r * 0.12)
            p.set_rot_euler(BoneID.SHIN_R, 0.22 + step_r * 0.42, 0.0, 0.0)
            p.set_rot_euler(BoneID.FOOT_R, -0.04 + step_r * 0.16, 0.0, 0.0)
        elif motif == 1:  # Quick march bounce with knee drive
            drive_l = max(0.0, sb)
            drive_r = max(0.0, -sb)
            p.set_rot_euler(BoneID.THIGH_L, -0.10 - drive_l * 0.55, 0.04, 0.04)
            p.set_rot_euler(BoneID.SHIN_L, 0.30 + drive_l * 0.65, 0.0, 0.0)
            p.set_rot_euler(BoneID.FOOT_L, -0.08 + drive_l * 0.30, 0.0, 0.0)
            p.set_rot_euler(BoneID.THIGH_R, -0.10 - drive_r * 0.55, -0.04, -0.04)
            p.set_rot_euler(BoneID.SHIN_R, 0.30 + drive_r * 0.65, 0.0, 0.0)
            p.set_rot_euler(BoneID.FOOT_R, -0.08 + drive_r * 0.30, 0.0, 0.0)
        elif motif == 2:  # Hip swing with body figure-8
            fig8 = math.sin(t * 2.0) * 0.5 * m
            p.set_rot_euler(BoneID.THIGH_L, -0.08 - max(0.0, fig8) * 0.25, 0.14 * m, 0.08)
            p.set_rot_euler(BoneID.SHIN_L, 0.20 + max(0.0, fig8) * 0.30, 0.0, 0.0)
            p.set_rot_euler(BoneID.FOOT_L, -0.02 + max(0.0, fig8) * 0.12, 0.0, 0.0)
            p.set_rot_euler(BoneID.THIGH_R, -0.08 - max(0.0, -fig8) * 0.25, -0.14 * m, -0.08)
            p.set_rot_euler(BoneID.SHIN_R, 0.20 + max(0.0, -fig8) * 0.30, 0.0, 0.0)
            p.set_rot_euler(BoneID.FOOT_R, -0.02 + max(0.0, -fig8) * 0.12, 0.0, 0.0)
            p.add_rot_euler(BoneID.PELVIS, 0.0, fig8 * 0.30, 0.0)
        elif motif == 3:  # Cross-step with body twist
            twist = sb * 0.40 * m
            p.set_rot_euler(BoneID.THIGH_L, -0.12, twist * 0.20, 0.10 + max(0.0, sb) * 0.18)
            p.set_rot_euler(BoneID.SHIN_L, 0.24 + max(0.0, sb) * 0.35, 0.0, 0.0)
            p.set_rot_euler(BoneID.FOOT_L, -0.04 + max(0.0, sb) * 0.14, 0.0, 0.0)
            p.set_rot_euler(BoneID.THIGH_R, -0.12, -twist * 0.20, -0.10 - max(0.0, -sb) * 0.18)
            p.set_rot_euler(BoneID.SHIN_R, 0.24 + max(0.0, -sb) * 0.35, 0.0, 0.0)
            p.set_rot_euler(BoneID.FOOT_R, -0.04 + max(0.0, -sb) * 0.14, 0.0, 0.0)
            p.add_rot_euler(BoneID.SPINE_UPPER, 0.0, -twist * 0.30, 0.0)
        elif motif == 4:  # Heel-toe rhythm with shoulder pop
            ht = (0.5 + 0.5 * sb) * m
            p.set_rot_euler(BoneID.THIGH_L, -0.06 - ht * 0.15, 0.06, 0.04)
            p.set_rot_euler(BoneID.SHIN_L, 0.14, 0.0, 0.0)
            p.set_rot_euler(BoneID.FOOT_L, 0.08 + ht * 0.22, 0.0, 0.0)
            p.set_rot_euler(BoneID.THIGH_R, -0.06 + ht * 0.15, -0.06, -0.04)
            p.set_rot_euler(BoneID.SHIN_R, 0.14, 0.0, 0.0)
            p.set_rot_euler(BoneID.FOOT_R, -0.08 - ht * 0.18, 0.0, 0.0)
            p.add_rot_euler(BoneID.CHEST, 0.0, 0.0, sb * 0.06)
        elif motif == 5:  # Quick squat bounce with body pop
            sq = (0.5 + 0.5 * beat2) * 0.5
            p.local_pos_offset[BoneID.PELVIS].y -= sq * 0.05
            p.set_rot_euler(BoneID.THIGH_L, -0.04 - sq * 0.32, 0.05 * m, 0.08)
            p.set_rot_euler(BoneID.SHIN_L, 0.12 + sq * 0.48, 0.0, 0.0)
            p.set_rot_euler(BoneID.FOOT_L, -0.02 + sq * 0.10, 0.0, 0.0)
            p.set_rot_euler(BoneID.THIGH_R, -0.04 - sq * 0.32, -0.05 * m, -0.08)
            p.set_rot_euler(BoneID.SHIN_R, 0.12 + sq * 0.48, 0.0, 0.0)
            p.set_rot_euler(BoneID.FOOT_R, -0.02 + sq * 0.10, 0.0, 0.0)
            p.add_rot_euler(BoneID.CHEST, sq * 0.12, 0.0, 0.0)
        elif motif == 6:  # Side lunge with body lean
            lunge_l = max(0.0, sh * m)
            lunge_r = max(0.0, -sh * m)
            p.set_rot_euler(BoneID.THIGH_L, -0.04 - lunge_l * 0.45, 0.10 * m, 0.14 + lunge_l * 0.10)
            p.set_rot_euler(BoneID.SHIN_L, 0.10 + lunge_l * 0.50, 0.0, 0.0)
            p.set_rot_euler(BoneID.FOOT_L, -0.02 + lunge_l * 0.12, 0.0, 0.0)
            p.set_rot_euler(BoneID.THIGH_R, -0.04 - lunge_r * 0.45, -0.10 * m, -0.14 - lunge_r * 0.10)
            p.set_rot_euler(BoneID.SHIN_R, 0.10 + lunge_r * 0.50, 0.0, 0.0)
            p.set_rot_euler(BoneID.FOOT_R, -0.02 + lunge_r * 0.12, 0.0, 0.0)
            p.add_rot_euler(BoneID.SPINE_UPPER, 0.0, -sh * 0.10 * m, 0.0)
        else:  # Bounce in place with knee wiggle
            wig = sb * 0.5
            p.set_rot_euler(BoneID.THIGH_L, -0.06 - max(0.0, wig) * 0.20, 0.04 + wig * 0.08, 0.04)
            p.set_rot_euler(BoneID.SHIN_L, 0.18 + max(0.0, wig) * 0.32, 0.0, 0.0)
            p.set_rot_euler(BoneID.FOOT_L, -0.04 + max(0.0, wig) * 0.12, 0.0, 0.0)
            p.set_rot_euler(BoneID.THIGH_R, -0.06 - max(0.0, -wig) * 0.20, -0.04 - wig * 0.08, -0.04)
            p.set_rot_euler(BoneID.SHIN_R, 0.18 + max(0.0, -wig) * 0.32, 0.0, 0.0)
            p.set_rot_euler(BoneID.FOOT_R, -0.04 + max(0.0, -wig) * 0.12, 0.0, 0.0)

    def _eval_urban_jazz(self, p: Pose, motif: int, t: float, m: float, e: float, drift: float) -> None:
        """Style 3: Syncopated modern jazz — deep body isolations, sharp hip
        snaps, and grounded jazz walk footwork. Torso and legs dominate."""
        g1 = math.sin(t * 2.80)
        g2 = math.sin(t * 1.40 + 0.65)
        snap = math.tanh(math.sin(t * 2.80 + drift * 0.8) * 2.4)
        g3 = math.sin(t * 0.95 + 1.2)

        # Sharp pelvic isolation & syncopated dip
        dip = -0.050 - abs(g1) * 0.032 * e
        p.local_pos_offset[BoneID.PELVIS] = Vec3(snap * 0.055 * m, dip, g3 * 0.022)
        p.set_rot_euler(BoneID.PELVIS, 0.10, snap * 0.26 * m, -g1 * 0.16 * m)

        # Chest isolation counter-snap — body wave
        p.set_rot_euler(BoneID.SPINE_LOWER, 0.06 + g2 * 0.08, -snap * 0.18 * m, g1 * 0.10 * m)
        p.set_rot_euler(BoneID.SPINE_UPPER, -0.05 + snap * 0.12, snap * 0.22 * m, -snap * 0.10 * m)
        p.set_rot_euler(BoneID.CHEST, 0.08 - g1 * 0.10, -g2 * 0.20 * m, snap * 0.12 * m)
        p.set_rot_euler(BoneID.NECK, -0.05, g2 * 0.14 * m, 0.0)
        p.set_rot_euler(BoneID.HEAD, 0.06 - g2 * 0.08, -snap * 0.22 * m, g1 * 0.10 * m)

        # Relaxed arms — jazz pocket pose with subtle accents
        p.set_rot_euler(BoneID.UPPER_ARM_L, -0.30 + snap * 0.08, 0.12, 0.18 + g1 * 0.06)
        p.set_rot_euler(BoneID.FOREARM_L, -0.55 - abs(g2) * 0.10, 0.0, -0.10)
        p.set_rot_euler(BoneID.UPPER_ARM_R, -0.30 - snap * 0.08, -0.12, -0.18 - g1 * 0.06)
        p.set_rot_euler(BoneID.FOREARM_R, -0.55 - abs(g2) * 0.10, 0.0, 0.10)

        # Motif-varied jazz footwork & body grooves
        if motif == 0:  # Jazz walk: alternating deep steps with body roll
            step_l = max(0.0, g1 * m)
            step_r = max(0.0, -g1 * m)
            p.set_rot_euler(BoneID.THIGH_L, -0.14 - step_l * 0.40, 0.06 * m, 0.08 + step_l * 0.12)
            p.set_rot_euler(BoneID.SHIN_L, 0.30 + step_l * 0.50, 0.0, 0.0)
            p.set_rot_euler(BoneID.FOOT_L, -0.08 + step_l * 0.22, 0.0, 0.0)
            p.set_rot_euler(BoneID.THIGH_R, -0.14 - step_r * 0.40, -0.06 * m, -0.08 - step_r * 0.12)
            p.set_rot_euler(BoneID.SHIN_R, 0.30 + step_r * 0.50, 0.0, 0.0)
            p.set_rot_euler(BoneID.FOOT_R, -0.08 + step_r * 0.22, 0.0, 0.0)
        elif motif == 1:  # Hip isolation with sharp snap
            hip_snap = snap * 0.6 * m
            p.set_rot_euler(BoneID.THIGH_L, -0.06 - max(0.0, hip_snap) * 0.22, 0.10 * m + hip_snap * 0.15, 0.06)
            p.set_rot_euler(BoneID.SHIN_L, 0.18 + abs(hip_snap) * 0.20, 0.0, 0.0)
            p.set_rot_euler(BoneID.FOOT_L, -0.04, 0.0, 0.0)
            p.set_rot_euler(BoneID.THIGH_R, -0.06 - max(0.0, -hip_snap) * 0.22, -0.10 * m - hip_snap * 0.15, -0.06)
            p.set_rot_euler(BoneID.SHIN_R, 0.18 + abs(hip_snap) * 0.20, 0.0, 0.0)
            p.set_rot_euler(BoneID.FOOT_R, -0.04, 0.0, 0.0)
            p.add_rot_euler(BoneID.PELVIS, 0.0, hip_snap, 0.0)
        elif motif == 2:  # Body roll with deep plie
            roll = (0.5 + 0.5 * g2) * 0.7
            p.local_pos_offset[BoneID.PELVIS].y -= roll * 0.05
            p.set_rot_euler(BoneID.THIGH_L, -0.04 - roll * 0.38, 0.06 * m, 0.10 + roll * 0.08)
            p.set_rot_euler(BoneID.SHIN_L, 0.14 + roll * 0.55, 0.0, 0.0)
            p.set_rot_euler(BoneID.FOOT_L, -0.02 + roll * 0.10, 0.0, 0.0)
            p.set_rot_euler(BoneID.THIGH_R, -0.04 - roll * 0.38, -0.06 * m, -0.10 - roll * 0.08)
            p.set_rot_euler(BoneID.SHIN_R, 0.14 + roll * 0.55, 0.0, 0.0)
            p.set_rot_euler(BoneID.FOOT_R, -0.02 + roll * 0.10, 0.0, 0.0)
            p.add_rot_euler(BoneID.SPINE_UPPER, roll * 0.20, 0.0, 0.0)
        elif motif == 3:  # Cross-step pivot with body spiral
            spiral = snap * 0.35 * m
            p.set_rot_euler(BoneID.THIGH_L, -0.08 + spiral * 0.35, spiral * 0.18, 0.06)
            p.set_rot_euler(BoneID.SHIN_L, 0.20 + abs(spiral) * 0.25, 0.0, 0.0)
            p.set_rot_euler(BoneID.FOOT_L, -0.04 + spiral * 0.16, 0.0, 0.0)
            p.set_rot_euler(BoneID.THIGH_R, -0.08 - spiral * 0.35, -spiral * 0.18, -0.06)
            p.set_rot_euler(BoneID.SHIN_R, 0.20 + abs(spiral) * 0.25, 0.0, 0.0)
            p.set_rot_euler(BoneID.FOOT_R, -0.04 - spiral * 0.16, 0.0, 0.0)
            p.add_rot_euler(BoneID.PELVIS, 0.0, spiral, 0.0)
        elif motif == 4:  # Sharp weight drop with knee pop
            drop = max(0.0, g1) * 0.6
            p.local_pos_offset[BoneID.PELVIS].y -= drop * 0.06
            p.set_rot_euler(BoneID.THIGH_L, -0.04 - drop * 0.35, 0.04, 0.08)
            p.set_rot_euler(BoneID.SHIN_L, 0.12 + drop * 0.52, 0.0, 0.0)
            p.set_rot_euler(BoneID.FOOT_L, -0.02 + drop * 0.12, 0.0, 0.0)
            p.set_rot_euler(BoneID.THIGH_R, -0.04 - drop * 0.35, -0.04, -0.08)
            p.set_rot_euler(BoneID.SHIN_R, 0.12 + drop * 0.52, 0.0, 0.0)
            p.set_rot_euler(BoneID.FOOT_R, -0.02 + drop * 0.12, 0.0, 0.0)
            p.add_rot_euler(BoneID.CHEST, drop * 0.15, 0.0, 0.0)
        elif motif == 5:  # Leg extend with body counterbalance
            ext_l = max(0.0, g2 * m) * 0.7
            ext_r = max(0.0, -g2 * m) * 0.7
            p.set_rot_euler(BoneID.THIGH_L, -0.02 - ext_l * 0.50, 0.06 * m, 0.14 + ext_l * 0.18)
            p.set_rot_euler(BoneID.SHIN_L, 0.08 + ext_l * 0.20, 0.0, 0.0)
            p.set_rot_euler(BoneID.FOOT_L, 0.06 + ext_l * 0.28, 0.0, 0.0)
            p.set_rot_euler(BoneID.THIGH_R, -0.02 - ext_r * 0.50, -0.06 * m, -0.14 - ext_r * 0.18)
            p.set_rot_euler(BoneID.SHIN_R, 0.08 + ext_r * 0.20, 0.0, 0.0)
            p.set_rot_euler(BoneID.FOOT_R, 0.06 + ext_r * 0.28, 0.0, 0.0)
            p.add_rot_euler(BoneID.CHEST, 0.0, -g2 * 0.12 * m, 0.0)
        elif motif == 6:  # Syncopated hip swing with toe pivot
            swing = g1 * 0.45 * m
            p.set_rot_euler(BoneID.THIGH_L, -0.06 - max(0.0, swing) * 0.25, 0.08 * m + swing * 0.12, 0.06)
            p.set_rot_euler(BoneID.SHIN_L, 0.16 + max(0.0, swing) * 0.22, 0.0, 0.0)
            p.set_rot_euler(BoneID.FOOT_L, 0.02 + swing * 0.14, 0.0, 0.0)
            p.set_rot_euler(BoneID.THIGH_R, -0.06 - max(0.0, -swing) * 0.25, -0.08 * m - swing * 0.12, -0.06)
            p.set_rot_euler(BoneID.SHIN_R, 0.16 + max(0.0, -swing) * 0.22, 0.0, 0.0)
            p.set_rot_euler(BoneID.FOOT_R, 0.02 - swing * 0.14, 0.0, 0.0)
            p.add_rot_euler(BoneID.PELVIS, 0.0, swing * 0.20, 0.0)
        else:  # Grounded groove with body wave pulse
            pulse = abs(g1) * 0.4
            p.local_pos_offset[BoneID.PELVIS].y -= pulse * 0.03
            p.set_rot_euler(BoneID.THIGH_L, -0.06 - pulse * 0.22, 0.04, 0.06)
            p.set_rot_euler(BoneID.SHIN_L, 0.16 + pulse * 0.32, 0.0, 0.0)
            p.set_rot_euler(BoneID.FOOT_L, -0.02 + pulse * 0.10, 0.0, 0.0)
            p.set_rot_euler(BoneID.THIGH_R, -0.06 - pulse * 0.22, -0.04, -0.06)
            p.set_rot_euler(BoneID.SHIN_R, 0.16 + pulse * 0.32, 0.0, 0.0)
            p.set_rot_euler(BoneID.FOOT_R, -0.02 + pulse * 0.10, 0.0, 0.0)
            p.add_rot_euler(BoneID.SPINE_LOWER, pulse * 0.10, 0.0, 0.0)


# =============================================================================
# OPTIMIZED CINEMATIC SMOKE PLUME, FALLING ASH & TEAM ICO DUST MOTES
# =============================================================================

@dataclass(slots=True)
class SmokeWisp:
    pos: Vec3
    vel: Vec3
    age: float
    max_age: float
    start_r: float
    end_r: float
    curl_phase: float
    curl_freq: float
    max_alpha: int


@dataclass(slots=True)
class FallingAshSpeck:
    pos: Vec3
    vel: Vec3
    age: float
    max_age: float
    size: float
    settled: bool = False


@dataclass(slots=True)
class DustMote:
    pos: Vec3
    phase: float
    speed: float
    radius: float


class AtmosphericParticleSystem:
    """
    Lightweight capped-pool particle system delivering cinematic curling
    cigarette smoke wisps, falling ash specks, and Team Ico drifting dust.
    """

    def __init__(self, seed: int = 303) -> None:
        self._rng = random.Random(seed)
        self.smoke: List[SmokeWisp] = []
        self.ash: List[FallingAshSpeck] = []
        self.dust: List[DustMote] = []
        self._ember_emit_accum = 0.0
        self._exhale_emit_accum = 0.0
        self._init_dust_motes()

    def _init_dust_motes(self) -> None:
        for _ in range(MAX_DUST_MOTES):
            self.dust.append(
                DustMote(
                    pos=Vec3(
                        self._rng.uniform(-2.1, 2.1),
                        self._rng.uniform(0.25, 2.35),
                        self._rng.uniform(-1.9, 2.1),
                    ),
                    phase=self._rng.uniform(0.0, TAU),
                    speed=self._rng.uniform(0.35, 0.85),
                    # Smaller dust motes: fine particulate, barely visible specks
                    radius=self._rng.uniform(0.0012, 0.0022),
                )
            )

    def spawn_ember_wisp(self, tip_pos: Vec3, char_vel: Vec3) -> None:
        if len(self.smoke) >= MAX_SMOKE_PARTICLES:
            self.smoke.pop(0)
        self.smoke.append(
            SmokeWisp(
                pos=tip_pos + Vec3(
                    self._rng.uniform(-0.003, 0.003),
                    0.004,
                    self._rng.uniform(-0.003, 0.003),
                ),
                vel=Vec3(
                    char_vel.x * 0.12 + self._rng.uniform(-0.014, 0.014),
                    self._rng.uniform(0.12, 0.18),
                    char_vel.z * 0.12 + self._rng.uniform(-0.014, 0.014),
                ),
                age=0.0,
                max_age=self._rng.uniform(1.6, 2.6),
                # Smaller smoke wisps: fine curling tendrils instead of big puffs
                start_r=self._rng.uniform(0.005, 0.007),
                end_r=self._rng.uniform(0.022, 0.034),
                curl_phase=self._rng.uniform(0.0, TAU),
                curl_freq=self._rng.uniform(2.2, 3.8),
                max_alpha=self._rng.randint(20, 32),
            )
        )

    def spawn_exhale_cloud(self, mouth_pos: Vec3, mouth_fwd: Vec3) -> None:
        if len(self.smoke) >= MAX_SMOKE_PARTICLES:
            self.smoke.pop(0)
        spread = Vec3(
            self._rng.uniform(-0.03, 0.03),
            self._rng.uniform(0.008, 0.04),
            self._rng.uniform(-0.03, 0.03),
        )
        self.smoke.append(
            SmokeWisp(
                pos=mouth_pos + mouth_fwd * 0.04,
                vel=mouth_fwd * self._rng.uniform(0.20, 0.30) + Vec3(0.0, 0.06, 0.0) + spread,
                age=0.0,
                max_age=self._rng.uniform(2.0, 3.2),
                # Smaller exhale puffs: delicate breath wisps not big clouds
                start_r=self._rng.uniform(0.009, 0.013),
                end_r=self._rng.uniform(0.038, 0.058),
                curl_phase=self._rng.uniform(0.0, TAU),
                curl_freq=self._rng.uniform(1.5, 2.8),
                max_alpha=self._rng.randint(28, 42),
            )
        )

    def spawn_ash_drop(self, tip_pos: Vec3) -> None:
        for _ in range(4):
            if len(self.ash) >= MAX_ASH_PARTICLES:
                self.ash.pop(0)
            self.ash.append(
                FallingAshSpeck(
                    pos=tip_pos + Vec3(
                        self._rng.uniform(-0.008, 0.008),
                        self._rng.uniform(-0.005, 0.005),
                        self._rng.uniform(-0.008, 0.008),
                    ),
                    vel=Vec3(
                        self._rng.uniform(-0.09, 0.09),
                        self._rng.uniform(-0.06, 0.04),
                        self._rng.uniform(-0.09, 0.09),
                    ),
                    age=0.0,
                    max_age=self._rng.uniform(3.2, 4.8),
                    size=self._rng.uniform(0.004, 0.008),
                )
            )

    def update(
        self,
        dt: float,
        elapsed: float,
        smoking: SmokingInteractionController,
        cig_tip_pos: Vec3,
        mouth_pos: Vec3,
        mouth_fwd: Vec3,
        char_vel: Vec3,
    ) -> None:
        # Emit ember smoke stream while lit
        if smoking.has_cigarette and smoking.is_lit:
            rate = 11.5 if smoking.ember_glow > 0.55 else 7.5
            self._ember_emit_accum += dt * rate
            while self._ember_emit_accum >= 1.0:
                self._ember_emit_accum -= 1.0
                self.spawn_ember_wisp(cig_tip_pos, char_vel)
        else:
            self._ember_emit_accum = 0.0

        # Emit exhale smoke breath
        if smoking.emit_exhale_puff > 0.05:
            self._exhale_emit_accum += dt * 22.0 * smoking.emit_exhale_puff
            while self._exhale_emit_accum >= 1.0:
                self._exhale_emit_accum -= 1.0
                self.spawn_exhale_cloud(mouth_pos, mouth_fwd)

        # Spawn falling ash on flick
        if smoking.drop_ash_event_pos is not None:
            self.spawn_ash_drop(smoking.drop_ash_event_pos)

        # Update smoke wisps — layered dual-frequency curl for organic turbulence.
        # Primary slow curl sets the drift direction; a faster secondary swirl
        # adds fine turbulent eddies so smoke reads as living, curling air.
        alive_smoke: List[SmokeWisp] = []
        for w in self.smoke:
            w.age += dt
            if w.age >= w.max_age:
                continue
            age_t = clamp01(w.age / w.max_age)
            # Buoyancy weakens as the wisp cools and disperses
            buoy = lerp(0.18, 0.08, age_t)
            # Primary curl (slow, large-scale drift)
            curl_x = math.sin(elapsed * w.curl_freq + w.curl_phase) * 0.045
            curl_z = math.cos(elapsed * w.curl_freq * 0.8 + w.curl_phase) * 0.045
            # Secondary swirl (faster, smaller-scale eddies) grows with age
            swirl_amp = 0.018 * age_t
            curl_x += math.sin(elapsed * w.curl_freq * 2.7 + w.curl_phase * 1.6) * swirl_amp
            curl_z += math.cos(elapsed * w.curl_freq * 3.1 + w.curl_phase * 2.2) * swirl_amp
            w.vel.x = damp(w.vel.x, curl_x, 2.5, dt)
            w.vel.z = damp(w.vel.z, curl_z, 2.5, dt)
            w.vel.y = damp(w.vel.y, buoy, 1.8, dt)
            w.pos.x += w.vel.x * dt
            w.pos.y += w.vel.y * dt
            w.pos.z += w.vel.z * dt
            alive_smoke.append(w)
        self.smoke = alive_smoke

        # Update falling ash
        alive_ash: List[FallingAshSpeck] = []
        for a in self.ash:
            a.age += dt
            if a.age >= a.max_age:
                continue
            if not a.settled:
                a.vel.y -= 3.6 * dt
                a.vel.x *= math.exp(-2.4 * dt)
                a.vel.z *= math.exp(-2.4 * dt)
                a.pos.x += (a.vel.x + math.sin(elapsed * 9.0 + a.age * 5.0) * 0.04) * dt
                a.pos.y += a.vel.y * dt
                a.pos.z += a.vel.z * dt
                if a.pos.y <= 0.008:
                    a.pos.y = 0.008
                    a.settled = True
            alive_ash.append(a)
        self.ash = alive_ash

        # Drift Team Ico dust motes gently through the dim room
        for dm in self.dust:
            dm.pos.x += math.sin(elapsed * dm.speed + dm.phase) * 0.018 * dt
            dm.pos.y += math.cos(elapsed * dm.speed * 0.7 + dm.phase * 1.3) * 0.012 * dt
            dm.pos.z += math.sin(elapsed * dm.speed * 0.5 + dm.phase * 2.1) * 0.015 * dt

    def build_render_lists(
        self,
        lighting: LightingRig,
        renderer: SceneRenderer,
        materials: Dict[str, Material],
    ) -> Tuple[
        List[Tuple[Vec3, float, Tuple[int, int, int], int]],
        List[Tuple[Vec3, float, Tuple[int, int, int], int]],
    ]:
        # Render settled/falling ash specks as tiny dark-grey triangles (fixed color,
        # no per-speck lighting — keeps them sub-centimeter and unobtrusive)
        ash_rgb = (72, 70, 74)
        for a in self.ash:
            s = a.size
            v0 = a.pos + Vec3(-s, 0.0, -s * 0.5)
            v1 = a.pos + Vec3(s, 0.0, -s * 0.5)
            v2 = a.pos + Vec3(0.0, s * 0.4, s)
            renderer.submit_triangle(v0, v1, v2, VEC3_UP, materials["cig_ash"], lighting, layer=2, grad_t=0.5, precomputed_color=ash_rgb)

        smoke_out: List[Tuple[Vec3, float, Tuple[int, int, int], int]] = []
        for w in self.smoke:
            u = clamp01(w.age / w.max_age)
            rad = lerp(w.start_r, w.end_r, smoothstep(0.0, 1.0, u))
            fade = smoothstep(0.0, 0.14, u) * (1.0 - smoothstep(0.32, 1.0, u))
            alpha = clamp(int(w.max_alpha * fade), 0, 255)
            if alpha <= 2:
                continue

            # Tint wisp softly by proximity to warm lamps vs cool window moonlight
            d_bed = w.pos.distance_to(lighting.bedside_lamp.pos)
            d_flr = w.pos.distance_to(lighting.floor_lamp.pos)
            d_moon = w.pos.distance_to(lighting.curtain_spill.pos)
            warm_w = clamp01(1.3 - min(d_bed, d_flr) * 0.35)
            cool_w = clamp01(1.2 - d_moon * 0.35)

            cr = int(clamp(155 + warm_w * 55 - cool_w * 28, 95, 225))
            cg = int(clamp(162 + warm_w * 28 - cool_w * 10, 105, 215))
            cb = int(clamp(182 - warm_w * 18 + cool_w * 48, 125, 235))
            smoke_out.append((w.pos, rad, (cr, cg, cb), alpha))

        dust_out: List[Tuple[Vec3, float, Tuple[int, int, int], int]] = []
        for dm in self.dust:
            d_lamp = min(
                dm.pos.distance_to(lighting.bedside_lamp.pos),
                dm.pos.distance_to(lighting.floor_lamp.pos),
            )
            in_moon_beam = 1.0 if (abs(dm.pos.x) < 0.45 and dm.pos.z > 0.5) else 0.0
            vis = clamp01(max(1.0 - d_lamp * 0.42, in_moon_beam * 0.72))
            if vis <= 0.18:
                continue
            # Lower dust mote alpha for more subtle, authentic fine particulate
            alpha = int(12 + vis * 20)
            if in_moon_beam > 0.5 and d_lamp > 1.8:
                col = (150, 182, 235)
            else:
                col = (235, 202, 155)
            dust_out.append((dm.pos, dm.radius, col, alpha))

        return smoke_out, dust_out


# =============================================================================
# CINEMATIC CAMERA DIRECTOR (HEAVY RAIN / ALAN WAKE / FATAL FRAME STYLE)
# =============================================================================

class CinematicCameraDirector:
    """
    Spring-damped cinematic third-person camera with:
    - Smooth mouse-orbit control (with pitch limits & wall collision pullback).
    - Subtle handheld breathing & step-coupled micro-sway.
    - Contextual framing push-ins when lighting a cigarette or inhaling.
    - Automatic indoor room boundary respect without jarring snaps.
    """

    def __init__(self, start_target: Vec3, start_yaw: float = 0.0) -> None:
        # Place initial camera looking at protagonist from front-3/4 angle so
        # her face, dark-brown hair, swimsuit, and dim-lit bedroom are framed immediately!
        self.yaw = start_yaw + 0.48
        self.pitch = 0.14
        self.distance = 2.05
        self.target_distance = 2.05
        self.fov_deg = DEFAULT_FOV_DEG

        self.smooth_target = start_target + Vec3(0.0, 1.18, 0.0)
        self.smooth_eye = self._compute_desired_eye(self.smooth_target)
        self._mouse_sens = 0.0028

    def apply_mouse_delta(self, dx: float, dy: float) -> None:
        self.yaw = wrap_angle(self.yaw - dx * self._mouse_sens)
        self.pitch = clamp(self.pitch + dy * self._mouse_sens, -0.38, 0.68)

    def _compute_desired_eye(self, focus: Vec3) -> Vec3:
        cp = math.cos(self.pitch)
        sp = math.sin(self.pitch)
        sy = math.sin(self.yaw)
        cy = math.cos(self.yaw)
        # Offset vector from focus to eye
        dir_x = sy * cp
        dir_y = sp
        dir_z = cy * cp
        return Vec3(
            focus.x + dir_x * self.distance,
            focus.y + dir_y * self.distance,
            focus.z + dir_z * self.distance,
        )

    def get_camera_forward_xz(self) -> Vec3:
        # Camera looks from eye toward focus -> horizontal forward is -dir
        fwd = Vec3(-math.sin(self.yaw), 0.0, -math.cos(self.yaw))
        return fwd.normalized()

    def get_camera_right_xz(self) -> Vec3:
        fwd = self.get_camera_forward_xz()
        # Cross(up, fwd) or Cross(fwd, up): with +X right?
        # Wait: let's match CameraProjection: right = world_up.cross(fwd)!
        return VEC3_UP.cross(fwd).normalized()

    def update(
        self,
        dt: float,
        elapsed: float,
        motor: CharacterMotor,
        smoking: SmokingInteractionController,
        is_dancing: bool,
        world: RoomCollisionWorld,
        proj: CameraProjection,
    ) -> None:
        # Dynamic framing intent based on player state
        if smoking.action == SmokingAction.LIGHT_CIG:
            des_dist = 1.42
            des_fov = 42.0
            focus_y = 1.32
            shoulder_off = 0.14
        elif smoking.action == SmokingAction.INHALE_DRAG:
            des_dist = 1.66
            des_fov = 44.0
            focus_y = 1.34
            shoulder_off = 0.15
        elif motor.speed > 2.1:
            des_dist = 2.32
            des_fov = 52.0
            focus_y = 1.18
            shoulder_off = 0.10
        elif is_dancing:
            des_dist = 2.26
            des_fov = 49.0
            focus_y = 1.12
            shoulder_off = 0.08
        else:
            des_dist = 2.02
            des_fov = 47.0
            focus_y = 1.22
            shoulder_off = 0.14

        self.target_distance = damp(self.target_distance, des_dist, 4.2, dt)
        self.distance = damp(self.distance, self.target_distance, 5.5, dt)
        self.fov_deg = damp(self.fov_deg, des_fov, 4.5, dt)
        proj.set_fov(self.fov_deg)

        # Subtle right-shoulder cinematic framing offset
        cam_right = self.get_camera_right_xz()
        handheld_x = fbm_1d(elapsed * 0.65, 2, 11) * 0.018
        handheld_y = fbm_1d(elapsed * 0.85, 2, 29) * 0.014

        raw_focus = Vec3(
            motor.pos.x + cam_right.x * shoulder_off + handheld_x,
            focus_y + handheld_y,
            motor.pos.z + cam_right.z * shoulder_off,
        )
        self.smooth_target = self.smooth_target.damp_to(raw_focus, 7.5, dt)

        desired_eye = self._compute_desired_eye(self.smooth_target)
        safe_eye = world.clamp_camera_position(self.smooth_target, desired_eye, margin=0.16)
        # Fast pull-in on wall contact, gentle ease-out when space opens
        eye_rate = 14.0 if safe_eye.distance_to(self.smooth_target) < self.smooth_eye.distance_to(self.smooth_target) else 6.5
        self.smooth_eye = self.smooth_eye.damp_to(safe_eye, eye_rate, dt)

        proj.set_look_at(self.smooth_eye, self.smooth_target, VEC3_UP)


# =============================================================================
# PROCEDURAL PCM SOUNDSCAPE, FOLEY & AMBIENT SYNTHESIZER (ZERO EXTERNAL ASSETS)
# =============================================================================

import array as _array
import struct as _struct


class SoundscapeSynthesizer:
    """
    Pure-Python procedural PCM synthesizer for PyGame mixer:
    - Distant late-evening urban night hum & soft window breeze pad.
    - Sparse, melancholic Team Ico-inspired warm harmonic resonance.
    - Surface-aware footsteps (oak planks vs woven rug) synced to stride phase.
    - Tactile lighter flint spark click, flame whoosh, and pack flip-top snap.
    Gracefully degrades to silent no-op if audio hardware is unavailable.
    """

    SAMPLE_RATE = 22050

    def __init__(self) -> None:
        self.enabled = False
        self._ambient_sound: Optional[pygame.mixer.Sound] = None
        self._step_wood_sounds: List[pygame.mixer.Sound] = []
        self._step_rug_sounds: List[pygame.mixer.Sound] = []
        self._lighter_click_sound: Optional[pygame.mixer.Sound] = None
        self._pack_snap_sound: Optional[pygame.mixer.Sound] = None
        self._exhale_sound: Optional[pygame.mixer.Sound] = None
        self._prev_stride_sin = 0.0
        self._step_cooldown = 0.0
        self._init_audio()

    def _init_audio(self) -> None:
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=self.SAMPLE_RATE, size=-16, channels=1, buffer=1024)
            self.enabled = True
            self._build_all_buffers()
            if self._ambient_sound is not None:
                ch = self._ambient_sound.play(loops=-1)
                if ch is not None:
                    ch.set_volume(0.22)
        except Exception:
            self.enabled = False

    def _samples_to_sound(self, samples: Sequence[float]) -> Optional[pygame.mixer.Sound]:
        if not self.enabled:
            return None
        pcm = _array.array("h")
        for s in samples:
            val = int(clamp(s, -1.0, 1.0) * 32767.0)
            pcm.append(val)
        try:
            return pygame.mixer.Sound(buffer=pcm.tobytes())
        except Exception:
            return None

    def _build_all_buffers(self) -> None:
        sr = self.SAMPLE_RATE
        rng = random.Random(909)

        # 1. Evolving 32-second dark ambient soundtrack
        # A proper dark ambient piece with layered evolving textures:
        # - Ultra-deep sub-bass drone (D0/D1) felt more than heard
        # - D minor harmonic stack with detuned voices for organic thickness
        # - Slowly crossfading A minor secondary tonal center for harmonic tension
        # - Third F minor voicing appearing late for unresolved darkness
        # - Three-band filtered noise bed (low rumble + mid air + high hiss)
        # - Sparse distant bell/chime tones at harmonic intervals
        # - Occasional sub-bass pulses (distant thunder-like)
        # - Metallic shimmer accents
        # - Slow heartbeat-like sub-bass throb for visceral unease
        # All frequencies snapped to exact cycle counts over 40s for seamless loop.
        amb_dur = 40.0
        amb_len = int(sr * amb_dur)
        amb_buf: List[float] = [0.0] * amb_len
        lp_noise = 0.0      # high-band air hiss
        lp_wind = 0.0       # mid-band wind
        lp_rumble = 0.0     # low-band rumble
        lp_bell = 0.0       # bell body resonance
        # Ultra-deep sub-bass drone (D0 ~18.4Hz — felt more than heard)
        sub_freq = 18.35
        # Primary D minor harmonic stack (root, fifth, octave, minor third, octave fifth)
        drone_freqs = (36.71, 73.42, 110.0, 146.83, 174.61, 220.0)
        # Secondary A minor voicing that slowly crossfades for harmonic movement
        alt_freqs = (55.0, 82.41, 110.0, 130.81, 164.81)
        # Third voicing: F minor (F2, Ab3, C4) for unresolved late-loop darkness
        third_freqs = (87.31, 103.83, 130.81)
        # Per-layer evolving amplitude envelopes (different periods for richness)
        env_periods = (amb_dur, amb_dur * 0.53, amb_dur * 1.27, amb_dur * 0.71,
                       amb_dur * 1.09, amb_dur * 0.83)
        env_phases = (0.0, 1.2, 2.4, 0.6, 1.8, 3.0)
        # Alt-layer crossfade: fades in 0.30..0.50, out 0.55..0.75
        # Third-layer: fades in 0.72..0.88 (late loop unresolved tension)
        # Distant bell tones (sparse, at harmonic intervals) — D5, A4, F5, D6
        bell_freqs = (587.33, 440.0, 698.46, 1174.66)
        bell_times = (0.15, 0.38, 0.62, 0.85)  # Normalized trigger times within the loop
        bell_dur = 4.5  # seconds of decay per bell tone
        # Precompute bell envelopes (Gaussian-shaped attacks with exponential decay)
        bell_envs: List[List[float]] = []
        for bt_norm in bell_times:
            bt = bt_norm * amb_dur
            env = [0.0] * amb_len
            for i in range(amb_len):
                t = i / sr
                dt = t - bt
                if 0.0 <= dt < bell_dur:
                    # Sharp attack + slow exponential decay + subtle ring modulation
                    attack = 1.0 - math.exp(-dt * 18.0)
                    decay = math.exp(-dt * 1.6)
                    env[i] = attack * decay
            bell_envs.append(env)

        for i in range(amb_len):
            t = i / sr
            prog = i / amb_len  # 0..1 over the full loop
            # Three-band filtered noise bed
            white = rng.uniform(-1.0, 1.0)
            lp_noise = lp_noise * 0.965 + white * 0.035     # high hiss
            lp_wind = lp_wind * 0.990 + white * 0.010       # mid wind
            lp_rumble = lp_rumble * 0.997 + white * 0.003   # low rumble
            wind_mod = 0.5 + 0.5 * math.sin(TAU * prog * 1.0 + 0.3)
            rumble_mod = 0.5 + 0.5 * math.sin(TAU * prog * 0.5 + 1.1)
            air = lp_noise * 0.08 * (0.7 + 0.3 * math.sin(TAU * prog))
            wind = lp_wind * 0.18 * (0.4 + 0.6 * wind_mod)
            rumble = lp_rumble * 0.35 * (0.5 + 0.5 * rumble_mod)

            # Primary drone layers (D minor) with evolving amplitudes + detune drift
            pad = 0.0
            for idx, f in enumerate(drone_freqs):
                cycles = round(f * amb_dur)
                f_loop = cycles / amb_dur
                env_p = env_periods[idx]
                env_cycles = round(1.0 / env_p * amb_dur) if env_p < amb_dur else 1
                env_freq = env_cycles / amb_dur
                env = 0.45 + 0.55 * math.sin(TAU * env_freq * t + env_phases[idx])
                drift = 1.0 + 0.0018 * math.sin(TAU * (1.0 / amb_dur * 3.0) * t + idx)
                # Deeper layers louder; higher layers quieter for dark ambient weight
                amp = 0.062 if idx == 0 else (0.040 if idx <= 2 else 0.024)
                pad += math.sin(TAU * f_loop * drift * t) * amp * env
                # Detuned second voice for chorus thickness (slight beat)
                pad += math.sin(TAU * f_loop * drift * 1.0035 * t + 0.7) * amp * 0.45 * env

            # Ultra-deep sub-bass drone (D0 ~18.4Hz) — felt as physical pressure
            sub_cycles = round(sub_freq * amb_dur)
            sub_f = sub_cycles / amb_dur
            sub_env = 0.5 + 0.5 * math.sin(TAU * t / amb_dur * 0.5 + 0.5)
            pad += math.sin(TAU * sub_f * t) * 0.048 * sub_env
            pad += math.sin(TAU * sub_f * 1.002 * t + 0.3) * 0.020 * sub_env  # detuned sub voice

            # Secondary A minor voicing crossfade (harmonic tension in the middle)
            alt_w = smoothstep(0.30, 0.45, prog) * (1.0 - smoothstep(0.55, 0.75, prog))
            alt_pad = 0.0
            for idx, f in enumerate(alt_freqs):
                cycles = round(f * amb_dur)
                f_loop = cycles / amb_dur
                drift = 1.0 + 0.0014 * math.sin(TAU * (1.0 / amb_dur * 2.5) * t + idx * 1.3)
                amp = 0.034 if idx <= 1 else 0.020
                alt_pad += math.sin(TAU * f_loop * drift * t) * amp
            pad += alt_pad * alt_w * 0.80

            # Third F minor voicing (late-loop unresolved darkness)
            third_w = smoothstep(0.72, 0.85, prog) * (1.0 - smoothstep(0.92, 1.0, prog))
            third_pad = 0.0
            for idx, f in enumerate(third_freqs):
                cycles = round(f * amb_dur)
                f_loop = cycles / amb_dur
                drift = 1.0 + 0.0012 * math.sin(TAU * (1.0 / amb_dur * 1.8) * t + idx * 0.9)
                amp = 0.026 if idx == 0 else 0.016
                third_pad += math.sin(TAU * f_loop * drift * t) * amp
            pad += third_pad * third_w * 0.75

            # Sparse distant bell tones (eerie, harmonic)
            bell = 0.0
            for bidx, bf in enumerate(bell_freqs):
                be = bell_envs[bidx][i]
                if be > 0.001:
                    cycles = round(bf * amb_dur)
                    f_loop = cycles / amb_dur
                    # Bell-like timbre: fundamental + inharmonic partials
                    bell += math.sin(TAU * f_loop * t) * be * 0.020
                    bell += math.sin(TAU * f_loop * 2.76 * t) * be * 0.010
                    bell += math.sin(TAU * f_loop * 5.40 * t) * be * 0.005

            # Occasional distant metallic shimmer (sparse, eerie)
            shimmer = 0.0
            sh_env = max(0.0, math.sin(TAU * prog * 2.0 - 0.5)) ** 4
            if sh_env > 0.01:
                sh_f = 880.0
                sh_cycles = round(sh_f * amb_dur)
                shimmer = math.sin(TAU * (sh_cycles / amb_dur) * t) * 0.010 * sh_env
                shimmer += math.sin(TAU * (sh_cycles / amb_dur * 1.5) * t) * 0.006 * sh_env

            # Occasional sub-bass pulse (distant thunder-like, ~4 times per loop)
            pulse = 0.0
            for pt_norm in (0.08, 0.34, 0.66, 0.90):
                pt = pt_norm * amb_dur
                dt = t - pt
                if 0.0 <= dt < 1.5:
                    pe = math.exp(-dt * 2.2) * (1.0 - math.exp(-dt * 22.0))
                    # Low sine sweep from ~30Hz down to ~16Hz
                    pf = 30.0 - 14.0 * (dt / 1.5)
                    pc = round(pf * amb_dur * 0.05)  # approx snap (short burst, snap less critical)
                    pulse += math.sin(TAU * pf * dt) * pe * 0.044

            # Slow heartbeat-like sub-bass throb (visceral unease, ~48 BPM)
            heartbeat = 0.0
            hb_bpm = 48.0
            hb_period = 60.0 / hb_bpm  # seconds per beat
            hb_phase = (t % hb_period) / hb_period
            if hb_phase < 0.15:
                # First thud (lub)
                hb_env = math.exp(-hb_phase * 30.0) * (1.0 - math.exp(-hb_phase * 200.0))
                heartbeat += math.sin(TAU * 42.0 * t) * hb_env * 0.020
            elif hb_phase < 0.30:
                # Second thud (dub, slightly softer)
                hb2 = hb_phase - 0.15
                hb_env = math.exp(-hb2 * 32.0) * (1.0 - math.exp(-hb2 * 200.0))
                heartbeat += math.sin(TAU * 38.0 * t) * hb_env * 0.014

            amb_buf[i] = clamp(pad + air + wind + rumble + bell + shimmer + pulse + heartbeat, -0.85, 0.85)
        self._ambient_sound = self._samples_to_sound(amb_buf)

        # 2. Oak plank footsteps (warm woody low-mid thud + crisp sneaker rubber tap)
        for variant in range(3):
            n = int(sr * 0.11)
            buf: List[float] = []
            f_base = 118.0 + variant * 11.0
            lp = 0.0
            for i in range(n):
                t = i / sr
                env = math.exp(-t * 36.0)
                thud = math.sin(TAU * f_base * t * math.exp(-t * 8.0)) * env * 0.55
                noise = rng.uniform(-1.0, 1.0)
                lp = lp * 0.72 + noise * 0.28
                tap = lp * math.exp(-t * 68.0) * 0.45
                buf.append((thud + tap) * 0.65)
            snd = self._samples_to_sound(buf)
            if snd is not None:
                self._step_wood_sounds.append(snd)

        # 3. Woven rug footsteps (muffled soft fabric brush)
        for variant in range(2):
            n = int(sr * 0.12)
            buf_r: List[float] = []
            lp = 0.0
            for i in range(n):
                t = i / sr
                env = math.exp(-t * 28.0) * smoothstep(0.0, 0.012, t)
                lp = lp * 0.88 + rng.uniform(-1.0, 1.0) * 0.12
                thud = math.sin(TAU * (78.0 + variant * 6.0) * t) * env * 0.22
                buf_r.append((lp * env * 0.70 + thud) * 0.55)
            snd = self._samples_to_sound(buf_r)
            if snd is not None:
                self._step_rug_sounds.append(snd)

        # 4. Metallic lighter flint click + brief warm flame whoosh
        n_clk = int(sr * 0.22)
        clk_buf: List[float] = []
        lp = 0.0
        for i in range(n_clk):
            t = i / sr
            # Crisp metallic ring at t=0 + flint spark at t=0.045
            ring = math.sin(TAU * 2850.0 * t) * math.exp(-t * 65.0) * 0.35
            spark = 0.0
            if t >= 0.042:
                ts = t - 0.042
                spark = rng.uniform(-1.0, 1.0) * math.exp(-ts * 110.0) * 0.50
                lp = lp * 0.85 + rng.uniform(-1.0, 1.0) * 0.15
                whoosh = lp * smoothstep(0.0, 0.025, ts) * math.exp(-ts * 12.0) * 0.32
                spark += whoosh
            clk_buf.append(ring + spark)
        self._lighter_click_sound = self._samples_to_sound(clk_buf)

        # 5. Cigarette pack flip-top cardboard snap
        n_pk = int(sr * 0.09)
        pk_buf: List[float] = []
        for i in range(n_pk):
            t = i / sr
            pop = math.sin(TAU * 420.0 * t) * math.exp(-t * 80.0) * 0.35
            crisp = rng.uniform(-1.0, 1.0) * math.exp(-t * 95.0) * 0.25
            pk_buf.append(pop + crisp)
        self._pack_snap_sound = self._samples_to_sound(pk_buf)

        # 6. Soft exhale breath whisper
        n_ex = int(sr * 0.55)
        ex_buf: List[float] = []
        lp = 0.0
        for i in range(n_ex):
            t = i / sr
            env = smoothstep(0.0, 0.12, t) * (1.0 - smoothstep(0.22, 0.55, t))
            lp = lp * 0.86 + rng.uniform(-1.0, 1.0) * 0.14
            ex_buf.append(lp * env * 0.22)
        self._exhale_sound = self._samples_to_sound(ex_buf)

    def update_footsteps(self, pos: Vec3, speed: float, stride_phase: float, dt: float) -> None:
        if not self.enabled:
            return
        self._step_cooldown = max(0.0, self._step_cooldown - dt)
        if speed < 0.28:
            self._prev_stride_sin = math.sin(stride_phase)
            return

        cur_sin = math.sin(stride_phase)
        # Heel-strike crossings near 0 (both + -> - and - -> +)
        crossed = (self._prev_stride_sin <= 0.0 < cur_sin) or (self._prev_stride_sin >= 0.0 > cur_sin)
        self._prev_stride_sin = cur_sin
        if crossed and self._step_cooldown <= 0.0:
            self._step_cooldown = 0.18
            on_rug = (-1.05 <= pos.x <= 0.95) and (-1.25 <= pos.z <= 1.05)
            pool = self._step_rug_sounds if (on_rug and self._step_rug_sounds) else self._step_wood_sounds
            if pool:
                snd = random.choice(pool)
                vol = clamp(0.14 + (speed / PLAYER_RUN_SPEED) * 0.22, 0.10, 0.38)
                snd.set_volume(vol)
                snd.play()

    def play_pack_snap(self) -> None:
        if self.enabled and self._pack_snap_sound is not None:
            self._pack_snap_sound.set_volume(0.28)
            self._pack_snap_sound.play()

    def play_lighter_strike(self) -> None:
        if self.enabled and self._lighter_click_sound is not None:
            self._lighter_click_sound.set_volume(0.32)
            self._lighter_click_sound.play()

    def play_exhale(self) -> None:
        if self.enabled and self._exhale_sound is not None:
            self._exhale_sound.set_volume(0.16)
            self._exhale_sound.play()


# =============================================================================
# ARCHITECTURAL MICRO-DETAILS, FOOT GROUNDING IK & INTRO FADE DIRECTOR
# =============================================================================

class BedroomDetailsBuilder:
    """
    Adds contemporary Japanese apartment authenticity without clutter:
    - Balcony railing & distant evening city skyline silhouettes through window gap.
    - Bedside digital alarm clock & glass of water on nightstand.
    - Power cord snaking from bedside lamp to wall outlet.
    - Wall light switch plate beside the interior bedroom door.
    - Curtain rail brackets, rings, and sneaker lace-eyelet ridges.
    """

    @staticmethod
    def build_details(mesh: StaticMesh, materials: Dict[str, Material]) -> None:
        hw = ROOM_HALF_W
        hd = ROOM_HALF_D

        # Register specialized detail materials cleanly
        materials["city_window_glow"] = Material(
            name="city_window_glow",
            base_color=Color3(0.95, 0.78, 0.48),
            roughness=0.2,
            emissive=Color3(0.65, 0.50, 0.28),
        )
        materials["city_building_silhouette"] = Material(
            name="city_building_silhouette",
            base_color=Color3(0.05, 0.06, 0.11),
            roughness=0.85,
            emissive=Color3(0.02, 0.03, 0.06),
        )
        materials["clock_display"] = Material(
            name="clock_display",
            base_color=Color3(0.24, 0.58, 0.62),
            roughness=0.2,
            emissive=Color3(0.18, 0.42, 0.45),
        )
        materials["glass_tumbler"] = Material(
            name="glass_tumbler",
            base_color=Color3(0.68, 0.78, 0.88),
            gradient_color=Color3(0.45, 0.56, 0.72),
            roughness=0.10,
            specular=0.88,
            rim_strength=0.42,
        )

        # 1. Exterior balcony railing & distant Tokyo apartment silhouettes (Z > hd)
        mesh.add_box(0.0, 0.96, hd + 0.36, 3.10, 0.04, 0.04, "metal_dark", layer=0)
        for rx in (-1.35, -0.68, 0.0, 0.68, 1.35):
            mesh.add_box(rx, 0.52, hd + 0.36, 0.03, 0.88, 0.03, "metal_dark", layer=0)

        # Distant urban silhouettes & tiny warm evening apartment lights visible in curtain gap
        mesh.add_box(-0.55, 0.88, hd + 2.8, 0.95, 1.85, 0.2, "city_building_silhouette", layer=0)
        mesh.add_box(0.48, 0.96, hd + 3.2, 1.10, 2.15, 0.2, "city_building_silhouette", layer=0)
        mesh.add_box(0.02, 1.25, hd + 2.6, 0.16, 0.08, 0.05, "city_window_glow", layer=0)
        mesh.add_box(-0.18, 1.48, hd + 2.6, 0.12, 0.07, 0.05, "city_window_glow", layer=0)
        mesh.add_box(0.22, 1.04, hd + 2.9, 0.14, 0.08, 0.05, "city_window_glow", layer=0)

        # 2. Curtain rail brackets & metal rings
        for bx in (-1.62, 0.0, 1.62):
            mesh.add_box(bx, 2.24, hd - 0.05, 0.03, 0.04, 0.08, "metal_dark", layer=2)
        for rx in (-1.45, -1.05, -0.65, -0.25, 0.23, 0.63, 1.03, 1.43):
            mesh.add_cylinder(
                Vec3(rx - 0.008, 2.24, hd - 0.09),
                Vec3(rx + 0.008, 2.24, hd - 0.09),
                0.021, 0.021, 8, "metal_chrome", layer=2,
            )

        # 3. Nightstand details: compact digital alarm clock & water glass
        ns_x, ns_y, ns_z = -0.70, 0.61, -2.01
        mesh.add_box(ns_x + 0.14, ns_y + 0.032, ns_z + 0.12, 0.095, 0.058, 0.052, "metal_dark", layer=2, yaw=-0.25)
        mesh.add_box(ns_x + 0.132, ns_y + 0.034, ns_z + 0.148, 0.074, 0.030, 0.008, "clock_display", layer=2, yaw=-0.25)
        mesh.add_cylinder(
            Vec3(ns_x - 0.15, ns_y, ns_z + 0.14),
            Vec3(ns_x - 0.15, ns_y + 0.092, ns_z + 0.14),
            0.028, 0.032, 8, "glass_tumbler", layer=2,
        )

        # 4. Lamp power cord running neatly down back of nightstand to wall outlet
        cord_pts = [
            Vec3(ns_x, 0.61, -2.23),
            Vec3(ns_x, 0.38, -2.31),
            Vec3(ns_x, 0.32, -hd + 0.025),
        ]
        for i in range(len(cord_pts) - 1):
            mesh.add_cylinder(cord_pts[i], cord_pts[i + 1], 0.006, 0.006, 5, "metal_dark", layer=2)

        # 5. Wall light switch plate beside interior door (Left wall X = -hw, Z = -0.14)
        mesh.add_box(-hw + 0.012, 1.18, -0.14, 0.016, 0.12, 0.075, "ac_plastic", layer=2)
        mesh.add_box(-hw + 0.022, 1.18, -0.14, 0.012, 0.055, 0.042, "sneaker_white", layer=2)

        # 6. Desk coaster & ceramic mug
        mesh.add_cylinder(Vec3(1.94, 0.78, -0.38), Vec3(1.94, 0.87, -0.38), 0.038, 0.041, 8, "bed_sheet", layer=2)

    @staticmethod
    def add_sneaker_lace_details(mesh: SkinnedMesh, skel: Skeleton) -> None:
        """Adds crisp low-poly criss-cross lace ridges along the tongue of both sneakers."""
        for is_right in (False, True):
            ft_b = BoneID.FOOT_R if is_right else BoneID.FOOT_L
            ak = skel.bind_world[ft_b].pos
            for row_idx in range(3):
                z_pos = ak.z + 0.036 + row_idx * 0.024
                y_pos = 0.082 - row_idx * 0.009
                w = 0.022 + row_idx * 0.002
                v0 = mesh.add_vert(Vec3(ak.x - w, y_pos, z_pos - 0.004), ft_b)
                v1 = mesh.add_vert(Vec3(ak.x + w, y_pos, z_pos + 0.004), ft_b)
                v2 = mesh.add_vert(Vec3(ak.x + w, y_pos + 0.006, z_pos + 0.002), ft_b)
                v3 = mesh.add_vert(Vec3(ak.x - w, y_pos + 0.006, z_pos - 0.006), ft_b)
                mesh.add_quad(v0, v1, v2, v3, "sneaker_white", 0.15, 0.25, layer=3, depth_bias=-0.005)


class FootGroundingIK:
    """
    Post-pose floor contact constraint solver.
    Measures lowest sneaker sole/toe world Y after FK evaluation and adjusts
    pelvis vertical offset cleanly so feet never clip below the wooden floor
    or hover unnaturally during deep dance bends or idle weight shifts.
    """

    def __init__(self) -> None:
        self._smooth_y_corr = 0.0

    def solve(self, pose: Pose, skeleton: Skeleton, root_pos: Vec3, root_yaw: float, dt: float) -> None:
        skeleton.evaluate_fk(pose, root_pos, root_yaw)
        lowest_y = 999.0
        for b_id in (BoneID.FOOT_L, BoneID.FOOT_R):
            f_xf = skeleton.world_transforms[b_id]
            # Check heel, ball, and toe sole heights
            for local_pt in (Vec3(0.0, -0.086, -0.03), Vec3(0.0, -0.086, 0.08), Vec3(0.0, -0.082, 0.16)):
                wy = f_xf.apply_point(local_pt).y
                if wy < lowest_y:
                    lowest_y = wy

        for b_id in (BoneID.TOE_L, BoneID.TOE_R):
            t_xf = skeleton.world_transforms[b_id]
            wy = t_xf.apply_point(Vec3(0.0, -0.026, 0.06)).y
            if wy < lowest_y:
                lowest_y = wy

        # Target correction brings lowest shoe contact point right onto Y = 0.002
        desired_corr = clamp(0.002 - lowest_y, -0.04, 0.16)
        self._smooth_y_corr = damp(self._smooth_y_corr, desired_corr, 22.0, dt)
        pose.local_pos_offset[BoneID.PELVIS].y += self._smooth_y_corr


class FacialMoodController:
    """
    Subtle cinematic micro-expressions via upper-eyelid softness and brow/head poise:
    - Focused gentle squint when lighting a cigarette or inhaling.
    - Serene softened gaze during poetic dance.
    """

    def __init__(self) -> None:
        self._soft_lid = 0.0

    def apply(
        self,
        pose: Pose,
        smoking_action: SmokingAction,
        dance_style: DanceStyle,
        dt: float,
    ) -> None:
        target = 0.0
        if smoking_action == SmokingAction.LIGHT_CIG:
            target = 0.24
        elif smoking_action == SmokingAction.INHALE_DRAG:
            target = 0.30
        elif dance_style == DanceStyle.POETIC_FLOW:
            target = 0.18

        self._soft_lid = damp(self._soft_lid, target, 4.5, dt)
        if self._soft_lid > 0.01:
            pose.add_rot_euler(BoneID.EYELID_L, self._soft_lid * 0.55, 0.0, 0.0)
            pose.add_rot_euler(BoneID.EYELID_R, self._soft_lid * 0.55, 0.0, 0.0)
            pose.local_pos_offset[BoneID.EYELID_L].y -= self._soft_lid * 0.004
            pose.local_pos_offset[BoneID.EYELID_R].y -= self._soft_lid * 0.004


class IntroFadeDirector:
    """Pure visual fade-in from darkness on game start (no text, no HUD)."""

    def __init__(self, duration: float = 2.2) -> None:
        self.duration = duration
        self.timer = 0.0
        self._overlay: Optional[pygame.Surface] = None
        self._size = (0, 0)

    def apply(self, screen: pygame.Surface, dt: float) -> None:
        if self.timer >= self.duration:
            return
        self.timer = min(self.duration, self.timer + dt)
        alpha = int((1.0 - smoothstep(0.15, self.duration, self.timer)) * 255)
        if alpha <= 1:
            return
        sz = screen.get_size()
        if self._overlay is None or self._size != sz:
            self._size = sz
            self._overlay = pygame.Surface(sz)
            self._overlay.fill((4, 5, 8))
        self._overlay.set_alpha(alpha)
        screen.blit(self._overlay, (0, 0))


# =============================================================================
# PROTAGONIST ANATOMICAL POLISH & HEADLESS DIAGNOSTIC SUITE
# =============================================================================

class ProtagonistDetailPolisher:
    """
    Adds fine anatomical & outfit silhouettes that elevate the PS3-era finish:
    - Subtle sculpted collarbone ridges below the neck base.
    - Competitive swimsuit back keyhole white piping edge.
    - White sneaker heel pull-tabs & cobalt tongue logo crest.
    """

    @staticmethod
    def polish_protagonist(mesh: SkinnedMesh, skel: Skeleton) -> None:
        BedroomDetailsBuilder.add_sneaker_lace_details(mesh, skel)

        # Subtle clavicle / collarbone anatomical ridges
        chest_pos = skel.bind_world[BoneID.CHEST].pos
        for side_sign, clav_b in ((1.0, BoneID.CLAVICLE_L), (-1.0, BoneID.CLAVICLE_R)):
            p_in = Vec3(side_sign * 0.022, chest_pos.y + 0.088, 0.056)
            p_out = Vec3(side_sign * 0.118, chest_pos.y + 0.098, 0.022)
            v0 = mesh.add_vert(p_in + Vec3(0.0, 0.004, 0.005), BoneID.CHEST, clav_b, 0.6)
            v1 = mesh.add_vert(p_in + Vec3(0.0, -0.005, 0.002), BoneID.CHEST, clav_b, 0.6)
            v2 = mesh.add_vert(p_out + Vec3(0.0, -0.005, 0.004), clav_b, BoneID.CHEST, 0.8)
            v3 = mesh.add_vert(p_out + Vec3(0.0, 0.004, 0.006), clav_b, BoneID.CHEST, 0.8)
            if side_sign > 0:
                mesh.add_quad(v0, v1, v2, v3, "skin", 0.18, 0.25, layer=3, depth_bias=-0.003)
            else:
                mesh.add_quad(v0, v3, v2, v1, "skin", 0.18, 0.25, layer=3, depth_bias=-0.003)

        # Sneaker heel pull-tabs & cobalt tongue crests
        for is_right in (False, True):
            ft_b = BoneID.FOOT_R if is_right else BoneID.FOOT_L
            ak = skel.bind_world[ft_b].pos
            # Heel pull loop tab
            hx0 = ak.x - 0.008
            hx1 = ak.x + 0.008
            hz = ak.z - 0.048
            t0 = mesh.add_vert(Vec3(hx0, 0.088, hz), ft_b)
            t1 = mesh.add_vert(Vec3(hx1, 0.088, hz), ft_b)
            t2 = mesh.add_vert(Vec3(hx1, 0.106, hz - 0.008), ft_b)
            t3 = mesh.add_vert(Vec3(hx0, 0.106, hz - 0.008), ft_b)
            mesh.add_quad(t0, t1, t2, t3, "sneaker_accent", 0.2, 0.3, layer=3)

            # Tongue cobalt athletic crest
            cz = ak.z + 0.025
            c0 = mesh.add_vert(Vec3(ak.x - 0.012, 0.086, cz), ft_b)
            c1 = mesh.add_vert(Vec3(ak.x + 0.012, 0.086, cz), ft_b)
            c2 = mesh.add_vert(Vec3(ak.x + 0.010, 0.098, cz - 0.006), ft_b)
            c3 = mesh.add_vert(Vec3(ak.x - 0.010, 0.098, cz - 0.006), ft_b)
            mesh.add_quad(c0, c1, c2, c3, "sneaker_accent", 0.2, 0.3, layer=3, depth_bias=-0.004)


class StrangeDaysDiagnostics:
    """Headless deterministic verification suite (--test CLI flag)."""

    @staticmethod
    def run_all() -> int:
        print("[Strange Days] Running headless studio verification suite...")
        # 1. Verify quaternion & transform orthogonality
        q = Quat.from_euler_yxz(0.7, -0.4, 0.25)
        v = Vec3(0.3, -0.8, 0.5)
        vr = q.rotate_vec(v)
        assert abs(vr.length() - v.length()) < 1e-5, "Quaternion rotation length mismatch"

        # 2. Verify indoor darkness vs active lamp lighting contrast
        mats = build_material_library()
        rig = LightingRig()
        for pl in rig.point_lights:
            pl.enabled = False
        rig.moon_intensity = 0.0
        rig.update(0.0)
        dark_col = rig.compute_surface_color(Vec3(0.0, 1.0, 0.0), VEC3_UP, Vec3(0.0, 1.5, -2.0), mats["wall_plaster"])
        assert max(dark_col.r, dark_col.g, dark_col.b) < 0.08, "Closed room without lights should be dark!"

        # Re-enable evening lamps
        rig.bedside_lamp.enabled = True
        rig.floor_lamp.enabled = True
        rig.curtain_spill.enabled = True
        rig.moon_intensity = 0.42
        rig.update(0.0)
        lit_col = rig.compute_surface_color(Vec3(-0.7, 0.7, -1.6), VEC3_UP, Vec3(0.0, 1.5, -0.5), mats["wall_plaster"])
        assert lit_col.r > dark_col.r * 3.0, "Lamp illumination failed"

        # 3. Verify protagonist rig & skinning integrity
        model = ProtagonistRigModel()
        ProtagonistDetailPolisher.polish_protagonist(model.mesh, model.skeleton)
        model.mesh.bind_to_skeleton(model.skeleton)
        pose = Pose()
        CoreLocomotionAnimator.eval_idle(pose, 1.0)
        model.skeleton.evaluate_fk(pose, Vec3(0.0, 0.0, 0.0), 0.0)
        model.mesh.deform(model.skeleton)
        assert len(model.mesh.deformed_verts) == len(model.mesh.verts)

        # 4. Verify collision world prevents escaping bedroom walls
        world = RoomCollisionWorld()
        out_pos, hit = world.resolve_character_position(Vec3(10.0, 0.0, -10.0), PLAYER_CAPSULE_RADIUS)
        assert hit and abs(out_pos.x) < ROOM_HALF_W and abs(out_pos.z) < ROOM_HALF_D

        # 5. Verify non-looped procedural dance diversity across all 3 styles
        dance = ProceduralDanceEngine(seed=123)
        for style in (DanceStyle.POETIC_FLOW, DanceStyle.IDOL_GROOVE, DanceStyle.URBAN_JAZZ):
            dance.toggle_style(style)
            samples: List[Quat] = []
            for step_i in range(240):
                dance.update(FIXED_DT)
                p_d = Pose()
                CoreLocomotionAnimator.eval_idle(p_d, step_i * FIXED_DT)
                dance.apply_to_pose(p_d, walk_speed_norm=0.4, angular_vel=0.5, cig_in_fingers=True)
                if step_i in (60, 150, 235):
                    samples.append(p_d.local_rot[BoneID.UPPER_ARM_L])
            # Confirm dance keeps evolving rather than snapping back to identical pose
            diff = abs(samples[0].w - samples[1].w) + abs(samples[0].x - samples[1].x) + abs(samples[0].y - samples[1].y)
            assert diff > 0.01, f"Dance style {style} appeared static"
            dance.stop()

        # 6. Verify smoking lifecycle (pack -> fingers -> mouth -> lighter -> ash -> burn out)
        pack = CigarettePackProp(Vec3(1.86, 0.78, 0.44))
        lighter = LighterProp(Vec3(-1.66, 0.44, 1.47))
        smoke_ctrl = SmokingInteractionController()
        motor = CharacterMotor(Vec3(1.42, 0.0, 0.44))
        assert smoke_ctrl.can_take_cigarette(motor.pos, pack)
        smoke_ctrl.start_take_cigarette(pack)
        for _ in range(90):
            smoke_ctrl.update(FIXED_DT, motor, pack, lighter, Vec3(1.4, 1.0, 0.4))
        assert smoke_ctrl.has_cigarette and not smoke_ctrl.in_mouth

        smoke_ctrl.start_toggle_grip_mode()
        for _ in range(45):
            smoke_ctrl.update(FIXED_DT, motor, pack, lighter, Vec3(1.4, 1.0, 0.4))
        assert smoke_ctrl.in_mouth

        motor.pos = Vec3(-1.18, 0.0, 1.47)
        assert smoke_ctrl.can_light_cigarette(motor.pos, lighter)
        smoke_ctrl.start_light_cigarette(lighter)
        for _ in range(130):
            smoke_ctrl.update(FIXED_DT, motor, pack, lighter, Vec3(-1.2, 1.4, 1.4))
        assert smoke_ctrl.is_lit

        smoke_ctrl.ash_length = 0.018
        smoke_ctrl.start_flick_ash()
        for _ in range(40):
            smoke_ctrl.update(FIXED_DT, motor, pack, lighter, Vec3(-1.2, 1.4, 1.4))
        assert smoke_ctrl.ash_length < 0.005

        print("[Strange Days] All verification checks passed successfully!")
        return 0


# =============================================================================
# GAME WORLD COORDINATOR, POSE PIPELINE & MAIN APPLICATION LOOP
# =============================================================================

# =============================================================================
# GAME WORLD COORDINATOR, POSE PIPELINE & MAIN APPLICATION LOOP
# =============================================================================

class StrangeDaysGame:
    """
    Master coordinator binding the modern Japanese bedroom world, dim-lit
    lighting rig, articulated protagonist, locomotion/dance/smoking controllers,
    smoke/dust atmospherics, and Heavy Rain-inspired cinematic camera.
    """

    def __init__(self, width: int = WINDOW_WIDTH, height: int = WINDOW_HEIGHT) -> None:
        self.width = width
        self.height = height
        self.fullscreen = False
        self.mouse_grabbed = True

        self.materials = build_material_library()
        build_mat_cache(self.materials)
        self.lighting = LightingRig()
        self.collision_world = RoomCollisionWorld()

        # Internal render target (soft PS2-era resolution) + window surface size
        self.render_scale = clamp(RENDER_SCALE, 0.5, 1.0)
        rw = max(320, int(width * self.render_scale))
        rh = max(240, int(height * self.render_scale))
        self.renderer = SceneRenderer(rw, rh)

        # Build static room architecture + modern furniture + architectural details + props
        self.room_mesh = StaticMesh()
        self.light_shafts = BedroomArchitectureBuilder.build_architecture(self.room_mesh)
        self.cig_pack, self.lighter = BedroomFurnitureBuilder.build_furniture(self.room_mesh, self.lighting)
        BedroomDetailsBuilder.build_details(self.room_mesh, self.materials)
        self.room_mesh.build_chunks()

        # Register static glow occluders (furniture volumes + lamp shades) so
        # lamp halos are depth-tested against the world and the character
        self.renderer.static_occluders.clear()
        for col in self.collision_world.colliders:
            cx = (col.min_x + col.max_x) * 0.5
            cy = (col.min_y + col.max_y) * 0.5
            cz = (col.min_z + col.max_z) * 0.5
            radius = 0.42 * math.sqrt(
                (col.max_x - col.min_x) ** 2 + (col.max_y - col.min_y) ** 2 + (col.max_z - col.min_z) ** 2
            )
            self.renderer.static_occluders.append((cx, cy, cz, radius))
        # Lamp shade spheres (small: halos sit just above them)
        self.renderer.static_occluders.append((self.lighting.bedside_lamp.pos.x, 0.865, self.lighting.bedside_lamp.pos.z, 0.10))
        self.renderer.static_occluders.append((self.lighting.floor_lamp.pos.x, 1.57, self.lighting.floor_lamp.pos.z, 0.12))
        self.renderer.character_occluders = [
            (0.0, 0.92, 0.0, 0.20),
            (0.0, 1.22, 0.0, 0.19),
            (0.0, 1.49, 0.007, 0.15),
        ]

        # Build protagonist skeletal rig, mesh & fine anatomical/sneaker polish
        self.protagonist = ProtagonistRigModel()
        ProtagonistDetailPolisher.polish_protagonist(self.protagonist.mesh, self.protagonist.skeleton)
        self.protagonist.mesh.bind_to_skeleton(self.protagonist.skeleton)

        self.motor = CharacterMotor(start_pos=Vec3(-0.08, 0.0, 0.08), start_yaw=0.22)
        self.camera = CinematicCameraDirector(self.motor.pos, start_yaw=self.motor.yaw)

        # Animation, grounding, mood, audio & interaction subsystems
        self.pose = Pose()
        self._walk_pose = Pose()
        self._run_pose = Pose()
        self.blink_gaze = BlinkAndGazeController()
        self.facial_mood = FacialMoodController()
        self.foot_ik = FootGroundingIK()
        self.hair_physics = HairPhysicsRig()
        self.idle_director = IdleVignetteDirector()
        self.dance_engine = ProceduralDanceEngine()
        self.smoking = SmokingInteractionController()
        self.particles = AtmosphericParticleSystem()
        self.soundscape = SoundscapeSynthesizer()
        self.intro_fade = IntroFadeDirector(duration=2.2)

        self.elapsed = 0.0
        self._last_dt = FIXED_DT
        self.running = True
        self._cig_finger_hold_weight = 0.0
        self._last_cig_tip = Vec3(0.0, 1.2, 0.0)
        self._last_mouth_pos = Vec3(0.0, 1.48, 0.0)
        self._last_mouth_fwd = Vec3(0.0, 0.0, 1.0)
        self._exhale_audio_armed = True
        self._render_surf: Optional[pygame.Surface] = None

    def handle_events(self, screen: pygame.Surface) -> pygame.Surface:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.VIDEORESIZE and not self.fullscreen:
                self.width = max(640, event.w)
                self.height = max(360, event.h)
                screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
                self.renderer.resize(
                    max(320, int(self.width * self.render_scale)),
                    max(240, int(self.height * self.render_scale)),
                )

            elif event.type == pygame.MOUSEMOTION:
                if self.mouse_grabbed:
                    dx, dy = event.rel
                    if abs(dx) > 0 or abs(dy) > 0:
                        self.camera.apply_mouse_delta(dx, dy)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.idle_director.notify_input()
                if event.button == 1:  # Left Click: switch cigarette fingers <-> lips
                    if not self.mouse_grabbed:
                        self.mouse_grabbed = True
                        pygame.event.set_grab(True)
                        pygame.mouse.set_visible(False)
                    self.smoking.start_toggle_grip_mode()
                elif event.button == 3:  # Right Click: drop / flick ash
                    self.smoking.start_flick_ash()

            elif event.type == pygame.KEYDOWN:
                self.idle_director.notify_input()
                key = event.key

                if key == pygame.K_ESCAPE:
                    self.running = False

                elif key == pygame.K_TAB:
                    self.mouse_grabbed = not self.mouse_grabbed
                    pygame.event.set_grab(self.mouse_grabbed)
                    pygame.mouse.set_visible(not self.mouse_grabbed)

                elif key == pygame.K_F11:
                    self.fullscreen = not self.fullscreen
                    if self.fullscreen:
                        info = pygame.display.Info()
                        self.width, self.height = info.current_w, info.current_h
                        screen = pygame.display.set_mode((self.width, self.height), pygame.FULLSCREEN)
                    else:
                        self.width, self.height = WINDOW_WIDTH, WINDOW_HEIGHT
                        screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
                    self.renderer.resize(
                        max(320, int(self.width * self.render_scale)),
                        max(240, int(self.height * self.render_scale)),
                    )

                elif key == pygame.K_1:
                    self.dance_engine.toggle_style(DanceStyle.POETIC_FLOW)

                elif key == pygame.K_2:
                    self.dance_engine.toggle_style(DanceStyle.IDOL_GROOVE)

                elif key == pygame.K_3:
                    self.dance_engine.toggle_style(DanceStyle.URBAN_JAZZ)

                elif key == pygame.K_e:
                    if self.smoking.can_take_cigarette(self.motor.pos, self.cig_pack):
                        self.smoking.start_take_cigarette(self.cig_pack)
                        self.soundscape.play_pack_snap()
                    elif self.smoking.can_light_cigarette(self.motor.pos, self.lighter):
                        self.smoking.start_light_cigarette(self.lighter)
                        self.soundscape.play_lighter_strike()

        return screen

    def _read_movement_input(self) -> Tuple[Vec3, bool]:
        keys = pygame.key.get_pressed()
        move_f = 0.0
        move_r = 0.0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            move_f += 1.0
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            move_f -= 1.0
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            move_r += 1.0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            move_r -= 1.0

        wants_run = bool(keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT])

        if abs(move_f) > 0.0 or abs(move_r) > 0.0:
            self.idle_director.notify_input()
            fwd = self.camera.get_camera_forward_xz()
            right = self.camera.get_camera_right_xz()
            wish = fwd * move_f + right * move_r
            return wish, wants_run

        return Vec3(0.0, 0.0, 0.0), wants_run

    def _compute_diegetic_look_target(self) -> Optional[Vec3]:
        """Subtle Fatal Frame / Heavy Rain style gaze toward nearby interactive props."""
        if self.dance_engine.is_dancing() or self.smoking.action != SmokingAction.NONE:
            return None
        if not self.smoking.has_cigarette:
            if self.motor.pos.distance_to(self.cig_pack.pos) < 1.85:
                return self.cig_pack.pos + Vec3(0.0, 0.05, 0.0)
        elif not self.smoking.is_lit:
            if self.motor.pos.distance_to(self.lighter.pos) < 1.85:
                return self.lighter.pos + Vec3(0.0, 0.04, 0.0)
        return None

    def update(self, dt: float) -> None:
        self.elapsed += dt
        wish_dir, wants_run = self._read_movement_input()

        is_dancing = self.dance_engine.is_dancing()
        # Running is strictly disabled while dancing (as designed)
        effective_run = wants_run and (not is_dancing)
        locked = self.smoking.is_movement_locked()

        # 1. Step character locomotion physics & bedroom collisions
        self.motor.step(wish_dir, effective_run, is_dancing, locked, self.collision_world, dt)

        # 2. Step smoking timeline & idle vignette timer
        is_idle_ready = (
            self.motor.speed < 0.08
            and (not is_dancing)
            and self.smoking.action == SmokingAction.NONE
        )
        self.idle_director.update(is_idle_ready, dt)
        self.dance_engine.update(dt)
        self.smoking.update(dt, self.motor, self.cig_pack, self.lighter, self._last_cig_tip)

        # 3. Assemble layered skeletal pose
        self._build_final_pose(dt)

        # 4. Update dynamic lights (lamps + transient lighter flame + cigarette ember)
        self.lighting.lighter_light.enabled = self.lighter.flame_strength > 0.02
        self.lighting.lighter_light.intensity = self.lighter.flame_strength * 1.45
        self.lighting.lighter_light.pos = self.lighter.get_flame_world_pos()

        if self.smoking.has_cigarette and self.smoking.is_lit:
            self.lighting.ember_light.enabled = True
            self.lighting.ember_light.intensity = 0.06 + self.smoking.ember_glow * 0.38
            self.lighting.ember_light.pos = self._last_cig_tip
        else:
            self.lighting.ember_light.enabled = False
            self.lighting.ember_light.intensity = 0.0

        self.lighting.update(self.elapsed)

        # Track the character with three occluder spheres (legs/torso/head) so
        # lamp halos are correctly hidden behind her from any camera angle
        px = self.motor.pos.x
        pz = self.motor.pos.z
        occ = self.renderer.character_occluders
        occ[0] = (px, 0.80, pz, 0.19)
        occ[1] = (px, 1.16, pz, 0.19)
        head_occ = self.protagonist.skeleton.world_transforms[BoneID.HEAD].pos
        occ[2] = (head_occ.x, head_occ.y, head_occ.z, 0.145)

        # 5. Update smoke plumes, falling ash, and Team Ico dust motes
        self.particles.update(
            dt,
            self.elapsed,
            self.smoking,
            self._last_cig_tip,
            self._last_mouth_pos,
            self._last_mouth_fwd,
            self.motor.vel,
        )

        # 6. Update cinematic camera director
        self.camera.update(
            dt,
            self.elapsed,
            self.motor,
            self.smoking,
            is_dancing,
            self.collision_world,
            self.renderer.proj,
        )

    def _build_final_pose(self, dt: float) -> None:
        # Base Idle -> Walk -> Run blend
        CoreLocomotionAnimator.eval_idle(self.pose, self.elapsed)
        spd = self.motor.speed

        if spd > 0.04:
            walk_w = smoothstep(0.03, 0.85, spd)
            CoreLocomotionAnimator.eval_walk(
                self._walk_pose,
                self.motor.stride_phase,
                clamp01(spd / PLAYER_WALK_SPEED),
                self.motor.turn_lean,
                self.motor.fwd_lean,
            )
            self.pose.blend_with(self._walk_pose, walk_w)

            if spd > PLAYER_WALK_SPEED * 1.05:
                run_w = smoothstep(PLAYER_WALK_SPEED * 1.05, PLAYER_RUN_SPEED * 0.88, spd)
                CoreLocomotionAnimator.eval_run(
                    self._run_pose,
                    self.motor.stride_phase,
                    clamp01(spd / PLAYER_RUN_SPEED),
                    self.motor.turn_lean,
                    self.motor.fwd_lean,
                )
                self.pose.blend_with(self._run_pose, run_w)

        # 180-degree pivot weight shift
        CoreLocomotionAnimator.apply_pivot_overlay(self.pose, self.motor.pivot_timer, self.motor.pivot_dir)

        # Random idle vignettes (>10s untouched)
        cig_in_fingers = self.smoking.has_cigarette and (not self.smoking.in_mouth)
        self.idle_director.apply_to_pose(self.pose, cig_in_fingers)

        # Procedural non-looped dances (keys 1, 2, 3) with walk & cigarette compatibility
        self.dance_engine.apply_to_pose(
            self.pose,
            self.motor.norm_speed,
            self.motor.angular_vel,
            cig_in_fingers,
        )

        # Smooth right-hand cigarette carry pose (preserved even during dance!)
        target_hold = 1.0 if cig_in_fingers else 0.0
        self._cig_finger_hold_weight = damp(self._cig_finger_hold_weight, target_hold, 9.5, dt)
        CoreLocomotionAnimator.apply_cigarette_finger_hold(
            self.pose,
            self._cig_finger_hold_weight,
            self.elapsed,
            spd > 0.15,
        )

        # Active smoking / pack / lighter IK & action overlays
        self.smoking.apply_pose_and_ik(self.pose, self.protagonist.skeleton, self.motor, self.lighter)

        # Subtle diegetic gaze: nearby interactive item, else soft camera gaze
        # (Fatal Frame-style eye contact whenever she stands still facing you)
        look_target = self._compute_diegetic_look_target()
        look_weight = 0.55
        is_dancing = self.dance_engine.is_dancing()
        if look_target is None and spd < 0.10 and (not is_dancing) and self.smoking.action == SmokingAction.NONE:
            cam_f = self.camera.get_camera_forward_xz()
            char_f = Vec3(math.sin(self.motor.yaw), 0.0, math.cos(self.motor.yaw))
            facing_cam = char_f.dot(cam_f)  # ~+1 when she looks toward the camera
            if facing_cam > 0.35:
                look_target = self.renderer.proj.pos + Vec3(0.0, -0.06, 0.0)
                look_weight = 0.30 * facing_cam
        self.protagonist.skeleton.apply_head_look_at(
            self.pose, self.motor.pos, self.motor.yaw, look_target, weight=look_weight
        )

        # Micro-expressions (soft lids while lighting/inhaling/dancing poetically)
        self.facial_mood.apply(self.pose, self.smoking.action, self.dance_engine.active_style, dt)

        # Eyelid blinking & micro eye darts
        self.blink_gaze.update(self.pose, dt)

        # First FK pass to drive hair secondary spring physics from true head motion
        self.protagonist.skeleton.evaluate_fk(self.pose, self.motor.pos, self.motor.yaw)
        head_xf = self.protagonist.skeleton.world_transforms[BoneID.HEAD]
        hair_angles = self.hair_physics.update(head_xf.pos, head_xf.rot, self.motor.yaw, dt, self.elapsed)

        # Apply hair physics chain rotations
        bc_p, bc_r = hair_angles["back_center"]
        bl_p, bl_r = hair_angles["back_left"]
        br_p, br_r = hair_angles["back_right"]
        tl_p, tl_r = hair_angles["temple_left"]
        tr_p, tr_r = hair_angles["temple_right"]
        bg_p, bg_r = hair_angles["bangs"]

        self.pose.set_rot_euler(BoneID.HAIR_BACK_C, bc_p, 0.0, bc_r)
        self.pose.set_rot_euler(BoneID.HAIR_BACK_L, bl_p, 0.0, bl_r)
        self.pose.set_rot_euler(BoneID.HAIR_BACK_R, br_p, 0.0, br_r)
        self.pose.set_rot_euler(BoneID.HAIR_TEMPLE_L, tl_p, 0.0, tl_r)
        self.pose.set_rot_euler(BoneID.HAIR_TEMPLE_R, tr_p, 0.0, tr_r)
        self.pose.set_rot_euler(BoneID.HAIR_BANGS, bg_p, 0.0, bg_r)

        # Final FK evaluation & update cigarette/mouth world anchors
        self.protagonist.skeleton.evaluate_fk(self.pose, self.motor.pos, self.motor.yaw)
        mouth_xf = self.protagonist.skeleton.world_transforms[BoneID.CIG_SOCKET_MOUTH]
        self._last_mouth_pos = mouth_xf.pos.copy()
        self._last_mouth_fwd = mouth_xf.rot.rotate_vec(VEC3_FORWARD).normalized()

        if self.smoking.has_cigarette:
            cig_xf = DynamicCigaretteProp.compute_transform(
                self.protagonist.skeleton, self.smoking.in_mouth
            )
            self._last_cig_tip = DynamicCigaretteProp.get_tip_world_pos(
                cig_xf, self.smoking.burn_progress, self.smoking.ash_length
            )
        else:
            self._last_cig_tip = self._last_mouth_pos

    def render(self, screen: pygame.Surface) -> None:
        # Internal cinematic-resolution surface, upscaled to the window at the end
        rw = self.renderer.width
        rh = self.renderer.height
        if self._render_surf is None or self._render_surf.get_size() != (rw, rh):
            self._render_surf = pygame.Surface((rw, rh))
        rt = self._render_surf

        # Deep dim-lit evening background clear
        rt.fill((7, 9, 15))
        self.renderer.begin_frame()

        # 1. Static bedroom architecture & furniture (baked lighting + chunk culling)
        self.room_mesh.render(self.renderer, self.materials, self.lighting)

        # 2. Interactive props (Cigarette Pack & Metallic Lighter + flame) —
        #    rebuilt meshes are skipped entirely when off-screen
        if not self.renderer.sphere_outside_frustum(self.cig_pack.pos.x, self.cig_pack.pos.y + 0.05, self.cig_pack.pos.z, 0.18):
            self.cig_pack.render(self.renderer, self.materials, self.lighting)
        lighter_pos = self.lighter.active_world_pos if self.lighter.active_world_pos is not None else self.lighter.pos
        if not self.renderer.sphere_outside_frustum(lighter_pos.x, lighter_pos.y + 0.06, lighter_pos.z, 0.18):
            self.lighter.render(self.renderer, self.materials, self.lighting, self.elapsed)

        # 3. Protagonist skinned mesh
        self.protagonist.update_and_render(
            self.pose,
            self.motor.pos,
            self.motor.yaw,
            self.renderer,
            self.materials,
            self.lighting,
        )

        # 4. Active handheld or lip-held cigarette
        if self.smoking.has_cigarette:
            cig_xf = DynamicCigaretteProp.compute_transform(
                self.protagonist.skeleton, self.smoking.in_mouth
            )
            DynamicCigaretteProp.render(
                cig_xf,
                self.smoking.is_lit,
                self.smoking.burn_progress,
                self.smoking.ash_length,
                self.smoking.ember_glow,
                self.renderer,
                self.materials,
                self.lighting,
            )

        # 5. Volumetric moonlight shaft quads from curtain gap
        for shaft in self.light_shafts:
            self.renderer.submit_alpha_quad(shaft, (110, 148, 225, 16))

        # 6. Prepare smoke & dust particles (plus falling ash tris)
        smoke_list, dust_list = self.particles.build_render_lists(
            self.lighting, self.renderer, self.materials
        )

        # 7. Flush opaque layered geometry
        self.renderer.flush_geometry(rt)

        # 8. Soft floor contact shadows beneath feet
        foot_l = self.protagonist.skeleton.world_transforms[BoneID.FOOT_L].pos
        foot_r = self.protagonist.skeleton.world_transforms[BoneID.FOOT_R].pos
        self.renderer.draw_contact_shadow(rt, Vec3(foot_l.x, 0.01, foot_l.z), 0.16, 0.72)
        self.renderer.draw_contact_shadow(rt, Vec3(foot_r.x, 0.01, foot_r.z), 0.16, 0.72)

        # 9. Flush volumetric halos, smoke plumes, and dust motes
        self.renderer.flush_atmospherics(rt, self.lighting, smoke_list, dust_list)

        # 10. Cinematic vignette & letterbox framing (zero UI/HUD!)
        self.renderer.post_fx.apply(rt)

        # 11. Upscale internal frame to the window
        if rt.get_size() == screen.get_size():
            screen.blit(rt, (0, 0))
        else:
            pygame.transform.smoothscale(rt, screen.get_size(), screen)


def main() -> int:
    if "--test" in sys.argv:
        return StrangeDaysDiagnostics.run_all()

    pygame.init()
    pygame.display.set_caption(APP_TITLE)
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
    pygame.event.set_grab(True)
    pygame.mouse.set_visible(False)

    clock = pygame.time.Clock()
    game = StrangeDaysGame(WINDOW_WIDTH, WINDOW_HEIGHT)

    prev_time = time.perf_counter()
    try:
        while game.running:
            now = time.perf_counter()
            dt = clamp(now - prev_time, 0.0005, MAX_FRAME_DT)
            prev_time = now

            screen = game.handle_events(screen)
            game.update(dt)
            game.render(screen)

            pygame.display.flip()
            clock.tick(TARGET_FPS)
    finally:
        pygame.event.set_grab(False)
        pygame.mouse.set_visible(True)
        pygame.quit()

    return 0


if __name__ == "__main__":
    sys.exit(main())

