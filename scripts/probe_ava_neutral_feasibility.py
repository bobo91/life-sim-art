"""Read-only host/Blender capability probe; no assets or inference are created.

Run with the system Python and, separately, Blender --background --python.
Only the explicitly requested JSON file inside this workspace is written.
"""
import argparse
import ctypes
import datetime
import importlib.util
import json
import os
from pathlib import Path
import platform
import sys


def memory_status():
    if os.name != "nt":
        return {"status": "not probed on this OS"}

    class Status(ctypes.Structure):
        _fields_ = [
            ("length", ctypes.c_ulong), ("load", ctypes.c_ulong),
            ("total_physical", ctypes.c_ulonglong),
            ("available_physical", ctypes.c_ulonglong),
            ("total_page", ctypes.c_ulonglong),
            ("available_page", ctypes.c_ulonglong),
            ("total_virtual", ctypes.c_ulonglong),
            ("available_virtual", ctypes.c_ulonglong),
            ("available_extended", ctypes.c_ulonglong),
        ]

    status = Status()
    status.length = ctypes.sizeof(status)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        return {"status": "GlobalMemoryStatusEx failed"}
    return {"physical_bytes": status.total_physical,
            "available_physical_bytes_at_probe": status.available_physical}


def windows_gpu_registry():
    """Driver-reported metadata, not a successful GPU-compute test."""
    if os.name != "nt":
        return []
    import winreg

    found = []
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                            r"HARDWARE\DEVICEMAP\VIDEO") as mapping:
            for index in range(winreg.QueryInfoKey(mapping)[1]):
                _, target, _ = winreg.EnumValue(mapping, index)
                prefix = "\\Registry\\Machine\\"
                if not isinstance(target, str) or not target.startswith(prefix):
                    continue
                values = {}
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                        target[len(prefix):]) as device:
                        for field in ["HardwareInformation.AdapterString",
                                      "HardwareInformation.qwMemorySize",
                                      "HardwareInformation.MemorySize"]:
                            try:
                                value, _ = winreg.QueryValueEx(device, field)
                                if isinstance(value, bytes):
                                    if field.endswith("AdapterString"):
                                        value = value.decode("utf-16-le", errors="replace").split("\0", 1)[0]
                                    else:
                                        value = int.from_bytes(value, "little")
                                values[field] = value
                            except OSError:
                                pass
                except OSError as exc:
                    values["error"] = str(exc)
                if values and values not in found:
                    found.append(values)
    except OSError as exc:
        found.append({"error": str(exc)})
    return found


def main():
    arguments = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args(arguments)
    root = Path(__file__).resolve().parents[1]
    output = Path(args.output).resolve()
    output.relative_to(root)
    result = {
        "schema": "ava-neutral-environment-probe-1",
        "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "python_version": sys.version,
        "python_executable": sys.executable,
        "os": platform.platform(),
        "processor": platform.processor(),
        "logical_cpu_count": os.cpu_count(),
        "memory": memory_status(),
        "gpu_driver_metadata": windows_gpu_registry(),
        "module_presence_in_this_interpreter_only": {
            name: importlib.util.find_spec(name) is not None
            for name in ["torch", "transformers", "diffusers", "PIL", "numpy"]
        },
        "new_meshes_renders_exports_or_ai_generations": 0,
    }
    try:
        import bpy
    except ImportError:
        result["blender"] = "not running inside Blender"
    else:
        bpy.context.preferences.use_preferences_save = False
        result["blender"] = {
            "version": bpy.app.version_string,
            "background": bpy.app.background,
            "online_access": bpy.app.online_access,
            "gpu_compute_tested": False,
            "render_tested_this_probe": False,
            "cycles_reported_devices": {},
        }
        preferences = bpy.context.preferences.addons["cycles"].preferences
        for backend in ["CUDA", "OPTIX", "HIP"]:
            try:
                devices = preferences.get_devices_for_type(backend)
                result["blender"]["cycles_reported_devices"][backend] = [
                    {"name": device.name, "type": device.type} for device in devices
                ]
            except Exception as exc:
                result["blender"]["cycles_reported_devices"][backend] = {"error": str(exc)}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=True))


if __name__ == "__main__":
    main()
