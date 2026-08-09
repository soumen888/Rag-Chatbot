# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files, copy_metadata

block_cipher = None

# Collect required metadata and data files for ChromaDB and ONNX Runtime
datas = []
datas += collect_data_files('chromadb')
datas += collect_data_files('onnxruntime')
datas += copy_metadata('chromadb')
datas += copy_metadata('onnxruntime')
datas += copy_metadata('tqdm')

# Hidden imports dynamically referenced by ChromaDB and SDKs
hiddenimports = [
    'chromadb',
    'chromadb.telemetry.product.posthog',
    'chromadb.segment.impl.metadata.sqlite',
    'chromadb.execution.executor.local',
    'chromadb.utils.embedding_functions.onnx_mini_lm_l6_v2',
    'onnxruntime',
    'google.genai',
    'google.genai.types',
    'rich',
    'rich.console',
    'rich.panel',
    'rich.table',
    'rich.live',
    'rich.prompt',
    'telethon',
    'psutil',
    'playwright',
    'bs4',
    'requests',
    'dotenv',
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ragchat',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
