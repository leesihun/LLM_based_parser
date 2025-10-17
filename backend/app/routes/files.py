"""File management routes."""

from __future__ import annotations

import os
from pathlib import Path

from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename

from backend.app.routes.context import RouteContext
from backend.common.errors import ValidationError


def create_blueprint(ctx: RouteContext) -> Blueprint:
    services = ctx.services
    file_handler = services.file_handler
    llm_client = services.llm_client

    bp = Blueprint("files", __name__, url_prefix="/api/files")

    # Define upload folder
    UPLOAD_FOLDER = Path(__file__).resolve().parents[3] / "uploads"
    UPLOAD_FOLDER.mkdir(exist_ok=True)

    ALLOWED_EXTENSIONS = {
        '.pdf', '.docx', '.xlsx', '.xls', '.txt', '.md',
        '.py', '.js', '.json', '.csv', '.html', '.xml', '.yml', '.yaml'
    }

    def allowed_file(filename: str) -> bool:
        """Check if file extension is allowed."""
        return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS

    @bp.post("/upload")
    @ctx.require_auth
    def upload_file():
        """Upload a file for analysis."""
        if 'file' not in request.files:
            raise ValidationError("No file provided")

        file = request.files['file']
        if file.filename == '':
            raise ValidationError("No file selected")

        if not allowed_file(file.filename):
            raise ValidationError(f"File type not allowed. Supported types: {', '.join(ALLOWED_EXTENSIONS)}")

        # Get user info from request
        user = getattr(request, "user", {})
        user_id = user.get("user_id", "unknown")

        # Create user-specific folder
        user_folder = UPLOAD_FOLDER / user_id
        user_folder.mkdir(exist_ok=True)

        # Secure the filename
        filename = secure_filename(file.filename)
        file_path = user_folder / filename

        # Save the file
        file.save(str(file_path))

        # Return file info
        return jsonify({
            "success": True,
            "file_id": file_path.stem,
            "filename": filename,
            "message": f"File '{filename}' uploaded successfully"
        }), 201

    @bp.get("")
    @ctx.require_auth
    def list_files():
        """List all files for the current user."""
        user = getattr(request, "user", {})
        user_id = user.get("user_id", "unknown")

        user_folder = UPLOAD_FOLDER / user_id
        if not user_folder.exists():
            return jsonify({"files": []})

        files = []
        for file_path in user_folder.iterdir():
            if file_path.is_file():
                files.append({
                    "file_id": file_path.stem,
                    "original_name": file_path.name,
                    "file_type": file_path.suffix,
                    "size": file_path.stat().st_size,
                    "uploaded_at": file_path.stat().st_mtime
                })

        return jsonify({"files": files})

    @bp.post("/<file_id>/read")
    @ctx.require_auth
    def read_file(file_id: str):
        """Read and analyze a file with a question."""
        payload = request.get_json(silent=True) or {}
        question = payload.get("question", "")
        session_id = payload.get("session_id")

        if not question:
            raise ValidationError("Question is required")

        user = getattr(request, "user", {})
        user_id = user.get("user_id", "unknown")

        # Find the file
        user_folder = UPLOAD_FOLDER / user_id
        file_path = None
        for f in user_folder.iterdir():
            if f.stem == file_id:
                file_path = f
                break

        if not file_path or not file_path.exists():
            raise ValidationError(f"File not found: {file_id}")

        # Read file content
        try:
            # Simple text file reading for now
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Create context with file content and question
            context_message = f"Based on the following file content:\n\n{content}\n\nUser question: {question}"

            # Get response from LLM
            response = llm_client.get_response(context_message, session_id=session_id)

            return jsonify({
                "response": response.get("response"),
                "session_id": response.get("session_id"),
                "file_id": file_id
            })
        except Exception as e:
            raise ValidationError(f"Failed to read file: {str(e)}")

    @bp.post("/<file_id>/analyze-json")
    @ctx.require_auth
    def analyze_json_file(file_id: str):
        """Perform comprehensive JSON analysis on the uploaded file."""
        user = getattr(request, "user", {})
        user_id = user.get("user_id", "unknown")

        # Find the file
        user_folder = UPLOAD_FOLDER / user_id
        file_path = None
        for f in user_folder.iterdir():
            if f.stem == file_id:
                file_path = f
                break

        if not file_path or not file_path.exists():
            raise ValidationError(f"File not found: {file_id}")

        # Check if it's a JSON file
        if file_path.suffix.lower() != '.json':
            raise ValidationError("File is not a JSON file")

        # Get enhanced processor from services
        try:
            from backend.services.files.enhanced_file_processor import EnhancedFileProcessor
            processor = EnhancedFileProcessor()

            # Perform analysis
            analysis = processor.analyze_file(str(file_path), '.json', user_id)

            return jsonify({
                "success": analysis.get('success', False),
                "file_id": file_id,
                "filename": file_path.name,
                "analysis": analysis
            })

        except Exception as e:
            raise ValidationError(f"Failed to analyze JSON file: {str(e)}")

    @bp.delete("/<file_id>")
    @ctx.require_auth
    def delete_file(file_id: str):
        """Delete a file."""
        user = getattr(request, "user", {})
        user_id = user.get("user_id", "unknown")

        # Find and delete the file
        user_folder = UPLOAD_FOLDER / user_id
        file_path = None
        for f in user_folder.iterdir():
            if f.stem == file_id:
                file_path = f
                break

        if not file_path or not file_path.exists():
            raise ValidationError(f"File not found: {file_id}")

        try:
            file_path.unlink()
            return jsonify({
                "success": True,
                "message": f"File deleted successfully"
            })
        except Exception as e:
            raise ValidationError(f"Failed to delete file: {str(e)}")

    return bp
