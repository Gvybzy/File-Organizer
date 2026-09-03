# 📁 File Organizer

A lightweight desktop file organizer built with **Python and PySide6** that automatically sorts files into categorized folders based on their file extensions.

## ✨ Features

* 📂 **Automatic File Organization** — Sorts files into folders such as Images, Documents, Music, Videos, Archives, Programs, and Code.
* 👀 **Preview** — See how files will be categorized before organizing them.
* ↩️ **Undo** — Revert the most recent organization operation.
* 🏷️ **Custom Categories** — Add your own file extensions and destination folders.
* 📜 **Activity Log** — Keeps a record of organization and undo operations.
* 📊 **Progress Tracking** — Shows the current progress while files are being organized.
* 📁 **Folder Selection** — Choose which folder you want to organize.
* 💾 **Persistent Settings** — Custom categories and organization data are saved locally.

## 📥 Download

Want to use File Organizer without installing Python?

### Windows

Download the latest `.exe` from the **GitHub Releases** page:

 *[Download File Organizer](../../releases/latest)**

The executable is provided as a packaged Windows application, so Python does not need to be installed separately.

> **Note:** Windows may display a security warning when running an executable downloaded from the internet. Only download releases from this repository.

## Built With

* 🐍 **Python**
* 🖥️ **PySide6**
* 📄 **JSON**
* 📁 **OS / shutil**

## Run From Source

If you prefer running the Python source code:

### 1. Clone the repository

```bash
git clone https://github.com/Gvybzy/File-Organizer.git
cd File-Organizer
```

### 2. Install the dependency

```bash
pip install PySide6
```

### 3. Run the application

```bash
python file_organizer.py
```

## How It Works

1. Click **Browse** and select the folder you want to organize.
2. Open the **Preview** tab to see how your files will be categorized.
3. Click **Organize**.
4. Files are moved into their corresponding category folders.
5. Use **Undo** if you want to reverse the latest organization operation.

## Default Categories

| File Types                                                      | Category  |
| --------------------------------------------------------------- | --------- |
| `.jpg`, `.jpeg`, `.png`, `.gif`, `.svg`, `.webp`                | Images    |
| `.pdf`, `.doc`, `.docx`, `.txt`, `.rtf`, `.odt`                 | Documents |
| `.xls`, `.xlsx`, `.ppt`, `.pptx`, `.csv`                        | Documents |
| `.mp3`, `.wav`, `.flac`, `.aac`, `.ogg`, `.wma`                 | Music     |
| `.mp4`, `.mkv`, `.avi`, `.mov`, `.wmv`, `.flv`                  | Videos    |
| `.zip`, `.rar`, `.7z`, `.tar`, `.gz`                            | Archives  |
| `.exe`, `.msi`, `.apk`                                          | Programs  |
| `.py`, `.js`, `.html`, `.css`, `.json`, `.xml`, `.cpp`, `.java` | Code      |
| Other extensions                                                | Other     |

## Custom Categories

File Organizer allows you to create your own categories.

For example:

```text
.xyz → My Files
.log → Logs
.psd → Photoshop
```

Custom categories are saved locally so they can be used again the next time the application starts.

## Activity Log

The application records organization actions in a local JSON log.

Example:

```text
[2026-09-03 19:30:12] organize
    Moved 24 files, skipped 2
```

The application keeps the most recent activity records instead of allowing the log to grow indefinitely.

## Undo

After organizing files, File Organizer stores the information needed to reverse the latest operation.

Click **Undo** to move the files back to their original locations.

 The Undo feature is intended for the most recent organization operation.

## Important

File Organizer **moves files rather than copying them**.

Before clicking **Organize**, make sure you selected the correct folder.

It is recommended to test the application on a folder containing non-critical files first.

## Project Status

**Version 1.0 — Functional**

Current functionality includes file organization, preview, custom categories, activity logging, progress tracking, and undo support.

### Possible Future Improvements

* Drag-and-drop folder support
* Duplicate file handling
* More advanced sorting rules
* File size/date-based organization
* Dark/light theme selection
* Improved error reporting
* Portable `.exe` distribution
* Additional customization options

## Project Structure

```text
File-Organizer/
│
├── file_organizer.py
├── README.md
├── requirements.txt
│
└── Generated files
    ├── organizer_log.json
    ├── undo_data.json
    └── custom_categories.json
```

## Author

**Gvybzy**

Built as part of my ongoing journey of learning Python, automation, and software development.

---

### Built with Python

Simple idea: **pick a folder → preview → organize → undo if needed.**
