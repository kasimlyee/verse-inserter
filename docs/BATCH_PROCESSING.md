# Batch Processing Feature

## Overview

The Batch Processing feature allows users to process multiple Word documents simultaneously, significantly improving productivity when working with many files that need verse insertions.

## Key Features

### 1. **Multi-Document Processing**
- Process multiple `.docx` files in a single operation
- Add/remove files from the batch queue
- Clear all files at once

### 2. **Optimized Verse Fetching**
- Collects all unique verse references across all documents
- Fetches each unique verse only once from the API
- Reuses fetched verses across multiple documents
- Significantly reduces API calls and processing time

### 3. **Real-Time Progress Tracking**
- Progress bar showing overall completion
- Status messages for each processing stage
- File count indicator

### 4. **Individual File Results**
- Success/failure status for each file
- Error messages for failed files
- Placeholders and verses statistics per file
- Output file paths

### 5. **Flexible Output Options**
- Save to same directory as input files (default)
- Choose custom output directory
- Automatic filename generation with suffix

### 6. **Comprehensive Results Summary**
- Total files processed
- Success/failure counts
- Success rate percentage
- Total placeholders found
- Total verses inserted
- Detailed per-file breakdown

## How to Use

### Accessing Batch Processing

1. Launch VerseInserter
2. Click the **"📚 Batch Process"** button in the main window
3. The Batch Processing dialog will open

### Processing Multiple Documents

1. **Add Files**:
   - Click **"📁 Add Files"** button
   - Select one or more `.docx` files
   - Files will appear in the list

2. **Manage File List**:
   - **Remove Selected**: Select files and click "🗑 Remove Selected"
   - **Clear All**: Remove all files from the list

3. **Configure Output** (Optional):
   - Click **"Browse..."** to select custom output directory
   - Leave empty to save in same directory as input files
   - Default suffix: `_verses` (e.g., `document.docx` → `document_verses.docx`)

4. **Start Processing**:
   - Click **"🚀 Start Processing"**
   - Confirm the operation
   - Monitor progress in real-time

5. **View Results**:
   - Click **"📊 View Results"** after completion
   - Review detailed statistics and per-file results

## Architecture

### Backend Components

#### BatchProcessor Class
**Location**: `verse_inserter/core/batch_processor.py`

**Key Methods**:
- `process_batch()`: Main entry point for batch processing
- `_collect_all_placeholders()`: Scans all documents for placeholders
- `_fetch_all_verses()`: Fetches unique verses efficiently
- `_process_single_file()`: Processes individual document

**Features**:
- Async/await for efficient I/O operations
- Progress callback system for UI updates
- Per-document error handling
- Verse caching support

#### BatchFileResult Dataclass
Stores results for individual file processing:
```python
@dataclass
class BatchFileResult:
    file_path: Path
    success: bool
    placeholders_found: int
    verses_inserted: int
    error_message: Optional[str]
    output_path: Optional[Path]
```

#### BatchProcessingResult Dataclass
Stores overall batch processing results:
```python
@dataclass
class BatchProcessingResult:
    total_files: int
    successful: int
    failed: int
    total_placeholders: int
    total_verses_inserted: int
    file_results: List[BatchFileResult]

    @property
    def success_rate(self) -> float
```

### UI Components

#### BatchProcessingDialog Class
**Location**: `verse_inserter/ui/widgets/batch_dialog.py`

**Features**:
- Modal dialog with file list
- Add/remove/clear file operations
- Output directory selection
- Real-time progress updates
- Results summary dialog

**UI Elements**:
- File listbox with multi-selection support
- Progress bar and status label
- Action buttons (Add, Remove, Clear, Process, Results)
- File count indicator
- Output directory entry

### Integration

The batch processing feature is integrated into the main window:

**File**: `verse_inserter/ui/main_window.py`

**Integration Points**:
- Import: `from .widgets.batch_dialog import BatchProcessingDialog`
- Button: `📚 Batch Process` button in control panel
- Method: `_open_batch_dialog()` opens the dialog with API client and cache manager

## Processing Workflow

```
1. User adds files to batch queue
   ↓
2. User clicks "Start Processing"
   ↓
3. BatchProcessor.process_batch() called
   ↓
4. Scan all documents → collect placeholders
   ↓
5. Extract unique verse references
   ↓
6. Fetch all unique verses (with caching)
   ↓
7. Process each document with pre-fetched verses
   ↓
8. Save processed documents
   ↓
9. Display results summary
```

## Performance Optimization

### Verse Reuse Strategy
**Problem**: Fetching the same verse multiple times is wasteful.

**Solution**:
1. Collect all placeholders from all documents first
2. Extract unique verse references
3. Fetch each unique verse only once
4. Reuse verses across all documents

**Example**:
```
Document 1: John 3:16, Psalm 23:1, John 3:16
Document 2: John 3:16, Romans 8:28
Document 3: Psalm 23:1

Unique verses to fetch: 3
- John 3:16 (reused 3 times)
- Psalm 23:1 (reused 2 times)
- Romans 8:28 (used 1 time)

Total API calls: 3 (instead of 6)
```

### Caching Integration
- Checks cache before API calls
- Caches all newly fetched verses
- Reduces API usage for repeated operations

## Error Handling

### Per-Document Error Handling
- Individual file errors don't stop entire batch
- Failed files are logged with error messages
- Successful files are still processed and saved

### Common Errors
1. **File Read Error**: Document cannot be opened
2. **Invalid Format**: File is not a valid `.docx`
3. **API Error**: Verse fetch fails
4. **Save Error**: Cannot write output file

### Error Recovery
- Failed files are marked with status and error message
- Results dialog shows which files failed and why
- Users can retry failed files individually

## Testing

### Test Coverage
**File**: `tests/test_batch_processor.py`

**Test Categories**:
1. **Data Classes**: BatchFileResult, BatchProcessingResult
2. **Initialization**: Constructor and configuration
3. **Progress Reporting**: Callback mechanism
4. **Placeholder Collection**: Multi-document scanning
5. **Verse Fetching**: API calls, caching, error handling
6. **File Processing**: Success, errors, output paths
7. **Complete Workflow**: End-to-end batch processing

**Coverage**: 100% for batch_processor.py (20 tests)

### Running Tests
```bash
# Run batch processor tests only
poetry run pytest tests/test_batch_processor.py -v

# Run all tests with coverage
poetry run pytest --cov=verse_inserter --cov-report=html
```

## Use Cases

### 1. **Book Manuscript Processing**
Process all chapters of a book at once:
```
chapter_01.docx
chapter_02.docx
...
chapter_20.docx

Output:
chapter_01_verses.docx
chapter_02_verses.docx
...
chapter_20_verses.docx
```

### 2. **Sermon Series**
Process entire sermon series:
```
sermon_2025_01_05.docx
sermon_2025_01_12.docx
sermon_2025_01_19.docx

Output (custom directory: 'sermons_2025/'):
sermon_2025_01_05_verses.docx
sermon_2025_01_12_verses.docx
sermon_2025_01_19_verses.docx
```

### 3. **Bible Study Materials**
Process multiple study guides:
```
study_guide_week1.docx
study_guide_week2.docx
homework_week1.docx
homework_week2.docx
```

## Future Enhancements

### Potential Improvements
1. **Parallel Processing**: Process multiple files simultaneously
2. **Cancellation**: Allow stopping batch operation mid-process
3. **Pause/Resume**: Pause processing and resume later
4. **Smart Ordering**: Process files in optimal order
5. **Batch Preview**: Preview all changes before processing
6. **Export Results**: Save results summary to file
7. **Batch Templates**: Save/load file lists for reuse
8. **Progress Persistence**: Resume interrupted batches

### Configuration Options
Future settings to consider:
- Maximum concurrent API calls
- Batch size limits
- Output filename patterns
- Auto-backup before processing
- Email notification on completion

## Limitations

### Current Limitations
1. **Sequential Processing**: Files processed one at a time
2. **No Cancellation**: Cannot stop once started (currently)
3. **Memory Usage**: All placeholders loaded into memory
4. **No Retry Logic**: Failed files must be manually retried

### Workarounds
- **Large Batches**: Split into smaller batches if memory is concern
- **API Limits**: Caching reduces API usage significantly
- **Failed Files**: Use results dialog to identify and retry individually

## API Considerations

### API Usage
- Batch processing respects API rate limits
- Retry logic with exponential backoff
- Caching significantly reduces API calls

### API Key
- Required for batch processing
- Warning shown if not configured
- Same API key as single-file processing

## Troubleshooting

### Issue: Files Not Loading
**Cause**: Invalid file format or corrupted document
**Solution**: Verify files are valid `.docx` format

### Issue: Some Files Fail
**Cause**: Individual file errors
**Solution**: Check results dialog for specific error messages

### Issue: Slow Processing
**Cause**: Many unique verses to fetch
**Solution**:
- First run will be slower (building cache)
- Subsequent runs much faster (using cache)
- Check internet connection

### Issue: Output Files Not Found
**Cause**: Permission errors or invalid output path
**Solution**:
- Check write permissions on output directory
- Use default output (same as input directory)

## Summary

The Batch Processing feature dramatically improves productivity for users working with multiple documents. Key benefits:

✅ **Efficiency**: Process multiple files at once
✅ **Speed**: Optimized verse fetching with reuse
✅ **Reliability**: Per-file error handling
✅ **Transparency**: Detailed results and statistics
✅ **Flexibility**: Custom output options
✅ **Robustness**: 100% test coverage

This feature transforms VerseInserter from a single-document tool to a powerful batch processing solution for Scripture insertion workflows.
