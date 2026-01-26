# Colored Logging Implementation

## Overview
Enhanced the NSE Scraper logging system with colored terminal output for better log readability and debugging experience.

## Problem Statement
The previous logging system had several issues:
- Duplicate timestamps on every log line (from both app and uvicorn)
- No visual distinction between different types of operations (API calls, DB operations, errors)
- Cluttered output making it hard to quickly identify important information
- Difficult to debug issues in production when monitoring logs

## Solution Implemented

### 1. **ColoredFormatter Class** (`Utils/logger.py`)
Added a custom formatter that applies ANSI colors to console output based on:

#### Log Level Colors:
- **DEBUG**: Cyan
- **INFO**: Green
- **WARNING**: Yellow  
- **ERROR**: Red
- **CRITICAL**: Bright Red

#### Module-Specific Colors:
- **API/Router/Controller**: Bright Blue (for API-related logs)
- **db/mongo**: Magenta (for database operations)
- **auth/firebase**: Bright Cyan (for authentication)
- **All others**: Default INFO color

### 2. **Key Features**
- **Console Only**: Colors only appear in terminal output
- **File Logs**: Plain text without ANSI codes for easier parsing
- **Graceful Fallback**: Works even if `colorama` package is missing
- **Cross-Platform**: Uses `colorama` for Windows compatibility
- **No Propagation**: Prevents duplicate logs by setting `logger.propagate = False`

### 3. **Files Modified**

#### `Utils/logger.py`
```python
# Added colorama imports with fallback
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False

# Created ColoredFormatter class
class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[1;31m', # Bright Red
    }
    
    # Special colors for specific module types
    MODULE_COLORS = {
        'api': '\033[1;34m',      # Bright Blue
        'db': '\033[35m',         # Magenta
        'auth': '\033[1;36m',     # Bright Cyan
    }
```

#### `main.py`
```python
# Reduced uvicorn logging verbosity
logging.getLogger("uvicorn").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
```

#### `requirements.txt` & `requirements.lite.txt`
```
colorama>=0.4.6
```

## Benefits

### Developer Experience
1. **Quick Error Identification**: Red errors immediately stand out
2. **API Call Tracking**: Blue bright logs show API/Router activity
3. **Database Operations**: Magenta logs distinguish DB operations
4. **Clean Output**: No more duplicate timestamps or cluttered logs
5. **Easy Debugging**: Visual separation makes log analysis faster

### Production Monitoring
- Easier to monitor Oracle VM logs via Docker
- Quickly identify errors when tailing logs
- Better distinction between different system components
- File logs remain plain text for log aggregation tools

## Usage

### Local Development
```bash
python main.py
```

Console output will show colored logs automatically.

### Docker Deployment
```bash
docker compose -f docker-compose.lite.txt logs -f
```

Colors will work in Docker terminal output (requires terminal with ANSI support).

### Viewing Specific Log Types
- Watch for errors: Red colored logs will stand out
- Track API calls: Look for bright blue colored module names (API.Controller.*, API.Router.*)
- Monitor DB operations: Magenta colored logs from Utils.db, Utils.mongo_client_master

## Testing

### Test Locally
1. Start the application:
   ```bash
   python main.py
   ```

2. Make API calls to see colored logs:
   ```bash
   curl http://localhost:1020/health
   curl http://localhost:1020/ipo/open
   ```

3. Observe colored output:
   - Green: INFO level logs (initialization messages)
   - Bright Blue: API/Router operations
   - Magenta: Database operations
   - Red: Any errors that occur

### Test in Production (Oracle VM)
1. SSH into the VM:
   ```bash
   ssh -i private-key.key ubuntu@161.118.180.210
   ```

2. Navigate to project and pull changes:
   ```bash
   cd ~/Stock-Market-Data
   git pull origin main
   ```

3. Rebuild and restart Docker container:
   ```bash
   docker compose -f docker-compose.lite.yml down
   docker compose -f docker-compose.lite.yml up -d --build
   ```

4. View colored logs:
   ```bash
   docker compose -f docker-compose.lite.yml logs -f --tail=50
   ```

## File Logs

Log files remain unchanged and contain plain text (no ANSI codes):
- `Logs/<module_name>.log`: All logs for that module
- `Logs/<module_name>_error.log`: Error logs only

This ensures log files can still be:
- Parsed by log aggregation tools
- Searched with grep/awk
- Processed by log analysis scripts
- Read by log viewers without ANSI escape code support

## Technical Details

### Color Implementation
- Uses ANSI escape codes (`\033[...m`) for colors
- `colorama` package handles Windows console compatibility
- Colors reset automatically after each log line
- Module detection uses lowercase matching on logger name

### Performance
- Minimal overhead (only affects string formatting)
- No impact on file logging (plain formatter used)
- Conditional color application based on module name

### Compatibility
- Works on Linux, Mac, Windows (via colorama)
- Docker terminal output supported
- SSH terminal sessions supported
- Falls back gracefully if colorama unavailable

## Future Enhancements

Potential improvements:
1. Add configuration option to disable colors
2. Custom color schemes via config.ini
3. More granular module-specific colors
4. Timestamp formatting customization
5. Log level filtering per module

## Related Documentation
- `docs/deployment_guide.md`: Deployment instructions
- `docs/ORACLE_CLOUD_DEPLOYMENT.md`: Oracle VM specific deployment
- `Utils/logger.py`: Logger implementation
- `config.ini`: Logging configuration options
