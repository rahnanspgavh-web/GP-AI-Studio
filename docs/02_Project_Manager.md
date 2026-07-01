# GP AI Studio - Project Manager

## Purpose

The Project Manager is responsible for creating, organizing and maintaining every GP AI Studio project.

Every title is treated as one independent project.

Examples

- Abhirami Anthathi
- Thirukkural
- Kandha Sashti Kavasam
- Temple Tour
- Health Topic
- Food Recipe

Each project contains everything required to generate and publish content.

---

# Workspace

Projects are created inside

I:\GP-AI-Workspace

under

01_Projects

Never save generated files inside the GP AI Studio application folder.

---

# Project Creation

When the user creates a project,

Example

Abhirami Anthathi

Automatically create

01_Projects
    Abhirami Anthathi

Inside create

00_Project
01_Research
02_Scripts
03_Prompts
04_Images
05_Videos
06_Audio
07_Subtitles
08_Final
09_Website
10_YouTube
11_Logs
12_Backups

---

# 02_Scripts

Automatically create

Tamil
English
Hindi

These language folders are available for every project.

Actual generation of Tamil, English and Hindi scripts happens only after user confirmation.

---

# Metadata

Inside

00_Project

create

project.json

progress.json

settings.json

---

# project.json

Store

Project Name

Project Type

Languages

Created Date

Modified Date

Workspace Path

Status

Version

---

# progress.json

Track

Research

Script

Translation

Prompt

Images

Videos

Audio

Subtitles

Final Video

Website

YouTube

Each item stores

Pending

Running

Completed

Failed

Skipped

---

# settings.json

Store

Default Language

Generate English

Generate Hindi

Script Provider

Image Provider

Video Provider

Audio Provider

Subtitle Provider

Website Enabled

YouTube Enabled

---

# Rules

Never overwrite an existing project.

If a project already exists,

ask the user whether to

Open Existing

Duplicate

Cancel

Never delete project data automatically.

Always ask for confirmation.

---

# Logging

Every project maintains its own log folder.

Store operation logs inside

11_Logs

---

# Backup

Every project maintains

12_Backups

Future versions will automatically create backups.

---

# Future Expansion

Support

Project Search

Project Rename

Project Archive

Project Duplicate

Project Export

Project Import

Project Statistics

Project Resume

Multi-language expansion

Additional AI providers

Cloud synchronization (optional)

---

# Goal

Every future engine

Research

Script

Prompt

Image

Video

Audio

Subtitle

Website

YouTube

must use the Project Manager instead of creating files independently.

The Project Manager is the single source of truth for every GP AI Studio project.