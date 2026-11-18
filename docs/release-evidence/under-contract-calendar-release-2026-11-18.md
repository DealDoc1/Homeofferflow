# Keep Under Contract calendar downloads compatible with long addresses

The calendar exporter folds lines at 75 UTF-8 bytes without splitting
characters and escapes entered line breaks. Each event now has its own
required timestamp. Event IDs, dates and all-day boundaries stay the
same for existing downloads.

The isolated candidate starts from `fcda998d` and advances the production
shell to v204. All 26 focused candidate checks and 35 primary-checkout
checks passed. Offline Chrome at 390px and 1280px exercised the timeline
form and actual download with a fictional offer and mocked storage.
The downloaded files passed byte-length, unfolded-text, timestamp,
event-count and date-boundary checks. Direct import into a calendar
application was not exercised.
