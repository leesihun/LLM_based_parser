# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is an LLM-based query analysis system for cellphone reviews, built around Ollama for local LLM inference. The system processes Korean and English Excel files containing positive/negative review data and provides semantic search, keyword extraction, and statistical analysis capabilities.

For the embedding, I'm using nomic-embed-text:latest and for the modle, gemma3:12b.
The configuraionts must be configurable via a seperate script.

First, read all of .xlsx files and make a big .md file containing all of the responses.
If some of columns are empty, don't change it.
Use keywords identifying language type, and pros and cons for easy identification.
Translate to enlgish if other language is used and correct the misspelled responses.

BAsed on the big .md file, the LLM will be ased questions such as 
1. How many responses are good and how many are bad?
2. What keyword is used most often? and how many times has it been mentioned? Semantically analyze it.
3. Give me an example of good review regarding screen size.
4. Give me an example of bad review regarding screen time.

The LLM must be able to answer these questions.

Plan before coding and check with me

The code you have created will be used on another computer locally. So don't test anything!!