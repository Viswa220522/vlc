#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Exercise a newly built portable VLC through its CLI; no GUI automation."""
import argparse
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import sys
import wave
import zlib

parser = argparse.ArgumentParser()
parser.add_argument('exe', type=Path)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
exe = args.exe.resolve()
output = args.output.resolve()
output.mkdir(parents=True, exist_ok=True)
# Windows VLC explicitly recognizes a sibling portable directory (dirs.c).
# Both VLC configuration and Qt state stay with this extracted test build.
portable = exe.parent / 'portable'
portable.mkdir(exist_ok=True)
qt_settings = portable / 'vlc' / 'vlc-qt-interface.ini'
qt_settings.parent.mkdir(exist_ok=True)
qt_settings.write_text('[MainWindow]\ncolor-scheme-index=2\n', encoding='utf-8')
wav = output / 'test-tone.wav'
with wave.open(str(wav), 'wb') as audio:
    audio.setnchannels(1)
    audio.setsampwidth(2)
    audio.setframerate(8000)
    # Quiet deterministic PCM input; audio output will be directed to dummy.
    audio.writeframes(b'\0\0' * 8000 * 2)

def chunk(kind, payload):
    return struct.pack('>I', len(payload)) + kind + payload + struct.pack('>I', zlib.crc32(kind + payload))

png = output / 'test-colors.png'
rows = b''.join(b'\0' + b''.join(bytes((211, 121, 24)) if x < 160 else bytes((27, 27, 27))
                                   for x in range(320)) for _ in range(180))
png.write_bytes(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 320, 180, 8, 2, 0, 0, 0))
                + chunk(b'IDAT', zlib.compress(rows)) + chunk(b'IEND', b''))
cases = []
common = [str(exe), '--ignore-config', '--no-one-instance', '--no-media-library',
          '--no-qt-privacy-ask', '--no-qt-updates-notif', '--no-qt-autoload-extensions',
          '--config=' + str(portable / 'test-vlcrc'), '--aout=dummy', '--vout=dummy', '-vv']

def run(name, options, required, forbidden, timeout=40, capture=False, video=False, library=False):
    log_path = output / (name + '.log')
    with log_path.open('wb') as log:
        environment = os.environ.copy()
        capture_path = output / (name + '.png')
        if capture:
            environment['VLC_QT_UI_TEST_OUTPUT'] = str(capture_path)
            environment['VLC_QT_UI_TEST_MAXIMIZE'] = '1'
        command = [arg for arg in common if not (video and arg == '--vout=dummy')
                   and not (library and arg == '--no-media-library')]
        if library:
            command.append('--media-library')
        process = subprocess.Popen(command + options, cwd=exe.parent, stdout=log, stderr=subprocess.STDOUT, env=environment)
        try:
            code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.terminate()
            process.wait(timeout=10)
            code = 'timeout'
    text = log_path.read_text(encoding='utf-8', errors='replace')
    missing = [pattern for pattern in required if not re.search(pattern, text, re.I)]
    errors = [pattern for pattern in forbidden if re.search(pattern, text, re.I)]
    if capture and not capture_path.is_file():
        missing.append('application scene capture')
    passed = code == 0 and not missing and not errors
    case = {'name': name, 'exit': code, 'passed': passed, 'missingEvidence': missing,
            'forbiddenDiagnostics': errors, 'log': str(log_path),
            'capture': str(capture_path) if capture_path.is_file() else None}
    cases.append(case)
    print(json.dumps(case), flush=True)

fatal = [r'no suitable (?:interface|decoder|demux)', r'cannot load.*(?:dll|plugin)',
         r'failed to (?:load|create).*interface', r'QQmlApplicationEngine failed',
         r'TypeError:', r'ReferenceError:', r'Binding loop detected', r'qrc:.*Error:',
         r'Type .* unavailable', r' is not a type', r'Error decoding:.*juxtopposed',
         r'Cannot open:.*juxtopposed']
run('native-audio-decode', ['--intf=dummy', '--play-and-exit', str(wav)],
    [r'using demux module', r'using audio decoder module'], fatal)
run('native-image-decode', ['--intf=dummy', '--image-duration=2', '--play-and-exit', str(png)],
    [r'using demux module', r'using video decoder module|using video output module'], fatal)
run('native-qt-startup', ['--intf=qt', '--qt-pin-controls', '--no-qt-system-tray',
    '--image-duration=8', '--play-and-exit', str(png)], [r'using interface module "qt"'], fatal, capture=True)
run('native-qt-player', ['--intf=qt', '--qt-pin-controls', '--no-qt-system-tray',
    '--no-qt-video-autoresize', '--image-duration=8', '--play-and-exit', str(png)],
    [r'using interface module "qt"', r'using (?:video output|vout display) module'], fatal, capture=True, video=True, library=True)
report = {'exe': str(exe), 'cases': cases,
          'scope': 'Native decoding, Qt startup/shutdown diagnostics, and the application scene capture. No external GUI input automation.'}
(output / 'native-report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
sys.exit(0 if all(c['passed'] for c in cases) else 1)
