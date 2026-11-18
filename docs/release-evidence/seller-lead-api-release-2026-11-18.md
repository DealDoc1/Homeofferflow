# Save and open private seller leads from the listing workspace

The agent dashboard uses authenticated read and create actions to manage
seller and landlord leads. The server derives the owner, verifies active
brokerage membership when associating a brokerage, and returns only
the 12 recent rows and fields needed for the list. Production already
has the required table capabilities.

Preparing a listing workspace copies the saved property address and
seller name while preserving the agent's Sale or Lease selection.
The dashboard clears private lead data on account change, ignores stale
responses, and tells agents to refresh before retrying an uncertain save.

The candidate targets production revision `bd1a1aa0` and serves shell
v203. Focused API, listing and error-message checks passed. Offline
Chrome at 390px and 1280px verified address validation, save and handoff,
Lease selection, uncertain-save recovery, and account-switch isolation
with fictional leads.
