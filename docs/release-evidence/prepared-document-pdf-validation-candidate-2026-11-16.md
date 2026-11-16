# Prepared Documents PDF recovery

Candidate based on reviewed GitHub main `2dd915a2`. Ports the saved-document
validation from roadmap checkpoint `e9d7627f` to the current Prepared
Documents queue. Both Preview and Download completed PDF validate the
response media type, nonempty body and PDF header before opening or saving
it. Expired requests and results from a changed account are discarded, and
recoverable failures restore the original button. Existing API routes and
access rules remain in use. Local shell v196.

66 focused Python tests passed, including the wrapper for 19 prepared-viewer
runtime cases. Chrome at 390px and 1280px verified error guidance, retry,
a valid preview and print link, focus restoration, and that the completed
download matched the local public PDF fixture byte for byte. The browser
used fictional records and simulated responses. No hosted deployment,
database mutation, or signature invitation occurred.
