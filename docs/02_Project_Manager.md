# GP AI Studio - Project Manager Specification

---

# Purpose

The Project Manager is the heart of GP AI Studio.

It is responsible for creating, loading, validating, maintaining, backing up and tracking every project created inside GP AI Studio.

Every content title is treated as one independent project.

Examples:

- Abhirami Anthathi
- Thirukkural
- Kandha Shashti Kavasam
- Bhagavad Gita
- Temple History

Each title = One Project

---

# Workspace Location

The workspace location is configured by the Workspace Manager.

Example:

I:\GP-AI-Workspace

The Project Manager must NEVER hardcode a drive letter.

It always loads the workspace path from the Workspace Manager configuration.

---

# Project Folder Structure

When creating a new project, automatically generate:

<Project Name>

│

├──00_Project

├──01_Research

├──02_Scripts

│ ├──Tamil

│ ├──English

│ └──Hindi

├──03_Prompts

├──04_Images

├──05_Videos

├──06_Audio

├──07_Subtitles

├──08_Final

├──09_Website

├──10_YouTube

├──11_Logs

└──12_Backups

---

# Project Metadata

Create

project.json

Contains:

- Project ID
- Project Name
- Category
- Created Date
- Last Modified Date
- Workspace Path
- Project Version
- Status
- Current Module

---

# Progress Tracking

Create

progress.json

Tracks completion of

Research

Scripts

Prompts

Images

Videos

Audio

Subtitles

Final Video

Website

YouTube

Every engine updates this file automatically.

---

# Project Settings

Create

settings.json

Contains

Default Language

Supported Languages

Video Resolution

Aspect Ratio

Video Duration

Image Style

Voice Style

Music Style

Subtitle Style

Output Format

---

# Language Support

Supported Languages

Tamil

English

Hindi

Language selection applies to

Research

Scripts

Prompts

Images

Videos

Audio

Subtitles

The user chooses the language(s).

---

# Functions

The Project Manager must support

Create Project

Open Project

Rename Project

Delete Project

Archive Project

Restore Project

Duplicate Project

Validate Project

Repair Project

Backup Project

---

# Validation

Whenever a project is opened

Verify folders

Verify JSON files

Create missing folders

Create missing JSON files

Repair corrupted configuration

---

# Logging

Store logs in

11_Logs

Log every important action

Project Created

Project Loaded

Project Updated

Research Completed

Script Generated

Image Generated

Video Generated

Audio Generated

Published

Backup Created

---

# Future Integration

Designed to work with

Workspace Manager

API Manager

Settings Manager

Research Engine

Script Engine

Prompt Engine

Image Engine

Video Engine

Audio Engine

Subtitle Engine

Video Composer

Website Publisher

YouTube Publisher

Automation Scheduler

Dashboard

---

# Design Rules

Use pathlib

No hardcoded paths

Automatic recovery

Automatic folder creation

Automatic JSON creation

Automatic progress tracking

Support thousands of projects

Safe for future expansion

Maintain backward compatibility

---

# Future Enhancements

Project Templates

Project Search

Project Tags

Project Statistics

Automatic Backup Scheduling

Project Export

Project Import

Cloud Synchronization (future)
