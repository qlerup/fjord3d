# Fjord3D

Fjord3D is a self-hosted library and toolbox for 3D models, with browser previews,
per-model metadata and Bambu Studio slicing for NAS and Docker workflows.

## Upgrading an existing installation

Update FjordHub first, then update Fjord3D. FjordHub migrates the previous app ID,
login permissions and installation registration. It preserves the actual mounted
database, model and thumbnail directories, builds the new image before stopping
the previous container, and checks the new container's health before retiring it.
If startup fails, the previous container is restarted.

For a manually managed installation, pull the repository and run
`sh "Useful Scripts/fjord3d-update.sh"` from the existing checkout. This script
also preserves existing mounts and performs the container transition. Existing
databases and installation markers retain their stored filenames when needed;
new installations use `fjord3d.db` and `fjord3d.install.json`.

The previous app ID, environment setting and Docker name are accepted only as
migration aliases. Existing NAS folder names do not need to be changed.

## What Is Implemented

### Core features

- Login and first-run setup (first user becomes admin)
- Folder/file browser in the web UI with side panel
- TUS resumable upload (large files / unstable networks)
- Create folder, rename, delete, and file metadata editing
- Share one or more folders with permissions:
  - `view`
  - `upload`
  - `manage`
- Share options:
  - Expiry (days/hours)
  - Password protection
  - Require visitor name
  - External DNS base URL

### 3D and preview

- 3D thumbnails in the file grid for `.glb`, `.gltf`, `.stl`, `.obj`, `.step`, `.stp`, `.3mf`, `.lys`
- In-browser 3D viewer for `.glb`, `.gltf`, `.stl`, `.obj`

### Slicer integration (Bambu Studio)

- Slicing through the Bambu Studio CLI from backend jobs
- Studio-inspired **Slice STL** modal with a large preview scene
- Rotation (X/Y/Z) with live preview and footprint/height info
- Profile selection in the modal:
  - Printer
  - Print profile
  - Filament profile
  - Support mode/type/style
- H2D/dual-nozzle controls for left/right nozzle selection in the modal
- Failed slice jobs expose the error and latest debug trace from the file drawer

`SLICING_DISABLED=0` keeps the slicer actions available for testing and normal use.
Set `SLICING_DISABLED=1` when slicing must be paused without removing the profiles.

### Slicer profiles in Settings

- Profile cards for:
  - Printer profile (`machine.json`)
  - Print settings (`process.json`)
  - Filament profile (`filament.json`)
  - Config bundles (`ini/cfg/conf/txt`)
- Upload methods:
  - `Upload files` button (modal)
  - Drag and drop directly on each profile card

### Printer bed sizes (bed mapping)

- Table includes:
  - Printer profile
  - Vendor
  - Model
  - X/Y (auto-detected from model)
  - Source
  - Actions
- `Add printer`, `Edit` (modal for manual X/Y), `Delete`
- Save/reset mapping
- Deleted rows are persisted as hidden so they do not auto-return on refresh

## Built-in Bambu Presets (Bed Sizes)

The following Bambu presets are included for automatic X/Y defaults:

- H2D / H2D Pro: `350 x 320`
- A1 mini: `180 x 180`
- A1: `256 x 256`
- P1S / P1P: `256 x 256`
- X1 / X1 Carbon / X1E: `256 x 256`

## Run Locally With Docker

### Fastest Setup (Recommended)

```bash
ssh <user>@<server-ip>
cd ~
git clone https://github.com/qlerup/fjord3d.git
cd fjord3d
chmod +x scripts/fresh_setup_lxc.sh
./scripts/fresh_setup_lxc.sh
```

This wizard is step-by-step and guides you through:

1. Basic app settings (port/timezone)
2. Upload destination strategy:
   - NAS path already mounted (for example Proxmox bind mount), or
   - Script-managed NFS mount in `/etc/fstab`
3. App data + thumbnail paths
4. Slicer defaults
5. Optional strict fs-type checks

After the questions, it runs preflight checks and starts Docker Compose.

Re-run later:

```bash
# full guided wizard again
./scripts/fresh_setup_lxc.sh

# only preflight + start (reuse existing .env)
./scripts/fresh_setup_lxc.sh --start-only

# backward-compatible alias (still works)
./scripts/fresh_setup.sh
```

### Proxmox Host -> LXC Bind-Mount (Manual quick commands)

Use this if you want uploads on NAS via a Proxmox host mount + LXC bind mount.

1. Mount NFS share on the Proxmox host:

```bash
mkdir -p /mnt/pve/synology-fjord3d
mount -t nfs 10.10.0.161:/volume1/Fjord3DProxmox /mnt/pve/synology-fjord3d
```

2. Verify host mount:

```bash
ls -la /mnt/pve/synology-fjord3d
```

3. Bind-mount share into the LXC (example CTID `1001`):

```bash
pct set 1001 -mp0 /mnt/pve/synology-fjord3d,mp=/mnt/fjord3d-nfs
pct restart 1001
```

4. Enter container and verify:

```bash
pct enter 1001
ls -la /mnt/fjord3d-nfs
```

5. Create uploads folder inside container:

```bash
mkdir -p /mnt/fjord3d-nfs/uploads
```

Then use this path in setup:

- `UPLOADS_HOST_DIR=/mnt/fjord3d-nfs/uploads`

### Manual Setup

```bash
cd fjord3d
cp .env.example .env
docker compose up -d --build
```

Then open:

- `http://<server-ip>:9090` (or the port configured in `.env`)
- `http://localhost:9090` if you are on the server itself

## Important Environment Variables (.env)

- `DATA_DIR`
- `UPLOADS_HOST_DIR`
- `TUS_TMP_DIR` (container path for resumable-upload temp files; default compose value keeps it on `/uploads`)
- `THUMBS_HOST_DIR`
- `THUMB_WORKER_COUNT`
- `THUMB_DEFER_MAX_SECONDS`
- `THUMB_MESH_RENDER_MAX_BYTES`
- `BAMBUSTUDIO_BIN` (default: `bambu-studio`)
- `BAMBUSTUDIO_TIMEOUT_SEC` (default: `1800`)
- `BAMBUSTUDIO_CONFIG_PATH` (optional)
- `BAMBUSTUDIO_PROFILE_ROOT` (optional)
- `BAMBUSTUDIO_PRINTER_PROFILES` (optional fallback list)
- `BAMBUSTUDIO_PRINT_PROFILES` (optional fallback list)
- `BAMBUSTUDIO_FILAMENT_PROFILES` (optional fallback list)
- `BAMBUSTUDIO_LOAD_SETTINGS` (optional direct load)
- `BAMBUSTUDIO_LOAD_FILAMENTS` (optional direct load)
- `BAMBUSTUDIO_ALLOW_PROFILE_FALLBACK` (`1`/`0`)
- `SMS_TOKEN_ENCRYPTION_KEY` (Fernet key for encrypted GatewayAPI token storage; setup/update scripts generate it when missing)
- `MAKERWORLD_CREDENTIALS_ENCRYPTION_KEY` (Fernet key for encrypted MakerWorld credential storage)
- `SLICER_PROFILE_MAX_BYTES`
- `EXPECT_UPLOADS_FSTYPES` (optional mount validation)
- `EXPECT_THUMBS_FSTYPES` (optional mount validation)
- `EXPECT_DATA_FSTYPES` (optional mount validation)
- `SETUP_NFS_UPLOADS_ENABLED` (`1`/`0`, optional rerun metadata)
- `SETUP_NFS_EXPORT` (optional rerun metadata)
- `SETUP_NFS_MOUNT_ROOT` (optional rerun metadata)
- `SETUP_NFS_UPLOADS_SUBDIR` (optional rerun metadata)
- `SETUP_NFS_FSTAB_OPTIONS` (optional rerun metadata)

## Bambu Studio Presets From Local Installation

If you want to pull default profiles directly from Bambu Studio on Windows, they are typically here:

`C:\Program Files\Bambu Studio\resources\profiles\BBL`

Usually split into:

- `filament`
- `machine`
- `process`

You can upload these files into the matching profile boxes in Fjord3D under Settings -> Slicer.

## Plate Assets For Slicer View

A versioned folder is provided for model/plate files so assets can travel with repo/deploy:

- `static/slicer-plates/`

Place plate files there to include them in installs for other users.
When model-to-file mapping is configured, the UI can switch plate assets automatically based on selected printer model.

## Useful Scripts

Helper scripts are included here:

- `Useful Scripts/fjord3d-update.sh`
- `Useful Scripts/fjord3d-cleanup.sh`
- `Useful Scripts/README.md`

These scripts support operations, updates, and cleanup for Fjord3D NAS deployments using Docker Compose.

## Data Paths

Inside the container:

- app state root: `/data`
- uploads root: `/uploads`
- thumbnails root: `/thumbs`

Typical split deployment:

- `${DATA_DIR}` -> `/data` (local disk, DB + internal app state)
- `${UPLOADS_HOST_DIR}` -> `/uploads` (NAS/NFS for shared files)
- `${THUMBS_HOST_DIR}` -> `/thumbs` (local or NAS, your choice)

Stored paths:

- database: `/data/fjord3d.db`
- uploaded files: `/uploads`
- thumbnails: `/thumbs`
- TUS temp files: `/uploads/.tus_uploads` by default, configurable with `TUS_TMP_DIR`
- slicer profiles: `/data/bambu/profiles`
- sliced output: `/data/bambu/sliced`

## Notes

- Large uploads should keep `TUS_TMP_DIR` on the same filesystem as `/uploads` (the Docker Compose default does this) so finalizing a file is a rename instead of a full copy.
- During multi-file TUS uploads, thumbnail workers are deferred until the active upload batch finishes.
- Very large raw mesh files skip automatic mesh thumbnail rendering when they exceed `THUMB_MESH_RENDER_MAX_BYTES`; embedded 3MF/LYS/PWSCENE preview images are still used when available.
- If Bambu Studio release auto-detection fails during build, pin an AppImage URL in `.env` and rebuild.
- `fjord3d-cleanup.sh` is destructive and should be used with care.
