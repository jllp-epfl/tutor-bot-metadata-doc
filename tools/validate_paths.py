import json
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Any
import os
import re


def list_non_hidden_files(root_folder: Path) -> List[str]:
    """
    Recursively list all non-hidden files under root_folder,
    returning their paths relative to root_folder as strings.
    """
    all_files = []
    for path in root_folder.rglob("*"):
        if path.is_file():
            # skip hidden files or those in hidden dirs
            rel_parts = path.relative_to(root_folder).parts
            if any(part.startswith(".") for part in rel_parts):
                continue
            all_files.append(str(path.relative_to(root_folder)))

    return all_files


def validate_gemini_json_structure(json_path: Path) -> bool:
    """Validate that a Gemini JSON file has the correct structure."""
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        required_fields = [
            "language",
            "general_description_en",
            "video_keywords_en",
            "video_keywords_fr",
            "video_segments",
        ]

        # Check top-level required fields
        for field in required_fields:
            if field not in data:
                return False

        # Check video_segments structure
        if not isinstance(data["video_segments"], list):
            return False

        for segment in data["video_segments"]:
            segment_required_fields = [
                "start_time",
                "end_time",
                "key_frame_time",
                "contains_math",
                "contains_diagram",
                "teacher_uses_pointer",
                "segment_audio_transcription_en",
                "segment_audio_transcription_fr",
                "extracted_text_video_frame",
                "short_description_video_segment_en",
                "short_description_video_segment_fr",
                "segment_keywords_en",
                "segment_keywords_fr",
            ]
            for field in segment_required_fields:
                if field not in segment:
                    return False

        return True
    except:
        return False


def validate_pdf_timestamp_json_structure(json_path: Path) -> bool:
    """Validate that a PDF timestamp JSON file has the correct structure."""
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            return False

        for item in data:
            if not isinstance(item, dict):
                return False
            if "page_number" not in item or "timestamps" not in item:
                return False
            if not isinstance(item["timestamps"], list):
                return False
            for timestamp in item["timestamps"]:
                if not isinstance(timestamp, dict):
                    return False
                if (
                    "start_timestamp" not in timestamp
                    or "end_timestamp" not in timestamp
                ):
                    return False

        return True
    except:
        return False


def validate_associated_video_lecture(
    video: Dict[str, Any], doc_id: int, index: int, root_folder: Path
) -> List[Tuple[str, str, int]]:
    """Validate a single associated video lecture."""
    errors = []
    prefix = f"associated_video_lectures[{index}]"

    # Check required fields exist
    required_fields = [
        "title",
        "is_gemini_processed_video",
        "original_link",
        "path",
        "srt_path",
        "pdf_page_video_ts_path",
    ]
    for field in required_fields:
        if field not in video:
            errors.append((f"{prefix}.{field}", "required field missing", doc_id))

    # Validate title doesn't contain "_"
    if "title" in video and video["title"] is not None and "_" in str(video["title"]):
        errors.append(
            (f"{prefix}.title", "cannot contain underscore characters", doc_id)
        )

    # Validate original_link contains "mediaspace" if not null
    if "original_link" in video and video["original_link"] is not None:
        if (
            not isinstance(video["original_link"], str)
            or "mediaspace" not in video["original_link"]
        ):
            errors.append(
                (
                    f"{prefix}.original_link",
                    "must be null or contain 'mediaspace'",
                    doc_id,
                )
            )

    # Validate srt_path ends in .srt and exists if not null
    if "srt_path" in video and video["srt_path"] is not None:
        if not isinstance(video["srt_path"], str) or not video["srt_path"].endswith(
            ".srt"
        ):
            errors.append(
                (f"{prefix}.srt_path", "must be null or end with '.srt'", doc_id)
            )
        else:
            # Check if file exists
            srt_full_path = root_folder / video["srt_path"]
            if not srt_full_path.exists() or not srt_full_path.is_file():
                errors.append((f"{prefix}.srt_path", "file does not exist", doc_id))

    # Validate pdf_page_video_ts_path exists and has correct structure if not null
    if (
        "pdf_page_video_ts_path" in video
        and video["pdf_page_video_ts_path"] is not None
    ):
        ts_full_path = root_folder / video["pdf_page_video_ts_path"]
        if not ts_full_path.exists() or not ts_full_path.is_file():
            errors.append(
                (f"{prefix}.pdf_page_video_ts_path", "file does not exist", doc_id)
            )
        elif not validate_pdf_timestamp_json_structure(ts_full_path):
            errors.append(
                (f"{prefix}.pdf_page_video_ts_path", "invalid JSON structure", doc_id)
            )

    return errors


def validate_document_fields(
    doc: Dict[str, Any], root_folder: Path
) -> List[Tuple[str, str, int]]:
    """
    Validate document field values according to business rules.
    Returns list of tuples: (field_name, error_message, document_id)
    """
    errors = []
    doc_id = doc.get("id", "unknown")

    # "week" has to be an int or null
    if "week" in doc and doc["week"] is not None:
        if not isinstance(doc["week"], int):
            errors.append(
                (
                    "week",
                    f"must be an integer or null, got: {type(doc['week']).__name__}",
                    doc_id,
                )
            )

    # "number" and "sub_number" has to be a string or null
    for field in ["number", "sub_number"]:
        if field in doc and doc[field] is not None:
            if not isinstance(doc[field], str):
                errors.append(
                    (
                        field,
                        f"must be a string or null, got: {type(doc[field]).__name__}",
                        doc_id,
                    )
                )

    # "model" has to be "gemini-2.5-flash", "gemini-2.5-pro" or null
    if "model" in doc and doc["model"] is not None:
        valid_models = ["gemini-2.5-flash", "gemini-2.5-pro"]
        if doc["model"] not in valid_models:
            errors.append(
                (
                    "model",
                    f"must be one of {valid_models} or null, got: {doc['model']}",
                    doc_id,
                )
            )

    # when "subtype" is "video_lecture", "path" must end in "json" and "is_video" must be true
    if doc.get("subtype") == "video_lecture" and not doc.get("is_qa"):  # new
        if "path" in doc and doc["path"] is not None:
            if not doc["path"].endswith(".json"):
                errors.append(
                    (
                        "path",
                        "must end with '.json' when subtype is 'video_lecture'",
                        doc_id,
                    )
                )
        if "is_video" in doc and doc["is_video"] is not True:
            errors.append(
                ("is_video", "must be true when subtype is 'video_lecture'", doc_id)
            )

    # "from" and "until" has to be a string in format "09/09/2025" or null
    date_pattern = re.compile(r"^\d{2}/\d{2}/\d{4}$")
    for field in ["from", "until"]:
        if field in doc and doc[field] is not None:
            if not isinstance(doc[field], str):
                errors.append(
                    (field, "must be a string in format 'DD/MM/YYYY' or null", doc_id)
                )
            elif not date_pattern.match(doc[field]):
                errors.append(
                    (
                        field,
                        f"must be in format 'DD/MM/YYYY', got: {doc[field]}",
                        doc_id,
                    )
                )

    # "tikz" has to be false or null
    if "tikz" in doc and doc["tikz"] is not None and doc["tikz"] is not False:
        errors.append(("tikz", f"must be false or null, got: {doc['tikz']}", doc_id))

    # "title" can't have "_" characters
    if "title" in doc and doc["title"] is not None:
        if "_" in str(doc["title"]):
            errors.append(("title", "cannot contain underscore characters", doc_id))

    # if "subtype" is "book_in_bibliography" then "one_chunk_per_page" and "one_chunk_per_doc" has to be false
    if doc.get("subtype") == "book_in_bibliography":
        for field in ["one_chunk_per_page", "one_chunk_per_doc"]:
            if field in doc and doc[field] is not False:
                errors.append(
                    (
                        field,
                        "must be false when subtype is 'book_in_bibliography'",
                        doc_id,
                    )
                )

    # "processing_method" has to be "gemini", "tesseract", "google" or null
    if "processing_method" in doc and doc["processing_method"] is not None:
        valid_methods = ["gemini", "tesseract", "google"]
        if doc["processing_method"] not in valid_methods:
            errors.append(
                (
                    "processing_method",
                    f"must be one of {valid_methods} or null, got: {doc['processing_method']}",
                    doc_id,
                )
            )

    # "srt_path" has to be null or be a string that ends in ".srt"
    if "srt_path" in doc and doc["srt_path"] is not None:
        if not isinstance(doc["srt_path"], str) or not doc["srt_path"].endswith(".srt"):
            errors.append(("srt_path", "must be null or end with '.srt'", doc_id))

    # "original_link" has to be null or be a string that contains "mediaspace"
    if "original_link" in doc and doc["original_link"] is not None:
        if (
            not isinstance(doc["original_link"], str)
            or "mediaspace" not in doc["original_link"]
        ):
            errors.append(
                ("original_link", "must be null or contain 'mediaspace'", doc_id)
            )

    # if "is_gemini_processed_video" is true then "is_video" has to be true too
    if doc.get("is_gemini_processed_video") is True:
        if doc.get("is_video") is not True:
            errors.append(
                (
                    "is_video",
                    "must be true when is_gemini_processed_video is true",
                    doc_id,
                )
            )

        # NEW RULE: if "is_gemini_processed_video" is true, validate JSON structure
        if "path" in doc and doc["path"] is not None:
            json_full_path = root_folder / doc["path"]
            if json_full_path.exists() and json_full_path.is_file():
                if not validate_gemini_json_structure(json_full_path):
                    errors.append(
                        ("path", "Gemini JSON file has invalid structure", doc_id)
                    )

    # validate associated_video_lectures structure
    if (
        "associated_video_lectures" in doc
        and doc["associated_video_lectures"] is not None
    ):
        if not isinstance(doc["associated_video_lectures"], list):
            errors.append(("associated_video_lectures", "must be a list", doc_id))
        else:
            for i, video in enumerate(doc["associated_video_lectures"]):
                if not isinstance(video, dict):
                    errors.append(
                        (
                            f"associated_video_lectures[{i}]",
                            "must be a dictionary",
                            doc_id,
                        )
                    )
                else:
                    video_errors = validate_associated_video_lecture(
                        video, doc_id, i, root_folder
                    )
                    errors.extend(video_errors)

    return errors


def validate_document_fields(
    doc: Dict[str, Any], root_folder: Path
) -> List[Tuple[str, str, int]]:
    """
    Validate document field values according to business rules.
    Returns list of tuples: (field_name, error_message, document_id)
    """
    errors = []
    doc_id = doc.get("id", "unknown")

    # "week" has to be an int or null
    if "week" in doc and doc["week"] is not None:
        if not isinstance(doc["week"], int):
            errors.append(
                (
                    "week",
                    f"must be an integer or null, got: {type(doc['week']).__name__}",
                    doc_id,
                )
            )

    # "number" and "sub_number" has to be a string or null
    for field in ["number", "sub_number"]:
        if field in doc and doc[field] is not None:
            if not isinstance(doc[field], str):
                errors.append(
                    (
                        field,
                        f"must be a string or null, got: {type(doc[field]).__name__}",
                        doc_id,
                    )
                )

    # "model" has to be "gemini-2.5-flash", "gemini-2.5-pro" or null
    if "model" in doc and doc["model"] is not None:
        valid_models = ["gemini-2.5-flash", "gemini-2.5-pro"]
        if doc["model"] not in valid_models:
            errors.append(
                (
                    "model",
                    f"must be one of {valid_models} or null, got: {doc['model']}",
                    doc_id,
                )
            )

    # when "subtype" is "video_lecture", "path" must end in "json" and "is_video" must be true
    if doc.get("subtype") == "video_lecture":
        if "path" in doc and doc["path"] is not None:
            if not doc["path"].endswith(".json"):
                errors.append(
                    (
                        "path",
                        "must end with '.json' when subtype is 'video_lecture'",
                        doc_id,
                    )
                )
        if "is_video" in doc and doc["is_video"] is not True:
            errors.append(
                ("is_video", "must be true when subtype is 'video_lecture'", doc_id)
            )

    # "from" and "until" has to be a string in format "09/09/2025" or null
    date_pattern = re.compile(r"^\d{2}/\d{2}/\d{4}$")
    for field in ["from", "until"]:
        if field in doc and doc[field] is not None:
            if not isinstance(doc[field], str):
                errors.append(
                    (field, "must be a string in format 'DD/MM/YYYY' or null", doc_id)
                )
            elif not date_pattern.match(doc[field]):
                errors.append(
                    (
                        field,
                        f"must be in format 'DD/MM/YYYY', got: {doc[field]}",
                        doc_id,
                    )
                )

    # "tikz" has to be false or null
    if "tikz" in doc and doc["tikz"] is not None and doc["tikz"] is not False:
        errors.append(("tikz", f"must be false or null, got: {doc['tikz']}", doc_id))

    # "title" can't have "_" characters
    if "title" in doc and doc["title"] is not None:
        if "_" in str(doc["title"]):
            errors.append(("title", "cannot contain underscore characters", doc_id))

    # if "subtype" is "book_in_bibliography" then "one_chunk_per_page" and "one_chunk_per_doc" has to be false
    if doc.get("subtype") == "book_in_bibliography":
        for field in ["one_chunk_per_page", "one_chunk_per_doc"]:
            if field in doc and doc[field] is not False:
                errors.append(
                    (
                        field,
                        "must be false when subtype is 'book_in_bibliography'",
                        doc_id,
                    )
                )

    # "processing_method" has to be "gemini", "tesseract", "google" or null
    if "processing_method" in doc and doc["processing_method"] is not None:
        valid_methods = ["gemini", "tesseract", "google"]
        if doc["processing_method"] not in valid_methods:
            errors.append(
                (
                    "processing_method",
                    f"must be one of {valid_methods} or null, got: {doc['processing_method']}",
                    doc_id,
                )
            )

    # "srt_path" has to be null or be a string that ends in ".srt"
    if "srt_path" in doc and doc["srt_path"] is not None:
        if not isinstance(doc["srt_path"], str) or not doc["srt_path"].endswith(".srt"):
            errors.append(("srt_path", "must be null or end with '.srt'", doc_id))

    # "original_link" has to be null or be a string that contains "mediaspace"
    if "original_link" in doc and doc["original_link"] is not None and doc["is_video"]:
        if not isinstance(doc["original_link"], str) or (
            "mediaspace" not in doc["original_link"]
            and "coursera" not in doc["original_link"]
            and "courseware" not in doc["original_link"]
            and "edx" not in doc["original_link"]
        ):
            errors.append(
                (
                    "original_link",
                    "must be null or contain 'mediaspace' or a MOOC platform",
                    doc_id,
                )
            )

    # if "is_gemini_processed_video" is true then "is_video" has to be true too
    if doc.get("is_gemini_processed_video") is True:
        if doc.get("is_video") is not True:
            errors.append(
                (
                    "is_video",
                    "must be true when is_gemini_processed_video is true",
                    doc_id,
                )
            )

        # if "is_gemini_processed_video" is true, validate JSON structure
        if "path" in doc and doc["path"] is not None:
            json_full_path = root_folder / doc["path"]
            if json_full_path.exists() and json_full_path.is_file():
                if not validate_gemini_json_structure(json_full_path):
                    errors.append(
                        ("path", "Gemini JSON file has invalid structure", doc_id)
                    )

    # validate associated_video_lectures structure
    if (
        "associated_video_lectures" in doc
        and doc["associated_video_lectures"] is not None
    ):
        if not isinstance(doc["associated_video_lectures"], list):
            errors.append(("associated_video_lectures", "must be a list", doc_id))
        else:
            for i, video in enumerate(doc["associated_video_lectures"]):
                if not isinstance(video, dict):
                    errors.append(
                        (
                            f"associated_video_lectures[{i}]",
                            "must be a dictionary",
                            doc_id,
                        )
                    )
                else:
                    video_errors = validate_associated_video_lecture(
                        video, doc_id, i, root_folder
                    )
                    errors.extend(video_errors)

    return errors


def extract_paths_from_document(doc: Dict[str, Any]) -> List[Tuple[str, str, int]]:
    """
    Extract all path attributes from a document.
    Returns list of tuples: (attribute_name, path_value, document_id)
    """
    paths = []
    doc_id = doc.get("id", "unknown")

    # Check main document paths
    path_attributes = ["path", "srt_path", "pdf_page_video_ts_path"]

    for attr in path_attributes:
        if attr in doc and doc[attr] is not None:
            paths.append((attr, doc[attr], doc_id))

    # Check associated video lectures
    if (
        "associated_video_lectures" in doc
        and doc["associated_video_lectures"] is not None
    ):
        for i, video in enumerate(doc["associated_video_lectures"]):
            video_path_attrs = ["path", "srt_path", "pdf_page_video_ts_path"]
            for attr in video_path_attrs:
                if attr in video and video[attr] is not None:
                    paths.append(
                        (f"associated_video_lectures[{i}].{attr}", video[attr], doc_id)
                    )

    return paths


def validate_json_file(
    json_file: Path, root_folder: Path
) -> Tuple[
    List[Tuple[str, str, int]], List[Tuple[str, str, int]], List[Tuple[str, str, int]]
]:
    """
    Validate all paths in a JSON file with exact case-sensitive checking.
    Returns: (valid_paths, invalid_paths, field_errors) with (attribute_name, path_value/error_message, document_id)
    """
    valid_paths = []
    invalid_paths = []
    field_errors = []

    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        if "documents" not in data:
            print(f"Warning: No 'documents' key found in {json_file}")
            return valid_paths, invalid_paths, field_errors

        for doc in data["documents"]:
            # Validate document fields -
            doc_field_errors = validate_document_fields(doc, root_folder)
            field_errors.extend(doc_field_errors)

            # Existing path validation
            paths_to_check = extract_paths_from_document(doc)

            for attr_name, path_value, doc_id in paths_to_check:
                # Construct full path relative to root folder
                full_path = root_folder / path_value
                filename = full_path.name

                folder_path_where_file_located = str(full_path.parent)
                all_files_in_dir = os.listdir(folder_path_where_file_located)
                if filename in all_files_in_dir:
                    valid_paths.append((attr_name, path_value, doc_id))
                else:
                    invalid_paths.append((attr_name, path_value, doc_id))

    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in file {json_file}: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error processing file {json_file}: {e}")
        sys.exit(1)
    return valid_paths, invalid_paths, field_errors


def main():
    parser = argparse.ArgumentParser(
        description="Validate file paths in JSON metadata files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "root_folder",
        type=str,
        help="Path to the root folder of the RAG course, containing metadata and content directories",
    )
    args = parser.parse_args()

    root_folder = Path(args.root_folder)

    if not root_folder.exists():
        print(f"Error: Root folder '{root_folder}' does not exist.")
        sys.exit(1)

    total_valid_paths = 0
    total_invalid_paths = 0
    total_field_errors = 0
    all_invalid_paths = []
    all_field_errors = []
    referenced_paths = set()
    types_set = set()
    subtypes_set = set()
    models_set = set()
    processing_methods_set = set()

    metadata_dir = root_folder / "metadata"

    for json_file in os.listdir(metadata_dir):
        if not json_file.endswith(".json"):
            continue

        json_file_path = metadata_dir / json_file

        try:
            with open(json_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            pass
        else:
            for doc in data.get("documents", []):
                if doc.get("type") is not None:
                    types_set.add(doc["type"])
                if doc.get("subtype") is not None:
                    subtypes_set.add(doc["subtype"])
                if doc.get("model") is not None:
                    models_set.add(doc["model"])
                if doc.get("processing_method") is not None:
                    processing_methods_set.add(doc["processing_method"])

        print(f"Validating: {json_file_path}")
        valid_paths, invalid_paths, field_errors = validate_json_file(
            json_file_path, root_folder
        )

        total_valid_paths += len(valid_paths)
        total_invalid_paths += len(invalid_paths)
        total_field_errors += len(field_errors)

        for attr_name, path_value, doc_id in invalid_paths:
            all_invalid_paths.append((json_file, doc_id, attr_name, path_value))

        # Collect field errors
        for field_name, error_message, doc_id in field_errors:
            all_field_errors.append((json_file, doc_id, field_name, error_message))

        # Record all referenced paths
        for attr_name, path_value, doc_id in valid_paths + invalid_paths:
            referenced_paths.add(path_value)

    print(f"\nTotal paths checked: {total_valid_paths + total_invalid_paths}")
    print(f"Number of valid paths: {total_valid_paths}")
    print(f"Number of invalid paths: {total_invalid_paths}")
    print(f"Number of field validation errors: {total_field_errors}")

    if all_invalid_paths:
        print("\nInvalid Paths:")
        for json_file, doc_id, attr_name, path_value in all_invalid_paths:
            print(f"File: {json_file}")
            print(f"  Document ID: {doc_id}")
            print(f"  Attribute: {attr_name}")
            print(f"  Path: {path_value}")
            print()
    else:
        print("All paths seem valid")

    if all_field_errors:
        print("\nField Validation Errors:")
        for json_file, doc_id, field_name, error_message in all_field_errors:
            print(f"File: {json_file}")
            print(f"  Document ID: {doc_id}")
            print(f"  Field: {field_name}")
            print(f"  Error: {error_message}")
            print()
    else:
        print("All document fields are valid")

    all_files = list_non_hidden_files(root_folder)

    unreferenced = []
    for f in all_files:
        if f not in referenced_paths and not f.startswith("metadata/"):
            unreferenced.append(f)

    print(f"\nTotal non-hidden files found: {len(all_files)}")
    print(
        f"Number of files referenced in metadata: {len(all_files) - len(unreferenced)}"
    )
    print(f"Number of files *not* referenced: {len(unreferenced)}")

    if unreferenced:
        print("\nUnreferenced Files:")
        for f in sorted(unreferenced):
            print(f"  {f}")
    else:
        print("All non-hidden files are referenced in the metadata!")

    print("\nMetadata Summary:")
    print(f"  Types: {', '.join(sorted(types_set))}")
    print(f"  Subtypes: {', '.join(sorted(subtypes_set))}")
    print(f"  Models: {', '.join(sorted(models_set))}")
    print(f"  Processing methods: {', '.join(sorted(processing_methods_set))}")


if __name__ == "__main__":
    main()
