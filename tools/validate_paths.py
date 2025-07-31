import json
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Any
import os


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
        sys.exit(1)
    except Exception as e:
        print(f"Error processing file {json_file}: {e}")
        sys.exit(1)
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
        valid_paths, invalid_paths = validate_json_file(json_file_path, root_folder)

        total_valid_paths += len(valid_paths)
        total_invalid_paths += len(invalid_paths)

        for attr_name, path_value, doc_id in invalid_paths:
            all_invalid_paths.append((json_file, doc_id, attr_name, path_value))

        # Record all referenced paths
        for attr_name, path_value, doc_id in valid_paths + invalid_paths:
            referenced_paths.add(path_value)

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
