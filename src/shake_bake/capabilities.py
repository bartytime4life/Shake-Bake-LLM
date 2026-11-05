"""Bounded, metadata-only observations of the environment running this process."""

from datetime import datetime, timezone
import hashlib
from itertools import islice
import json
import os
from pathlib import Path
import platform
import re


def _text(path, limit=65536, *, prefix=False):
    try:
        with path.open('rb') as stream:
            raw = stream.read(limit if prefix else limit + 1)
        return raw.decode('utf-8', errors='replace') if len(raw) <= limit else ''
    except (OSError, ValueError):
        return ''


def _integer(text):
    text = text.strip()
    return int(text) if re.fullmatch(r'[0-9]{1,18}', text) else None


def computer_snapshot(*, proc=Path('/proc'), sys=Path('/sys')):
    memory = {}
    for line in _text(proc / 'meminfo').splitlines():
        match = re.fullmatch(r'(MemTotal|MemAvailable):\s+([0-9]{1,15}) kB', line)
        if match:
            memory[match[1]] = int(match[2]) * 1024
    cpu_model = None
    for line in _text(proc / 'cpuinfo', 16384, prefix=True).splitlines():
        key, separator, value = line.partition(':')
        if separator and key.strip() in ('model name', 'Hardware'):
            cpu_model = value.strip()[:160] or None
            break
    try:
        logical_cpus = len(os.sched_getaffinity(0))
    except (AttributeError, OSError):
        logical_cpus = os.cpu_count()
    # Root cgroup limits are reported only when directly observable. Nested
    # cgroups/other container runtimes may impose limits this view cannot see.
    limit = _integer(_text(sys / 'fs/cgroup/memory.max', 64))
    used = _integer(_text(sys / 'fs/cgroup/memory.current', 64))
    if limit == 0:
        limit = None
    available = memory.get('MemAvailable')
    if limit is not None and used is not None:
        headroom = max(0, limit - used)
        available = min(available, headroom) if available is not None else headroom
    gpus = []
    drm = sys / 'class/drm'
    try:
        cards = sorted(islice(drm.iterdir(), 64))
    except OSError:
        cards = []
    for card in cards:
        if not re.fullmatch(r'card[0-9]{1,3}', card.name):
            continue
        vendor, device = (_text(card / 'device' / name, 64).strip() for name in ('vendor', 'device'))
        if not re.fullmatch(r'0x[0-9a-fA-F]{4}', vendor) or not re.fullmatch(r'0x[0-9a-fA-F]{4}', device):
            continue
        try:
            driver = (card / 'device/driver').readlink().name
            if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', driver):
                driver = None
        except OSError:
            driver = None
        gpus.append({'vendor': {'0x10de':'NVIDIA', '0x1002':'AMD', '0x8086':'Intel'}.get(vendor.lower(), vendor.lower()),
                     'device_id': device.lower(), 'driver': driver,
                     'vram_total_bytes': _integer(_text(card / 'device/mem_info_vram_total', 64))})
    stable = {'system': platform.system(), 'machine': platform.machine(), 'kernel': platform.release(),
              'cpu_model': cpu_model, 'available_logical_cpus': logical_cpus,
              'physical_ram_bytes': memory.get('MemTotal'), 'container_memory_limit_bytes': limit, 'gpus': gpus}
    fingerprint = hashlib.sha256(json.dumps(stable, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return {'kind':'local_capability_snapshot', 'observed_at':datetime.now(timezone.utc).isoformat(),
            **stable, 'available_memory_bytes':available, 'python':platform.python_version(),
            'capability_sha256':fingerprint, 'model_accuracy':None, 'measured_model_memory_bytes':None,
            'limits':['Observes this process environment; it does not identify or qualify another PC.',
                      'Available memory is a point-in-time estimate; unobserved container limits may apply.',
                      'No detected GPU means unknown, not proof of CPU-only hardware.',
                      'Fingerprint is a coarse change indicator, not a unique installation identity or attestation.']}
