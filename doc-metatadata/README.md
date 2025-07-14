
This document describes the JSON structure for RAG courses
For a complete example with sample data, see: (./rag_course_content_metadata_example.json) 

### Root Level Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `course_info` | object | Yes | General course information and metadata. See [Course Info Object](#course-info-object) |
| `documents` | array | Yes | Array of document objects representing course materials. See [Document Object](#document-object) |

### Course Info Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `course_title` | string | Yes | Full title of the course as it appears in the curriculum |
| `course_id` | string | Yes | Unique course identifier  |
| `academic_course` | string | Yes | Academic year in format "YYYY-YYYY" |
| `semester` | integer | Yes | Semester number (1 for fall, 2 for spring) |
| `admin_info_link` | string | No | URL to administrative information page |
| `coursebook_link` | string | No | URL to coursebook page |

### Document Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | integer | Yes | Unique identifier for the document within the course |
| `type` | string | Yes | Primary document category. Values: `theory`, `practice`, `exam`, `other` |
| `subtype` | string | No | Secondary categorization based on document type. See [Document Subtype Values](#document-subtype-values) for valid values per type |
| `is_solution` | boolean/null | No | Whether this document contains solutions. `null` for non-applicable documents |
| `is_qa` | boolean | Yes | Whether this document is a Q&A Ed Discussion metadata JSON file |
| `is_video` | boolean | Yes | Whether this document is a video file |
| `is_gemini_processed_video` | boolean | Yes | Whether the video has been processed by a Gemini model |
| `title` | string | Yes | Title of the document |
| `week` | integer | No | Course week number when document is relevant |
| `from` | string | Yes | Start date of document availability in DD/MM/YYYY format (inclusive) |
| `until` | string | Yes | End date of document availability in DD/MM/YYYY format (exclusive) |
| `number` | string | No | Used for practice documents: the number of the exercise, or if it's part of a series it will be the number of the series. |
| `sub_number` | string | No | Used for practice documents: the number of the exercise only if it's part of a series. When the series has parts e.g. Series 1, Part 2, Exercise 5, then sub_number will be "2.5" |
| `path` | string | No | File path for the document from the root folder  |
| `original_link` | string | No | URL to the original source of the document |
| `pipeline_link` | string | No | URL to processed version in the pipeline system |
| `srt_path` | string | No | File path to subtitle file (for video content) |
| `processing_method` | string | Yes | Method used to process the document. Values: `gemini`, `google`, `tesseract` |
| `model` | string | No | Specific Gemini model used for processing. Values: `gemini-2.5-pro`, `gemini-2.5-flash`, `gemini-2.0-flash`  |
| `one_chunk_per_page` | boolean | Yes | Whether the page is processed as one chunk |
| `one_chunk_per_doc` | boolean | Yes | Whether the full document is processed as one chunk |
| `associated_video_lectures` | array/null | No | Array of related video lectures. See [Video Lecture Object](#video-lecture-object) |

### Elements in associated_video_lectures 

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | Yes | Title of the video lecture |
| `is_gemini_processed_video` | boolean | Yes | Whether this video has been processed by a Gemini model |
| `original_link` | string | Yes | public URL of the video (on mediaspace) |
| `pipeline_link` | string | No | Set to `null` if `is_gemini_processed_video` is `false`. If it's `true` root file path to Gemini video processing JSON file   |
| `srt_path` | string | No | File path from root to the subtitle file. Set to `null` in case there is no subtitle |
| `pdf_page_video_ts_path` | string | No | File path from root to the PDF-video timestamp mapping file |


## Field Value Constraints

### Document Type Values
- `theory`: Theoretical content like lectures, slides, books
- `practice`: Practical content like exercises, labs, projects
- `exam`: Exams
- `other`: Other content

### Document Subtype Values
Each document type has specific allowed subtypes:
  - `theory`: lecture_slides, video_lecture, book_in_bibliography, lecture_notes, booc
  - `practice`: exercise, case_study, project, series, labs
  - `exam`: midterm_exam, mockup_exam, previous_year_exam
  - `other`: No subtypes defined yet (should be null)

#### Theory Subtype Descriptions
- `lecture_slides`: Presentation slides from lectures
- `video_lecture`: Recorded lecture videos
- `book_in_bibliography`: Referenced books from course bibliography
- `lecture_notes`: Written lecture notes and materials
- `booc`: BOOCs (Book and Open Online Courses) 

#### Practice Subtype Descriptions
- `exercise`: Practice exercises and problem sets
- `series`: Exercise series 
- `lab`: Exercises or assignments reffered to as lab sessions
- `project`: Course projects
- `case_study`: Exercises known as case studies

#### Exam Subtype Descriptions
- `midterm_exam`: Mid-semester exams
- `mockup_exam`: Practice/mock exams
- `previous_year_exam`: Exams from previous years


#### Other Subtypes
- Currently no defined subtypes for the "other" category


### Processing Method Values
- `tesseract`: Processed using Tesseract: For long less relevant PDFs without math
- `google`: Processed using Google Cloud Vision. Intermediate option. For documents with math
- `gemini`: Processed using Gemini models. For PDFs with math and critically important diagrams/figures

### Gemini models
- `gemini-2.5-pro`: Higher performing model.
- `gemini-2.5-flash`: More affordable model
- `gemini-2.0-flash`: Previous gen affordable model



## Notes
- All dates must be in DD/MM/YYYY format
- Document IDs must be unique but there will be skipped by Elastic Search
- Video documents should have `is_video` set to `true`
- If `is_solution` is `true`, the document contains the solution of the exercise or exam 
- If `associated_video_lectures` is present, it should be an array (it can be empty)
- Processing method is required for all documents
- Model field should be populated when processing_method is `gemini`
- Some fields may be `null` when not applicable (e.g., `week` for reference materials)
- Video documents typically have `path: null` and use `original_link` instead
- The `pipeline_link` points to the Google Drive or Sharepoint URL
- Documents can have multiple associated video lectures for supplementary content


