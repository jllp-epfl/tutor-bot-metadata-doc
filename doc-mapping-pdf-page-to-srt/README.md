# PDF-to-Video Timestamp Mapping

This JSON file defines a mapping from PDF page numbers to corresponding video lecture segments, so viewers can jump directly to the relevant part of the video for each PDF page.

## Structure

```json
[
  {
    "page_number": 1,
    "timestamps": [
      {
        "start_timestamp": "0:00:00.0",
        "end_timestamp":   "0:00:15.0"
      },
      {
        "start_timestamp": "0:00:24.33",
        "end_timestamp":   "0:00:25.48"
      }
    ]
  },
  {
    "page_number": 2,
    "timestamps": [
      {
        "start_timestamp": "0:00:24.0",
        "end_timestamp":   "0:01:45.0"
      }
    ]
  }
]
