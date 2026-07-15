## [1.0.0] - 2026-07-15

### 🚀 Features

- [**breaking**] Moved backup system to use a dedicated internal app directory
- Added confirm_to_recover_backup function that bundles confirmation prompting
- Implemented command-specific backup convention
- Implemented a `QualityControl` class that reports and exits with error code
- Added backup recover feature in `log-format`
- Added write safety features in `log-format`
- Implemented Quality Control context manager in `log-extend`
- Added `dataframe_confirm_inplace_modification_with_backup` function in io.csv
- Added QC context manager in `check-duplicates`
- Minimally implemented the `check-tz` command

### 🐛 Bug Fixes

- Updated `fix_timezone_issue` function to operate on a copy of the input dataframe instead of inplace
- Fixed circular import problem in `utils.paths` while fetching app name
## [0.1.0] - 2026-07-08

### 🚀 Features

- Updated `log-format` to add missing rows and have additional safety measures
- Updated `check-gaps` to run for single file
- Implemented `check-duplicates` command for timestamp duplication checks
- Added overwrite confirmation for --output in log-format
- Added `log-extend` command to be safely extending log master files with new data

### 🐛 Bug Fixes

- Fixed bug in `fix_timezone_issue`

### 📚 Documentation

- Improved documentation
## [0.0.1] - 2026-06-17

### 🐛 Bug Fixes

- Fixed bad argument definition in log_diff function signature that caused log-diff command to crush
## [0.0.0] - 2026-06-17

### 🚀 Features

- Hsieh model clean implementation
- Updated hsieh2d
- Added `Matlab73` class for reading .mat files
- Migrated meteo package from UAB repo
- Added `MatlabFluxDataFrame` class for table extraction from `.mat` files
- Added `transformations` pkg with outliers module
- Added `filling.py` module
- Added csv timeseries reader in fluxy.io
- Migrated basic functinality from `volt_conv2` function of matlab scripts
- Added timeseries file concatenation script
- Added xema variables mapper
- Added tz_offsets module for timeseries checks related to TZ issues
- Added radiation in column duplicates for XEMADataFrame to be used for gap filling
- Added master cli entry point for suite
- Updated csv concat script to be final met file builder before processing
- Implemented tz checks into build-metlog and proper logging // deployment-ready
- Implemented output option for naming ouput file
- Implemented config.yaml printing function
- Added config command for configuration related actions
- Added timestamp and record recovery workflows in `utils.conversions`
- Added year, doy, time column creation workflow
- Finished format-log command standalone implementation
- Updated met-build to prompt for TZ issue fixing
- Added functionality to look for timezone gaps of arbitrary length (not only 1 fix hour)
- Added print functionality to format-log command
- Added log-diff cli command for visualizing log-file differences

### 🐛 Bug Fixes

- Xema client checks for request status and raises error
- Corrected find_timeseries_gaps to give last 2x gap // TODO pass this effect into fix_timezone_issue
- Fixed `potential_timezone_issue` detector function to mark any overlap multiple of 4 (1 hour)
- Corrected timestamp recovery workflow for new time format (.5-24)
- Corrected add_year_doy_time func to format Time as float (.5-24)
- Fixed timezone issue correction function to run for periods with gaps
- Added explicit TIMESTAMP index check to avoid mystical errors
- Removed RECORD from drop_duplicates subset which could cause inconsistencies
