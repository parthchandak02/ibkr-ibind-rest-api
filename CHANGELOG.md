# Changelog

All notable changes to this project will be documented in this file.

## [1.1.0] - 2025-04-07

### Added
- Proper pagination support for positions (fixes 100 position limit)
- New `/positions` endpoint with pagination support
- New `/positions/csv` endpoint for exporting all positions to CSV
- Development mode with `dev.py` script for faster iterations
- Updated documentation with clearer examples

### Fixed
- Fixed pagination issue where only first 100 positions were returned
- Improved CSV export with proper formatting and calculations
- Added better error handling for API responses

### Changed
- Updated Docker Compose configuration to allow for easier development
- Improved logging for debugging

## [1.0.0] - 2025-03-20

### Added
- Initial release of the IBKR REST API
- Support for paper and live trading environments
- Order placement and management
- Account information retrieval
- Basic position data
