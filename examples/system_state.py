#!/usr/bin/env python3
"""Display the complete ECO-0600 system state in a hierarchical view."""

import asyncio
import os
import sys

from pysensorlinx import Sensorlinx, SensorlinxDevice


def temp_str(t):
    """Format a Temperature object as a short string."""
    if t is None:
        return "—"
    return f"{t.to_fahrenheit():.1f}°F"


def status_icon(active):
    """Return a status indicator."""
    return "ON" if active else "off"


def print_system_state(state):
    # ── Weather Shutdown ──
    ws = state.get("weatherShutdown")
    shutdowns_active = []
    if ws:
        for key in ("wwsd", "cwsd"):
            entry = ws.get(key, {})
            if entry.get("activated"):
                shutdowns_active.append(entry.get("title", key.upper()))

    if shutdowns_active:
        print(f"  *** WEATHER SHUTDOWN ACTIVE: {', '.join(shutdowns_active)} ***")
        print()

    # ── Build a map of temperature sensors by type ──
    temp_by_type = {}
    temps = state.get("temperatures") or []
    for t in temps:
        t_type = t.get("type")
        if t_type:
            temp_by_type[t_type] = t

    # ── Build a map of pumps by mode ──
    pumps_by_mode = {}
    for p in state.get("pumps") or []:
        mode = p.get("mode")
        if mode:
            pumps_by_mode.setdefault(mode, []).append(p)

    # ── Demands ──
    demands = state.get("demands") or []
    stages = state.get("stages") or []
    backup = state.get("backup")
    rv = state.get("reversingValve")

    # Map demand names to temperature types
    demand_temp_map = {
        "hd": "single",   # heat demand → hot tank (or single tank)
        "cd": "single",   # cool demand → cold tank (or single tank)
        "dhw": "dhw",      # DHW demand → DHW tank
    }

    # Map demand names to relevant pump modes
    demand_pump_map = {
        "hd": ["heating", "system"],
        "cd": ["cooling", "system"],
        "dhw": ["dhw"],
    }

    for demand in demands:
        if not demand.get("enabled"):
            continue

        name = demand.get("name", "?")
        title = demand.get("title", name)
        active = demand.get("activated", False)

        marker = ">>>" if active else "   "
        label = f"[{status_icon(active)}]"
        print(f"  {marker} {title} Demand {label}")

        # Show associated temperature sensor
        t_type = demand_temp_map.get(name)
        temp = temp_by_type.get(t_type)
        if temp:
            current = temp_str(temp.get("current"))
            target = temp_str(temp.get("target"))
            a_state = temp.get("activatedState")

            # Check if this demand is affected by weather shutdown
            shutdown_label = None
            if ws and name == "hd" and ws.get("wwsd", {}).get("activated"):
                shutdown_label = "WWSD"
            elif ws and name == "cd" and ws.get("cwsd", {}).get("activated"):
                shutdown_label = "CWSD"

            tank_line = f"        Tank: {current}"
            if temp.get("target") is not None:
                tank_line += f" / target {target}"
            if a_state and active:
                tank_line += f"  ({a_state})"
            if shutdown_label:
                tank_line += f"  [{shutdown_label}]"
            print(tank_line)

        # Show stages and backup only under the active demand that drives them
        # (stages respond to hd/cd, not dhw)
        if active and name in ("hd", "cd"):
            if stages:
                running = [s for s in stages if s.get("activated")]
                enabled = [s for s in stages if s.get("enabled")]
                if running:
                    for s in running:
                        print(f"        Stage: {s['title']} [ON]  runtime {s.get('runTime', '?')}")
                else:
                    print(f"        Stages: {len(enabled)} enabled, none running")

            if backup:
                bk_status = status_icon(backup.get("activated"))
                if backup.get("enabled") or backup.get("activated"):
                    print(f"        Backup: [{bk_status}]  runtime {backup.get('runTime', '?')}")

            # Reversing valve (relevant for heat/cool switching)
            if rv:
                print(f"        Reversing Valve: [{status_icon(rv.get('activated'))}]")

        # Show associated pumps
        pump_modes = demand_pump_map.get(name, [])
        for mode in pump_modes:
            for p in pumps_by_mode.get(mode, []):
                p_status = status_icon(p.get("activated"))
                print(f"        {p.get('title', 'Pump')}: [{p_status}]  mode={mode}")

        print()

    # ── Outdoor temperature ──
    outdoor = temp_by_type.get("outdoor")
    if outdoor:
        print(f"  Outdoor: {temp_str(outdoor.get('current'))}")

    # ── Weather shutdown status ──
    if ws and not shutdowns_active:
        print(f"  Weather Shutdown: none active")


async def main():
    email = os.getenv("SENSORLINX_EMAIL")
    password = os.getenv("SENSORLINX_PASSWORD")
    building_id = os.getenv("SENSORLINX_BUILDING_ID")
    device_id = os.getenv("SENSORLINX_DEVICE_ID")

    if not email or not password:
        print("Set SENSORLINX_EMAIL and SENSORLINX_PASSWORD environment variables.", file=sys.stderr)
        sys.exit(1)

    api = Sensorlinx()
    try:
        await api.login(email, password)

        # Auto-discover building and device if not specified
        if not building_id:
            buildings = await api.get_buildings()
            building_id = buildings[0]["id"]
        if not device_id:
            devices = await api.get_devices(building_id)
            device_id = devices[0]["syncCode"]

        device = SensorlinxDevice(api, building_id, device_id)
        state = await device.get_system_state()

        print()
        print(f"  ECO-0600 System State  ({device_id})")
        print(f"  {'=' * 40}")
        print()
        print_system_state(state)
        print()
    finally:
        await api.close()


if __name__ == "__main__":
    asyncio.run(main())
