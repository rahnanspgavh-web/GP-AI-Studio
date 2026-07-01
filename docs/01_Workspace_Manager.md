# GP AI Studio - Workspace Manager

## Purpose

The Workspace Manager is responsible for managing the physical storage location for all GP AI Studio projects and generated content.

The application source code remains on the SSD.

All generated projects, images, videos, audio, exports, logs and backups are stored in a user-selected Workspace on an external hard drive.

---

## Requirements

On first launch:

1. Check whether a workspace has already been configured.

2. If not:

   Ask the user to select a folder.

   Example:

   H:\GP-AI-Workspace

3. Automatically create the following folders:

```
01_Projects
02_Assets
03_Exports
04_Backups
05_Templates
06_Downloads
07_Logs
08_Cache
```

4. Create a configuration file:

```
workspace.json
```

Store:

- Workspace path
- Creation date
- GP AI Studio version

5. On future launches:

- Automatically load `workspace.json`.
- Verify the workspace exists.
- If it is missing, ask the user to reconnect the drive.

---

## Rules

- Never hardcode drive letters.
- Always verify the workspace exists before use.
- Never delete user files automatically.
- Always ask for confirmation before deleting anything.

---

## Future Enhancements

- Support multiple workspaces.
- Allow moving a workspace to another drive.
- Allow backup and restore.
- Display workspace usage (size, free space, project count).