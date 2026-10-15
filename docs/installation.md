# Installation and recovery

## Before installing

Use Home Assistant Core **2026.10.0**, the exact tested API baseline. The HACS minimum version is an installation floor, not a promise that every later Core version works. The standalone Python package and portable core API do not install a Home Assistant integration for you.

Configure your camera with the built-in ONVIF integration first. A working video stream alone does not prove compatibility: this helper requires a PTZ-capable profile, readable normalized pan, and fresh, advancing timezone-aware status timestamps. You also need one or more existing binary sensors that turn `on` during the detections you want to observe. They can be independent of the camera; the helper does not create detection sensors.

Read the selected release's notes and keep a Home Assistant backup. Beta and RC assets are prereleases for testing. A stable release still needs calibration and first-run checks on your own camera and firmware. No hardware compatibility list has been established by the offline tests.

## Manual installation with verified bytes

1. Download all assets from **one** [release](https://github.com/ha-homelab/ha-onvif-room-direction/releases) into an empty workstation directory. Use the [signed-release verification instructions](release-signatures.md) and the independently reviewed source commit before extracting the integration ZIP. Do not mix files from different releases.
2. Stop Home Assistant before replacing an existing installation. Back up its current integration folder outside `custom_components`, so an old copy cannot be discovered as another integration.
3. Extract **`onvif_room_direction.zip`** into the `onvif_room_direction` directory under your actual Home Assistant configuration directory. Do not extract the GitHub source archive there. The required layout is:

   ```text
   <HA configuration directory>/
     custom_components/
       onvif_room_direction/
         __init__.py
         manifest.json
         core.py
         adapter.py
         sensor.py
         config_flow.py
         const.py
         diagnostics.py
         strings.json
         translations/
           en.json
         LICENSE
   ```

   `manifest.json` must be one level below `custom_components`, inside `onvif_room_direction`. An extra nested `onvif_room_direction` or repository directory prevents discovery. The Home Assistant process must be able to read these files.
4. Start or restart Home Assistant, then open **Settings → Devices & services → Add integration → ONVIF Room Direction**. This is a UI configuration integration; there is no YAML configuration block.
5. Select the existing ONVIF camera and detection sources. Replace the synthetic example sectors using [calibration](calibration.md). The helper does not import Home Assistant areas: each label is a sensor state you choose.

## HACS installation

Use the HACS menu's **Custom repositories** action, enter `https://github.com/ha-homelab/ha-onvif-room-direction`, and choose **Integration**. Download the desired release and restart Home Assistant, then add and configure the integration as above. For current interface details see the official [custom repository guide](https://www.hacs.xyz/docs/faq/custom_repositories/) and [integration guide](https://www.hacs.xyz/docs/use/repositories/type/integration/).

This repository supplies `hacs.json` and the integration-root ZIP expected by HACS. It is not claimed to be in the default HACS catalog. Its download path does not replace the separate Sigstore verification procedure. Use manual installation of verified bytes when that verification is part of your installation policy. Avoid alternating manual file overlays and HACS updates without checking which release is actually installed.

## First-run acceptance

- With every selected detection source off, expect `unknown` with reason `idle`. There should be no status polling by this helper.
- During a controlled detection, a valid pan appears in the sensor attributes. Expect `unknown`/`unconfirmed` initially, then the calibrated area after sufficient fresh observations. A gap or inner sector boundary remains unknown.
- When all sources turn off, the area clears immediately. An unavailable source does not count as on; another on source keeps observation active.
- Save options with the helper disabled. Expect `unknown`/`disabled`. Enable it again and confirm that a previous area is not reused without new observations.
- Resolve any `unavailable` state using [the reason guide](troubleshooting.md) before connecting automations. Do not substitute a previously confirmed area for an unknown result.

## Upgrade, rollback and removal

Before upgrading, retain the verified previous ZIP, its release identity, and a Home Assistant backup that includes configuration entries. Copy your sources, calibration sectors and timing settings somewhere private. A folder backup alone does not preserve HA-managed configuration. Do not post this information in a public issue.

For a manual upgrade, stop Home Assistant, replace the entire integration directory with the verified release contents, and start Home Assistant. This avoids leftover files from an older version. With HACS, use its update/download controls and restart when requested. Do not remove and recreate the helper merely to update its files: retaining the config entry preserves its sensor identity. Confirm the loaded version in integration diagnostics and repeat the first-run checks.

Options changes reload this helper automatically and reset confirmation. File updates require a Home Assistant restart. A camera entity rename is handled through its registry identity; renamed detection entities must be reselected in options. Removing and re-adding the built-in ONVIF device creates a new binding: recreate the helper deliberately and check dependent dashboards and automations.

To roll back a release with a compatible stored configuration format, stop Home Assistant, restore the complete previous verified integration directory, and restart. For HACS, select the previous release through its download controls and restart. If release notes describe a configuration migration that the older release cannot read, restore the corresponding Home Assistant backup as well. Recheck calibration and detection after recovery.

To remove the helper, delete its config entry under Devices & services, then remove its files through your installation method and restart. Check references to its sensor in your own automations. The built-in ONVIF camera and its credentials belong to that separate integration.
