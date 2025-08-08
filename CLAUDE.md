# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Important notice.

- THis codebase is intended to be used elsewhere, not this computer
- Don't test ollama functionality ever.
- Always build modular script with comments to show what funtionality is what.
- Forget everything previously mentioned, including the gits
- LLM backbone is provided here. Based on this, build features.
- Organize all files. ex. source files in /src, authorizations in /auth folder, etc.

## Repository Overview

Upon the provided backbone code, add the following features.
 - setup a new .py file for each features and changes to the existing codes must be minimal

### Setup preparation
1. First gather all of the .xlsx files in data and combine them to a big .md file
2. Read the .md file and setup a RAG system using chromadb

### LLM serve
- For the followings, add buttons to enable such features to the webui.
1. Add capability to RAG using the RAG system set up previously.
2. Add capability to 'READ' the .md file provided.


### System settings
- Add capabilty to upload files to the LLM.
- The LLM should be capable of 'READING' the filie.