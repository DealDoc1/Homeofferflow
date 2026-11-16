# Saved offer PDF recovery on the production baseline

Candidate based on `d39d4d19d`. Ports the reviewed offer-print guard from
roadmap commit `95993b7a3`. Both unsigned and signed offer downloads now
check for an empty body and a missing PDF header before displaying the
preview. When the response is incomplete or mislabeled, the preview stays
closed and the original action becomes available again. A request that times
out or loses its session while reading the file cannot open the preview.
The local app shell is v195.

The offer-print browser runtime and 30 focused Python checks passed.
Fictional Chrome runs at 390px and 1280px exercised invalid responses,
visible recovery text, valid PDF preview and links, and focus restoration
after closing. Browser requests were intercepted and served from local
fixtures. Native printing and production are unverified. This candidate is
independent of the seller listing migration and SignWell QA packet.
