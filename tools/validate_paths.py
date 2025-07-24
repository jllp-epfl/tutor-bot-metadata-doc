import json
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Any
import os


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
) -> Tuple[List[Tuple[str, str, int]], List[Tuple[str, str, int]]]:
    """
    Validate all paths in a JSON file with exact case-sensitive checking.
    Returns: (valid_paths, invalid_paths) with (attribute_name, path_value, document_id)
    """
    valid_paths = []
    invalid_paths = []

    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        if "documents" not in data:
            print(f"Warning: No 'documents' key found in {json_file}")
            return valid_paths, invalid_paths

        for doc in data["documents"]:
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
    except Exception as e:
        print(f"Error processing file {json_file}: {e}")

    return valid_paths, invalid_paths


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
    all_invalid_paths = []

    metadata_dir = root_folder / "metadata"

    # for json_file in json_files:
    for json_file in os.listdir(metadata_dir):
        if not json_file.endswith(".json"):
            continue

        json_file_path = metadata_dir / json_file

        print(f"Validating: {json_file_path}")
        valid_paths, invalid_paths = validate_json_file(json_file_path, root_folder)

        total_valid_paths += len(valid_paths)
        total_invalid_paths += len(invalid_paths)

        for attr_name, path_value, doc_id in invalid_paths:
            all_invalid_paths.append((json_file, doc_id, attr_name, path_value))

    print(f"\nTotal paths checked: {total_valid_paths + total_invalid_paths}")
    print(f"Number of valid paths: {total_valid_paths}")
    print(f"Number of invalid paths: {total_invalid_paths}")

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


if __name__ == "__main__":
    main()
