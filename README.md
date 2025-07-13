# tutor-bot-metadata-doc
Repository with metadata and config files from a Tutor Bot


# Project JSON Definitions

This repository contains several JSON datasets, each documented in its own folder.

## Available Definitions

| Folder                                | Description                                             |
|---------------------------------------|---------------------------------------------------------|
| [doc-metatadata](./doc-metatadata)      |  Example of metadata JSON file from a course.  |
| [doc-mapping-pdf-page-to-srt](./doc-mapping-pdf-page-to-srt)      |  Example JSON file that maps the page numbering of a PDF file with the subtitle timestamps of a video.  |
| [doc-mapping-exercise-numbering](./doc-mapping-exercise-numbering)      |  Example of a JSON file to map the numbering of the exercises from different editions of the course.  |
| [doc-inter-gemini-video](./doc-inter-gemini-video)      |  Example of gemini-based video preprocessing JSON file.  |


# RAG Course Folder Structure

```
COURSE Algebra/  
├── metadata/  
│   ├── algebra_metadata_general.json  
│   ├── algebra_metadata_week_1.json  
│   ├── algebra_metadata_week_2.json  
│   ├── algebra_metadata_qa_2024_theory_1.json  
│   ├── algebra_metadata_qa_2024_practice_1.json  
│   └── algebra_metadata_qa_2024_exam_1.json  
└── content/  
    ├── general/  
    │   ├── *.pdf  
    │   ├── *.txt  
    │   ├── *.c
    │   └── *.srt  
    ├── week 1/  
    │   ├── *.pdf  
    │   ├── *.txt  
    │   ├── *_mapping.json    
    │   └── *.srt  
    └── week 2/  
        ├── *.pdf  
        └── *.txt  
```


## Notes
- All JSON files in the metadata folder have the same structure
- Every metadata JSON file in the metadata folder, the IDs start by number 1
